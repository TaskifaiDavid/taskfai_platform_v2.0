import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Toaster } from '@/components/ui/toast'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useAuthStore } from '@/stores/auth'

// Pages
import { Login } from '@/pages/Login'
import { Dashboard } from '@/pages/Dashboard'
import { DashboardBuilder } from '@/pages/DashboardBuilder'
import { Uploads } from '@/pages/Uploads'
import { Chat } from '@/pages/Chat'
import { Analytics } from '@/pages/Analytics'
import { Dashboards } from '@/pages/Dashboards'
import { Admin } from '@/pages/Admin'
import { Settings } from '@/pages/Settings'
import { MFASettings } from '@/pages/MFASettings'
import { TenantList } from '@/pages/TenantList'
import { TenantOnboarding } from '@/pages/TenantOnboarding'
import { BibbiUploads } from '@/pages/BibbiUploads'

function AppRoutes() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />}
      />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="dashboard/builder" element={<DashboardBuilder />} />
        <Route path="uploads" element={<Uploads />} />
        <Route path="bibbi/uploads" element={<BibbiUploads />} />
        <Route path="chat" element={<Chat />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="dashboards" element={<Dashboards />} />
        <Route path="settings" element={<Settings />} />
        <Route path="settings/security" element={<MFASettings />} />
        <Route
          path="admin"
          element={
            <ProtectedRoute requireAdmin>
              <Admin />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/tenants"
          element={
            <ProtectedRoute requireAdmin>
              <TenantList />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/tenants/new"
          element={
            <ProtectedRoute requireAdmin>
              <TenantOnboarding />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <TooltipProvider delayDuration={200}>
        <AppRoutes />
        <Toaster />
      </TooltipProvider>
    </BrowserRouter>
  )
}
