from app.schemas.news import NewsAnalysisResponse, NewsEventCreate

HIGH_IMPACT_KEYWORDS = {
    "cpi",
    "fomc",
    "interest rate",
    "rate decision",
    "nfp",
    "nonfarm",
    "inflation",
    "fed",
    "ecb",
    "boe",
    "war",
    "geopolitical",
}
MEDIUM_IMPACT_KEYWORDS = {
    "gdp",
    "retail sales",
    "pmi",
    "unemployment",
    "jobless",
    "consumer confidence",
}
BULLISH_KEYWORDS = {"beats", "higher", "surges", "rises", "hawkish", "strong"}
BEARISH_KEYWORDS = {"misses", "lower", "falls", "drops", "dovish", "weak"}


def analyze_news_event(event: NewsEventCreate) -> NewsAnalysisResponse:
    text = f"{event.title} {event.summary or ''}".lower()
    reasons: list[str] = []

    high_matches = sorted(keyword for keyword in HIGH_IMPACT_KEYWORDS if keyword in text)
    medium_matches = sorted(keyword for keyword in MEDIUM_IMPACT_KEYWORDS if keyword in text)

    if high_matches:
        impact = "high"
        relevance_score = 90
        reasons.append(f"High-impact keywords detected: {', '.join(high_matches)}.")
    elif medium_matches:
        impact = "medium"
        relevance_score = 65
        reasons.append(f"Medium-impact keywords detected: {', '.join(medium_matches)}.")
    else:
        impact = "low"
        relevance_score = 35
        reasons.append("No major macro risk keywords detected.")

    bullish_hits = sum(1 for keyword in BULLISH_KEYWORDS if keyword in text)
    bearish_hits = sum(1 for keyword in BEARISH_KEYWORDS if keyword in text)

    if bullish_hits > bearish_hits:
        sentiment = "bullish"
        reasons.append("Bullish language appears stronger than bearish language.")
    elif bearish_hits > bullish_hits:
        sentiment = "bearish"
        reasons.append("Bearish language appears stronger than bullish language.")
    else:
        sentiment = "neutral"
        reasons.append("No clear directional sentiment detected.")

    return NewsAnalysisResponse(
        sentiment=sentiment,
        impact=impact,
        relevance_score=relevance_score,
        reasons=reasons,
    )
