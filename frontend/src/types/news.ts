export interface NewsRisk {
  can_trade: boolean;
  risk_level: "low" | "medium" | "high";
  blocking_event?: string | null;
  minutes_to_event?: number | null;
  reason?: string;
  warning?: string;
  reasons?: string[];
}
