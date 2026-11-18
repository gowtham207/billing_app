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
  list: (page = 1, pageSize = 20) => api.get<Page<Invoice>>('/billing/invoices', { params: { page, page_size: pageSize } }).then((response) => response.data),
  payments: (id: string) => api.get<{ payment_id: string; payment_no: string; payment_date: string | null; amount_applied: string; payment_status: string; reference_no: string | null }[]>(`/billing/invoices/${id}/payments`).then((response) => response.data),
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

export type QuotationRecord = {
  id: string
  customer_id: string
  branch_id: string | null
  quotation_no: string
  quotation_date: string
  valid_until: string | null
  status_id: string | null
  subtotal: string
  discount_total: string
  tax_total: string
  grand_total: string
  notes: string | null
}

export type QuotationItemRecord = {
  id: string
  product_id: string | null
  description: string
  quantity: string
  unit_price: string
  discount_amount: string
  tax_rate: string
  line_total: string
}

export const quotationService = {
  list: (page = 1) => api.get<Page<QuotationRecord>>('/billing/quotations', { params: { page, page_size: 50 } }).then((response) => response.data),
  get: (id: string) => api.get<QuotationRecord>(`/billing/quotations/${id}`).then((response) => response.data),
  items: (id: string) => api.get<QuotationItemRecord[]>(`/billing/quotations/${id}/items`).then((response) => response.data),
  create: (body: Record<string, unknown>) => api.post<QuotationRecord>('/billing/quotations', body).then((response) => response.data),
  update: (id: string, body: Record<string, unknown>) => api.put<QuotationRecord>(`/billing/quotations/${id}`, body).then((response) => response.data),
  send: (id: string) => api.post<QuotationRecord>(`/billing/quotations/${id}/send`).then((response) => response.data),
  accept: (id: string) => api.post<QuotationRecord>(`/billing/quotations/${id}/accept`).then((response) => response.data),
  reject: (id: string) => api.post<QuotationRecord>(`/billing/quotations/${id}/reject`).then((response) => response.data),
  convert: (id: string) => api.post<{ id: string; order_no: string }>(`/billing/quotations/${id}/convert-to-order`).then((response) => response.data),
  remove: (id: string) => api.delete(`/billing/quotations/${id}`),
}

export type SalesOrderRecord = {
  id: string
  customer_id: string
  branch_id: string | null
  quotation_id: string | null
  order_no: string
  order_date: string
  status_id: string | null
  subtotal: string
  discount_total: string
  tax_total: string
  grand_total: string
  notes: string | null
}

export const orderService = {
  list: (page = 1) => api.get<Page<SalesOrderRecord>>('/billing/orders', { params: { page, page_size: 50 } }).then((response) => response.data),
  get: (id: string) => api.get<SalesOrderRecord>(`/billing/orders/${id}`).then((response) => response.data),
  items: (id: string) => api.get<QuotationItemRecord[]>(`/billing/orders/${id}/items`).then((response) => response.data),
  create: (body: Record<string, unknown>) => api.post<SalesOrderRecord>('/billing/orders', body).then((response) => response.data),
  update: (id: string, body: Record<string, unknown>) => api.put<SalesOrderRecord>(`/billing/orders/${id}`, body).then((response) => response.data),
  confirm: (id: string) => api.post<SalesOrderRecord>(`/billing/orders/${id}/confirm`).then((response) => response.data),
  cancel: (id: string) => api.post<SalesOrderRecord>(`/billing/orders/${id}/cancel`).then((response) => response.data),
  convert: (id: string) => api.post<Invoice>(`/billing/orders/${id}/convert-to-invoice`).then((response) => response.data),
  remove: (id: string) => api.delete(`/billing/orders/${id}`),
}

export const documentService = {
  list: (path: string, page = 1, pageSize = 20) => api.get<Page<Record<string, unknown>>>(path, { params: { page, page_size: pageSize } }).then((response) => response.data),
  create: (path: string, body: Record<string, unknown>) => api.post(path, body).then((response) => response.data),
  action: (path: string) => api.post(path).then((response) => response.data),
}
