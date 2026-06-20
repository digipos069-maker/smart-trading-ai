export interface SwingPoint {
  time: string;
  index: number;
  price: number;
  type: string;
}

export interface StructureEvent {
  time: string;
  index: number;
  direction: string;
  broken_level: number;
  confidence: number;
}

export interface LiquiditySweep {
  time: string;
  index: number;
  direction: string;
  swept_level: number;
  candle_high: number;
  candle_low: number;
}

export interface FVG {
  time: string;
  index: number;
  direction: string;
  upper: number;
  lower: number;
  midpoint: number;
  is_filled?: boolean;
}

export interface IFVG {
  time: string;
  index: number;
  original_fvg_index: number;
  direction: string;
  upper: number;
  lower: number;
  midpoint: number;
}

export interface OrderBlock {
  time: string;
  index: number;
  direction: string;
  high: number;
  low: number;
  midpoint: number;
  bos_index: number;
}

export interface OTEZone {
  direction: string;
  ote_low: number;
  ote_high: number;
  fib_62: number;
  fib_705: number;
  fib_79: number;
}

export interface TradeModel {
  name: string;
  direction: string;
  confidence: number;
  reason: string;
  entry_zone?: Record<string, number> | null;
  invalid_level?: number | null;
  target_level?: number | null;
}

export interface ICTAnalysis {
  symbol: string;
  timeframe: string;
  bias: string;
  score: number;
  setup_type: string;
  swing_points: SwingPoint[];
  bos_events: StructureEvent[];
  mss_events: StructureEvent[];
  liquidity_sweeps: LiquiditySweep[];
  fvgs: FVG[];
  ifvgs: IFVG[];
  order_blocks: OrderBlock[];
  ote_zones: OTEZone[];
  session_ranges: unknown[];
  trade_models: TradeModel[];
  entry_zone: Record<string, number> | null;
  stop_loss: number | null;
  take_profit: number | null;
  explanation: string[];
}
