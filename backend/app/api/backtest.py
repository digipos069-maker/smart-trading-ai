from fastapi import APIRouter

from app.services.risk_service import calculate_position_risk

router = APIRouter()


@router.get("/sample")
def sample_backtest() -> dict[str, float]:
    return calculate_position_risk(balance=10_000, risk_percent=1.0)
