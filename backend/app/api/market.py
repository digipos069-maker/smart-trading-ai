from fastapi import APIRouter

from app.services.mt5_service import get_market_status

router = APIRouter()


@router.get("/status")
def market_status() -> dict[str, str]:
    return get_market_status()
