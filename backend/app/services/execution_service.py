from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.trade_execution import TradeExecution
from app.schemas.execution import ExecuteSignalRequest, TradeExecutionResponse
from app.schemas.ict import ICTAnalysisResponse
from app.services import mt5_service
from app.services.mt5_service import MT5ConnectionError, MT5DataError


class TradingDisabledError(RuntimeError):
    pass


class TradeValidationError(ValueError):
    pass


def get_execution_status() -> dict[str, Any]:
    return {
        "trading_enabled": settings.TRADING_ENABLED,
        "trading_mode": settings.TRADING_MODE,
        "auto_execute_signals": settings.AUTO_EXECUTE_SIGNALS,
        "mt5_status": mt5_service.get_market_status(),
    }


def execute_signal_request(
    db: Session,
    request: ExecuteSignalRequest,
) -> TradeExecutionResponse:
    return execute_ict_signal(
        db=db,
        analysis=request.analysis,
        account_balance=request.account_balance,
        risk_percent=request.risk_percent,
        comment=request.comment,
    )


def execute_ict_signal(
    db: Session,
    analysis: ICTAnalysisResponse,
    account_balance: float | None = None,
    risk_percent: float | None = None,
    comment: str = "Smart Trading AI signal",
) -> TradeExecutionResponse:
    _validate_trading_enabled()
    _validate_signal(analysis)

    mt5_service.initialize_mt5()
    mt5 = mt5_service.mt5
    if mt5 is None:
        raise MT5ConnectionError("MetaTrader5 package is not installed.")

    symbol = mt5_service.validate_symbol(analysis.symbol)
    if not mt5.symbol_select(symbol, True):
        code, message = mt5.last_error()
        raise MT5DataError(f"Symbol '{symbol}' is not available in MT5: {code} {message}")

    account = mt5.account_info()
    if account is None:
        code, message = mt5.last_error()
        raise MT5ConnectionError(f"MT5 account is not available: {code} {message}")
    _validate_account_mode(mt5, account)

    tick = mt5.symbol_info_tick(symbol)
    symbol_info = mt5.symbol_info(symbol)
    if tick is None or symbol_info is None:
        code, message = mt5.last_error()
        raise MT5DataError(f"MT5 symbol info is not available: {code} {message}")

    direction = analysis.bias.lower()
    order_type = mt5.ORDER_TYPE_BUY if direction == "bullish" else mt5.ORDER_TYPE_SELL
    price = float(tick.ask if direction == "bullish" else tick.bid)
    stop_loss = float(analysis.stop_loss)
    take_profit = float(analysis.take_profit)
    risk_value = _resolve_risk_percent(risk_percent)
    balance = float(account_balance if account_balance is not None else account.balance)

    _validate_price_levels(direction, price, stop_loss, take_profit)
    volume = _calculate_volume(
        balance=balance,
        risk_percent=risk_value,
        entry_price=price,
        stop_loss=stop_loss,
        symbol_info=symbol_info,
    )

    order_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": settings.EXECUTION_DEVIATION_POINTS,
        "magic": settings.EXECUTION_MAGIC_NUMBER,
        "comment": comment[:31],
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(order_request)
    response_payload = _mt5_result_to_dict(result)
    success = result is not None and result.retcode in {
        mt5.TRADE_RETCODE_DONE,
        mt5.TRADE_RETCODE_PLACED,
    }
    message = response_payload.get("comment") or response_payload.get("retcode_external")

    execution = TradeExecution(
        symbol=symbol,
        timeframe=analysis.timeframe,
        direction=direction,
        volume=volume,
        entry_price=price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_percent=risk_value,
        score=analysis.score,
        status="sent" if success else "rejected",
        mt5_order=response_payload.get("order"),
        mt5_deal=response_payload.get("deal"),
        mt5_retcode=response_payload.get("retcode"),
        message=str(message) if message is not None else None,
        raw_request=jsonable_encoder(order_request),
        raw_response=jsonable_encoder(response_payload),
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    return _to_response(execution)


def get_recent_executions(db: Session, limit: int = 50) -> list[TradeExecutionResponse]:
    statement = select(TradeExecution).order_by(TradeExecution.created_at.desc()).limit(limit)
    return [_to_response(item) for item in db.scalars(statement).all()]


def _validate_trading_enabled() -> None:
    if not settings.TRADING_ENABLED:
        raise TradingDisabledError(
            "Trading execution is disabled. Set TRADING_ENABLED=true only after demo testing."
        )


def _validate_signal(analysis: ICTAnalysisResponse) -> None:
    if analysis.score < settings.EXECUTION_MIN_SCORE:
        raise TradeValidationError(
            f"Signal score {analysis.score} is below EXECUTION_MIN_SCORE {settings.EXECUTION_MIN_SCORE}."
        )
    if analysis.bias not in {"bullish", "bearish"}:
        raise TradeValidationError("Only bullish or bearish ICT signals can be executed.")
    if analysis.stop_loss is None or analysis.take_profit is None:
        raise TradeValidationError("Signal must include stop_loss and take_profit.")


def _validate_account_mode(mt5: Any, account: Any) -> None:
    mode = settings.TRADING_MODE.lower()
    if mode not in {"demo", "live"}:
        raise TradeValidationError("TRADING_MODE must be either 'demo' or 'live'.")
    if mode == "demo" and hasattr(mt5, "ACCOUNT_TRADE_MODE_DEMO"):
        if account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            raise TradingDisabledError(
                "TRADING_MODE=demo but the connected MT5 account is not a demo account."
            )


def _resolve_risk_percent(value: float | None) -> float:
    risk_percent = float(value if value is not None else settings.EXECUTION_RISK_PERCENT)
    if risk_percent <= 0:
        raise TradeValidationError("Risk percent must be greater than zero.")
    if risk_percent > settings.EXECUTION_MAX_RISK_PERCENT:
        raise TradeValidationError(
            f"Risk percent {risk_percent} exceeds EXECUTION_MAX_RISK_PERCENT "
            f"{settings.EXECUTION_MAX_RISK_PERCENT}."
        )
    return risk_percent


def _validate_price_levels(
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
) -> None:
    if direction == "bullish" and not (stop_loss < entry_price < take_profit):
        raise TradeValidationError(
            "Skipped bullish execution because current market price is outside the signal range: "
            f"stop_loss={stop_loss}, entry_price={entry_price}, take_profit={take_profit}."
        )
    if direction == "bearish" and not (take_profit < entry_price < stop_loss):
        raise TradeValidationError(
            "Skipped bearish execution because current market price is outside the signal range: "
            f"take_profit={take_profit}, entry_price={entry_price}, stop_loss={stop_loss}."
        )


def _calculate_volume(
    balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss: float,
    symbol_info: Any,
) -> float:
    risk_amount = balance * (risk_percent / 100)
    price_risk = abs(entry_price - stop_loss)
    tick_size = float(getattr(symbol_info, "trade_tick_size", 0) or 0)
    tick_value = float(getattr(symbol_info, "trade_tick_value", 0) or 0)
    if price_risk <= 0 or tick_size <= 0 or tick_value <= 0:
        raise TradeValidationError("Cannot calculate lot size from MT5 symbol tick settings.")

    loss_per_lot = (price_risk / tick_size) * tick_value
    raw_volume = risk_amount / loss_per_lot
    volume_min = float(getattr(symbol_info, "volume_min", 0.01) or 0.01)
    volume_max = float(getattr(symbol_info, "volume_max", raw_volume) or raw_volume)
    volume_step = float(getattr(symbol_info, "volume_step", 0.01) or 0.01)

    volume = max(volume_min, min(volume_max, raw_volume))
    steps = round(volume / volume_step)
    normalized = steps * volume_step
    return round(max(volume_min, min(volume_max, normalized)), 8)


def _mt5_result_to_dict(result: Any) -> dict[str, Any]:
    if result is None:
        code, message = mt5_service.mt5.last_error() if mt5_service.mt5 else (None, "unknown")
        return {"retcode": code, "comment": message}
    if hasattr(result, "_asdict"):
        payload = result._asdict()
        if "request" in payload and hasattr(payload["request"], "_asdict"):
            payload["request"] = payload["request"]._asdict()
        return payload
    return {"comment": str(result)}


def _to_response(execution: TradeExecution) -> TradeExecutionResponse:
    return TradeExecutionResponse(
        id=execution.id,
        symbol=execution.symbol,
        timeframe=execution.timeframe,
        direction=execution.direction,
        volume=execution.volume,
        entry_price=execution.entry_price,
        stop_loss=execution.stop_loss,
        take_profit=execution.take_profit,
        risk_percent=execution.risk_percent,
        score=execution.score,
        status=execution.status,
        mt5_order=execution.mt5_order,
        mt5_deal=execution.mt5_deal,
        mt5_retcode=execution.mt5_retcode,
        message=execution.message,
        created_at=execution.created_at or datetime.now(timezone.utc),
    )
