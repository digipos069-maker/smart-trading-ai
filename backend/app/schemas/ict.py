from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SwingPoint(BaseModel):
    time: datetime
    index: int = Field(ge=0)
    price: float
    type: str


class StructureEvent(BaseModel):
    time: datetime
    index: int = Field(ge=0)
    direction: str
    broken_level: float
    confidence: float = Field(ge=0, le=100)


class LiquiditySweep(BaseModel):
    time: datetime
    index: int = Field(ge=0)
    direction: str
    swept_level: float
    candle_high: float
    candle_low: float


class FVG(BaseModel):
    time: datetime
    index: int = Field(ge=0)
    direction: str
    upper: float
    lower: float
    midpoint: float
    is_filled: bool = False


class IFVG(BaseModel):
    time: datetime
    index: int = Field(ge=0)
    original_fvg_index: int = Field(ge=0)
    direction: str
    upper: float
    lower: float
    midpoint: float


class OrderBlock(BaseModel):
    time: datetime
    index: int = Field(ge=0)
    direction: str
    high: float
    low: float
    midpoint: float
    bos_index: int = Field(ge=0)


class OTEZone(BaseModel):
    direction: str
    ote_low: float
    ote_high: float
    fib_62: float
    fib_705: float
    fib_79: float


class SessionRange(BaseModel):
    session_name: str
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    midpoint: float


class ICTAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    timeframe: str
    bias: str
    score: int = Field(ge=0, le=100)
    setup_type: str
    swing_points: list[SwingPoint]
    bos_events: list[StructureEvent]
    mss_events: list[StructureEvent]
    liquidity_sweeps: list[LiquiditySweep]
    fvgs: list[FVG]
    ifvgs: list[IFVG]
    order_blocks: list[OrderBlock]
    ote_zones: list[OTEZone]
    session_ranges: list[SessionRange]
    entry_zone: dict[str, float] | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    explanation: list[str]
