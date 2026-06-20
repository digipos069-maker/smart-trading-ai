import { useState } from "react";

import { SYMBOLS } from "../components/chart/ChartToolbar";
import { NewsRiskPanel } from "../components/panels/NewsRiskPanel";
import { useNewsRisk } from "../hooks/useNewsRisk";
import type { SymbolCode } from "../types/market";

export function NewsPage() {
  const [symbol, setSymbol] = useState<SymbolCode>("XAUUSD");
  const newsRisk = useNewsRisk(symbol);

  return (
    <div className="max-w-3xl space-y-4">
      <select
        value={symbol}
        onChange={(event) => setSymbol(event.target.value as SymbolCode)}
        className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
      >
        {SYMBOLS.map((item) => (
          <option key={item}>{item}</option>
        ))}
      </select>
      <NewsRiskPanel newsRisk={newsRisk.data} loading={newsRisk.isLoading} error={newsRisk.error} />
      <div className="rounded-md border border-line bg-slate-900 p-4 text-sm text-slate-400">
        News endpoints are treated as live API data. No placeholder news is rendered when the API is unavailable.
      </div>
    </div>
  );
}
