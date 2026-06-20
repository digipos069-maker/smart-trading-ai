from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.news_event import NewsEvent
from app.schemas.news import NewsEventCreate
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
