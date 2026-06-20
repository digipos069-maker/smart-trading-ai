import { useTranslation } from "react-i18next";

import type { ICTAnalysis } from "../../types/ict";
import { EmptyState, LoadingBlock } from "../ui/State";

export function ICTSignalPanel({
  analysis,
  loading,
}: {
  analysis?: ICTAnalysis;
  loading?: boolean;
}) {
  const { t } = useTranslation();

  if (loading) return <LoadingBlock label={t("states.loadingIct")} />;
  if (!analysis) return <EmptyState message={t("states.noIct")} />;

  const biasClass =
    analysis.bias === "bullish"
      ? "text-emerald-300"
      : analysis.bias === "bearish"
        ? "text-red-300"
        : "text-slate-300";

  return (
    <section className="rounded-md border border-line bg-slate-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-100">{t("panels.ictSignal")}</h2>
        <span className={`text-sm font-semibold uppercase ${biasClass}`}>{analysis.bias}</span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <Info label={t("common.score")} value={analysis.score} />
        <Info label={t("common.setup")} value={analysis.setup_type} />
        <Info label={t("common.entry")} value={formatZone(analysis.entry_zone)} />
        <Info label="SL" value={formatNumber(analysis.stop_loss)} />
        <Info label="TP" value={formatNumber(analysis.take_profit)} />
        <Info label={t("common.models")} value={analysis.trade_models.map((item) => item.name).join(", ") || "-"} />
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <Count label="FVG" value={analysis.fvgs.length} />
        <Count label="Sweeps" value={analysis.liquidity_sweeps.length} />
        <Count label="BOS/MSS" value={analysis.bos_events.length + analysis.mss_events.length} />
      </div>
      <ul className="mt-4 space-y-2 text-xs text-slate-400">
        {analysis.explanation.map((item) => (
          <li key={item}>• {item}</li>
        ))}
      </ul>
    </section>
  );
}

function Info({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md bg-slate-950 p-2">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 truncate text-slate-200">{value}</div>
    </div>
  );
}

function Count({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-slate-950 p-2 text-center">
      <div className="text-slate-500">{label}</div>
      <div className="font-semibold text-slate-100">{value}</div>
    </div>
  );
}

function formatNumber(value?: number | null) {
  return typeof value === "number" ? value.toFixed(2) : "-";
}

function formatZone(zone?: Record<string, number> | null) {
  if (!zone) return "-";
  return `${formatNumber(zone.low)} - ${formatNumber(zone.high)}`;
}
