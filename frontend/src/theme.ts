export type AppTheme = "dark" | "light";

export const DEFAULT_CHART_LABEL_CONFIDENCE = 70;

export function getSavedTheme(): AppTheme {
  return localStorage.getItem("theme") === "light" ? "light" : "dark";
}

export function applyTheme(theme: AppTheme) {
  localStorage.setItem("theme", theme);
  document.documentElement.dataset.theme = theme;
}

export function getChartLabelConfidence(): number {
  const savedValue = Number(localStorage.getItem("chartLabelConfidence"));
  if (!Number.isFinite(savedValue)) return DEFAULT_CHART_LABEL_CONFIDENCE;

  return clampConfidence(savedValue);
}

export function saveChartLabelConfidence(value: number) {
  localStorage.setItem("chartLabelConfidence", String(clampConfidence(value)));
}

function clampConfidence(value: number): number {
  return Math.min(100, Math.max(0, Math.round(value)));
}

applyTheme(getSavedTheme());
