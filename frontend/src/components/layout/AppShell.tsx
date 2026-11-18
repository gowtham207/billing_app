import {
  ArrowLeftRight,
  BarChart3,
  Bell,
  Boxes,
  Building2,
  CalendarCheck2,
  ChevronDown,
  ChevronsLeft,
  ClipboardList,
  Contact,
  CreditCard,
  FileMinus,
  FileText,
  Kanban,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Package,
  PanelLeft,
  Receipt,
  Ruler,
  Search,
  Settings,
  ShoppingCart,
  Sun,
  Tags,
  Target,
  UserRound,
  Users,
  Wallet,
  Warehouse,
  X,
  type LucideIcon,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { BrandLockup } from '@/components/brand/BrandMark'
import { useSession } from '@/hooks/session'
import { accessService, dashboardService } from '@/services/dashboard.service'

type NavItem = { label: string; to: string; icon: LucideIcon; end?: boolean }
type NavGroup = { label: string; icon: LucideIcon; to?: string; end?: boolean; children?: NavItem[] }

const sections: { label: string; items: NavGroup[] }[] = [
  {
    label: 'Overview',
    items: [{ label: 'Dashboard', to: '/', icon: LayoutDashboard, end: true }],
  },
  {
    label: 'Workspace',
    items: [
      {
        label: 'CRM',
        icon: Users,
        children: [
          { label: 'Customers', to: '/crm/customers', icon: UserRound },
          { label: 'Leads', to: '/crm/leads', icon: Contact },
          { label: 'Opportunities', to: '/crm/opportunities', icon: Target },
          { label: 'Activities', to: '/crm/activities', icon: CalendarCheck2 },
          { label: 'CRM Kanban', to: '/crm/kanban', icon: Kanban },
        ],
      },
      {
        label: 'Inventory',
        icon: Package,
        children: [
          { label: 'Products', to: '/inventory/products', icon: Package },
          { label: 'Categories', to: '/inventory/categories', icon: Tags },
          { label: 'Brands', to: '/inventory/brands', icon: Tags },
          { label: 'Units', to: '/inventory/units', icon: Ruler },
          { label: 'Warehouses', to: '/inventory/warehouses', icon: Warehouse },
          { label: 'Stock Management', to: '/inventory/stock', icon: Boxes },
          { label: 'Stock Movements', to: '/inventory/movements', icon: ArrowLeftRight },
        ],
      },
      {
        label: 'Billing',
        icon: Receipt,
        children: [
          { label: 'Billing Dashboard', to: '/billing', icon: LayoutDashboard, end: true },
          { label: 'Quotations', to: '/billing/quotations', icon: FileText },
          { label: 'Sales Orders', to: '/billing/orders', icon: ClipboardList },
          { label: 'Invoices', to: '/billing/invoices', icon: Receipt },
          { label: 'Payments', to: '/billing/payments', icon: CreditCard },
          { label: 'Credit Notes', to: '/billing/credit-notes', icon: FileMinus },
          { label: 'Billing Settings', to: '/billing/settings', icon: Settings },
        ],
      },
    ],
  },
  {
    label: 'Finance',
    items: [
      { label: 'Purchasing', to: '/purchasing', icon: ShoppingCart },
      { label: 'Expenses', to: '/expenses', icon: Wallet },
      { label: 'Reports', to: '/reports', icon: BarChart3 },
    ],
  },
  {
    label: 'Directory',
    items: [
      { label: 'Organizations', to: '/settings/organization', icon: Building2 },
      { label: 'Users', to: '/settings/users', icon: Users },
      { label: 'Roles', to: '/settings/roles', icon: Settings },
    ],
  },
]

function useMinWidth(px: number) {
  const query = `(min-width: ${px}px)`
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches)
  useEffect(() => {
    const media = window.matchMedia(query)
    const update = () => setMatches(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [query])
  return matches
}

function initials(name?: string | null) {
  const parts = (name || 'Account').trim().split(/\s+/).slice(0, 2)
  return parts.map((part) => part[0]?.toUpperCase() ?? '').join('') || 'A'
}

function linkClass(active: boolean, child = false) {
  return `nav-link ${child ? 'nav-child' : ''} ${active ? 'active' : ''}`
}

export function AppShell() {
  const session = useSession()
  const location = useLocation()
  const navigate = useNavigate()
  const isDesktop = useMinWidth(1024)
  const isTabletUp = useMinWidth(768)
  const [preferExpanded, setPreferExpanded] = useState<boolean | null>(() => {
    const stored = localStorage.getItem('billing.sidebar')
    return stored == null ? null : stored === 'expanded'
  })
  const [mobileOpen, setMobileOpen] = useState(false)
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({})
  const [flyout, setFlyout] = useState<{ label: string; top: number } | null>(null)
  const [query, setQuery] = useState('')
  const [searchOpen, setSearchOpen] = useState(false)
  const [notesOpen, setNotesOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const expanded = preferExpanded ?? isDesktop
  const compact = isTabletUp && !expanded && !mobileOpen
  const crumbs = location.pathname.split('/').filter(Boolean)

  useEffect(() => {
    setMobileOpen(false)
    setFlyout(null)
    setSearchOpen(false)
    setNotesOpen(false)
    setProfileOpen(false)
  }, [location.pathname])

  const notifications = useQuery({
    queryKey: ['notifications'],
    enabled: Boolean(session.organizationId),
    queryFn: () => accessService.notifications(),
  })
  const unread = (notifications.data?.items ?? []).length
  const search = useQuery({
    queryKey: ['search', query],
    enabled: query.trim().length > 1,
    queryFn: async () => ({
      customers: await dashboardService.searchCustomers(query),
      products: await dashboardService.searchProducts(query),
    }),
  })

  const toggleSidebar = () => {
    if (!isTabletUp) {
      setMobileOpen(true)
      return
    }
    const next = !expanded
    setPreferExpanded(next)
    localStorage.setItem('billing.sidebar', next ? 'expanded' : 'compact')
    setFlyout(null)
  }

  const groupOpen = (group: NavGroup) => {
    if (group.label in openGroups) return openGroups[group.label]
    return group.children?.some((child) => location.pathname === child.to || location.pathname.startsWith(`${child.to}/`)) ?? true
  }

  const sidebar = (forceExpanded = false) => {
    const collapsed = forceExpanded ? false : compact
    return (
      <aside className={`sidebar flex h-full w-72 flex-col bg-sidebar text-white ${collapsed ? 'compact' : ''}`}>
        <div className="flex items-center justify-between gap-2 border-b border-white/10 px-3 py-4">
          <BrandLockup tone="light" compact={collapsed} />
          {forceExpanded ? (
            <button className="rounded-lg p-2 text-white/80 hover:bg-white/10" onClick={() => setMobileOpen(false)} aria-label="Close menu">
              <X size={18} />
            </button>
          ) : null}
        </div>
        {collapsed ? null : <p className="hide-compact px-4 pt-3 text-[11px] leading-4 text-white/55">One Platform. Every Business Operation.</p>}
        <nav className="sidebar-scroll mt-3 flex-1 space-y-4 overflow-y-auto px-2 pb-4">
          {sections.map((section) => (
            <div key={section.label} className="space-y-1">
              <p className="nav-section hide-compact">{section.label}</p>
              {section.items.map((group) => {
                const Icon = group.icon
                if (!group.children) {
                  return (
                    <NavLink key={group.label} to={group.to!} end={group.end} title={group.label} className={({ isActive }) => linkClass(isActive)} onClick={() => setMobileOpen(false)}>
                      <Icon size={16} /> <span className="hide-compact truncate">{group.label}</span>
                    </NavLink>
                  )
                }
                const active = group.children.some((child) => location.pathname === child.to || location.pathname.startsWith(`${child.to}/`))
                if (collapsed) {
                  return (
                    <button
                      key={group.label}
                      type="button"
                      title={group.label}
                      className={linkClass(active || flyout?.label === group.label)}
                      onClick={(event) => {
                        const top = event.currentTarget.getBoundingClientRect().top
                        setFlyout((current) => (current?.label === group.label ? null : { label: group.label, top }))
                      }}
                    >
                      <Icon size={16} />
                    </button>
                  )
                }
                const opened = groupOpen(group)
                return (
                  <div key={group.label}>
                    <button type="button" className="nav-section" onClick={() => setOpenGroups((current) => ({ ...current, [group.label]: !opened }))}>
                      <span className="flex items-center gap-2"><Icon size={14} /> {group.label}</span>
                      <ChevronDown size={14} className={opened ? '' : '-rotate-90'} />
                    </button>
                    {opened ? group.children.map((child) => (
                      <NavLink key={child.to} to={child.to} end={child.end} className={({ isActive }) => linkClass(isActive, true)} onClick={() => setMobileOpen(false)}>
                        <child.icon size={15} /> <span className="truncate">{child.label}</span>
                      </NavLink>
                    )) : null}
                  </div>
                )
              })}
            </div>
          ))}
        </nav>
        <div className="border-t border-white/10 p-2">
          <div className={`mb-1 flex items-center gap-2 rounded-lg px-2 py-2 ${collapsed ? 'justify-center' : ''}`}>
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand text-xs font-semibold text-white">{initials(session.user?.full_name)}</span>
            {collapsed ? null : (
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{session.user?.full_name ?? 'Account'}</p>
                <p className="truncate text-xs text-white/55">{session.user?.email}</p>
              </div>
            )}
          </div>
          <button className="nav-link" title="Logout" onClick={() => session.logout().then(() => navigate('/login'))}>
            <LogOut size={16} /> <span className="hide-compact">Logout</span>
          </button>
        </div>
      </aside>
    )
  }

  const flyoutGroup = sections.flatMap((section) => section.items).find((group) => group.label === flyout?.label)

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <div className="flex min-h-screen">
        <div className={`sticky top-0 hidden h-dvh shrink-0 md:block ${compact ? 'w-[4.5rem]' : 'w-72'}`}>{sidebar()}</div>
        {mobileOpen ? (
          <div className="fixed inset-0 z-40 bg-navy/50 md:hidden" onClick={() => setMobileOpen(false)}>
            <div className="h-full w-72 max-w-[86vw]" onClick={(event) => event.stopPropagation()}>{sidebar(true)}</div>
          </div>
        ) : null}
        {flyout && flyoutGroup?.children ? (
          <>
            <button className="fixed inset-0 z-40" aria-label="Close navigation" onClick={() => setFlyout(null)} />
            <div className="fixed z-50 w-56 rounded-xl border border-white/10 bg-sidebar p-2 text-white shadow-none" style={{ top: Math.min(flyout.top, window.innerHeight - 280), left: 84 }}>
              <p className="px-2 py-1 text-xs font-semibold tracking-wide text-white/55 uppercase">{flyoutGroup.label}</p>
              {flyoutGroup.children.map((child) => (
                <NavLink key={child.to} to={child.to} end={child.end} className={({ isActive }) => linkClass(isActive)} onClick={() => setFlyout(null)}>
                  <child.icon size={15} /> {child.label}
                </NavLink>
              ))}
            </div>
          </>
        ) : null}
        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-20 border-b border-line bg-surface">
            <div className="flex items-center gap-2 px-3 py-2.5 sm:px-4">
              <button className="icon-button" onClick={toggleSidebar} aria-label={isTabletUp ? 'Toggle sidebar' : 'Open menu'}>
                {isTabletUp ? (expanded ? <ChevronsLeft size={18} /> : <PanelLeft size={18} />) : <Menu size={18} />}
              </button>
              <div className="relative min-w-0 flex-1">
                <Search className="absolute top-2.5 left-2 text-muted" size={16} />
                <input className="control w-full py-2 pr-8 pl-8 text-sm" placeholder="Search customers and products" value={query} onChange={(event) => { setQuery(event.target.value); setSearchOpen(true) }} onFocus={() => setSearchOpen(true)} />
                {query ? <button className="absolute top-2.5 right-2 text-muted" onClick={() => setQuery('')} aria-label="Clear search"><X size={14} /></button> : null}
                {searchOpen && query.trim().length > 1 ? (
                  <div className="menu-panel absolute z-30 mt-1 max-h-72 w-full overflow-y-auto p-2 text-sm">
                    {(search.data?.customers ?? []).map((customer) => <button key={customer.id} className="menu-item" onClick={() => { setSearchOpen(false); navigate(`/crm/customers/${customer.id}`) }}>{customer.display_name}</button>)}
                    {(search.data?.products ?? []).map((product) => <button key={product.id} className="menu-item" onClick={() => { setSearchOpen(false); navigate(`/inventory/products/${product.id}`) }}>{product.name}</button>)}
                    {!search.data?.customers.length && !search.data?.products.length ? <p className="px-2 py-1 text-muted">No matches</p> : null}
                  </div>
                ) : null}
              </div>
              <div className="relative">
                <button className="icon-button" onClick={() => { setNotesOpen((value) => !value); setProfileOpen(false) }} aria-label="Notifications">
                  <Bell size={18} />
                  {unread > 0 ? <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-cyan" /> : null}
                </button>
                {notesOpen ? (
                  <div className="menu-panel absolute right-0 z-30 mt-1 w-72 p-2 text-sm">
                    {(notifications.data?.items ?? []).length === 0 ? <p className="px-2 py-2 text-muted">No notifications</p> : notifications.data?.items.map((item) => (
                      <button key={item.id} className="menu-item" onClick={() => accessService.markRead(item.id).then(() => notifications.refetch())}>
                        {item.title || item.message || item.body || 'Notification'}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              <button className="icon-button" onClick={() => session.setTheme(session.theme === 'dark' ? 'light' : 'dark')} aria-label="Toggle theme">
                {session.theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
              </button>
              <div className="relative">
                <button className="icon-button flex items-center gap-2 text-sm" onClick={() => { setProfileOpen((value) => !value); setNotesOpen(false) }}>
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-brand text-xs font-semibold text-white">{initials(session.user?.full_name)}</span>
                  <span className="hidden max-w-32 truncate sm:inline">{session.user?.full_name ?? 'Account'}</span>
                  <ChevronDown size={14} className="hidden sm:block" />
                </button>
                {profileOpen ? (
                  <div className="menu-panel absolute right-0 z-30 mt-1 w-52 p-2 text-sm">
                    <p className="px-2 py-1 text-muted">{session.user?.email}</p>
                    <button className="menu-item" onClick={() => session.logout().then(() => navigate('/login'))}>Logout</button>
                  </div>
                ) : null}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-1 px-3 pb-2 text-xs text-muted sm:px-4">
              <FileText size={12} /> <button onClick={() => navigate('/')}>Home</button>
              {crumbs.map((crumb, index) => <span key={`${crumb}-${index}`}>/ <button onClick={() => navigate(`/${crumbs.slice(0, index + 1).join('/')}`)} className="capitalize">{crumb.replaceAll('-', ' ')}</button></span>)}
            </div>
          </header>
          <main className="p-3 sm:p-4 md:p-6"><Outlet /></main>
        </div>
      </div>
    </div>
  )
}
