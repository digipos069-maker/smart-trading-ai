import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { BacktestPage } from "../pages/BacktestPage";
import { DashboardPage } from "../pages/DashboardPage";
import { ICTAnalysisPage } from "../pages/ICTAnalysisPage";
import { JournalPage } from "../pages/JournalPage";
import { NewsPage } from "../pages/NewsPage";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/ict" element={<ICTAnalysisPage />} />
          <Route path="/news" element={<NewsPage />} />
          <Route path="/backtest" element={<BacktestPage />} />
          <Route path="/journal" element={<JournalPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
