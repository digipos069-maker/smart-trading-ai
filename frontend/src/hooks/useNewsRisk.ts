import { useQuery } from "@tanstack/react-query";

import { fetchNewsRisk } from "../services/newsApi";
import type { SymbolCode } from "../types/market";

export function useNewsRisk(symbol: SymbolCode) {
  return useQuery({
    queryKey: ["news-risk", symbol],
    queryFn: () => fetchNewsRisk(symbol),
    retry: false,
  });
}
