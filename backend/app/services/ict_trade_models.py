from collections.abc import Sequence

from app.schemas.ict import (
    FVG,
    IFVG,
    LiquiditySweep,
    OTEZone,
    OrderBlock,
    SessionRange,
    StructureEvent,
    SwingPoint,
    TradeModel,
)


def detect_trade_models(
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
    entry_zone: dict[str, float] | None,
    stop_loss: float | None,
    take_profit: float | None,
) -> list[TradeModel]:
    models = [
        _detect_turtle_soup(bias, liquidity_sweeps, mss_events, entry_zone, stop_loss, take_profit),
        _detect_amd(bias, liquidity_sweeps, mss_events, bos_events, fvgs, entry_zone, stop_loss, take_profit),
        _detect_crt(candles, bias, mss_events, bos_events, entry_zone, stop_loss, take_profit),
        _detect_silver_bullet(candles, bias, liquidity_sweeps, fvgs, ifvgs, session_ranges, entry_zone, stop_loss, take_profit),
        _detect_judas_swing(bias, liquidity_sweeps, mss_events, session_ranges, entry_zone, stop_loss, take_profit),
        _detect_power_of_three(bias, liquidity_sweeps, bos_events, order_blocks, entry_zone, stop_loss, take_profit),
        _detect_breaker_model(bias, ifvgs, mss_events, entry_zone, stop_loss, take_profit),
        _detect_ote_continuation(bias, bos_events, ote_zones, entry_zone, stop_loss, take_profit),
    ]
    return [model for model in models if model is not None]


def _detect_turtle_soup(
    bias: str,
    sweeps: Sequence[LiquiditySweep],
    mss_events: Sequence[StructureEvent],
    entry_zone: dict[str, float] | None,
    stop_loss: float | None,
    take_profit: float | None,
) -> TradeModel | None:
    if bias == "bullish" and _latest_sweep(sweeps, "sell_side") and _latest_direction(mss_events, "bullish"):
        return _model("turtle_soup", "bullish", 82, "Sell-side liquidity sweep followed by bullish MSS.", entry_zone, stop_loss, take_profit)
    if bias == "bearish" and _latest_sweep(sweeps, "buy_side") and _latest_direction(mss_events, "bearish"):
        return _model("turtle_soup", "bearish", 82, "Buy-side liquidity sweep followed by bearish MSS.", entry_zone, stop_loss, take_profit)
    return None


def _detect_amd(
    bias: str,
    sweeps: Sequence[LiquiditySweep],
    mss_events: Sequence[StructureEvent],
    bos_events: Sequence[StructureEvent],
    fvgs: Sequence[FVG],
    entry_zone: dict[str, float] | None,
    stop_loss: float | None,
    take_profit: float | None,
) -> TradeModel | None:
    structure = _latest_direction(mss_events, bias) or _latest_direction(bos_events, bias)
    fvg = _latest_direction(fvgs, bias)
    sweep = _latest_sweep(sweeps, "sell_side" if bias == "bullish" else "buy_side")
    if bias in {"bullish", "bearish"} and sweep and structure and fvg:
        return _model("amd", bias, 78, "Accumulation/manipulation/distribution profile detected from sweep, displacement, and FVG.", entry_zone, stop_loss, take_profit)
    return None


def _detect_crt(
    candles: Sequence[object],
    bias: str,
    mss_events: Sequence[StructureEvent],
    bos_events: Sequence[StructureEvent],
    entry_zone: dict[str, float] | None,
    stop_loss: float | None,
    take_profit: float | None,
) -> TradeModel | None:
    if len(candles) < 4 or bias not in {"bullish", "bearish"}:
        return None
    previous = candles[-2]
    current = candles[-1]
    broke_previous_low = current.low < previous.low and current.close > previous.low
    broke_previous_high = current.high > previous.high and current.close < previous.high
    if bias == "bullish" and broke_previous_low and (_latest_direction(mss_events, bias) or _latest_direction(bos_events, bias)):
        return _model("crt", "bullish", 72, "Candle range theory reversal after taking prior candle low.", entry_zone, stop_loss, take_profit)
    if bias == "bearish" and broke_previous_high and (_latest_direction(mss_events, bias) or _latest_direction(bos_events, bias)):
        return _model("crt", "bearish", 72, "Candle range theory reversal after taking prior candle high.", entry_zone, stop_loss, take_profit)
    return None


def _detect_silver_bullet(
    candles: Sequence[object],
    bias: str,
    sweeps: Sequence[LiquiditySweep],
    fvgs: Sequence[FVG],
    ifvgs: Sequence[IFVG],
    session_ranges: Sequence[SessionRange],
    entry_zone: dict[str, float] | None,
    stop_loss: float | None,
    take_profit: float | None,
) -> TradeModel | None:
    if not candles or bias not in {"bullish", "bearish"}:
        return None
    active_session = session_ranges[-1].session_name if session_ranges else ""
    has_gap = _latest_direction(ifvgs, bias) or _latest_direction(fvgs, bias)
    sweep = _latest_sweep(sweeps, "sell_side" if bias == "bullish" else "buy_side")
    if active_session in {"london", "new_york"} and sweep and has_gap:
        return _model("silver_bullet", bias, 76, "Session liquidity sweep with directional FVG/IFVG.", entry_zone, stop_loss, take_profit)
    return None


def _detect_judas_swing(
    bias: str,
    sweeps: Sequence[LiquiditySweep],
    mss_events: Sequence[StructureEvent],
    session_ranges: Sequence[SessionRange],
    entry_zone: dict[str, float] | None,
    stop_loss: float | None,
    take_profit: float | None,
) -> TradeModel | None:
    has_asia = any(session.session_name == "asia" for session in session_ranges)
    sweep = _latest_sweep(sweeps, "sell_side" if bias == "bullish" else "buy_side")
    if bias in {"bullish", "bearish"} and has_asia and sweep and _latest_direction(mss_events, bias):
        return _model("judas_swing", bias, 74, "Asia range manipulation followed by MSS in the opposite direction.", entry_zone, stop_loss, take_profit)
    return None


def _detect_power_of_three(
    bias: str,
    sweeps: Sequence[LiquiditySweep],
    bos_events: Sequence[StructureEvent],
    order_blocks: Sequence[OrderBlock],
    entry_zone: dict[str, float] | None,
    stop_loss: float | None,
    take_profit: float | None,
) -> TradeModel | None:
    sweep = _latest_sweep(sweeps, "sell_side" if bias == "bullish" else "buy_side")
    if bias in {"bullish", "bearish"} and sweep and _latest_direction(bos_events, bias) and _latest_direction(order_blocks, bias):
        return _model("power_of_three", bias, 75, "Accumulation sweep, manipulation, and directional expansion with order block.", entry_zone, stop_loss, take_profit)
    return None


def _detect_breaker_model(
    bias: str,
    ifvgs: Sequence[IFVG],
    mss_events: Sequence[StructureEvent],
    entry_zone: dict[str, float] | None,
    stop_loss: float | None,
    take_profit: float | None,
) -> TradeModel | None:
    if bias in {"bullish", "bearish"} and _latest_direction(ifvgs, bias) and _latest_direction(mss_events, bias):
        return _model("breaker_ifvg", bias, 73, "IFVG inversion with market structure shift.", entry_zone, stop_loss, take_profit)
    return None


def _detect_ote_continuation(
    bias: str,
    bos_events: Sequence[StructureEvent],
    ote_zones: Sequence[OTEZone],
    entry_zone: dict[str, float] | None,
    stop_loss: float | None,
    take_profit: float | None,
) -> TradeModel | None:
    if bias in {"bullish", "bearish"} and ote_zones and _latest_direction(bos_events, bias):
        return _model("ote_continuation", bias, 70, "Directional BOS with price model offering an OTE retracement zone.", entry_zone, stop_loss, take_profit)
    return None


def _model(
    name: str,
    direction: str,
    confidence: float,
    reason: str,
    entry_zone: dict[str, float] | None,
    invalid_level: float | None,
    target_level: float | None,
) -> TradeModel:
    return TradeModel(
        name=name,
        direction=direction,
        confidence=confidence,
        reason=reason,
        entry_zone=entry_zone,
        invalid_level=invalid_level,
        target_level=target_level,
    )


def _latest_sweep(
    sweeps: Sequence[LiquiditySweep],
    direction: str,
) -> LiquiditySweep | None:
    return next((item for item in reversed(sweeps) if item.direction == direction), None)


def _latest_direction(items, direction: str):
    return next((item for item in reversed(items) if item.direction == direction), None)
