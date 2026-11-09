import React from 'react'
import { Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout.jsx'
import ProtectedRoute from './components/ui/ProtectedRoute.jsx'
import AnalyzePage from './pages/AnalyzePage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import EditorPage from './pages/EditorPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import InterviewPage from './pages/InterviewPage.jsx'
import JobMatchPage from './pages/JobMatchPage.jsx'
import LandingPage from './pages/LandingPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import RoadmapPage from './pages/RoadmapPage.jsx'
import SavedAnalysisPage from './pages/SavedAnalysisPage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<LandingPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="analyze" element={<AnalyzePage />} />
        <Route path="results" element={<ResultsPage />} />
        <Route path="editor" element={<EditorPage />} />
        <Route path="roadmap" element={<RoadmapPage />} />
        <Route path="interview" element={<InterviewPage />} />
        <Route path="jobs" element={<JobMatchPage />} />
        <Route path="dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
        <Route path="analyses/:id" element={<ProtectedRoute><SavedAnalysisPage /></ProtectedRoute>} />
        <Route path="profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
        <Route path="settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
