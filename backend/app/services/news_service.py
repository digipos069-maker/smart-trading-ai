from datetime import datetime, timezone

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.news_event import NewsEvent
from app.schemas.news import NewsEventCreate, NewsRiskResponse
from app.services.news_ai_service import analyze_news_event


def save_news_event(db: Session, event: NewsEventCreate) -> NewsEvent:
    analysis = analyze_news_event(event)
    values = {
        "title": event.title,
        "summary": event.summary,
        "source": event.source,
        "url": str(event.url) if event.url else None,
        "symbol": event.symbol.upper() if event.symbol else None,
        "currency": event.currency.upper() if event.currency else None,
        "category": event.category,
        "sentiment": analysis.sentiment,
        "impact": analysis.impact,
        "relevance_score": analysis.relevance_score,
        "published_at": event.published_at,
    }

    if values["url"]:
        statement = insert(NewsEvent).values(values)
        statement = statement.on_conflict_do_update(
            constraint="uq_news_events_source_url",
            set_=values,
        ).returning(NewsEvent)
        saved = db.scalars(statement).one()
    else:
        saved = NewsEvent(**values)
        db.add(saved)

    db.commit()
    db.refresh(saved)
    return saved


def get_latest_news(
    db: Session,
    limit: int = 50,
    symbol: str | None = None,
    impact: str | None = None,
) -> list[NewsEvent]:
    statement: Select[tuple[NewsEvent]] = select(NewsEvent)

    if symbol:
        statement = statement.where(NewsEvent.symbol == symbol.upper())
    if impact:
        statement = statement.where(NewsEvent.impact == impact.lower())

    statement = statement.order_by(NewsEvent.published_at.desc()).limit(limit)
    return list(db.scalars(statement).all())


def get_news_risk(db: Session, symbol: str) -> NewsRiskResponse:
    events = get_latest_news(db, limit=20, symbol=symbol)
    high_impact = next((event for event in events if event.impact == "high"), None)
    if high_impact is None:
        return NewsRiskResponse(
            can_trade=True,
            risk_level="low",
            blocking_event=None,
            minutes_to_event=None,
            reason="No high-impact saved news event found for this symbol.",
        )

    now = datetime.now(timezone.utc)
    event_time = high_impact.published_at
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    minutes = int((event_time - now).total_seconds() / 60)
    near_event = abs(minutes) <= 120

    return NewsRiskResponse(
        can_trade=not near_event,
        risk_level="high" if near_event else "medium",
        blocking_event=high_impact.title,
        minutes_to_event=minutes,
        reason=(
            "High-impact news is near the current time."
            if near_event
            else "High-impact news exists, but it is not inside the 120 minute risk window."
        ),
    )
