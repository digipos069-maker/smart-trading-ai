import { useState } from "react";

import { ChartToolbar } from "../components/chart/ChartToolbar";
import { ICTOverlay } from "../components/chart/ICTOverlay";
import { TradingChart } from "../components/chart/TradingChart";
import { AIAnalysisPanel } from "../components/panels/AIAnalysisPanel";
import { ICTSignalPanel } from "../components/panels/ICTSignalPanel";
import { NewsRiskPanel } from "../components/panels/NewsRiskPanel";
import { ErrorState } from "../components/ui/State";
import { useCandles } from "../hooks/useCandles";
import { useFullAIAnalysis } from "../hooks/useFullAIAnalysis";
import { useICTAnalysis } from "../hooks/useICTAnalysis";
import { useNewsRisk } from "../hooks/useNewsRisk";
import type { SymbolCode, Timeframe } from "../types/market";

export function DashboardPage() {
  const [symbol, setSymbol] = useState<SymbolCode>("XAUUSD");
  const [timeframe, setTimeframe] = useState<Timeframe>("M5");
  const candles = useCandles(symbol, timeframe);
  const ict = useICTAnalysis(symbol, timeframe);
  const newsRisk = useNewsRisk(symbol);
  const ai = useFullAIAnalysis(symbol, timeframe, ict.data, newsRisk.data);

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
      <section className="min-w-0 space-y-4">
        <ChartToolbar
          symbol={symbol}
          timeframe={timeframe}
          onSymbolChange={setSymbol}
          onTimeframeChange={setTimeframe}
        />
        {candles.error ? <ErrorState message={candles.error.message} /> : null}
        <TradingChart
          candles={candles.data?.candles}
          analysis={ict.data}
          loading={candles.isLoading}
        />
        <ICTOverlay analysis={ict.data} />
      </section>
      <aside className="space-y-4">
        <ICTSignalPanel analysis={ict.data} loading={ict.isLoading} />
        <NewsRiskPanel
          newsRisk={newsRisk.data}
          loading={newsRisk.isLoading}
          error={newsRisk.error}
        />
        <AIAnalysisPanel analysis={ai.data} loading={ai.isLoading} error={ai.error} />
      </aside>
    </div>
  );
}
