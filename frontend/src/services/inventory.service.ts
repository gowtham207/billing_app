import { api } from '@/services/api'
import type { Brand, Category, Page, Product, Unit, Warehouse } from '@/types/api'

export const categoryService = {
  list: (q?: string) => api.get<Page<Category>>('/inventory/categories', { params: { q, page_size: 100 } }).then((response) => response.data),
  create: (body: Record<string, unknown>) => api.post<Category>('/inventory/categories', body).then((response) => response.data),
  update: (id: string, body: Record<string, unknown>) => api.put<Category>(`/inventory/categories/${id}`, body).then((response) => response.data),
  remove: (id: string) => api.delete(`/inventory/categories/${id}`),
}

export const productService = {
  list: (params: { page?: number; page_size?: number; q?: string; category_id?: string }) =>
    api.get<Page<Product>>('/inventory/products', { params: { page_size: 20, ...params } }).then((response) => response.data),
  get: (id: string) => api.get<Product>(`/inventory/products/${id}`).then((response) => response.data),
  create: (body: Record<string, unknown>) => api.post<Product>('/inventory/products', body).then((response) => response.data),
  update: (id: string, body: Record<string, unknown>) => api.put<Product>(`/inventory/products/${id}`, body).then((response) => response.data),
  remove: (id: string) => api.delete(`/inventory/products/${id}`),
  variants: (id: string) => api.get<{ id: string; variant_name: string; variant_sku: string; selling_price: string | null }[]>(`/inventory/products/${id}/variants`).then((response) => response.data),
  addVariant: (id: string, body: Record<string, unknown>) => api.post(`/inventory/products/${id}/variants`, body).then((response) => response.data),
}

export const inventoryService = {
  brands: () => api.get<Page<Brand>>('/inventory/brands', { params: { page_size: 100 } }).then((response) => response.data),
  createBrand: (name: string) => api.post<Brand>('/inventory/brands', { name }).then((response) => response.data),
  updateBrand: (id: string, name: string) => api.put(`/inventory/brands/${id}`, { name }),
  deleteBrand: (id: string) => api.delete(`/inventory/brands/${id}`),
  units: () => api.get<Page<Unit>>('/inventory/units', { params: { page_size: 100 } }).then((response) => response.data),
  createUnit: (body: { name: string; symbol: string }) => api.post<Unit>('/inventory/units', body).then((response) => response.data),
  updateUnit: (id: string, body: { name: string; symbol: string }) => api.put(`/inventory/units/${id}`, body),
  deleteUnit: (id: string) => api.delete(`/inventory/units/${id}`),
  warehouses: () => api.get<Page<Warehouse>>('/inventory/warehouses', { params: { page_size: 100 } }).then((response) => response.data),
  createWarehouse: (body: { code: string; name: string; address?: string }) => api.post<Warehouse>('/inventory/warehouses', body).then((response) => response.data),
  updateWarehouse: (id: string, body: Record<string, unknown>) => api.put(`/inventory/warehouses/${id}`, body),
  deleteWarehouse: (id: string) => api.delete(`/inventory/warehouses/${id}`),
  stock: () => api.get('/inventory/stock', { params: { page_size: 100 } }).then((response) => response.data),
  lowStock: () => api.get('/inventory/stock/low-stock').then((response) => response.data),
  movements: () => api.get('/inventory/stock/movements', { params: { page_size: 50 } }).then((response) => response.data),
  opening: (body: { warehouse_id: string; lines: { product_id: string; quantity: string; unit_cost: string }[] }) =>
    api.post('/inventory/stock/opening', body).then((response) => response.data),
  upload: (entityType: string, entityId: string, file: File) => {
    const form = new FormData()
    form.append('entity_type', entityType)
    form.append('entity_id', entityId)
    form.append('file', file)
    return api.post('/attachments', form).then((response) => response.data)
  },
}
