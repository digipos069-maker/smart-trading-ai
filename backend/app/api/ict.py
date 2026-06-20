from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.ict_signal import ICTSignal
from app.schemas.ict import ICTAnalysisResponse
from app.services.candle_service import get_saved_candles
from app.services.ict_engine import analyze_ict_setup
from app.services.mt5_service import validate_symbol, validate_timeframe

router = APIRouter()

MIN_CANDLES_FOR_ICT = 50


@router.get("/analyze", response_model=ICTAnalysisResponse)
def analyze_ict(
    db: Annotated[Session, Depends(get_db)],
    symbol: Annotated[str, Query(description="Trading symbol")] = "XAUUSD",
    timeframe: Annotated[str, Query(description="Timeframe")] = "M5",
    limit: Annotated[int, Query(ge=MIN_CANDLES_FOR_ICT, le=5000)] = 500,
) -> ICTAnalysisResponse:
    try:
        normalized_symbol = validate_symbol(symbol)
        normalized_timeframe = validate_timeframe(timeframe)
        candles = get_saved_candles(db, normalized_symbol, normalized_timeframe, limit)

        if len(candles) < MIN_CANDLES_FOR_ICT:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Not enough candles for ICT analysis. "
                    f"Need at least {MIN_CANDLES_FOR_ICT}, found {len(candles)}."
                ),
            )

        analysis = analyze_ict_setup(candles, normalized_symbol, normalized_timeframe)
        _save_ict_signal(db, analysis)
        return analysis
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load candles or persist ICT signal.",
        ) from exc


def _save_ict_signal(db: Session, analysis: ICTAnalysisResponse) -> None:
    entry_zone = analysis.entry_zone or {}
    signal = ICTSignal(
        symbol=analysis.symbol,
        timeframe=analysis.timeframe,
        bias=analysis.bias,
        score=analysis.score,
        setup_type=analysis.setup_type,
        entry_zone_low=entry_zone.get("low"),
        entry_zone_high=entry_zone.get("high"),
        stop_loss=analysis.stop_loss,
        take_profit=analysis.take_profit,
        raw_analysis=jsonable_encoder(analysis),
    )
    db.add(signal)
    db.commit()
