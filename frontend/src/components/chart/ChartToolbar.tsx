import type { SymbolCode, Timeframe } from "../../types/market";

export const SYMBOLS: SymbolCode[] = ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSD", "NQ"];
export const TIMEFRAMES: Timeframe[] = ["M1", "M5", "M15", "H1", "H4", "D1"];

export function ChartToolbar({
  symbol,
  timeframe,
  onSymbolChange,
  onTimeframeChange,
}: {
  symbol: SymbolCode;
  timeframe: Timeframe;
  onSymbolChange: (value: SymbolCode) => void;
  onTimeframeChange: (value: Timeframe) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md border border-line bg-slate-900 p-2">
      <select
        value={symbol}
        onChange={(event) => onSymbolChange(event.target.value as SymbolCode)}
        className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
      >
        {SYMBOLS.map((item) => (
          <option key={item}>{item}</option>
        ))}
      </select>
      <select
        value={timeframe}
        onChange={(event) => onTimeframeChange(event.target.value as Timeframe)}
        className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
      >
        {TIMEFRAMES.map((item) => (
          <option key={item}>{item}</option>
        ))}
      </select>
    </div>
  );
}
