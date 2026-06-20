import {
  ColorType,
  createChart,
  CandlestickSeries,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

import type { ICTAnalysis } from "../../types/ict";
import type { Candle } from "../../types/market";
import { EmptyState, LoadingBlock } from "../ui/State";

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
      timeScale: { borderColor: "#1f2937", timeVisible: true },
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
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !candles?.length) return;
    const data = candles.map((candle) => ({
      time: Math.floor(new Date(candle.time).getTime() / 1000) as UTCTimestamp,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));
    seriesRef.current.setData(data);
    seriesRef.current.setMarkers(
      buildMarkers(analysis).map((marker) => ({
        ...marker,
        time: marker.time as UTCTimestamp,
      })),
    );
    seriesRef.current.priceScale().applyOptions({ autoScale: true });
    chartRef.current?.timeScale().fitContent();
  }, [candles, analysis]);

  useEffect(() => {
    if (!seriesRef.current || !analysis) return;
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
    lines.forEach((line) =>
      seriesRef.current?.createPriceLine({
        price: line.price,
        color: line.color,
        lineWidth: 1,
        title: line.title,
      }),
    );
  }, [analysis]);

  if (loading) return <LoadingBlock label={t("states.loadingChart")} />;
  if (!candles?.length) return <EmptyState message={t("states.noCandles")} />;

  return <div ref={containerRef} className="min-h-[520px] rounded-md border border-line" />;
}

function buildMarkers(analysis?: ICTAnalysis) {
  if (!analysis) return [];
  return [
    ...analysis.liquidity_sweeps.map((item) => ({
      time: Math.floor(new Date(item.time).getTime() / 1000),
      position: item.direction === "sell_side" ? "belowBar" : "aboveBar",
      color: "#f59e0b",
      shape: "circle",
      text: item.direction === "sell_side" ? "SSL" : "BSL",
    })),
    ...analysis.bos_events.map((item) => ({
      time: Math.floor(new Date(item.time).getTime() / 1000),
      position: item.direction === "bullish" ? "aboveBar" : "belowBar",
      color: "#38bdf8",
      shape: "arrowUp",
      text: "BOS",
    })),
    ...analysis.mss_events.map((item) => ({
      time: Math.floor(new Date(item.time).getTime() / 1000),
      position: item.direction === "bullish" ? "aboveBar" : "belowBar",
      color: "#a78bfa",
      shape: "arrowDown",
      text: "MSS",
    })),
  ];
}
