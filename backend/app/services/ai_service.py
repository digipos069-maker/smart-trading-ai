import json
from typing import Any, TypeVar

from fastapi.encoders import jsonable_encoder
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_analysis import AIAnalysis
from app.schemas.ai import (
    AIFullAnalysisResponse,
    AIJournalReviewResponse,
    AINewsSummaryResponse,
    AIRiskWarningResponse,
    AISetupResponse,
)

T = TypeVar("T", bound=BaseModel)

EDUCATIONAL_WARNING = (
    "Educational decision support only. This is not financial advice and must not "
    "be used as an automated trade instruction."
)


def _client() -> AsyncOpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None
    return AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=settings.OPENAI_TIMEOUT_SECONDS,
    )


async def explain_ict_setup(
    ict_analysis: dict[str, Any],
    news_context: list[dict[str, Any]] | None = None,
) -> AISetupResponse:
    """Explain an existing ICT analysis without creating new trade signals."""
    fallback = _fallback_setup_response(ict_analysis)
    prompt = _prompt(
        "Explain this ICT setup in simple trading language.",
        {
            "ict_analysis": ict_analysis,
            "news_context": news_context or [],
            "required_focus": [
                "liquidity sweep",
                "MSS or BOS",
                "FVG or IFVG",
                "order block",
                "OTE",
                "session timing",
                "missing confirmations",
            ],
        },
    )
    return await _generate_structured(AISetupResponse, prompt, fallback)


async def score_setup_quality(
    ict_analysis: dict[str, Any],
    news_context: list[dict[str, Any]] | None = None,
) -> AISetupResponse:
    """Score setup quality from known ICT/news context; never guarantee outcomes."""
    fallback = _fallback_setup_response(ict_analysis)
    prompt = _prompt(
        "Score the setup quality using the provided scoring guide.",
        {
            "ict_analysis": ict_analysis,
            "news_context": news_context or [],
            "scoring_guide": {
                "liquidity_sweep": 20,
                "mss_or_bos": 20,
                "fvg_or_ifvg": 20,
                "order_block_or_ote": 15,
                "session_timing": 10,
                "news_safety": 15,
            },
            "rule": "Penalize high-impact nearby news. Never promise profit.",
        },
    )
    return await _generate_structured(AISetupResponse, prompt, fallback)


async def summarize_news_for_symbol(
    symbol: str,
    news_events: list[dict[str, Any]],
) -> AINewsSummaryResponse:
    """Summarize news context for a symbol without duplicating news detection logic."""
    fallback = AINewsSummaryResponse(
        symbol=symbol,
        sentiment="neutral",
        summary="AI news summary unavailable.",
        important_events=[],
        confidence=0,
        risk_warning=EDUCATIONAL_WARNING,
    )
    prompt = _prompt(
        "Summarize the important news risks for this symbol.",
        {
            "symbol": symbol,
            "news_events": news_events,
            "symbol_focus": {
                "XAUUSD": ["USD", "CPI", "NFP", "FOMC", "interest rates", "Fed speech"],
                "EURUSD": ["EUR", "USD"],
                "GBPUSD": ["GBP", "USD"],
                "BTCUSD": ["USD", "Fed", "CPI", "FOMC", "risk sentiment"],
            },
        },
    )
    return await _generate_structured(AINewsSummaryResponse, prompt, fallback)


async def create_risk_warning(
    symbol: str,
    ict_analysis: dict[str, Any],
    news_context: list[dict[str, Any]] | None,
    account_risk: dict[str, Any] | None = None,
) -> AIRiskWarningResponse:
    """Create a pre-trade risk warning; this function never permits auto-trading."""
    fallback = _fallback_risk_warning(ict_analysis, news_context)
    prompt = _prompt(
        "Create a risk warning for this possible trade.",
        {
            "symbol": symbol,
            "ict_analysis": ict_analysis,
            "news_context": news_context or [],
            "account_risk": account_risk or {},
            "checks": [
                "high-impact news",
                "low setup score",
                "unclear bias",
                "wide stop loss",
                "overtrading risk",
            ],
        },
    )
    return await _generate_structured(AIRiskWarningResponse, prompt, fallback)


async def review_trade_journal(trades: list[dict[str, Any]]) -> AIJournalReviewResponse:
    """Review historical trades and return constructive coaching only."""
    fallback = AIJournalReviewResponse(
        summary="AI journal review unavailable.",
        strengths=[],
        mistakes=[],
        best_conditions=[],
        improvement_plan=["Review risk per trade and wait for clear confirmation."],
        risk_notes=[EDUCATIONAL_WARNING],
    )
    prompt = _prompt(
        "Review these past trades constructively. Do not shame the user.",
        {"trades": trades},
    )
    return await _generate_structured(AIJournalReviewResponse, prompt, fallback)


async def full_ai_analysis(
    symbol: str,
    timeframe: str,
    ict_analysis: dict[str, Any],
    news_context: list[dict[str, Any]] | None,
    account_risk: dict[str, Any] | None = None,
) -> AIFullAnalysisResponse:
    """Combine setup explanation, score, news, and risk warning for the frontend."""
    setup_score = int(ict_analysis.get("score") or 0)
    fallback = AIFullAnalysisResponse(
        symbol=symbol,
        timeframe=timeframe,
        bias=_bias_from_ict(ict_analysis),
        score=setup_score,
        grade=_grade(setup_score),
        confidence=0,
        summary="AI analysis unavailable.",
        explanation=[],
        news_summary="AI news summary unavailable.",
        risk_warning="Do not trade based only on unavailable AI analysis.",
        can_trade=False,
        suggested_action="wait",
        important_levels={
            "entry_zone": ict_analysis.get("entry_zone"),
            "stop_loss": ict_analysis.get("stop_loss"),
            "take_profit": ict_analysis.get("take_profit"),
        },
    )
    prompt = _prompt(
        "Create one complete frontend-friendly AI analysis.",
        {
            "symbol": symbol,
            "timeframe": timeframe,
            "ict_analysis": ict_analysis,
            "news_context": news_context or [],
            "account_risk": account_risk or {},
        },
    )
    return await _generate_structured(AIFullAnalysisResponse, prompt, fallback)


def save_ai_analysis(
    db: Session,
    analysis_type: str,
    raw_input: dict[str, Any],
    raw_output: BaseModel,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> AIAnalysis:
    output = jsonable_encoder(raw_output)
    record = AIAnalysis(
        symbol=symbol,
        timeframe=timeframe,
        analysis_type=analysis_type,
        sentiment=output.get("bias") or output.get("sentiment") or "neutral",
        score=output.get("score"),
        confidence=output.get("confidence"),
        summary=output.get("summary"),
        risk_warning=output.get("risk_warning") or output.get("warning"),
        recommendation=output.get("suggested_action") or output.get("recommendation"),
        raw_input=jsonable_encoder(raw_input),
        raw_output=output,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


async def _generate_structured(
    response_model: type[T],
    prompt: str,
    fallback: T,
) -> T:
    client = _client()
    if client is None:
        return fallback

    schema = response_model.model_json_schema()
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a trading analysis assistant. Return only valid JSON. "
                        "Never execute trades, promise profit, or guarantee win rate. "
                        f"Always include this safety stance: {EDUCATIONAL_WARNING}"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": schema,
                    "strict": True,
                },
            },
        )
        content = response.choices[0].message.content or "{}"
        return response_model.model_validate(json.loads(content))
    except (OpenAIError, json.JSONDecodeError, ValidationError, IndexError, KeyError):
        return fallback


def _prompt(task: str, payload: dict[str, Any]) -> str:
    return json.dumps(
        {
            "task": task,
            "payload": payload,
            "hard_rules": [
                "Do not execute trades.",
                "Do not give buy or sell orders.",
                "Do not guarantee profit or win rate.",
                "Always include risk warning and educational decision-support framing.",
                "If news risk is high, suggest waiting or avoiding.",
                "If ICT signal is weak, suggest waiting.",
            ],
        },
        default=str,
    )


def _fallback_setup_response(ict_analysis: dict[str, Any]) -> AISetupResponse:
    score = int(ict_analysis.get("score") or 0)
    return AISetupResponse(
        bias=_bias_from_ict(ict_analysis),
        summary="AI analysis unavailable.",
        explanation=[],
        missing_confirmations=["Use ICT and news context manually before making decisions."],
        score=score,
        grade=_grade(score),
        reason="OpenAI analysis could not be completed.",
        strengths=[],
        weaknesses=["AI analysis unavailable."],
        confidence=0,
        risk_warning="Do not trade based only on unavailable AI analysis.",
    )


def _fallback_risk_warning(
    ict_analysis: dict[str, Any],
    news_context: list[dict[str, Any]] | None,
) -> AIRiskWarningResponse:
    score = int(ict_analysis.get("score") or 0)
    high_news = any(str(item.get("impact", "")).lower() == "high" for item in news_context or [])
    risk_level = "high" if high_news or score < 50 else "medium"
    return AIRiskWarningResponse(
        can_trade=False if risk_level == "high" else score >= 70,
        risk_level=risk_level,
        warning="Risk review is conservative because AI analysis is unavailable.",
        reasons=["AI analysis unavailable.", EDUCATIONAL_WARNING],
        suggested_action="avoid" if high_news else "wait",
    )


def _bias_from_ict(ict_analysis: dict[str, Any]) -> str:
    bias = str(ict_analysis.get("bias", "neutral")).lower()
    return bias if bias in {"bullish", "bearish", "neutral"} else "neutral"


def _grade(score: int) -> str:
    # Grade is deliberately simple so route tests can assert deterministic output.
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"
