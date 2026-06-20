import { useState } from "react";
import { useTranslation } from "react-i18next";

import { applyTheme, getSavedTheme, type AppTheme } from "../theme";

export function SettingsPage() {
  const { t } = useTranslation();
  const [theme, setTheme] = useState<AppTheme>(getSavedTheme());

  function updateTheme(value: AppTheme) {
    setTheme(value);
    applyTheme(value);
  }

  return (
    <div className="max-w-3xl space-y-4">
      <section className="rounded-md border border-line bg-slate-900 p-4">
        <h2 className="text-sm font-semibold text-slate-100">{t("settings.title")}</h2>
        <p className="mt-1 text-sm text-slate-500">{t("settings.subtitle")}</p>

        <div className="mt-6 grid gap-4 md:grid-cols-[180px_minmax(0,1fr)]">
          <div>
            <div className="text-sm font-medium text-slate-200">{t("settings.theme")}</div>
            <div className="mt-1 text-xs text-slate-500">{t("settings.themeHint")}</div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <ThemeOption
              active={theme === "dark"}
              title={t("settings.dark")}
              description={t("settings.darkDescription")}
              onClick={() => updateTheme("dark")}
            />
            <ThemeOption
              active={theme === "light"}
              title={t("settings.light")}
              description={t("settings.lightDescription")}
              onClick={() => updateTheme("light")}
            />
          </div>
        </div>
      </section>
    </div>
  );
}

function ThemeOption({
  active,
  title,
  description,
  onClick,
}: {
  active: boolean;
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded-md border p-4 text-left transition",
        active
          ? "border-cyan-400 bg-cyan-500/10"
          : "border-line bg-slate-950 hover:border-slate-500",
      ].join(" ")}
    >
      <div className="text-sm font-semibold text-slate-100">{title}</div>
      <div className="mt-1 text-xs text-slate-500">{description}</div>
    </button>
  );
}
