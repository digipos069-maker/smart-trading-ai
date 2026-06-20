import { useQuery } from "@tanstack/react-query";

import { fetchCandles } from "../services/marketApi";
import type { SymbolCode, Timeframe } from "../types/market";

export function useCandles(symbol: SymbolCode, timeframe: Timeframe) {
  return useQuery({
    queryKey: ["candles", symbol, timeframe],
    queryFn: () => fetchCandles({ symbol, timeframe, limit: 500 }),
  });
}
