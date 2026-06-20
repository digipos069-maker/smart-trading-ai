from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.ict import ICTAnalysisResponse


class ExecutionStatusResponse(BaseModel):
    trading_enabled: bool
    trading_mode: str
    auto_execute_signals: bool
    mt5_status: dict[str, str]


class ExecuteSignalRequest(BaseModel):
    analysis: ICTAnalysisResponse
    account_balance: float | None = Field(
        default=None,
        gt=0,
        description="Optional manual balance override for lot sizing. Uses MT5 account balance when omitted.",
    )
    risk_percent: float | None = Field(
        default=None,
        gt=0,
        le=10,
        description="Optional risk override. Defaults to EXECUTION_RISK_PERCENT.",
    )
    comment: str = "Smart Trading AI signal"


class TradeExecutionResponse(BaseModel):
    id: int | None = None
    symbol: str
    timeframe: str | None
    direction: str
    volume: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_percent: float
    score: int | None = None
    status: str
    mt5_order: int | None = None
    mt5_deal: int | None = None
    mt5_retcode: int | None = None
    message: str | None = None
    created_at: datetime | None = None
