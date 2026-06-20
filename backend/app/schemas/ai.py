from typing import Any, Literal

from pydantic import BaseModel, Field

Bias = Literal["bullish", "bearish", "neutral"]
AnalysisType = Literal[
    "setup_explanation",
    "setup_score",
    "news_summary",
    "risk_warning",
    "journal_review",
    "backtest_review",
    "full_analysis",
]
SuggestedAction = Literal["wait", "avoid", "reduce_risk", "normal"]


class AISetupRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "M5"
    ict_analysis: dict[str, Any]
    news_context: list[dict[str, Any]] | None = None


class AISetupResponse(BaseModel):
    bias: Bias
    summary: str
    explanation: list[str] = []
    missing_confirmations: list[str] = []
    score: int = Field(default=0, ge=0, le=100)
    grade: Literal["A", "B", "C", "D"] = "D"
    reason: str = ""
    strengths: list[str] = []
    weaknesses: list[str] = []
    confidence: float = Field(ge=0, le=100)
    risk_warning: str


class AINewsSummaryRequest(BaseModel):
    symbol: str = "XAUUSD"
    news_events: list[dict[str, Any]]


class AINewsSummaryResponse(BaseModel):
    symbol: str
    sentiment: Bias
    summary: str
    important_events: list[str]
    confidence: float = Field(ge=0, le=100)
    risk_warning: str


class AIRiskWarningRequest(BaseModel):
    symbol: str = "XAUUSD"
    ict_analysis: dict[str, Any]
    news_context: list[dict[str, Any]] | None = None
    account_risk: dict[str, Any] | None = None


class AIRiskWarningResponse(BaseModel):
    can_trade: bool
    risk_level: Literal["low", "medium", "high"]
    warning: str
    reasons: list[str]
    suggested_action: SuggestedAction


class AIJournalReviewRequest(BaseModel):
    trades: list[dict[str, Any]]


class AIJournalReviewResponse(BaseModel):
    summary: str
    strengths: list[str]
    mistakes: list[str]
    best_conditions: list[str]
    improvement_plan: list[str]
    risk_notes: list[str]


class AIBacktestReviewRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "M5"
    strategy_name: str = "ict_liquidity_mss_fvg"
    metrics: dict[str, Any]
    trades: list[dict[str, Any]]


class AIBacktestReviewResponse(BaseModel):
    summary: str
    performance_grade: Literal["A", "B", "C", "D"]
    strengths: list[str]
    weaknesses: list[str]
    best_conditions: list[str]
    worst_conditions: list[str]
    risk_notes: list[str]
    improvement_plan: list[str]
    confidence: float = Field(ge=0, le=100)
    warning: str


class AIFullAnalysisRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "M5"
    ict_analysis: dict[str, Any]
    news_context: list[dict[str, Any]] | None = None
    account_risk: dict[str, Any] | None = None


class AIFullAnalysisResponse(BaseModel):
    symbol: str
    timeframe: str
    bias: Bias
    score: int = Field(ge=0, le=100)
    grade: Literal["A", "B", "C", "D"]
    confidence: float = Field(ge=0, le=100)
    summary: str
    explanation: list[str]
    news_summary: str
    risk_warning: str
    can_trade: bool
    suggested_action: SuggestedAction
    important_levels: dict[str, Any]
