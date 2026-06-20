import { useTranslation } from "react-i18next";

import { EmptyState } from "../components/ui/State";

export function JournalPage() {
  const { t } = useTranslation();

  return (
    <div className="max-w-3xl rounded-md border border-line bg-slate-900 p-4">
      <h2 className="mb-3 text-sm font-semibold text-slate-100">{t("nav.journal")}</h2>
      <EmptyState message={t("common.noData")} />
    </div>
  );
}
