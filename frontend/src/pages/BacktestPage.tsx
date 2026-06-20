import { useMutation, useQuery } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";

import { BacktestResultPanel } from "../components/panels/BacktestResultPanel";
import { ErrorState, LoadingBlock } from "../components/ui/State";
import { fetchBacktestResults, runBacktest } from "../services/backtestApi";
import type { BacktestRequest, BacktestResponse } from "../types/backtest";

const defaultModels = [
  "turtle_soup",
  "amd",
  "crt",
  "silver_bullet",
  "judas_swing",
  "power_of_three",
  "breaker_ifvg",
  "ote_continuation",
];

export function BacktestPage() {
  const [result, setResult] = useState<BacktestResponse | undefined>();
  const [form, setForm] = useState<BacktestRequest>({
    name: "XAUUSD M5 Backtest",
    symbol: "XAUUSD",
    timeframe: "M5",
    start_date: "2026-01-01",
    end_date: "2026-06-20",
    risk_per_trade: 1,
    min_score: 75,
    min_rr: 1,
    target_rr: 2,
    initial_balance: 10000,
    allowed_trade_models: defaultModels,
    session_filter: null,
  });
  const mutation = useMutation({
    mutationFn: runBacktest,
    onSuccess: setResult,
  });
  const summaries = useQuery({
    queryKey: ["backtest-results"],
    queryFn: fetchBacktestResults,
  });

  const modelText = useMemo(() => form.allowed_trade_models?.join(",") ?? "", [form.allowed_trade_models]);

  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate(form);
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
      <form onSubmit={submit} className="space-y-3 rounded-md border border-line bg-slate-900 p-4">
        <h2 className="text-sm font-semibold text-slate-100">Run Backtest</h2>
        <Input label="Symbol" value={form.symbol} onChange={(value) => setForm({ ...form, symbol: value })} />
        <Input label="Timeframe" value={form.timeframe} onChange={(value) => setForm({ ...form, timeframe: value })} />
        <Input label="Start date" type="date" value={form.start_date} onChange={(value) => setForm({ ...form, start_date: value })} />
        <Input label="End date" type="date" value={form.end_date} onChange={(value) => setForm({ ...form, end_date: value })} />
        <Input label="Min score" type="number" value={String(form.min_score)} onChange={(value) => setForm({ ...form, min_score: Number(value) })} />
        <Input label="Initial balance" type="number" value={String(form.initial_balance)} onChange={(value) => setForm({ ...form, initial_balance: Number(value) })} />
        <Input label="Target RR" type="number" value={String(form.target_rr ?? "")} onChange={(value) => setForm({ ...form, target_rr: value ? Number(value) : null })} />
        <label className="block text-xs text-slate-500">
          Models
          <textarea
            value={modelText}
            onChange={(event) =>
              setForm({
                ...form,
                allowed_trade_models: event.target.value.split(",").map((item) => item.trim()).filter(Boolean),
              })
            }
            className="mt-1 h-24 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
          />
        </label>
        <button
          disabled={mutation.isPending}
          className="w-full rounded-md bg-cyan-500 px-3 py-2 text-sm font-semibold text-slate-950 disabled:opacity-50"
        >
          {mutation.isPending ? "Running..." : "Run backtest"}
        </button>
        {mutation.error ? <ErrorState message={mutation.error.message} /> : null}
      </form>
      <section className="space-y-4">
        {mutation.isPending ? <LoadingBlock label="Running backtest" /> : null}
        <BacktestResultPanel result={result} />
        <div className="rounded-md border border-line bg-slate-900 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-100">Recent Results</h2>
          <div className="space-y-2 text-sm text-slate-400">
            {summaries.data?.slice(0, 5).map((item) => (
              <div key={item.id} className="flex justify-between rounded-md bg-slate-950 p-2">
                <span>{item.name ?? `${item.symbol} ${item.timeframe}`}</span>
                <span>WR {item.win_rate}% / PF {item.profit_factor}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="block text-xs text-slate-500">
      {label}
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
      />
    </label>
  );
}
