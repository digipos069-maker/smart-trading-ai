import { apiClient } from "./apiClient";
import type { BacktestRequest, BacktestResponse, BacktestSummary } from "../types/backtest";

export async function runBacktest(payload: BacktestRequest) {
  const { data } = await apiClient.post<BacktestResponse>("/backtest/run", payload);
  return data;
}

export async function fetchBacktestResults() {
  const { data } = await apiClient.get<BacktestSummary[]>("/backtest/results");
  return data;
}

export async function fetchBacktestResult(id: number) {
  const { data } = await apiClient.get<BacktestResponse>(`/backtest/results/${id}`);
  return data;
}
