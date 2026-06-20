import type { BacktestResponse } from "../../types/backtest";
import { MetricCard } from "../ui/MetricCard";
import { EmptyState } from "../ui/State";
import { useTranslation } from "react-i18next";

export function BacktestResultPanel({ result }: { result?: BacktestResponse }) {
  const { t } = useTranslation();

  if (!result) return <EmptyState message={t("backtest.empty")} />;
  const metrics = result.metrics;
  return (
    <section className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Trades" value={metrics.total_trades} />
        <MetricCard label="Win rate" value={`${metrics.win_rate}%`} tone="good" />
        <MetricCard label="Profit factor" value={metrics.profit_factor} />
        <MetricCard label="Net R" value={metrics.net_r} tone={metrics.net_r >= 0 ? "good" : "bad"} />
        <MetricCard label="P/L" value={metrics.net_profit_loss} tone={metrics.net_profit_loss >= 0 ? "good" : "bad"} />
        <MetricCard label="Return" value={`${metrics.return_percent}%`} />
        <MetricCard label="Max DD" value={metrics.max_drawdown} tone="bad" />
        <MetricCard label="Best session" value={metrics.best_session ?? "-"} />
      </div>
      <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-100">
        {result.warning}
      </div>
      <div className="overflow-auto rounded-md border border-line">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-900 text-xs text-slate-500">
            <tr>
              <th className="px-3 py-2">Entry</th>
              <th className="px-3 py-2">Dir</th>
              <th className="px-3 py-2">Session</th>
              <th className="px-3 py-2">Result</th>
              <th className="px-3 py-2">R</th>
              <th className="px-3 py-2">P/L</th>
              <th className="px-3 py-2">Models</th>
            </tr>
          </thead>
          <tbody>
            {result.trades.map((trade) => (
              <tr key={`${trade.entry_time}-${trade.exit_time}`} className="border-t border-line">
                <td className="px-3 py-2 text-slate-300">{new Date(trade.entry_time).toLocaleString()}</td>
                <td
                  className={[
                    "px-3 py-2 capitalize",
                    trade.direction === "bearish" ? "text-red-300" : "text-emerald-300",
                  ].join(" ")}
                >
                  {trade.direction}
                </td>
                <td className="px-3 py-2">{trade.session}</td>
                <td
                  className={[
                    "px-3 py-2 capitalize",
                    trade.result === "win"
                      ? "text-emerald-300"
                      : trade.result === "loss"
                        ? "text-red-300"
                        : "text-slate-300",
                  ].join(" ")}
                >
                  {trade.result}
                </td>
                <td className="px-3 py-2">{trade.r_multiple}</td>
                <td className={trade.profit_loss >= 0 ? "px-3 py-2 text-emerald-300" : "px-3 py-2 text-red-300"}>
                  {trade.profit_loss}
                </td>
                <td className="px-3 py-2 text-slate-400">{trade.trade_models?.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
