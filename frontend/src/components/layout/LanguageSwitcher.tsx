import { useTranslation } from "react-i18next";

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  function changeLanguage(language: string) {
    localStorage.setItem("language", language);
    void i18n.changeLanguage(language);
  }

  return (
    <label className="flex items-center gap-2 text-xs text-slate-500">
      {t("language.label")}
      <select
        value={i18n.language}
        onChange={(event) => changeLanguage(event.target.value)}
        className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-100"
      >
        <option value="en">{t("language.en")}</option>
        <option value="kh">{t("language.kh")}</option>
      </select>
    </label>
  );
}
