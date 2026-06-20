from fastapi import APIRouter

from app.services.ai_service import generate_trade_insight

router = APIRouter()


@router.get("/insight")
def trade_insight() -> dict[str, str]:
    return generate_trade_insight()
