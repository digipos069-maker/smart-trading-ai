import { apiClient } from "./apiClient";
import type { ICTAnalysis } from "../types/ict";
import type { SymbolCode, Timeframe } from "../types/market";

export async function fetchICTAnalysis(params: {
  symbol: SymbolCode;
  timeframe: Timeframe;
  limit?: number;
}) {
  const { data } = await apiClient.get<ICTAnalysis>("/ict/analyze", {
    params: { ...params, limit: params.limit ?? 500 },
  });
  return data;
}
