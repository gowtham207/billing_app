import { Building2, KeyRound, LayoutDashboard, Link2, LogOut, Moon, Shield, Sun, Users } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useSession } from '@/session'

const links = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/organizations', label: 'Organizations', icon: Building2, end: false },
  { to: '/users', label: 'Workspace users', icon: Users, end: false },
  { to: '/mapping', label: 'User mapping', icon: Link2, end: false },
  { to: '/admins', label: 'Administrators', icon: Shield, end: false },
  { to: '/permissions', label: 'Permissions', icon: KeyRound, end: false },
]

export function Shell() {
  const session = useSession()
  const navigate = useNavigate()
  return (
    <div className="min-h-screen bg-canvas md:flex">
      <aside className="bg-sidebar text-white md:min-h-screen md:w-64">
        <div className="flex items-center gap-3 px-4 py-4">
          <svg width="36" height="36" viewBox="0 0 64 64" aria-hidden="true">
            <rect width="64" height="64" rx="16" fill="#102A43" />
            <path d="M30 50 41.5 24l6.2 9.2 4.8-7.4L58 50Z" fill="#2563EB" stroke="#FFFFFF" strokeWidth="2.2" strokeLinejoin="round" />
            <path d="M46.3 25.6 50.4 33.6h-8.2Z" fill="#38BDF8" />
            <path fill="#FFFFFF" fillRule="evenodd" d="M10 15h13.8c5.7 0 9.5 3.5 9.5 8.8s-3.9 9-9.7 9H16.6V50H10V15Zm6.6 5.1v7.4h6.6c2.4 0 3.8-1.3 3.8-3.7s-1.4-3.7-3.8-3.7h-6.6Z" />
          </svg>
          <div>
            <p className="text-sm font-semibold">PeakSuite</p>
            <p className="text-xs text-white/60">Admin console</p>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-2 pb-3 md:block md:space-y-1 md:px-2">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className={({ isActive }) => `nav-link whitespace-nowrap ${isActive ? 'active' : ''}`}>
              <link.icon size={16} /> {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-end gap-2 border-b border-line bg-surface px-4 py-3">
          <span className="mr-auto truncate text-sm text-muted">{session.user?.email}</span>
          <button className="rounded-lg p-2 hover:bg-brand/10" aria-label="Toggle theme" onClick={() => session.setTheme(session.theme === 'dark' ? 'light' : 'dark')}>
            {session.theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <button className="inline-flex items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-brand/10" onClick={() => session.logout().then(() => navigate('/login'))}>
            <LogOut size={16} /> Sign out
          </button>
        </header>
        <main className="p-4 md:p-6"><Outlet /></main>
      </div>
    </div>
  )
}
