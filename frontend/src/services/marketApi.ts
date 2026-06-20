import { apiClient } from "./apiClient";
import type { MarketDataResponse, SymbolCode, Timeframe } from "../types/market";

export async function fetchCandles(params: {
  symbol: SymbolCode;
  timeframe: Timeframe;
  limit?: number;
}) {
  const { data } = await apiClient.get<MarketDataResponse>("/market/candles", {
    params: { ...params, limit: params.limit ?? 500 },
  });
  return data;
}
