import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { bindSession } from '@/services/api'
import { authService } from '@/services/auth.service'
import type { MeResponse, Membership, User } from '@/types/api'
import { allows } from '@/utils/permissions'

type Session = {
  accessToken: string
  refreshToken: string
  organizationId: string | null
  branchId: string | null
  branchChosen: boolean
  user: User | null
  permissions: string[]
  roles: string[]
  organizations: Membership[]
}

type SessionContextValue = Session & {
  ready: boolean
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
  setBranchId: (id: string) => void
  skipBranch: () => void
  can: (permission: string) => boolean
  login: (email: string, password: string) => Promise<MeResponse>
  logout: () => Promise<void>
  switchOrganization: (organizationId: string) => Promise<void>
  refreshProfile: () => Promise<void>
}

const STORAGE = 'billing.session'
const THEME = 'billing.theme'
const empty: Session = {
  accessToken: '',
  refreshToken: '',
  organizationId: null,
  branchId: null,
  branchChosen: false,
  user: null,
  permissions: [],
  roles: [],
  organizations: [],
}

const SessionContext = createContext<SessionContextValue | null>(null)

function readStored(): Session {
  const raw = localStorage.getItem(STORAGE)
  if (!raw) return empty
  return { ...empty, ...JSON.parse(raw) }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session>(readStored)
  const [ready, setReady] = useState(false)
  const [theme, setThemeState] = useState<'light' | 'dark'>(() => (localStorage.getItem(THEME) === 'dark' ? 'dark' : 'light'))

  const persist = (next: Session) => {
    setSession(next)
    if (!next.accessToken) localStorage.removeItem(STORAGE)
    else localStorage.setItem(STORAGE, JSON.stringify(next))
  }

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem(THEME, theme)
  }, [theme])

  useEffect(() => {
    bindSession(
      () => ({ accessToken: session.accessToken || null, refreshToken: session.refreshToken || null }),
      (tokens) => {
        setSession((current) => {
          const next = { ...current, accessToken: tokens.accessToken, refreshToken: tokens.refreshToken, organizationId: tokens.organizationId }
          localStorage.setItem(STORAGE, JSON.stringify(next))
          return next
        })
      },
      () => persist(empty),
    )
  }, [session.accessToken, session.refreshToken])

  const refreshProfile = async () => {
    const me = await authService.me()
    setSession((current) => {
      const next = {
        ...current,
        user: me.user,
        organizationId: me.organization_id,
        organizations: me.organizations,
        permissions: me.permissions,
        roles: me.roles,
      }
      localStorage.setItem(STORAGE, JSON.stringify(next))
      return next
    })
  }

  useEffect(() => {
    if (!session.accessToken) {
      setReady(true)
      return
    }
    refreshProfile().catch(() => persist(empty)).finally(() => setReady(true))
    // Restore the profile once when the stored token is first available.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const acceptTokens = async (tokens: { access_token: string; refresh_token: string; organization_id: string | null; user?: User }) => {
    const sameOrganization = Boolean(tokens.organization_id) && tokens.organization_id === session.organizationId
    persist({
      ...session,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      organizationId: tokens.organization_id,
      branchId: sameOrganization ? session.branchId : null,
      branchChosen: sameOrganization ? session.branchChosen : false,
      user: tokens.user ?? session.user,
    })
    const me = await authService.me()
    persist({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      organizationId: me.organization_id,
      branchId: sameOrganization ? session.branchId : null,
      branchChosen: sameOrganization ? session.branchChosen : false,
      user: me.user,
      permissions: me.permissions,
      roles: me.roles,
      organizations: me.organizations,
    })
    return me
  }

  const value = useMemo<SessionContextValue>(
    () => ({
      ...session,
      ready,
      theme,
      setTheme: setThemeState,
      setBranchId: (branchId) => persist({ ...session, branchId, branchChosen: true }),
      skipBranch: () => persist({ ...session, branchId: null, branchChosen: true }),
      can: (permission) => allows({ permissions: session.permissions, roles: session.roles, platformAdmin: Boolean(session.user?.is_platform_admin) }, permission),
      login: async (email, password) => acceptTokens(await authService.login(email, password)),
      logout: async () => {
        if (session.refreshToken) await authService.logout(session.refreshToken).catch(() => undefined)
        persist(empty)
      },
      switchOrganization: async (organizationId) => { await acceptTokens(await authService.switchOrganization(organizationId)) },
      refreshProfile,
    }),
    [session, ready, theme],
  )

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error('Session is unavailable')
  return value
}
