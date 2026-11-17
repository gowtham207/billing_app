import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({ baseURL })

type TokenReader = () => { accessToken: string | null; refreshToken: string | null }
type TokenWriter = (tokens: { accessToken: string; refreshToken: string; organizationId: string | null }) => void
type SessionEnd = () => void

let readTokens: TokenReader = () => ({ accessToken: null, refreshToken: null })
let writeTokens: TokenWriter = () => undefined
let endSession: SessionEnd = () => undefined

export function bindSession(reader: TokenReader, writer: TokenWriter, end: SessionEnd) {
  readTokens = reader
  writeTokens = writer
  endSession = end
}

api.interceptors.request.use((config) => {
  const { accessToken } = readTokens()
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

let refreshing: Promise<string | null> | null = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (!original || original.url?.includes('/auth/refresh') || original._retry || error.response?.status !== 401) {
      return Promise.reject(error)
    }
    const { refreshToken } = readTokens()
    if (!refreshToken) {
      endSession()
      return Promise.reject(error)
    }
    original._retry = true
    refreshing ??= api
      .post('/auth/refresh', { refresh_token: refreshToken })
      .then(({ data }) => {
        writeTokens({
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          organizationId: data.organization_id,
        })
        return data.access_token as string
      })
      .catch(() => {
        endSession()
        return null
      })
      .finally(() => {
        refreshing = null
      })
    const next = await refreshing
    if (!next) return Promise.reject(error)
    original.headers.Authorization = `Bearer ${next}`
    return api(original)
  },
)

export function apiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((item) => item.msg ?? JSON.stringify(item)).join(', ')
    if (!error.response) return 'The API is not reachable. Start the backend and check VITE_API_BASE_URL.'
  }
  return error instanceof Error ? error.message : 'Request failed'
}
