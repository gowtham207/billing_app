import { api } from '@/services/api'
import type { Activity, Customer, Invoice, Product } from '@/types/api'

export const dashboardService = {
  overview: () => api.get<Record<string, number>>('/dashboard/overview').then((response) => response.data),
  salesChart: () => api.get<{ period: string; total: number }[]>('/dashboard/sales-chart').then((response) => response.data),
  recentInvoices: () => api.get<Invoice[]>('/dashboard/recent-invoices').then((response) => response.data),
  lowStock: () => api.get<Record<string, unknown>[]>('/dashboard/low-stock').then((response) => response.data),
  topProducts: () => api.get<Record<string, unknown>[]>('/dashboard/top-selling-products').then((response) => response.data),
  topCustomers: () => api.get<Record<string, unknown>[]>('/dashboard/top-customers').then((response) => response.data),
  activity: () => api.get<{ status_changes: { entity_type: string; entity_id: string; changed_at: string }[] }>('/dashboard/activity-feed').then((response) => response.data),
  outstanding: () => api.get<{ count: number; outstanding: number }>('/dashboard/outstanding-payments').then((response) => response.data),
  customers: () => api.get<{ customers: number }>('/dashboard/customer-summary').then((response) => response.data),
  inventory: () => api.get<{ products: number; low_stock: number }>('/dashboard/inventory-summary').then((response) => response.data),
  sales: () => api.get<{ count: number; total: number }>('/dashboard/sales-summary').then((response) => response.data),
  recentCustomers: () => api.get<{ items: Customer[] }>('/crm/customers', { params: { page_size: 5 } }).then((response) => response.data.items),
  recentActivities: () => api.get<{ items: Activity[] }>('/crm/activities', { params: { page_size: 5 } }).then((response) => response.data.items),
  productCount: () => api.get<{ products: number }>('/dashboard/inventory-summary').then((response) => response.data),
  searchProducts: (q: string) => api.get<{ items: Product[] }>('/inventory/products', { params: { q, page_size: 5 } }).then((response) => response.data.items),
  searchCustomers: (q: string) => api.get<{ items: Customer[] }>('/crm/customers', { params: { q, page_size: 5 } }).then((response) => response.data.items),
}

export const reportService = {
  run: (name: string) => api.get<Record<string, unknown>[]>(`/reports/${name}`).then((response) => response.data),
  download: async (name: string, format: 'csv' | 'xlsx' | 'pdf') => {
    const response = await api.get('/reports/export', { params: { name, format }, responseType: 'blob' })
    return response.data as Blob
  },
}

export const accessService = {
  members: () => api.get<{ items: { id: string; user_id: string; member_status: string; joined_at?: string | null }[] }>('/access/members', { params: { page_size: 100 } }).then((response) => response.data),
  invite: (email: string, fullName: string) => api.post('/access/members/invite', { email, full_name: fullName }).then((response) => response.data),
  setStatus: (id: string, member_status: string) => api.patch(`/access/members/${id}/status`, { member_status }).then((response) => response.data),
  roles: () => api.get<{ items: { id: string; role_key: string; name: string; description: string | null; is_system: boolean }[] }>('/access/roles', { params: { page_size: 100 } }).then((response) => response.data),
  createRole: (body: { role_key: string; name: string; description?: string }) => api.post('/access/roles', body).then((response) => response.data),
  permissions: () => api.get<{ id: string; permission_key: string; module_key: string; description: string | null }[]>('/access/permissions').then((response) => response.data),
  rolePermissions: (id: string) => api.get<{ permission_ids: string[] }>(`/access/roles/${id}/permissions`).then((response) => response.data),
  setRolePermissions: (id: string, ids: string[]) => api.put(`/access/roles/${id}/permissions`, { ids }),
  notifications: () => api.get<{ items: { id: string; title?: string; body?: string; message?: string; is_read: boolean; created_at: string }[] }>('/notifications').then((response) => response.data),
  markRead: (id: string) => api.patch(`/notifications/${id}/read`),
}
