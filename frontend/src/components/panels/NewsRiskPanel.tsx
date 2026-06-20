import type { NewsRisk } from "../../types/news";
import { EmptyState, ErrorState, LoadingBlock } from "../ui/State";

export function NewsRiskPanel({
  newsRisk,
  loading,
  error,
}: {
  newsRisk?: NewsRisk;
  loading?: boolean;
  error?: Error | null;
}) {
  if (loading) return <LoadingBlock label="Loading news risk" />;
  if (error) return <ErrorState message="News risk API unavailable." />;
  if (!newsRisk) return <EmptyState message="No news risk available." />;

  const highRisk = newsRisk.risk_level === "high";
  return (
    <section
      className={[
        "rounded-md border p-4",
        highRisk ? "border-red-500/40 bg-red-950/30" : "border-line bg-slate-900",
      ].join(" ")}
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-100">News Risk</h2>
        <span className={highRisk ? "text-red-300" : "text-emerald-300"}>
          {newsRisk.can_trade ? "Can trade" : "Wait"}
        </span>
      </div>
      <div className="space-y-2 text-sm text-slate-300">
        <Row label="Risk" value={newsRisk.risk_level} />
        <Row label="Blocking event" value={newsRisk.blocking_event ?? "-"} />
        <Row
          label="Minutes to event"
          value={newsRisk.minutes_to_event === undefined ? "-" : String(newsRisk.minutes_to_event)}
        />
        <p className="pt-2 text-xs text-slate-400">
          {newsRisk.reason ?? newsRisk.warning ?? newsRisk.reasons?.join(" ") ?? "No reason supplied."}
        </p>
      </div>
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-slate-500">{label}</span>
      <span className="text-right capitalize">{value}</span>
    </div>
  );
}
