export type SymbolCode = "XAUUSD" | "EURUSD" | "GBPUSD" | "BTCUSD" | "NQ";
export type Timeframe = "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1";

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  tick_volume: number;
  spread: number;
}

export interface MarketDataResponse {
  provider: string;
  symbol: string;
  timeframe: string;
  count: number;
  candles: Candle[];
}
