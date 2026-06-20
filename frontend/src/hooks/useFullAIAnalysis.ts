import { useQuery } from "@tanstack/react-query";

import { fetchFullAIAnalysis } from "../services/aiApi";
import type { ICTAnalysis } from "../types/ict";
import type { NewsRisk } from "../types/news";
import type { SymbolCode, Timeframe } from "../types/market";

export function useFullAIAnalysis(
  symbol: SymbolCode,
  timeframe: Timeframe,
  ictAnalysis?: ICTAnalysis,
  newsRisk?: NewsRisk,
) {
  return useQuery({
    queryKey: ["ai-full", symbol, timeframe, ictAnalysis?.score, newsRisk?.risk_level],
    queryFn: () =>
      fetchFullAIAnalysis({
        symbol,
        timeframe,
        ict_analysis: ictAnalysis as unknown as Record<string, unknown>,
        news_context: newsRisk ? [newsRisk as unknown as Record<string, unknown>] : [],
      }),
    enabled: Boolean(ictAnalysis),
    retry: false,
  });
}
