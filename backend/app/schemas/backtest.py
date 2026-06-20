from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

BACKTEST_WARNING = "Backtest results do not guarantee future performance."


class BacktestRequest(BaseModel):
    name: str | None = None
    symbol: str = "XAUUSD"
    timeframe: str = "M5"
    start_date: date
    end_date: date
    risk_per_trade: float = Field(default=1.0, gt=0)
    min_score: int = Field(default=70, ge=0, le=100)
    min_rr: float = Field(default=1.5, gt=0)
    target_rr: float | None = Field(default=2.0, gt=0)
    require_liquidity_sweep: bool = True
    require_structure_break: bool = True
    strategy_name: str = "ict_liquidity_mss_fvg"
    initial_balance: float = Field(default=10_000, gt=0)
    session_filter: Literal["Asia", "London", "New York", "Overlap"] | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "BacktestRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date.")
        return self


class BacktestTrade(BaseModel):
    entry_time: datetime
    exit_time: datetime
    symbol: str
    timeframe: str
    session: str
    direction: Literal["bullish", "bearish"]
    entry_price: float
    stop_loss: float
    take_profit: float
    risk: float
    reward: float
    rr: float
    risk_amount: float
    profit_loss: float
    balance_after: float
    result: Literal["win", "loss", "breakeven"]
    r_multiple: float
    setup_score: int
    setup_type: str
    reason: str


class BacktestMetrics(BaseModel):
    initial_balance: float
    ending_balance: float
    net_profit_loss: float
    return_percent: float
    gross_profit_amount: float
    gross_loss_amount: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate: float
    loss_rate: float
    average_r: float
    average_rr: float
    profit_factor: float
    max_drawdown: float
    net_r: float
    expectancy: float
    best_session: str | None
    best_symbol: str | None
    best_timeframe: str | None


class BacktestResponse(BaseModel):
    id: int | None = None
    name: str | None
    symbol: str
    timeframe: str
    strategy_name: str
    start_date: date
    end_date: date
    warning: str = BACKTEST_WARNING
    metrics: BacktestMetrics
    trades: list[BacktestTrade]


class BacktestSummaryResponse(BaseModel):
    id: int
    name: str | None
    symbol: str
    timeframe: str
    strategy_name: str
    start_date: date
    end_date: date
    total_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    net_r: float
    created_at: datetime
