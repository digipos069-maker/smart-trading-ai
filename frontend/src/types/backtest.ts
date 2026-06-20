export interface BacktestRequest {
  name?: string | null;
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  risk_per_trade: number;
  min_score: number;
  min_rr?: number;
  target_rr?: number | null;
  allowed_trade_models?: string[] | null;
  initial_balance: number;
  session_filter?: string | null;
}

export interface BacktestTrade {
  entry_time: string;
  exit_time: string;
  symbol: string;
  timeframe: string;
  session: string;
  direction: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  risk_amount: number;
  profit_loss: number;
  balance_after: number;
  result: string;
  r_multiple: number;
  setup_score: number;
  setup_type: string;
  trade_models: string[];
}

export interface BacktestMetrics {
  initial_balance: number;
  ending_balance: number;
  net_profit_loss: number;
  return_percent: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  net_r: number;
  expectancy: number;
  best_session: string | null;
}

export interface BacktestResponse {
  id: number | null;
  name: string | null;
  symbol: string;
  timeframe: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  warning: string;
  metrics: BacktestMetrics;
  trades: BacktestTrade[];
}

export interface BacktestSummary {
  id: number;
  name: string | null;
  symbol: string;
  timeframe: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  net_r: number;
  created_at: string;
}
