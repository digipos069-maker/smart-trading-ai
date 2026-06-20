export function Header() {
  return (
    <header className="border-b border-line bg-slate-950/80 px-4 py-3 backdrop-blur">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-semibold text-slate-100">Market Intelligence</h1>
          <p className="text-xs text-slate-500">ICT, AI, news risk, and backtesting</p>
        </div>
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-200">
          No live trade execution
        </div>
      </div>
    </header>
  );
}
