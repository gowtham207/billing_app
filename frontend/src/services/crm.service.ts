import { api } from '@/services/api'
import type { Activity, Lead, Opportunity, Page, StatusDefinition, StatusGroup } from '@/types/api'

export const crmService = {
  leads: (params: { page?: number; page_size?: number; q?: string }) => api.get<Page<Lead>>('/crm/leads', { params }).then((response) => response.data),
  createLead: (body: Record<string, unknown>) => api.post<Lead>('/crm/leads', body).then((response) => response.data),
  updateLead: (id: string, body: Record<string, unknown>) => api.put<Lead>(`/crm/leads/${id}`, body).then((response) => response.data),
  leadStatus: (id: string, status: string) => api.patch<Lead>(`/crm/leads/${id}/status`, { status }).then((response) => response.data),
  sources: () => api.get<Page<{ id: string; name: string }>>('/crm/lead-sources', { params: { page_size: 100 } }).then((response) => response.data),
  opportunities: (params: { page?: number; q?: string }) =>
    api.get<Page<Opportunity>>('/crm/opportunities', { params: { page_size: 100, ...params } }).then((response) => response.data),
  createOpportunity: (body: Record<string, unknown>) => api.post<Opportunity>('/crm/opportunities', body).then((response) => response.data),
  stage: (id: string, status: string) => api.patch<Opportunity>(`/crm/opportunities/${id}/stage`, { status }).then((response) => response.data),
  activities: (params: { page?: number; q?: string }) =>
    api.get<Page<Activity>>('/crm/activities', { params: { page_size: 50, ...params } }).then((response) => response.data),
  createActivity: (body: Record<string, unknown>) => api.post<Activity>('/crm/activities', body).then((response) => response.data),
  completeActivity: (id: string) => api.patch(`/crm/activities/${id}/complete`),
  myTasks: () => api.get<Activity[]>('/crm/activities/my-tasks').then((response) => response.data),
  statuses: () => api.get<Page<StatusDefinition>>('/workflows/statuses', { params: { page_size: 100 } }).then((response) => response.data),
  groups: () => api.get<Page<StatusGroup>>('/workflows/status-groups', { params: { page_size: 100 } }).then((response) => response.data),
  createStatus: (body: Record<string, unknown>) => api.post<StatusDefinition>('/workflows/statuses', body).then((response) => response.data),
}
