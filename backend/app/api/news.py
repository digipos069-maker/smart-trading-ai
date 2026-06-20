from fastapi import APIRouter

from app.services.news_service import get_latest_news

router = APIRouter()


@router.get("/")
def latest_news() -> list[dict[str, str]]:
    return get_latest_news()
