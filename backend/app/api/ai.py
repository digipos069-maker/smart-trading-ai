from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.ai import (
    AIBacktestReviewRequest,
    AIBacktestReviewResponse,
    AIFullAnalysisRequest,
    AIFullAnalysisResponse,
    AIJournalReviewRequest,
    AIJournalReviewResponse,
    AINewsSummaryRequest,
    AINewsSummaryResponse,
    AIRiskWarningRequest,
    AIRiskWarningResponse,
    AISetupRequest,
    AISetupResponse,
)
from app.services.ai_service import (
    create_risk_warning,
    explain_ict_setup,
    full_ai_analysis,
    review_backtest_result,
    review_trade_journal,
    save_ai_analysis,
    score_setup_quality,
    summarize_news_for_symbol,
)

router = APIRouter()


@router.post("/explain-setup", response_model=AISetupResponse)
async def explain_setup(
    request: AISetupRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AISetupResponse:
    response = await explain_ict_setup(request.ict_analysis, request.news_context)
    _save_or_500(db, "setup_explanation", request.model_dump(), response, request.symbol, request.timeframe)
    return response


@router.post("/score-setup", response_model=AISetupResponse)
async def score_setup(
    request: AISetupRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AISetupResponse:
    response = await score_setup_quality(request.ict_analysis, request.news_context)
    _save_or_500(db, "setup_score", request.model_dump(), response, request.symbol, request.timeframe)
    return response


@router.post("/news-summary", response_model=AINewsSummaryResponse)
async def news_summary(
    request: AINewsSummaryRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AINewsSummaryResponse:
    response = await summarize_news_for_symbol(request.symbol, request.news_events)
    _save_or_500(db, "news_summary", request.model_dump(), response, request.symbol, None)
    return response


@router.post("/risk-warning", response_model=AIRiskWarningResponse)
async def risk_warning(
    request: AIRiskWarningRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIRiskWarningResponse:
    response = await create_risk_warning(
        request.symbol,
        request.ict_analysis,
        request.news_context,
        request.account_risk,
    )
    _save_or_500(db, "risk_warning", request.model_dump(), response, request.symbol, None)
    return response


@router.post("/journal-review", response_model=AIJournalReviewResponse)
async def journal_review(
    request: AIJournalReviewRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIJournalReviewResponse:
    response = await review_trade_journal(request.trades)
    _save_or_500(db, "journal_review", request.model_dump(), response, None, None)
    return response


@router.post("/backtest-review", response_model=AIBacktestReviewResponse)
async def backtest_review(
    request: AIBacktestReviewRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIBacktestReviewResponse:
    response = await review_backtest_result(
        request.symbol,
        request.timeframe,
        request.strategy_name,
        request.metrics,
        request.trades,
    )
    _save_or_500(
        db,
        "backtest_review",
        request.model_dump(),
        response,
        request.symbol,
        request.timeframe,
    )
    return response


@router.post("/full-analysis", response_model=AIFullAnalysisResponse)
async def full_analysis(
    request: AIFullAnalysisRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIFullAnalysisResponse:
    response = await full_ai_analysis(
        request.symbol,
        request.timeframe,
        request.ict_analysis,
        request.news_context,
        request.account_risk,
    )
    _save_or_500(db, "full_analysis", request.model_dump(), response, request.symbol, request.timeframe)
    return response


def _save_or_500(
    db: Session,
    analysis_type: str,
    raw_input: dict,
    raw_output,
    symbol: str | None,
    timeframe: str | None,
) -> None:
    try:
        save_ai_analysis(db, analysis_type, raw_input, raw_output, symbol, timeframe)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save AI analysis.",
        ) from exc
