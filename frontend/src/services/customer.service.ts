import { api } from '@/services/api'
import type { Address, Customer, Page } from '@/types/api'

export const customerService = {
  list: (params: { page?: number; page_size?: number; q?: string; is_active?: boolean }) =>
    api.get<Page<Customer>>('/crm/customers', { params }).then((response) => response.data),
  get: (id: string) => api.get<Customer>(`/crm/customers/${id}`).then((response) => response.data),
  create: (body: Record<string, unknown>) => api.post<Customer>('/crm/customers', body).then((response) => response.data),
  update: (id: string, body: Record<string, unknown>) => api.put<Customer>(`/crm/customers/${id}`, body).then((response) => response.data),
  remove: (id: string) => api.delete(`/crm/customers/${id}`),
  addresses: (id: string) => api.get<Address[]>(`/crm/customers/${id}/addresses`).then((response) => response.data),
  addAddress: (id: string, body: Record<string, unknown>) => api.post<Address>(`/crm/customers/${id}/addresses`, body).then((response) => response.data),
  updateAddress: (id: string, addressId: string, body: Record<string, unknown>) =>
    api.put<Address>(`/crm/customers/${id}/addresses/${addressId}`, body).then((response) => response.data),
  notes: (id: string) => api.get<{ id: string; note: string; created_at: string }[]>(`/crm/customers/${id}/notes`).then((response) => response.data),
  addNote: (id: string, note: string) => api.post(`/crm/customers/${id}/notes`, { customer_id: id, note }).then((response) => response.data),
  outstanding: (id: string) => api.get<{ outstanding?: string | number }>(`/billing/customers/${id}/outstanding`).then((response) => response.data),
}
