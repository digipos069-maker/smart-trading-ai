from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.execution import (
    ExecuteSignalRequest,
    ExecutionStatusResponse,
    TradeExecutionResponse,
)
from app.services.execution_service import (
    TradeValidationError,
    TradingDisabledError,
    execute_signal_request,
    get_execution_status,
    get_recent_executions,
)
from app.services.mt5_service import MT5ConnectionError, MT5DataError

router = APIRouter()


@router.get("/status", response_model=ExecutionStatusResponse)
def execution_status() -> ExecutionStatusResponse:
    return ExecutionStatusResponse(**get_execution_status())


@router.post(
    "/signal",
    response_model=TradeExecutionResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def execute_signal(
    request: ExecuteSignalRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TradeExecutionResponse:
    try:
        return execute_signal_request(db, request)
    except TradingDisabledError as exc:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TradeValidationError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except (MT5ConnectionError, MT5DataError) as exc:
        raise HTTPException(status_code=http_status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/orders", response_model=list[TradeExecutionResponse])
def recent_orders(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[TradeExecutionResponse]:
    return get_recent_executions(db, limit)
