import { useQuery } from "@tanstack/react-query";

import { fetchICTAnalysis } from "../services/ictApi";
import type { SymbolCode, Timeframe } from "../types/market";

export function useICTAnalysis(symbol: SymbolCode, timeframe: Timeframe) {
  return useQuery({
    queryKey: ["ict", symbol, timeframe],
    queryFn: () => fetchICTAnalysis({ symbol, timeframe, limit: 500 }),
  });
}
