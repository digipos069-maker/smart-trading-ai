from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NewsEventBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    source: str = Field(default="manual", max_length=128)
    url: str | None = None
    symbol: str | None = Field(default=None, max_length=32)
    currency: str | None = Field(default=None, max_length=16)
    category: str | None = Field(default=None, max_length=64)
    published_at: datetime


class NewsEventCreate(NewsEventBase):
    summary: str | None = None


class NewsEventResponse(NewsEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    summary: str | None = None
    sentiment: str
    impact: str
    relevance_score: int = Field(ge=0, le=100)
    created_at: datetime


class NewsAnalysisResponse(BaseModel):
    sentiment: str
    impact: str
    relevance_score: int = Field(ge=0, le=100)
    reasons: list[str]


class NewsListResponse(BaseModel):
    count: int
    events: list[NewsEventResponse]
