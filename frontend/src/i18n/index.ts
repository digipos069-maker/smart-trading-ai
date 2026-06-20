import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import kh from "./locales/kh.json";

const savedLanguage = localStorage.getItem("language") ?? "en";
document.documentElement.lang = savedLanguage;

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    kh: { translation: kh },
  },
  lng: savedLanguage,
  fallbackLng: "en",
  interpolation: {
    escapeValue: false,
  },
});

i18n.on("languageChanged", (language) => {
  document.documentElement.lang = language;
});

export default i18n;
