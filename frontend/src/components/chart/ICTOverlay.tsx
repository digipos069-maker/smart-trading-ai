import type { ICTAnalysis } from "../../types/ict";

export function ICTOverlay({ analysis }: { analysis?: ICTAnalysis }) {
  if (!analysis) return null;
  return (
    <div className="grid gap-2 text-xs text-slate-300 sm:grid-cols-2 lg:grid-cols-4">
      <OverlayItem label="FVG" value={analysis.fvgs.length} />
      <OverlayItem label="IFVG" value={analysis.ifvgs.length} />
      <OverlayItem label="Order blocks" value={analysis.order_blocks.length} />
      <OverlayItem label="Sweeps" value={analysis.liquidity_sweeps.length} />
    </div>
  );
}

function OverlayItem({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-slate-900 px-3 py-2">
      <span className="text-slate-500">{label}</span>
      <span className="ml-2 font-semibold text-slate-100">{value}</span>
    </div>
  );
}
