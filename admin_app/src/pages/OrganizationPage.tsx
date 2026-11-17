import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { adminApi, apiError, type Branch, type Member, type Permission, type Role } from '@/api'
import { Button, DataTable, Field, PageHeader, StatusBadge, useToast } from '@/ui'

export function OrganizationPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const queryClient = useQueryClient()
  const organizations = useQuery({ queryKey: ['admin-orgs'], queryFn: () => adminApi.organizations() })
  const organization = organizations.data?.items.find((item) => item.id === id)
  const branches = useQuery({ queryKey: ['admin-branches', id], queryFn: () => adminApi.branches(id) })
  const members = useQuery({ queryKey: ['admin-members', id], queryFn: () => adminApi.members(id) })
  const roles = useQuery({ queryKey: ['admin-roles', id], queryFn: () => adminApi.roles(id) })
  const [profile, setProfile] = useState<{ display_name: string; legal_name: string; email: string; phone: string } | null>(null)
  const [branch, setBranch] = useState({ code: '', name: '', phone: '' })
  const [member, setMember] = useState({ email: '', full_name: '', password: '' })
  const [role, setRole] = useState({ role_key: '', name: '' })
  const [selectedRole, setSelectedRole] = useState('')
  const permissions = useQuery({ queryKey: ['admin-permissions'], queryFn: () => adminApi.permissions() })
  const assigned = useQuery({ queryKey: ['role-permissions', id, selectedRole], enabled: Boolean(selectedRole), queryFn: () => adminApi.rolePermissions(id, selectedRole) })
  const [notice, setNotice] = useState('')
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['admin-branches', id] })
    queryClient.invalidateQueries({ queryKey: ['admin-members', id] })
    queryClient.invalidateQueries({ queryKey: ['admin-roles', id] })
    queryClient.invalidateQueries({ queryKey: ['admin-orgs'] })
  }
  if (!organization && organizations.isLoading) return <p className="text-sm text-muted">Loading organization…</p>
  if (!organization) return <p className="text-sm">Organization not found. <Link className="text-brand" to="/organizations">Back to organizations</Link></p>
  const current = profile ?? { display_name: organization.display_name, legal_name: organization.legal_name, email: organization.email ?? '', phone: organization.phone ?? '' }
  return (
    <div className="space-y-4">
      <PageHeader title={organization.display_name} subtitle={organization.code}>
        <StatusBadge value={organization.status} />
        <Button variant="secondary" onClick={() => adminApi.activateOrganization(id).then(refresh).catch((error) => toast(apiError(error), 'error'))}>Activate</Button>
        <Button variant="secondary" onClick={() => adminApi.deactivateOrganization(id).then(refresh).catch((error) => toast(apiError(error), 'error'))}>Suspend</Button>
        <Button variant="danger" onClick={() => { if (window.confirm('Delete this organization?')) adminApi.deleteOrganization(id).then(() => navigate('/organizations')).catch((error) => toast(apiError(error), 'error')) }}>Delete</Button>
      </PageHeader>
      <Link className="text-sm text-brand" to="/organizations">All organizations</Link>
      {notice ? <p className="notice">{notice}</p> : null}
      <form className="panel grid gap-3 p-4 md:grid-cols-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await adminApi.updateOrganization(id, current)
          toast('Organization saved')
          refresh()
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <Field label="Display name" value={current.display_name} onChange={(event) => setProfile({ ...current, display_name: event.target.value })} />
        <Field label="Legal name" value={current.legal_name} onChange={(event) => setProfile({ ...current, legal_name: event.target.value })} />
        <Field label="Email" value={current.email} onChange={(event) => setProfile({ ...current, email: event.target.value })} />
        <Field label="Phone" value={current.phone} onChange={(event) => setProfile({ ...current, phone: event.target.value })} />
        <Button className="w-fit" type="submit">Save profile</Button>
      </form>
      <section className="space-y-3">
        <h2 className="font-semibold">Branches</h2>
        <form className="flex flex-wrap gap-2" onSubmit={async (event) => {
          event.preventDefault()
          try {
            await adminApi.createBranch(id, branch)
            setBranch({ code: '', name: '', phone: '' })
            toast('Branch created')
            refresh()
          } catch (error) {
            toast(apiError(error), 'error')
          }
        }}>
          <Field label="Code" value={branch.code} onChange={(event) => setBranch({ ...branch, code: event.target.value })} required />
          <Field label="Name" value={branch.name} onChange={(event) => setBranch({ ...branch, name: event.target.value })} required />
          <Field label="Phone" value={branch.phone} onChange={(event) => setBranch({ ...branch, phone: event.target.value })} />
          <Button className="self-end" type="submit">Add branch</Button>
        </form>
        <DataTable
          rows={branches.data ?? []}
          empty="No branches yet."
          rowKey={(item: Branch) => item.id}
          columns={[
            { key: 'code', label: 'Code', render: (item) => item.code },
            { key: 'name', label: 'Name', render: (item) => item.name },
            { key: 'phone', label: 'Phone', render: (item) => item.phone || '—' },
            { key: 'office', label: 'Head office', render: (item) => item.is_head_office ? 'Yes' : 'No' },
            { key: 'status', label: 'Status', render: (item) => <StatusBadge value={item.is_active ? 'Active' : 'Inactive'} /> },
            { key: 'action', label: '', render: (item) => item.is_active ? <Button variant="ghost" onClick={() => adminApi.deactivateBranch(id, item.id).then(refresh).catch((error) => toast(apiError(error), 'error'))}>Deactivate</Button> : null },
          ]}
        />
      </section>
      <section className="space-y-3">
        <h2 className="font-semibold">Users</h2>
        <form className="flex flex-wrap gap-2" onSubmit={async (event) => {
          event.preventDefault()
          try {
            const created = await adminApi.inviteMember(id, { ...member, password: member.password || undefined })
            setMember({ email: '', full_name: '', password: '' })
            setNotice(created.temporary_password ? `Temporary password for ${member.email}: ${created.temporary_password}` : 'User invited.')
            toast('User invited')
            refresh()
          } catch (error) {
            toast(apiError(error), 'error')
          }
        }}>
          <Field label="Name" value={member.full_name} onChange={(event) => setMember({ ...member, full_name: event.target.value })} />
          <Field label="Email" type="email" value={member.email} onChange={(event) => setMember({ ...member, email: event.target.value })} required />
          <Field label="Password" type="password" value={member.password} onChange={(event) => setMember({ ...member, password: event.target.value })} />
          <Button className="self-end" type="submit">Add user</Button>
        </form>
        <DataTable
          rows={members.data ?? []}
          empty="No users in this organization."
          rowKey={(item: Member) => item.id}
          columns={[
            { key: 'full_name', label: 'Name', render: (item) => item.full_name },
            { key: 'email', label: 'Email', render: (item) => item.email },
            { key: 'joined_at', label: 'Joined', render: (item) => item.joined_at ? item.joined_at.slice(0, 10) : '—' },
            { key: 'status', label: 'Status', render: (item) => <StatusBadge value={item.member_status} /> },
            { key: 'action', label: '', render: (item) => <Button variant="ghost" onClick={() => adminApi.setMemberStatus(id, item.id, item.member_status === 'active' ? 'disabled' : 'active').then(refresh).catch((error) => toast(apiError(error), 'error'))}>{item.member_status === 'active' ? 'Disable' : 'Activate'}</Button> },
          ]}
        />
      </section>
      <section className="space-y-3">
        <h2 className="font-semibold">Roles</h2>
        <form className="flex flex-wrap gap-2" onSubmit={async (event) => {
          event.preventDefault()
          try {
            await adminApi.createRole(id, role)
            setRole({ role_key: '', name: '' })
            toast('Role created')
            refresh()
          } catch (error) {
            toast(apiError(error), 'error')
          }
        }}>
          <Field label="Role name" value={role.name} onChange={(event) => setRole({ ...role, name: event.target.value })} required />
          <Field label="Role key" value={role.role_key} onChange={(event) => setRole({ ...role, role_key: event.target.value })} required />
          <Button className="self-end" type="submit">Add role</Button>
        </form>
        <DataTable
          rows={roles.data?.items ?? []}
          empty="No roles yet."
          rowKey={(item: Role) => item.id}
          columns={[
            { key: 'name', label: 'Role', render: (item) => <button className="font-medium text-brand" onClick={() => setSelectedRole(item.id)}>{item.name}</button> },
            { key: 'role_key', label: 'Key', render: (item) => item.role_key },
            { key: 'description', label: 'Description', render: (item) => item.description || '—' },
            { key: 'type', label: 'Type', render: (item) => <StatusBadge value={item.is_system ? 'System' : 'Custom'} /> },
            { key: 'action', label: '', render: (item) => item.is_system ? null : <Button variant="ghost" onClick={() => adminApi.deleteRole(id, item.id).then(refresh).catch((error) => toast(apiError(error), 'error'))}>Delete</Button> },
          ]}
        />
        <h3 className="text-sm font-semibold">Role permissions</h3>
        <DataTable
          rows={selectedRole ? (permissions.data ?? []) : []}
          empty={selectedRole ? 'No permissions are defined.' : 'Select a role to edit its permissions.'}
          rowKey={(item: Permission) => item.id}
          columns={[
            { key: 'assigned', label: 'Assigned', render: (item) => {
              const ids = new Set(assigned.data?.permission_ids ?? [])
              return <input type="checkbox" checked={ids.has(item.id)} onChange={async (event) => {
                const next = new Set(ids)
                if (event.target.checked) next.add(item.id)
                else next.delete(item.id)
                try {
                  await adminApi.setRolePermissions(id, selectedRole, [...next])
                  queryClient.invalidateQueries({ queryKey: ['role-permissions', id, selectedRole] })
                } catch (error) {
                  toast(apiError(error), 'error')
                }
              }} />
            } },
            { key: 'module_key', label: 'Module', render: (item) => item.module_key },
            { key: 'permission_key', label: 'Permission', render: (item) => item.permission_key },
            { key: 'description', label: 'Description', render: (item) => item.description || '—' },
          ]}
        />
      </section>
    </div>
  )
}
