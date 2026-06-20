from fastapi import APIRouter

from app.services.ict_engine import analyze_market_structure

router = APIRouter()


@router.get("/analysis")
def ict_analysis() -> dict[str, str]:
    return analyze_market_structure()
