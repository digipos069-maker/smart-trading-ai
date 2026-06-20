from collections.abc import Sequence
from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.schemas.ict import (
    FVG,
    ICTAnalysisResponse,
    IFVG,
    LiquiditySweep,
    OTEZone,
    OrderBlock,
    SessionRange,
    StructureEvent,
    SwingPoint,
)
from app.services.ict_trade_models import detect_trade_models


def _confidence(close: float, broken_level: float) -> float:
    if broken_level == 0:
        return 50.0
    distance = abs(close - broken_level) / abs(broken_level)
    return round(min(100.0, 60.0 + distance * 10_000), 2)


def _body_direction(candle: object) -> str:
    if candle.close > candle.open:
        return "bullish"
    if candle.close < candle.open:
        return "bearish"
    return "neutral"


def detect_swing_points(
    candles: Sequence[object],
    left: int = 3,
    right: int = 3,
) -> list[SwingPoint]:
    swings: list[SwingPoint] = []
    if len(candles) < left + right + 1:
        return swings

    for index in range(left, len(candles) - right):
        candle = candles[index]
        left_window = candles[index - left : index]
        right_window = candles[index + 1 : index + right + 1]

        # A swing is only confirmed after the right-side candles have closed.
        if all(candle.high > nearby.high for nearby in left_window + right_window):
            swings.append(
                SwingPoint(
                    time=candle.time,
                    index=index,
                    price=candle.high,
                    type="swing_high",
                )
            )

        if all(candle.low < nearby.low for nearby in left_window + right_window):
            swings.append(
                SwingPoint(
                    time=candle.time,
                    index=index,
                    price=candle.low,
                    type="swing_low",
                )
            )

    return swings


def detect_bos(
    candles: Sequence[object],
    swing_points: Sequence[SwingPoint],
) -> list[StructureEvent]:
    events: list[StructureEvent] = []
    broken_levels: set[tuple[str, int]] = set()

    for index, candle in enumerate(candles):
        prior_swings = [swing for swing in swing_points if swing.index < index]
        high = next((s for s in reversed(prior_swings) if s.type == "swing_high"), None)
        low = next((s for s in reversed(prior_swings) if s.type == "swing_low"), None)

        if high and candle.close > high.price and ("bullish", high.index) not in broken_levels:
            broken_levels.add(("bullish", high.index))
            events.append(
                StructureEvent(
                    time=candle.time,
                    index=index,
                    direction="bullish",
                    broken_level=high.price,
                    confidence=_confidence(candle.close, high.price),
                )
            )

        if low and candle.close < low.price and ("bearish", low.index) not in broken_levels:
            broken_levels.add(("bearish", low.index))
            events.append(
                StructureEvent(
                    time=candle.time,
                    index=index,
                    direction="bearish",
                    broken_level=low.price,
                    confidence=_confidence(candle.close, low.price),
                )
            )

    return events


def detect_mss(
    candles: Sequence[object],
    swing_points: Sequence[SwingPoint],
) -> list[StructureEvent]:
    bos_events = detect_bos(candles, swing_points)
    events: list[StructureEvent] = []
    prior_direction: str | None = None

    for event in bos_events:
        # MSS is treated as the first opposing structural break after a prior trend.
        if prior_direction and prior_direction != event.direction:
            events.append(
                StructureEvent(
                    time=event.time,
                    index=event.index,
                    direction=event.direction,
                    broken_level=event.broken_level,
                    confidence=min(100.0, event.confidence + 5.0),
                )
            )
        prior_direction = event.direction

    return events


def detect_liquidity_sweep(
    candles: Sequence[object],
    swing_points: Sequence[SwingPoint],
) -> list[LiquiditySweep]:
    sweeps: list[LiquiditySweep] = []
    swept_levels: set[tuple[str, int]] = set()

    for index, candle in enumerate(candles):
        prior_swings = [swing for swing in swing_points if swing.index < index]
        high = next((s for s in reversed(prior_swings) if s.type == "swing_high"), None)
        low = next((s for s in reversed(prior_swings) if s.type == "swing_low"), None)

        # Buy-side liquidity is swept when wick takes the high but close rejects it.
        if high and candle.high > high.price and candle.close < high.price:
            key = ("buy_side", high.index)
            if key not in swept_levels:
                swept_levels.add(key)
                sweeps.append(
                    LiquiditySweep(
                        time=candle.time,
                        index=index,
                        direction="buy_side",
                        swept_level=high.price,
                        candle_high=candle.high,
                        candle_low=candle.low,
                    )
                )

        # Sell-side liquidity is swept when wick takes the low but close reclaims it.
        if low and candle.low < low.price and candle.close > low.price:
            key = ("sell_side", low.index)
            if key not in swept_levels:
                swept_levels.add(key)
                sweeps.append(
                    LiquiditySweep(
                        time=candle.time,
                        index=index,
                        direction="sell_side",
                        swept_level=low.price,
                        candle_high=candle.high,
                        candle_low=candle.low,
                    )
                )

    return sweeps


def detect_fvg(candles: Sequence[object]) -> list[FVG]:
    fvgs: list[FVG] = []

    for index in range(2, len(candles)):
        current = candles[index]
        anchor = candles[index - 2]

        # Bullish imbalance leaves a gap between candle i low and candle i-2 high.
        if current.low > anchor.high:
            lower = anchor.high
            upper = current.low
            fvgs.append(
                FVG(
                    time=current.time,
                    index=index,
                    direction="bullish",
                    upper=upper,
                    lower=lower,
                    midpoint=(upper + lower) / 2,
                    is_filled=_is_fvg_filled(candles[index + 1 :], "bullish", lower),
                )
            )

        # Bearish imbalance leaves a gap between candle i high and candle i-2 low.
        if current.high < anchor.low:
            lower = current.high
            upper = anchor.low
            fvgs.append(
                FVG(
                    time=current.time,
                    index=index,
                    direction="bearish",
                    upper=upper,
                    lower=lower,
                    midpoint=(upper + lower) / 2,
                    is_filled=_is_fvg_filled(candles[index + 1 :], "bearish", upper),
                )
            )

    return fvgs


def _is_fvg_filled(
    future_candles: Sequence[object],
    direction: str,
    fill_level: float,
) -> bool:
    if direction == "bullish":
        return any(candle.low <= fill_level for candle in future_candles)
    return any(candle.high >= fill_level for candle in future_candles)


def detect_ifvg(candles: Sequence[object], fvgs: Sequence[FVG]) -> list[IFVG]:
    ifvgs: list[IFVG] = []

    for fvg in fvgs:
        for index in range(fvg.index + 1, len(candles)):
            candle = candles[index]
            if fvg.direction == "bullish" and candle.close < fvg.lower:
                ifvgs.append(
                    IFVG(
                        time=candle.time,
                        index=index,
                        original_fvg_index=fvg.index,
                        direction="bearish",
                        upper=fvg.upper,
                        lower=fvg.lower,
                        midpoint=fvg.midpoint,
                    )
                )
                break

            if fvg.direction == "bearish" and candle.close > fvg.upper:
                ifvgs.append(
                    IFVG(
                        time=candle.time,
                        index=index,
                        original_fvg_index=fvg.index,
                        direction="bullish",
                        upper=fvg.upper,
                        lower=fvg.lower,
                        midpoint=fvg.midpoint,
                    )
                )
                break

    return ifvgs


def detect_order_blocks(
    candles: Sequence[object],
    bos_events: Sequence[StructureEvent],
) -> list[OrderBlock]:
    order_blocks: list[OrderBlock] = []

    for event in bos_events:
        search_start = max(0, event.index - 20)
        prior_candles = range(event.index - 1, search_start - 1, -1)
        required_direction = "bearish" if event.direction == "bullish" else "bullish"

        # ICT order block is the last opposing candle before displacement/BOS.
        for index in prior_candles:
            candle = candles[index]
            if _body_direction(candle) == required_direction:
                order_blocks.append(
                    OrderBlock(
                        time=candle.time,
                        index=index,
                        direction=event.direction,
                        high=candle.high,
                        low=candle.low,
                        midpoint=(candle.high + candle.low) / 2,
                        bos_index=event.index,
                    )
                )
                break

    return order_blocks


def detect_ote_zone(swing_low: float, swing_high: float, direction: str) -> OTEZone:
    price_range = swing_high - swing_low
    if direction == "bullish":
        fib_62 = swing_high - price_range * 0.62
        fib_705 = swing_high - price_range * 0.705
        fib_79 = swing_high - price_range * 0.79
    else:
        fib_62 = swing_low + price_range * 0.62
        fib_705 = swing_low + price_range * 0.705
        fib_79 = swing_low + price_range * 0.79

    return OTEZone(
        direction=direction,
        ote_low=min(fib_62, fib_79),
        ote_high=max(fib_62, fib_79),
        fib_62=fib_62,
        fib_705=fib_705,
        fib_79=fib_79,
    )


def detect_session_range(
    candles: Sequence[object],
    timezone: str = "Asia/Phnom_Penh",
) -> list[SessionRange]:
    if not candles:
        return []

    tz = ZoneInfo(timezone)
    sessions = {
        "asia": (time(6, 0), time(14, 0)),
        "london": (time(14, 0), time(22, 0)),
        "new_york": (time(19, 0), time(3, 0)),
    }
    ranges: list[SessionRange] = []

    for session_name, (start, end) in sessions.items():
        session_candles = [
            candle
            for candle in candles
            if _is_in_session(candle.time.astimezone(tz).time(), start, end)
        ]
        if not session_candles:
            continue

        high = max(candle.high for candle in session_candles)
        low = min(candle.low for candle in session_candles)
        ranges.append(
            SessionRange(
                session_name=session_name,
                start_time=session_candles[0].time,
                end_time=session_candles[-1].time,
                high=high,
                low=low,
                midpoint=(high + low) / 2,
            )
        )

    return ranges


def _is_in_session(value: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= value < end
    return value >= start or value < end


def analyze_ict_setup(
    candles: Sequence[object],
    symbol: str,
    timeframe: str,
) -> ICTAnalysisResponse:
    swing_points = detect_swing_points(candles)
    bos_events = detect_bos(candles, swing_points)
    mss_events = detect_mss(candles, swing_points)
    liquidity_sweeps = detect_liquidity_sweep(candles, swing_points)
    fvgs = detect_fvg(candles)
    ifvgs = detect_ifvg(candles, fvgs)
    order_blocks = detect_order_blocks(candles, bos_events)
    session_ranges = detect_session_range(candles)

    last_index = len(candles) - 1
    bias = _resolve_bias(bos_events, mss_events, liquidity_sweeps)
    ote_zones = _build_ote_zones(swing_points, bias)
    entry_zone = _select_entry_zone(order_blocks, ote_zones, bias, last_index)
    stop_loss = _select_stop_loss(entry_zone, order_blocks, bias, last_index)
    take_profit = _select_take_profit(entry_zone, swing_points, bias)
    score, explanation = _score_setup(
        candles,
        bias,
        swing_points,
        bos_events,
        mss_events,
        liquidity_sweeps,
        fvgs,
        ifvgs,
        order_blocks,
        ote_zones,
        session_ranges,
    )
    trade_models = detect_trade_models(
        candles,
        bias,
        swing_points,
        bos_events,
        mss_events,
        liquidity_sweeps,
        fvgs,
        ifvgs,
        order_blocks,
        ote_zones,
        session_ranges,
        entry_zone,
        stop_loss,
        take_profit,
    )

    setup_type = _build_setup_type(liquidity_sweeps, mss_events, bos_events, fvgs, ifvgs)

    return ICTAnalysisResponse(
        symbol=symbol,
        timeframe=timeframe,
        bias=bias,
        score=score,
        setup_type=setup_type,
        swing_points=swing_points,
        bos_events=bos_events,
        mss_events=mss_events,
        liquidity_sweeps=liquidity_sweeps,
        fvgs=fvgs,
        ifvgs=ifvgs,
        order_blocks=order_blocks,
        ote_zones=ote_zones,
        session_ranges=session_ranges,
        trade_models=trade_models,
        entry_zone=entry_zone,
        stop_loss=stop_loss,
        take_profit=take_profit,
        explanation=explanation,
    )


def _resolve_bias(
    bos_events: Sequence[StructureEvent],
    mss_events: Sequence[StructureEvent],
    liquidity_sweeps: Sequence[LiquiditySweep],
) -> str:
    if mss_events:
        return mss_events[-1].direction
    if bos_events:
        return bos_events[-1].direction
    if liquidity_sweeps:
        latest = liquidity_sweeps[-1]
        return "bullish" if latest.direction == "sell_side" else "bearish"
    return "neutral"


def _build_ote_zones(
    swing_points: Sequence[SwingPoint],
    bias: str,
) -> list[OTEZone]:
    if bias not in {"bullish", "bearish"}:
        return []

    latest_high = next((s for s in reversed(swing_points) if s.type == "swing_high"), None)
    latest_low = next((s for s in reversed(swing_points) if s.type == "swing_low"), None)
    if not latest_high or not latest_low:
        return []

    return [detect_ote_zone(latest_low.price, latest_high.price, bias)]


def _select_entry_zone(
    order_blocks: Sequence[OrderBlock],
    ote_zones: Sequence[OTEZone],
    bias: str,
    last_index: int,
) -> dict[str, float] | None:
    block = next(
        (
            item
            for item in reversed(order_blocks)
            if item.direction == bias and last_index - item.bos_index <= 30
        ),
        None,
    )
    if block:
        return {"low": block.low, "high": block.high}
    if ote_zones:
        zone = ote_zones[-1]
        return {"low": zone.ote_low, "high": zone.ote_high}
    return None


def _select_stop_loss(
    entry_zone: dict[str, float] | None,
    order_blocks: Sequence[OrderBlock],
    bias: str,
    last_index: int,
) -> float | None:
    if not entry_zone:
        return None
    block = next(
        (
            item
            for item in reversed(order_blocks)
            if item.direction == bias and last_index - item.bos_index <= 30
        ),
        None,
    )
    if block:
        return block.low if bias == "bullish" else block.high
    return entry_zone["low"] if bias == "bullish" else entry_zone["high"]


def _select_take_profit(
    entry_zone: dict[str, float] | None,
    swing_points: Sequence[SwingPoint],
    bias: str,
) -> float | None:
    if not entry_zone:
        return None
    if bias == "bullish":
        high = next(
            (
                s
                for s in reversed(swing_points)
                if s.type == "swing_high" and s.price > entry_zone["high"]
            ),
            None,
        )
        return high.price if high else None
    if bias == "bearish":
        low = next(
            (
                s
                for s in reversed(swing_points)
                if s.type == "swing_low" and s.price < entry_zone["low"]
            ),
            None,
        )
        return low.price if low else None
    return None


def _score_setup(
    candles: Sequence[object],
    bias: str,
    swing_points: Sequence[SwingPoint],
    bos_events: Sequence[StructureEvent],
    mss_events: Sequence[StructureEvent],
    liquidity_sweeps: Sequence[LiquiditySweep],
    fvgs: Sequence[FVG],
    ifvgs: Sequence[IFVG],
    order_blocks: Sequence[OrderBlock],
    ote_zones: Sequence[OTEZone],
    session_ranges: Sequence[SessionRange],
) -> tuple[int, list[str]]:
    score = 0
    explanation: list[str] = []
    last_index = len(candles) - 1
    recent_sweep = _latest_recent_sweep(liquidity_sweeps, bias, last_index)
    recent_structure = _latest_recent_structure(
        list(mss_events) or list(bos_events), bias, last_index
    )
    recent_fvg = _latest_recent_fvg(list(ifvgs) or list(fvgs), bias, last_index)
    recent_order_block = _latest_recent_order_block(order_blocks, bias, last_index)

    if _has_balanced_swings(swing_points):
        score += 15
        explanation.append("Balanced swing structure detected.")
    if recent_sweep:
        score += 20
        explanation.append("Recent directional liquidity sweep detected.")
    if recent_structure:
        score += 20
        explanation.append("Recent BOS or MSS confirms current bias.")
    if recent_fvg:
        score += 20
        explanation.append("Recent directional FVG or IFVG supports entry.")
    if recent_order_block or ote_zones:
        score += 15
        explanation.append("Fresh order block or OTE zone available.")
    if candles and _current_session_name(candles[-1].time) in {"London", "New York", "Overlap"}:
        score += 10
        explanation.append("Signal appears during an active high-liquidity session.")

    if not explanation:
        explanation.append("No high-probability ICT confluence detected.")

    return min(score, 100), explanation


def _has_balanced_swings(swing_points: Sequence[SwingPoint]) -> bool:
    return any(item.type == "swing_high" for item in swing_points) and any(
        item.type == "swing_low" for item in swing_points
    )


def _latest_recent_sweep(
    liquidity_sweeps: Sequence[LiquiditySweep],
    bias: str,
    last_index: int,
    lookback: int = 30,
) -> LiquiditySweep | None:
    required_direction = "sell_side" if bias == "bullish" else "buy_side"
    return next(
        (
            item
            for item in reversed(liquidity_sweeps)
            if item.direction == required_direction and last_index - item.index <= lookback
        ),
        None,
    )


def _latest_recent_structure(
    structure_events: Sequence[StructureEvent],
    bias: str,
    last_index: int,
    lookback: int = 25,
) -> StructureEvent | None:
    return next(
        (
            item
            for item in reversed(structure_events)
            if item.direction == bias and last_index - item.index <= lookback
        ),
        None,
    )


def _latest_recent_fvg(
    gaps: Sequence[FVG | IFVG],
    bias: str,
    last_index: int,
    lookback: int = 25,
) -> FVG | IFVG | None:
    return next(
        (
            item
            for item in reversed(gaps)
            if item.direction == bias and last_index - item.index <= lookback
        ),
        None,
    )


def _latest_recent_order_block(
    order_blocks: Sequence[OrderBlock],
    bias: str,
    last_index: int,
    lookback: int = 30,
) -> OrderBlock | None:
    return next(
        (
            item
            for item in reversed(order_blocks)
            if item.direction == bias and last_index - item.bos_index <= lookback
        ),
        None,
    )


def _current_session_name(value: datetime, timezone: str = "Asia/Phnom_Penh") -> str:
    local_time = value.astimezone(ZoneInfo(timezone)).time()
    if time(19, 0) <= local_time < time(22, 0):
        return "Overlap"
    if time(6, 0) <= local_time < time(14, 0):
        return "Asia"
    if time(14, 0) <= local_time < time(22, 0):
        return "London"
    if local_time >= time(19, 0) or local_time < time(3, 0):
        return "New York"
    return "Unknown"


def _build_setup_type(
    liquidity_sweeps: Sequence[LiquiditySweep],
    mss_events: Sequence[StructureEvent],
    bos_events: Sequence[StructureEvent],
    fvgs: Sequence[FVG],
    ifvgs: Sequence[IFVG],
) -> str:
    parts: list[str] = []
    if liquidity_sweeps:
        parts.append("liquidity_sweep")
    if mss_events:
        parts.append("mss")
    elif bos_events:
        parts.append("bos")
    if ifvgs:
        parts.append("ifvg")
    elif fvgs:
        parts.append("fvg")
    return "_".join(parts) if parts else "no_setup"
