from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.news import NewsEventCreate, NewsEventResponse, NewsListResponse
from app.services.news_service import get_latest_news, save_news_event

router = APIRouter()


@router.get("", response_model=NewsListResponse)
def latest_news(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    symbol: str | None = None,
    impact: str | None = Query(default=None, pattern="^(low|medium|high)$"),
) -> NewsListResponse:
    events = get_latest_news(db, limit=limit, symbol=symbol, impact=impact)
    return NewsListResponse(count=len(events), events=events)


@router.post("", response_model=NewsEventResponse, status_code=status.HTTP_201_CREATED)
def create_news_event(
    event: NewsEventCreate,
    db: Annotated[Session, Depends(get_db)],
) -> NewsEventResponse:
    try:
        return save_news_event(db, event)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save news event.",
        ) from exc
