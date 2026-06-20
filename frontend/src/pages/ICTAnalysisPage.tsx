import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ChartToolbar } from "../components/chart/ChartToolbar";
import { ICTSignalPanel } from "../components/panels/ICTSignalPanel";
import { useICTAnalysis } from "../hooks/useICTAnalysis";
import type { SymbolCode, Timeframe } from "../types/market";

export function ICTAnalysisPage() {
  const { t } = useTranslation();
  const [symbol, setSymbol] = useState<SymbolCode>("XAUUSD");
  const [timeframe, setTimeframe] = useState<Timeframe>("M5");
  const ict = useICTAnalysis(symbol, timeframe);

  return (
    <div className="space-y-4">
      <ChartToolbar
        symbol={symbol}
        timeframe={timeframe}
        onSymbolChange={setSymbol}
        onTimeframeChange={setTimeframe}
      />
      <ICTSignalPanel analysis={ict.data} loading={ict.isLoading} />
      <section className="rounded-md border border-line bg-slate-900 p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-100">
          {t("panels.detectedTradeModels")}
        </h2>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {ict.data?.trade_models.map((model) => (
            <div key={`${model.name}-${model.direction}`} className="rounded-md bg-slate-950 p-3">
              <div className="flex justify-between gap-3">
                <span className="font-medium text-cyan-200">{model.name}</span>
                <span>{model.confidence}%</span>
              </div>
              <p className="mt-2 text-sm text-slate-400">{model.reason}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
