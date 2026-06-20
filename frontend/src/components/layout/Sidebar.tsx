import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

const items = [
  { to: "/", label: "nav.dashboard" },
  { to: "/ict", label: "nav.ict" },
  { to: "/news", label: "nav.news" },
  { to: "/backtest", label: "nav.backtest" },
  { to: "/journal", label: "nav.journal" },
];

export function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside className="hidden w-60 shrink-0 border-r border-line bg-slate-950/90 p-4 md:block">
      <div className="mb-8">
        <div className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
          {t("app.name")}
        </div>
        <div className="mt-1 text-xs text-slate-500">{t("app.subtitle")}</div>
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
            {t(item.label)}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
