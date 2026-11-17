import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { adminApi, bindSession, type AdminAccount } from '@/api'

type Session = {
  accessToken: string
  refreshToken: string
  organizationId: string | null
  user: AdminAccount | null
}

type SessionValue = Session & {
  ready: boolean
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const STORAGE = 'peaksuite.admin.session'
const THEME = 'peaksuite.admin.theme'
const empty: Session = { accessToken: '', refreshToken: '', organizationId: null, user: null }
const SessionContext = createContext<SessionValue | null>(null)

function readStored(): Session {
  const raw = localStorage.getItem(STORAGE)
  if (!raw) return empty
  return { ...empty, ...JSON.parse(raw) }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session>(readStored)
  const [ready, setReady] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (localStorage.getItem(THEME) === 'dark' ? 'dark' : 'light'))

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
      (tokens) => persist({ ...session, ...tokens, user: session.user }),
      () => persist(empty),
    )
  }, [session.accessToken, session.refreshToken])

  useEffect(() => {
    if (!session.accessToken) {
      setReady(true)
      return
    }
    adminApi.me()
      .then((me) => {
        persist({ ...session, user: me.user })
      })
      .catch(() => persist(empty))
      .finally(() => setReady(true))
    // Restore the signed-in administrator once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const value = useMemo<SessionValue>(() => ({
    ...session,
    ready,
    theme,
    setTheme,
    login: async (email, password) => {
      const tokens = await adminApi.login(email, password)
      persist({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        organizationId: tokens.organization_id,
        user: tokens.user ?? null,
      })
      const me = await adminApi.me()
      persist({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        organizationId: tokens.organization_id,
        user: me.user,
      })
    },
    logout: async () => {
      if (session.refreshToken) await adminApi.logout(session.refreshToken)
      persist(empty)
    },
  }), [session, ready, theme])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const value = useContext(SessionContext)
  if (!value) throw new Error('Session is unavailable')
  return value
}
