import { NavLink } from "react-router-dom";

const items = [
  { to: "/", label: "Dashboard" },
  { to: "/ict", label: "ICT" },
  { to: "/news", label: "News" },
  { to: "/backtest", label: "Backtest" },
  { to: "/journal", label: "Journal" },
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 border-r border-line bg-slate-950/90 p-4 md:block">
      <div className="mb-8">
        <div className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
          Smart Trading AI
        </div>
        <div className="mt-1 text-xs text-slate-500">Analysis dashboard only</div>
      </div>
      <nav className="space-y-1">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              [
                "block rounded-md px-3 py-2 text-sm transition",
                isActive
                  ? "bg-cyan-500/10 text-cyan-200"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-100",
              ].join(" ")
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
