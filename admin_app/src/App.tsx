import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Shell } from '@/shell'
import { useSession } from '@/session'
import { AdminsPage } from '@/pages/AdminsPage'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { MappingPage } from '@/pages/MappingPage'
import { OrganizationPage } from '@/pages/OrganizationPage'
import { OrganizationsPage } from '@/pages/OrganizationsPage'
import { PermissionsPage } from '@/pages/PermissionsPage'
import { UsersPage } from '@/pages/UsersPage'

function Guard({ children }: { children: ReactNode }) {
  const session = useSession()
  if (!session.ready) return <p className="grid min-h-screen place-items-center text-sm text-muted">Loading session…</p>
  if (!session.accessToken || !session.user) return <Navigate to="/login" replace />
  return children
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Guard><Shell /></Guard>}>
        <Route index element={<HomePage />} />
        <Route path="organizations" element={<OrganizationsPage />} />
        <Route path="organizations/:id" element={<OrganizationPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="mapping" element={<MappingPage />} />
        <Route path="admins" element={<AdminsPage />} />
        <Route path="permissions" element={<PermissionsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
