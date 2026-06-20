import { useTranslation } from "react-i18next";

import type { FullAIAnalysis } from "../../types/ai";
import { EmptyState, ErrorState, LoadingBlock } from "../ui/State";

export function AIAnalysisPanel({
  analysis,
  loading,
  error,
}: {
  analysis?: FullAIAnalysis;
  loading?: boolean;
  error?: Error | null;
}) {
  const { t } = useTranslation();

  if (loading) return <LoadingBlock label={t("states.loadingAi")} />;
  if (error) return <ErrorState message={t("states.aiUnavailable")} />;
  if (!analysis) return <EmptyState message={t("states.noAi")} />;

  return (
    <section className="rounded-md border border-line bg-slate-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-100">{t("panels.aiAnalysis")}</h2>
        <span className="rounded bg-slate-950 px-2 py-1 text-xs text-cyan-200">
          {t("common.grade")} {analysis.grade}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <Box label={t("common.bias")} value={analysis.bias} />
        <Box label={t("common.score")} value={analysis.score} />
        <Box label={t("common.confidence")} value={`${analysis.confidence}%`} />
      </div>
      <p className="mt-4 text-sm text-slate-300">{analysis.summary}</p>
      <div className="mt-4 space-y-3 text-xs text-slate-400">
        <div>
          <div className="mb-1 text-slate-500">{t("common.explanation")}</div>
          <ul className="space-y-1">
            {analysis.explanation.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
        <div>
          <div className="mb-1 text-slate-500">News</div>
          <p>{analysis.news_summary}</p>
        </div>
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-2 text-amber-200">
          {analysis.risk_warning}
        </div>
        <div className="text-slate-300">
          {t("common.suggestedAction")}: {analysis.suggested_action}
        </div>
      </div>
    </section>
  );
}

function Box({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md bg-slate-950 p-2">
      <div className="text-slate-500">{label}</div>
      <div className="mt-1 font-semibold text-slate-100">{value}</div>
    </div>
  );
}
