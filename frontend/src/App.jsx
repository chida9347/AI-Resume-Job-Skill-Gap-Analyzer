import React from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout.jsx'
import BuilderPage from './pages/BuilderPage.jsx'
import PageLoader from './components/ui/PageLoader.jsx'
import ProtectedRoute from './components/ui/ProtectedRoute.jsx'
import { useAuth } from './context/AuthContext.jsx'
import AnalyzePage from './pages/AnalyzePage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import EditorPage from './pages/EditorPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import InterviewPage from './pages/InterviewPage.jsx'
import JobMatchPage from './pages/JobMatchPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import RoadmapPage from './pages/RoadmapPage.jsx'
import SavedAnalysisPage from './pages/SavedAnalysisPage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'

function RootRedirect() {
  const { user, loading } = useAuth()
  if (loading) return <PageLoader label="Opening your workspace..." />
  return <Navigate to={user ? '/dashboard' : '/login'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="login" element={<LoginPage />} />
      <Route path="register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="builder" element={<BuilderPage />} />
        <Route path="analyze" element={<AnalyzePage />} />
        <Route path="results" element={<ResultsPage />} />
        <Route path="editor" element={<EditorPage />} />
        <Route path="roadmap" element={<RoadmapPage />} />
        <Route path="interview" element={<InterviewPage />} />
        <Route path="jobs" element={<JobMatchPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="analyses/:id" element={<SavedAnalysisPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
