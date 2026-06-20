from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

from fastapi.encoders import jsonable_encoder
from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session

from app.models.backtest_result import BacktestResult
from app.schemas.backtest import (
    BACKTEST_WARNING,
    BacktestMetrics,
    BacktestRequest,
    BacktestResponse,
    BacktestSummaryResponse,
    BacktestTrade,
)
from app.services.candle_service import get_saved_candles_by_date_range
from app.services.ict_engine import analyze_ict_setup
from app.services.mt5_service import validate_symbol, validate_timeframe

MIN_ROLLING_WINDOW = 50
ROLLING_WINDOW = 120
MAX_HOLDING_CANDLES = {"M1": 120, "M5": 96, "M15": 64, "H1": 48, "H4": 30, "D1": 20}


@dataclass(frozen=True)
class TradeCandidate:
    signal_index: int
    signal_time: datetime
    symbol: str
    timeframe: str
    direction: str
    entry_low: float
    entry_high: float
    stop_loss: float
    take_profit: float
    setup_score: int
    setup_type: str
    reason: str


def run_backtest(db: Session, request: BacktestRequest) -> BacktestResponse:
    """Run a historical ICT backtest and persist the result."""
    symbol = validate_symbol(request.symbol)
    timeframe = validate_timeframe(request.timeframe)
    candles = get_saved_candles_by_date_range(
        db, symbol, timeframe, request.start_date, request.end_date
    )
    if len(candles) < MIN_ROLLING_WINDOW + 2:
        raise ValueError(
            f"Not enough candles for backtest. Need at least {MIN_ROLLING_WINDOW + 2}, "
            f"found {len(candles)}."
        )

    candidates = generate_ict_trade_candidates(
        candles, symbol, timeframe, request.min_score
    )
    trades: list[BacktestTrade] = []
    next_available_index = 0

    for candidate in candidates:
        if candidate.signal_index < next_available_index:
            continue

        candles_after_signal = candles[candidate.signal_index + 1 :]
        trade = simulate_trade(candles_after_signal, candidate)
        if trade is None:
            continue
        if request.session_filter and trade.session != request.session_filter:
            continue

        trades.append(trade)
        next_available_index = candidate.signal_index + 1 + _trade_duration(
            candles_after_signal, trade.exit_time
        )

    metrics = calculate_metrics(trades)
    saved = save_backtest_result(db, request, symbol, timeframe, trades, metrics)
    return BacktestResponse(
        id=saved.id,
        name=request.name,
        symbol=symbol,
        timeframe=timeframe,
        strategy_name=request.strategy_name,
        start_date=request.start_date,
        end_date=request.end_date,
        warning=BACKTEST_WARNING,
        metrics=metrics,
        trades=trades,
    )


def generate_ict_trade_candidates(
    candles: list[object],
    symbol: str,
    timeframe: str,
    min_score: int,
) -> list[TradeCandidate]:
    """Generate signals from rolling historical windows without future candles."""
    candidates: list[TradeCandidate] = []
    for index in range(MIN_ROLLING_WINDOW, len(candles) - 1):
        window_start = max(0, index - ROLLING_WINDOW + 1)
        analysis = analyze_ict_setup(candles[window_start : index + 1], symbol, timeframe)
        if analysis.score < min_score or analysis.bias not in {"bullish", "bearish"}:
            continue
        if not analysis.entry_zone or analysis.stop_loss is None or analysis.take_profit is None:
            continue

        entry_low = float(analysis.entry_zone["low"])
        entry_high = float(analysis.entry_zone["high"])
        if entry_low > entry_high:
            entry_low, entry_high = entry_high, entry_low

        candidates.append(
            TradeCandidate(
                signal_index=index,
                signal_time=candles[index].time,
                symbol=symbol,
                timeframe=timeframe,
                direction=analysis.bias,
                entry_low=entry_low,
                entry_high=entry_high,
                stop_loss=float(analysis.stop_loss),
                take_profit=float(analysis.take_profit),
                setup_score=analysis.score,
                setup_type=analysis.setup_type,
                reason="ICT setup met minimum score using candles available at signal time.",
            )
        )
    return candidates


def simulate_trade(
    candles_after_signal: list[object],
    candidate: TradeCandidate,
) -> BacktestTrade | None:
    """Simulate one trade after a signal; same-candle SL/TP resolves to SL first."""
    max_holding = MAX_HOLDING_CANDLES.get(candidate.timeframe, 96)
    entry_price: float | None = None
    entry_time: datetime | None = None
    observed = candles_after_signal[:max_holding]
    if not observed:
        return None

    for offset, candle in enumerate(observed):
        if candle.low <= candidate.entry_high and candle.high >= candidate.entry_low:
            entry_price = (candidate.entry_low + candidate.entry_high) / 2
            entry_time = candle.time
            post_entry = observed[offset:]
            break
    else:
        return None

    result = "breakeven"
    exit_price = observed[-1].close
    exit_time = observed[-1].time

    for candle in post_entry:
        if candidate.direction == "bullish":
            if candle.low <= candidate.stop_loss:
                result, exit_price, exit_time = "loss", candidate.stop_loss, candle.time
                break
            if candle.high >= candidate.take_profit:
                result, exit_price, exit_time = "win", candidate.take_profit, candle.time
                break
        else:
            if candle.high >= candidate.stop_loss:
                result, exit_price, exit_time = "loss", candidate.stop_loss, candle.time
                break
            if candle.low <= candidate.take_profit:
                result, exit_price, exit_time = "win", candidate.take_profit, candle.time
                break

    risk = _risk(candidate.direction, entry_price, candidate.stop_loss)
    reward = _reward(candidate.direction, entry_price, candidate.take_profit)
    if risk <= 0 or reward <= 0:
        return None

    r_multiple = calculate_trade_r_multiple(
        candidate.direction,
        entry_price,
        candidate.stop_loss,
        candidate.take_profit,
        exit_price,
        result,
    )
    if result == "breakeven" and abs(r_multiple) >= 0.01:
        result = "win" if r_multiple > 0 else "loss"

    return BacktestTrade(
        entry_time=entry_time,
        exit_time=exit_time,
        symbol=candidate.symbol,
        timeframe=candidate.timeframe,
        session=detect_trade_session(entry_time),
        direction=candidate.direction,
        entry_price=round(entry_price, 5),
        stop_loss=round(candidate.stop_loss, 5),
        take_profit=round(candidate.take_profit, 5),
        risk=round(risk, 5),
        reward=round(reward, 5),
        rr=round(reward / risk, 2),
        result=result,
        r_multiple=round(r_multiple, 2),
        setup_score=candidate.setup_score,
        setup_type=candidate.setup_type,
        reason=candidate.reason,
    )


def calculate_trade_r_multiple(
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    exit_price: float,
    result: str,
) -> float:
    risk = _risk(direction, entry_price, stop_loss)
    reward = _reward(direction, entry_price, take_profit)
    if risk <= 0:
        return 0
    if result == "win":
        return reward / risk
    if result == "loss":
        return -1
    profit_or_loss = (
        exit_price - entry_price if direction == "bullish" else entry_price - exit_price
    )
    return profit_or_loss / risk


def calculate_metrics(trades: list[BacktestTrade]) -> BacktestMetrics:
    total = len(trades)
    wins = sum(1 for trade in trades if trade.result == "win")
    losses = sum(1 for trade in trades if trade.result == "loss")
    breakeven = sum(1 for trade in trades if trade.result == "breakeven")
    r_values = [trade.r_multiple for trade in trades]
    rr_values = [trade.rr for trade in trades]
    gross_profit = sum(value for value in r_values if value > 0)
    gross_loss = abs(sum(value for value in r_values if value < 0))
    net_r = sum(r_values)

    return BacktestMetrics(
        total_trades=total,
        winning_trades=wins,
        losing_trades=losses,
        breakeven_trades=breakeven,
        win_rate=round((wins / total) * 100, 2) if total else 0,
        loss_rate=round((losses / total) * 100, 2) if total else 0,
        average_r=round(net_r / total, 2) if total else 0,
        average_rr=round(sum(rr_values) / total, 2) if total else 0,
        profit_factor=round(gross_profit / gross_loss, 2) if gross_loss else round(gross_profit, 2),
        max_drawdown=round(_max_drawdown(r_values), 2),
        net_r=round(net_r, 2),
        expectancy=round(net_r / total, 2) if total else 0,
        best_session=_best_group(trades, "session"),
        best_symbol=_best_group(trades, "symbol"),
        best_timeframe=_best_group(trades, "timeframe"),
    )


def detect_trade_session(
    entry_time: datetime,
    timezone: str = "Asia/Phnom_Penh",
) -> str:
    local_time = entry_time.astimezone(ZoneInfo(timezone)).time()
    if time(19, 0) <= local_time < time(22, 0):
        return "Overlap"
    if time(6, 0) <= local_time < time(14, 0):
        return "Asia"
    if time(14, 0) <= local_time < time(22, 0):
        return "London"
    if local_time >= time(19, 0) or local_time < time(3, 0):
        return "New York"
    return "Unknown"


def save_backtest_result(
    db: Session,
    request: BacktestRequest,
    symbol: str,
    timeframe: str,
    trades: list[BacktestTrade],
    metrics: BacktestMetrics,
) -> BacktestResult:
    result = BacktestResult(
        name=request.name,
        symbol=symbol,
        timeframe=timeframe,
        strategy_name=request.strategy_name,
        start_date=request.start_date,
        end_date=request.end_date,
        total_trades=metrics.total_trades,
        winning_trades=metrics.winning_trades,
        losing_trades=metrics.losing_trades,
        win_rate=metrics.win_rate,
        average_r=metrics.average_r,
        average_rr=metrics.average_rr,
        profit_factor=metrics.profit_factor,
        max_drawdown=metrics.max_drawdown,
        net_r=metrics.net_r,
        best_session=metrics.best_session,
        best_symbol=metrics.best_symbol,
        best_timeframe=metrics.best_timeframe,
        raw_trades=jsonable_encoder(trades),
        metrics=jsonable_encoder(metrics),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_backtest_summaries(
    db: Session,
    symbol: str | None = None,
    timeframe: str | None = None,
    strategy_name: str | None = None,
    limit: int = 20,
) -> list[BacktestSummaryResponse]:
    statement: Select[tuple[BacktestResult]] = select(BacktestResult)
    if symbol:
        statement = statement.where(BacktestResult.symbol == validate_symbol(symbol))
    if timeframe:
        statement = statement.where(BacktestResult.timeframe == validate_timeframe(timeframe))
    if strategy_name:
        statement = statement.where(BacktestResult.strategy_name == strategy_name)

    statement = statement.order_by(BacktestResult.created_at.desc()).limit(limit)
    return [BacktestSummaryResponse.model_validate(item, from_attributes=True) for item in db.scalars(statement)]


def get_backtest_result(db: Session, result_id: int) -> BacktestResponse | None:
    result = db.get(BacktestResult, result_id)
    if result is None:
        return None
    return BacktestResponse(
        id=result.id,
        name=result.name,
        symbol=result.symbol,
        timeframe=result.timeframe,
        strategy_name=result.strategy_name,
        start_date=result.start_date,
        end_date=result.end_date,
        warning=BACKTEST_WARNING,
        metrics=BacktestMetrics.model_validate(result.metrics),
        trades=[BacktestTrade.model_validate(trade) for trade in result.raw_trades],
    )


def delete_backtest_result(db: Session, result_id: int) -> bool:
    statement = delete(BacktestResult).where(BacktestResult.id == result_id)
    result = db.execute(statement)
    db.commit()
    return bool(result.rowcount)


def _risk(direction: str, entry_price: float, stop_loss: float) -> float:
    return entry_price - stop_loss if direction == "bullish" else stop_loss - entry_price


def _reward(direction: str, entry_price: float, take_profit: float) -> float:
    return take_profit - entry_price if direction == "bullish" else entry_price - take_profit


def _max_drawdown(r_values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in r_values:
        equity += value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)
    return max_drawdown


def _best_group(trades: list[BacktestTrade], field: str) -> str | None:
    grouped: dict[str, float] = defaultdict(float)
    counts = Counter()
    for trade in trades:
        key = str(getattr(trade, field))
        grouped[key] += trade.r_multiple
        counts[key] += 1
    if not grouped:
        return None
    return max(grouped, key=lambda key: (grouped[key], counts[key]))


def _trade_duration(candles_after_signal: list[object], exit_time: datetime) -> int:
    for index, candle in enumerate(candles_after_signal, start=1):
        if candle.time == exit_time:
            return index
    return 1
