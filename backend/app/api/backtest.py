from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestSummaryResponse,
)
from app.services.backtest_service import (
    delete_backtest_result,
    get_backtest_result,
    get_backtest_summaries,
    run_backtest,
)

router = APIRouter()


@router.post("/run", response_model=BacktestResponse)
def run_backtest_endpoint(
    request: BacktestRequest,
    db: Annotated[Session, Depends(get_db)],
) -> BacktestResponse:
    try:
        return run_backtest(db, request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run or save backtest.",
        ) from exc


@router.get("/results", response_model=list[BacktestSummaryResponse])
def list_backtest_results(
    db: Annotated[Session, Depends(get_db)],
    symbol: str | None = None,
    timeframe: str | None = None,
    strategy_name: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[BacktestSummaryResponse]:
    try:
        return get_backtest_summaries(db, symbol, timeframe, strategy_name, limit)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("/results/{result_id}", response_model=BacktestResponse)
def read_backtest_result(
    result_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> BacktestResponse:
    result = get_backtest_result(db, result_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest result not found.",
        )
    return result


@router.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_backtest_result(
    result_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    if not delete_backtest_result(db, result_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest result not found.",
        )
