from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class NewsEvent(Base):
    __tablename__ = "news_events"
    __table_args__ = (
        UniqueConstraint("source", "url", name="uq_news_events_source_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    sentiment: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    impact: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    relevance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
