import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const api = axios.create({ baseURL })

type Tokens = { accessToken: string | null; refreshToken: string | null }
let readTokens = (): Tokens => ({ accessToken: null, refreshToken: null })
let writeTokens = (_tokens: { accessToken: string; refreshToken: string; organizationId: string | null }) => {}
let endSession = () => {}

export function bindSession(
  reader: () => Tokens,
  writer: (tokens: { accessToken: string; refreshToken: string; organizationId: string | null }) => void,
  end: () => void,
) {
  readTokens = reader
  writeTokens = writer
  endSession = end
}

api.interceptors.request.use((config) => {
  const { accessToken } = readTokens()
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

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
    try {
      const { data } = await api.post('/admin/auth/refresh', { refresh_token: refreshToken })
      writeTokens({ accessToken: data.access_token, refreshToken: data.refresh_token, organizationId: data.organization_id })
      original.headers.Authorization = `Bearer ${data.access_token}`
      return api(original)
    } catch (refreshError) {
      endSession()
      return Promise.reject(refreshError)
    }
  },
)

export function apiError(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((item) => item.msg ?? 'Invalid value').join(', ')
    if (!error.response) return 'The API is not reachable.'
  }
  return error instanceof Error ? error.message : 'Request failed'
}

export type Page<T> = { items: T[]; total: number; page: number; page_size: number }

export type User = {
  id: string
  email: string
  full_name: string
  phone: string | null
  is_platform_admin: boolean
  is_active: boolean
  last_login_at: string | null
  created_at: string
}

export type Organization = {
  id: string
  code: string
  legal_name: string
  display_name: string
  email: string | null
  phone: string | null
  status: string
  default_currency: string
  timezone: string
  temporary_owner_password?: string
}

export type Branch = {
  id: string
  code: string
  name: string
  email: string | null
  phone: string | null
  is_head_office: boolean
  is_active: boolean
}

export type Member = {
  id: string
  user_id: string
  full_name: string
  email: string
  member_status: string
  joined_at: string | null
  is_active: boolean
}

export type Role = {
  id: string
  role_key: string
  name: string
  description: string | null
  is_system: boolean
}

export type MembershipMap = {
  id: string
  user_id: string
  full_name: string
  email: string
  organization_id: string
  organization_name: string
  organization_code: string
  member_status: string
  roles: string[]
  branches: string[]
}

export type Permission = {
  id: string
  permission_key: string
  module_key: string
  description: string | null
}

export type AdminAccount = {
  id: string
  email: string
  full_name: string
  is_active: boolean
  last_login_at: string | null
  created_at: string
}

export const adminApi = {
  login: (email: string, password: string) => api.post('/admin/auth/login', { email, password }).then((response) => response.data),
  me: () => api.get<{ user: AdminAccount }>('/admin/auth/me').then((response) => response.data),
  logout: (refreshToken: string) => api.post('/admin/auth/logout', { refresh_token: refreshToken }).catch(() => undefined),
  organizations: (q = '') => api.get<Page<Organization>>('/admin/organizations', { params: { q, page_size: 100 } }).then((response) => response.data),
  createOrganization: (body: Record<string, string>) => api.post<Organization>('/admin/organizations', body).then((response) => response.data),
  updateOrganization: (id: string, body: Record<string, string>) => api.put<Organization>(`/admin/organizations/${id}`, body).then((response) => response.data),
  activateOrganization: (id: string) => api.post(`/admin/organizations/${id}/activate`),
  deactivateOrganization: (id: string) => api.post(`/admin/organizations/${id}/deactivate`),
  deleteOrganization: (id: string) => api.delete(`/admin/organizations/${id}`),
  branches: (id: string) => api.get<Branch[]>(`/admin/organizations/${id}/branches`).then((response) => response.data),
  createBranch: (id: string, body: { code: string; name: string; email?: string; phone?: string }) => api.post(`/admin/organizations/${id}/branches`, body),
  deactivateBranch: (orgId: string, branchId: string) => api.delete(`/admin/organizations/${orgId}/branches/${branchId}`),
  members: (id: string) => api.get<Member[]>(`/admin/organizations/${id}/members`).then((response) => response.data),
  inviteMember: (id: string, body: { email: string; full_name: string; password?: string }) => api.post<{ temporary_password?: string }>(`/admin/organizations/${id}/members`, body).then((response) => response.data),
  setMemberStatus: (orgId: string, memberId: string, member_status: string) => api.patch(`/admin/organizations/${orgId}/members/${memberId}`, { member_status }),
  roles: (id: string) => api.get<Page<Role>>(`/admin/organizations/${id}/roles`).then((response) => response.data),
  createRole: (id: string, body: { role_key: string; name: string; description?: string }) => api.post(`/admin/organizations/${id}/roles`, body),
  deleteRole: (orgId: string, roleId: string) => api.delete(`/admin/organizations/${orgId}/roles/${roleId}`),
  rolePermissions: (orgId: string, roleId: string) => api.get<{ permission_ids: string[] }>(`/admin/organizations/${orgId}/roles/${roleId}/permissions`).then((response) => response.data),
  setRolePermissions: (orgId: string, roleId: string, ids: string[]) => api.put(`/admin/organizations/${orgId}/roles/${roleId}/permissions`, { ids }),
  memberships: () => api.get<MembershipMap[]>('/admin/memberships').then((response) => response.data),
  mapUser: (body: { user_id: string; organization_id: string; role_id?: string; branch_id?: string; member_status?: string }) => api.post('/admin/memberships', body),
  mapUsers: (body: { user_id: string; organizations: { organization_id: string; role_id?: string; branch_id?: string }[] }) => api.post('/admin/memberships/bulk', body),
  unmapUser: (organizationId: string, memberId: string) => api.delete(`/admin/memberships/${organizationId}/${memberId}`),
  users: (q = '') => api.get<Page<User>>('/admin/users', { params: { q, page_size: 100 } }).then((response) => response.data),
  createUser: (body: { email: string; full_name: string; password: string; phone?: string }) => api.post<User>('/admin/users', body).then((response) => response.data),
  updateUser: (id: string, body: { is_active?: boolean; full_name?: string; email?: string; phone?: string | null; password?: string }) => api.patch(`/admin/users/${id}`, body),
  admins: (q = '') => api.get<AdminAccount[]>('/admin/admins', { params: { q } }).then((response) => response.data),
  createAdmin: (body: { email: string; full_name: string; password: string }) => api.post('/admin/admins', body),
  updateAdmin: (id: string, body: { is_active?: boolean; full_name?: string }) => api.patch(`/admin/admins/${id}`, body),
  permissions: (q = '') => api.get<Permission[]>('/admin/permissions', { params: { q } }).then((response) => response.data),
  createPermission: (body: { permission_key: string; module_key: string; description?: string }) => api.post('/admin/permissions', body),
  deletePermission: (id: string) => api.delete(`/admin/permissions/${id}`),
}
