import { apiClient } from "./apiClient";
import type { NewsRisk } from "../types/news";
import type { SymbolCode } from "../types/market";

export async function fetchNewsRisk(symbol: SymbolCode) {
  const { data } = await apiClient.get<NewsRisk>("/news/risk", {
    params: { symbol },
  });
  return data;
}

export async function fetchNewsAnalysis(symbol: SymbolCode) {
  const { data } = await apiClient.get("/news/analyze", { params: { symbol } });
  return data;
}
