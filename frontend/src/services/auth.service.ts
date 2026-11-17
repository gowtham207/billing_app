import { api } from '@/services/api'
import type { MeResponse, Membership, TokenResponse } from '@/types/api'

export const authService = {
  login: (email: string, password: string) => api.post<TokenResponse>('/auth/login', { email, password }).then((response) => response.data),
  logout: (refreshToken: string) => api.post('/auth/logout', { refresh_token: refreshToken }),
  me: () => api.get<MeResponse>('/auth/me').then((response) => response.data),
  organizations: () => api.get<Membership[]>('/auth/organizations').then((response) => response.data),
  switchOrganization: (organizationId: string) =>
    api.post<TokenResponse>('/auth/switch-organization', { organization_id: organizationId }).then((response) => response.data),
}
