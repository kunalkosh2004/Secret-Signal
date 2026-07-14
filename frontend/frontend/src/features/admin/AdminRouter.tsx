import { Routes, Route } from 'react-router-dom'
import { AdminLayout } from './components/AdminLayout'
import { AdminOverview } from './pages/AdminOverview'
import { InfrastructurePage } from './pages/InfrastructurePage'
import { MatchesPage } from './pages/MatchesPage'
import { MatchDetailPage } from './pages/MatchDetailPage'
import { SignalAIPage } from './pages/SignalAIPage'
import { ReplayEnginePage } from './pages/ReplayEnginePage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { LogsPage } from './pages/LogsPage'
import { SettingsPlaceholder } from './pages/SettingsPlaceholder'

export function AdminRouter() {
  return (
    <Routes>
      <Route element={<AdminLayout />}>
        <Route index element={<AdminOverview />} />
        <Route path="activity" element={<AdminOverview />} />
        <Route path="matches" element={<MatchesPage />} />
        <Route path="matches/history" element={<MatchesPage />} />
        <Route path="matches/:gameId" element={<MatchDetailPage />} />
        <Route path="infrastructure" element={<InfrastructurePage />} />
        <Route path="infrastructure/redis" element={<InfrastructurePage />} />
        <Route path="infrastructure/postgres" element={<InfrastructurePage />} />
        <Route path="replay" element={<ReplayEnginePage />} />
        <Route path="signal-ai" element={<SignalAIPage />} />
        <Route path="signal-ai/model" element={<SignalAIPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="logs" element={<LogsPage />} />
        <Route path="settings" element={<SettingsPlaceholder />} />
      </Route>
    </Routes>
  )
}
