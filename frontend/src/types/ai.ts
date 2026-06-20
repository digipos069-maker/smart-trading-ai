export interface FullAIAnalysisRequest {
  symbol: string;
  timeframe: string;
  ict_analysis: Record<string, unknown>;
  news_context?: Record<string, unknown>[] | null;
  account_risk?: Record<string, unknown> | null;
}

export interface FullAIAnalysis {
  symbol: string;
  timeframe: string;
  bias: string;
  score: number;
  grade: "A" | "B" | "C" | "D";
  confidence: number;
  summary: string;
  explanation: string[];
  news_summary: string;
  risk_warning: string;
  can_trade: boolean;
  suggested_action: "wait" | "avoid" | "reduce_risk" | "normal";
  important_levels: Record<string, unknown>;
}
