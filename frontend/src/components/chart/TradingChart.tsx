import {
  ColorType,
  createChart,
  createSeriesMarkers,
  CandlestickSeries,
  type IChartApi,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type IPriceLine,
  type SeriesMarker,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

import type { ICTAnalysis } from "../../types/ict";
import type { Candle } from "../../types/market";
import { EmptyState, LoadingBlock } from "../ui/State";

const MIN_LABEL_CONFIDENCE = 70;

export function TradingChart({
  candles,
  analysis,
  loading,
}: {
  candles?: Candle[];
  analysis?: ICTAnalysis;
  loading?: boolean;
}) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const markersRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);
  const priceLinesRef = useRef<IPriceLine[]>([]);

  useEffect(() => {
    if (!containerRef.current || chartRef.current) return;
    const chart = createChart(containerRef.current, {
      height: 520,
      layout: {
        background: { type: ColorType.Solid, color: "#020617" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "#111827" },
        horzLines: { color: "#111827" },
      },
      rightPriceScale: { borderColor: "#1f2937" },
      localization: {
        timeFormatter: formatLocalDateTime,
      },
      timeScale: {
        borderColor: "#1f2937",
        timeVisible: true,
        tickMarkFormatter: formatLocalTick,
      },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });
    chartRef.current = chart;
    seriesRef.current = series;
    markersRef.current = createSeriesMarkers(series, []);

    const resize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      markersRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    if (!candles?.length) {
      seriesRef.current.setData([]);
      markersRef.current?.setMarkers([]);
      return;
    }
    const data = candles.map((candle) => ({
      time: Math.floor(new Date(candle.time).getTime() / 1000) as UTCTimestamp,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));
    seriesRef.current.setData(data);
    markersRef.current?.setMarkers(buildMarkers(analysis));
    seriesRef.current.priceScale().applyOptions({ autoScale: true });
    chartRef.current?.timeScale().fitContent();
  }, [candles, analysis]);

  useEffect(() => {
    if (!seriesRef.current) return;
    priceLinesRef.current.forEach((line) => seriesRef.current?.removePriceLine(line));
    priceLinesRef.current = [];

    if (!hasHighConfidenceAnalysis(analysis)) return;

    const lines = [
      analysis.entry_zone
        ? {
            price: (analysis.entry_zone.low + analysis.entry_zone.high) / 2,
            color: "#38bdf8",
            title: "Entry",
          }
        : null,
      analysis.stop_loss ? { price: analysis.stop_loss, color: "#ef4444", title: "SL" } : null,
      analysis.take_profit ? { price: analysis.take_profit, color: "#22c55e", title: "TP" } : null,
    ].filter(Boolean) as { price: number; color: string; title: string }[];
    priceLinesRef.current = lines.map((line) =>
      seriesRef.current!.createPriceLine({
        price: line.price,
        color: line.color,
        lineWidth: 1,
        title: line.title,
      }),
    );
  }, [analysis]);

  return (
    <div className="relative min-h-[520px] rounded-md border border-line">
      <div ref={containerRef} className="min-h-[520px]" />
      {loading ? (
        <div className="absolute inset-0 bg-slate-950/80 p-4">
          <LoadingBlock label={t("states.loadingChart")} />
        </div>
      ) : null}
      {!loading && !candles?.length ? (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 p-4">
          <EmptyState message={t("states.noCandles")} />
        </div>
      ) : null}
    </div>
  );
}

function buildMarkers(analysis?: ICTAnalysis): SeriesMarker<Time>[] {
  if (!hasHighConfidenceAnalysis(analysis)) return [];
  return [
    ...analysis.liquidity_sweeps.map((item) => ({
      time: Math.floor(new Date(item.time).getTime() / 1000) as UTCTimestamp,
      position: item.direction === "sell_side" ? "belowBar" as const : "aboveBar" as const,
      color: "#f59e0b",
      shape: "circle" as const,
      text: item.direction === "sell_side" ? "SSL" : "BSL",
    })),
    ...analysis.bos_events.map((item) => ({
      time: Math.floor(new Date(item.time).getTime() / 1000) as UTCTimestamp,
      position: item.direction === "bullish" ? "aboveBar" as const : "belowBar" as const,
      color: "#38bdf8",
      shape: "arrowUp" as const,
      text: "BOS",
    })),
    ...analysis.mss_events.map((item) => ({
      time: Math.floor(new Date(item.time).getTime() / 1000) as UTCTimestamp,
      position: item.direction === "bullish" ? "aboveBar" as const : "belowBar" as const,
      color: "#a78bfa",
      shape: "arrowDown" as const,
      text: "MSS",
    })),
  ];
}

function hasHighConfidenceAnalysis(analysis?: ICTAnalysis): analysis is ICTAnalysis {
  return Boolean(analysis && analysis.score > MIN_LABEL_CONFIDENCE);
}

function formatLocalDateTime(time: Time): string {
  const date = chartTimeToDate(time);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatLocalTick(time: Time): string {
  const date = chartTimeToDate(time);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function chartTimeToDate(time: Time): Date {
  if (typeof time === "number") {
    return new Date(time * 1000);
  }

  if (typeof time === "string") {
    return new Date(time);
  }

  return new Date(time.year, time.month - 1, time.day);
}
