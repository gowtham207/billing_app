import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { adminApi, apiError, type MembershipMap } from '@/api'
import { Button, DataTable, PageHeader, SelectField, StatusBadge, useToast } from '@/ui'

export function MappingPage() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [userId, setUserId] = useState('')
  const [organizationId, setOrganizationId] = useState('')
  const [roleId, setRoleId] = useState('')
  const mappings = useQuery({ queryKey: ['admin-memberships'], queryFn: adminApi.memberships })
  const users = useQuery({ queryKey: ['admin-users'], queryFn: () => adminApi.users() })
  const organizations = useQuery({ queryKey: ['admin-orgs'], queryFn: () => adminApi.organizations() })
  const roles = useQuery({ queryKey: ['admin-roles', organizationId], enabled: Boolean(organizationId), queryFn: () => adminApi.roles(organizationId) })
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['admin-memberships'] })
  return (
    <div className="space-y-4">
      <PageHeader title="User organization mapping" subtitle="Assign a workspace user to an organization. A user can belong to more than one." />
      <form className="panel grid gap-3 p-4 md:grid-cols-4" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await adminApi.mapUser({ user_id: userId, organization_id: organizationId, role_id: roleId || undefined, member_status: 'active' })
          setRoleId('')
          toast('User mapped to the organization')
          refresh()
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <SelectField label="User" value={userId} onChange={(event) => setUserId(event.target.value)} required>
          <option value="">Select user</option>
          {(users.data?.items ?? []).map((user) => <option key={user.id} value={user.id}>{user.full_name} · {user.email}</option>)}
        </SelectField>
        <SelectField label="Organization" value={organizationId} onChange={(event) => { setOrganizationId(event.target.value); setRoleId('') }} required>
          <option value="">Select organization</option>
          {(organizations.data?.items ?? []).map((organization) => <option key={organization.id} value={organization.id}>{organization.display_name}</option>)}
        </SelectField>
        <SelectField label="Role" value={roleId} onChange={(event) => setRoleId(event.target.value)}>
          <option value="">No role</option>
          {(roles.data?.items ?? []).map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}
        </SelectField>
        <Button className="self-end" type="submit">Map user</Button>
      </form>
      <DataTable
        rows={mappings.data ?? []}
        empty={mappings.isLoading ? 'Loading mappings…' : 'No user is mapped to an organization yet.'}
        rowKey={(row) => `${row.organization_id}-${row.id}`}
        columns={[
          { key: 'full_name', label: 'User', render: (row: MembershipMap) => row.full_name },
          { key: 'email', label: 'Email', render: (row) => row.email },
          { key: 'organization_name', label: 'Organization', render: (row) => row.organization_name },
          { key: 'organization_code', label: 'Code', render: (row) => row.organization_code },
          { key: 'roles', label: 'Roles', render: (row) => row.roles.length ? row.roles.join(', ') : '—' },
          { key: 'member_status', label: 'Status', render: (row) => <StatusBadge value={row.member_status} /> },
          { key: 'action', label: '', render: (row) => row.member_status === 'removed' ? null : <Button variant="ghost" onClick={() => adminApi.unmapUser(row.organization_id, row.id).then(refresh).catch((error) => toast(apiError(error), 'error'))}>Remove</Button> },
        ]}
      />
    </div>
  )
}
