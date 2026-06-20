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
  if (loading) return <LoadingBlock label="Loading AI analysis" />;
  if (error) return <ErrorState message="AI analysis unavailable." />;
  if (!analysis) return <EmptyState message="No AI analysis loaded." />;

  return (
    <section className="rounded-md border border-line bg-slate-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-100">AI Analysis</h2>
        <span className="rounded bg-slate-950 px-2 py-1 text-xs text-cyan-200">
          Grade {analysis.grade}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <Box label="Bias" value={analysis.bias} />
        <Box label="Score" value={analysis.score} />
        <Box label="Conf." value={`${analysis.confidence}%`} />
      </div>
      <p className="mt-4 text-sm text-slate-300">{analysis.summary}</p>
      <div className="mt-4 space-y-3 text-xs text-slate-400">
        <div>
          <div className="mb-1 text-slate-500">Explanation</div>
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
        <div className="text-slate-300">Suggested action: {analysis.suggested_action}</div>
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
