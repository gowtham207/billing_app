import { api } from '@/services/api'
import type { BillingSettings, Invoice, InvoiceItem, Page, Payment, TaxRate } from '@/types/api'

export const billingService = {
  settings: () => api.get<BillingSettings>('/billing/settings').then((response) => response.data),
  updateSettings: (body: Partial<BillingSettings>) => api.put<BillingSettings>('/billing/settings', body).then((response) => response.data),
  taxRates: () => api.get<Page<TaxRate>>('/billing/tax-rates', { params: { page_size: 100 } }).then((response) => response.data),
  createTaxRate: (body: { tax_code: string; name: string; rate: number }) => api.post<TaxRate>('/billing/tax-rates', body).then((response) => response.data),
  paymentMethods: () => api.get<Page<{ id: string; display_name?: string; name?: string }>>('/billing/payment-methods', { params: { page_size: 50 } }).then((response) => response.data),
}

export const invoiceService = {
  list: (page = 1) => api.get<Page<Invoice>>('/billing/invoices', { params: { page, page_size: 20 } }).then((response) => response.data),
  get: (id: string) => api.get<Invoice>(`/billing/invoices/${id}`).then((response) => response.data),
  items: (id: string) => api.get<InvoiceItem[]>(`/billing/invoices/${id}/items`).then((response) => response.data),
  create: (body: Record<string, unknown>) => api.post<Invoice>('/billing/invoices', body).then((response) => response.data),
  update: (id: string, body: Record<string, unknown>) => api.put<Invoice>(`/billing/invoices/${id}`, body).then((response) => response.data),
  approve: (id: string) => api.post<Invoice>(`/billing/invoices/${id}/approve`).then((response) => response.data),
  post: (id: string) => api.post<Invoice>(`/billing/invoices/${id}/post`).then((response) => response.data),
  cancel: (id: string) => api.post<Invoice>(`/billing/invoices/${id}/cancel`).then((response) => response.data),
  pdfBlob: async (id: string) => {
    const response = await api.get(`/billing/invoices/${id}/pdf`, { responseType: 'blob' })
    return response.data as Blob
  },
}

export const paymentService = {
  list: (page = 1) => api.get<Page<Payment>>('/billing/payments', { params: { page, page_size: 20 } }).then((response) => response.data),
  create: (body: Record<string, unknown>) => api.post<Payment>('/billing/payments', body).then((response) => response.data),
  allocate: (id: string, invoiceId: string, amount: string) =>
    api.post(`/billing/payments/${id}/allocate`, { allocations: [{ invoice_id: invoiceId, amount }] }).then((response) => response.data),
}

export const documentService = {
  list: (path: string, page = 1) => api.get<Page<Record<string, unknown>>>(path, { params: { page, page_size: 20 } }).then((response) => response.data),
  create: (path: string, body: Record<string, unknown>) => api.post(path, body).then((response) => response.data),
  action: (path: string) => api.post(path).then((response) => response.data),
}
