import { api } from '@/services/api'
import type { Address, Branch, Organization } from '@/types/api'

export const organizationService = {
  get: (id: string) => api.get<Organization>(`/organizations/${id}`).then((response) => response.data),
  update: (id: string, body: Partial<Organization>) => api.put<Organization>(`/organizations/${id}`, body).then((response) => response.data),
  branches: (id: string) => api.get<Branch[]>(`/organizations/${id}/branches`).then((response) => response.data),
  createBranch: (id: string, body: { code: string; name: string }) => api.post<Branch>(`/organizations/${id}/branches`, body).then((response) => response.data),
  addresses: (id: string) => api.get<Address[]>(`/organizations/${id}/addresses`).then((response) => response.data),
  createAddress: (id: string, body: Partial<Address> & { address_type: string; line1: string; country_code: string }) =>
    api.post<Address>(`/organizations/${id}/addresses`, body).then((response) => response.data),
  updateAddress: (addressId: string, body: Partial<Address>) => api.put<Address>(`/organizations/addresses/${addressId}`, body).then((response) => response.data),
}
