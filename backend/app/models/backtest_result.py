from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class BacktestResult(Base):
    __tablename__ = "backtest_results"
    __table_args__ = (
        Index("ix_backtest_results_symbol", "symbol"),
        Index("ix_backtest_results_timeframe", "timeframe"),
        Index("ix_backtest_results_strategy_name", "strategy_name"),
        Index("ix_backtest_results_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False)
    average_r: Mapped[float] = mapped_column(Float, nullable=False)
    average_rr: Mapped[float] = mapped_column(Float, nullable=False)
    profit_factor: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=False)
    net_r: Mapped[float] = mapped_column(Float, nullable=False)
    best_session: Mapped[str | None] = mapped_column(String(32), nullable=True)
    best_symbol: Mapped[str | None] = mapped_column(String(32), nullable=True)
    best_timeframe: Mapped[str | None] = mapped_column(String(8), nullable=True)
    raw_trades: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
