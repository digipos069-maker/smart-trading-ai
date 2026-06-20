export type AppTheme = "dark" | "light";

export function getSavedTheme(): AppTheme {
  return localStorage.getItem("theme") === "light" ? "light" : "dark";
}

export function applyTheme(theme: AppTheme) {
  localStorage.setItem("theme", theme);
  document.documentElement.dataset.theme = theme;
}

applyTheme(getSavedTheme());
