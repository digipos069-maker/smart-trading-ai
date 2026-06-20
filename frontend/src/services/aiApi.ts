import { apiClient } from "./apiClient";
import type { FullAIAnalysis, FullAIAnalysisRequest } from "../types/ai";

export async function fetchFullAIAnalysis(payload: FullAIAnalysisRequest) {
  const { data } = await apiClient.post<FullAIAnalysis>("/ai/full-analysis", payload);
  return data;
}
