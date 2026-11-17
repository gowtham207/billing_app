import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Building2, MapPin, Pencil, Search } from 'lucide-react'
import { useState } from 'react'
import { adminApi, apiError, type MembershipMap, type User } from '@/api'
import { Button, Field, Modal, SelectField, useToast } from '@/ui'

const emptyCreate = { full_name: '', email: '', password: '', phone: '' }

type OrgPick = { organization_id: string; role_id: string; branch_id: string }

export function UsersPage() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [q, setQ] = useState('')
  const [organizationFilter, setOrganizationFilter] = useState('')
  const [branchFilter, setBranchFilter] = useState('')
  const [creating, setCreating] = useState(false)
  const [createForm, setCreateForm] = useState(emptyCreate)
  const [createOrgs, setCreateOrgs] = useState<OrgPick[]>([])
  const [editing, setEditing] = useState<User | null>(null)
  const [editForm, setEditForm] = useState({ full_name: '', email: '', phone: '', password: '', is_active: true })
  const [assigning, setAssigning] = useState<User | null>(null)
  const [assignOrgs, setAssignOrgs] = useState<OrgPick[]>([])

  const users = useQuery({ queryKey: ['admin-users', q], queryFn: () => adminApi.users(q) })
  const organizations = useQuery({ queryKey: ['admin-orgs'], queryFn: () => adminApi.organizations() })
  const memberships = useQuery({ queryKey: ['admin-memberships'], queryFn: adminApi.memberships })
  const filterBranches = useQuery({ queryKey: ['admin-branches', organizationFilter], enabled: Boolean(organizationFilter), queryFn: () => adminApi.branches(organizationFilter) })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    queryClient.invalidateQueries({ queryKey: ['admin-memberships'] })
  }

  const activeMaps = (memberships.data ?? []).filter((row) => row.member_status !== 'removed')
  const mapsFor = (userId: string) => activeMaps.filter((row) => row.user_id === userId && (!organizationFilter || row.organization_id === organizationFilter))
  const branchChoices = organizationFilter
    ? (filterBranches.data ?? []).map((branch) => branch.name)
    : [...new Set(activeMaps.flatMap((row) => row.branches))].sort((left, right) => left.localeCompare(right))

  const rows = (users.data?.items ?? []).filter((user) => {
    const maps = mapsFor(user.id)
    if (organizationFilter && maps.length === 0) return false
    if (branchFilter && !maps.some((row) => row.branches.includes(branchFilter))) return false
    return true
  })

  const openEdit = (user: User) => {
    setEditing(user)
    setEditForm({ full_name: user.full_name, email: user.email, phone: user.phone ?? '', password: '', is_active: user.is_active })
  }

  const openAssign = (user: User) => {
    setAssigning(user)
    setAssignOrgs([])
  }

  const saveOrganisations = async (userId: string, picks: OrgPick[]) => {
    if (picks.length === 0) return
    await adminApi.mapUsers({
      user_id: userId,
      organizations: picks.map((pick) => ({
        organization_id: pick.organization_id,
        role_id: pick.role_id || undefined,
        branch_id: pick.branch_id || undefined,
      })),
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <label className="relative min-w-56 flex-1">
          <Search className="pointer-events-none absolute top-2.5 left-3 text-muted" size={16} />
          <input className="control w-full py-2 pr-3 pl-9 text-sm" placeholder="Search by name or email..." value={q} onChange={(event) => setQ(event.target.value)} />
        </label>
        <label className="relative">
          <Building2 className="pointer-events-none absolute top-2.5 left-3 text-muted" size={16} />
          <select className="control appearance-none py-2 pr-8 pl-9 text-sm" value={organizationFilter} onChange={(event) => { setOrganizationFilter(event.target.value); setBranchFilter('') }}>
            <option value="">All organisations</option>
            {(organizations.data?.items ?? []).map((organization) => <option key={organization.id} value={organization.id}>{organization.display_name}</option>)}
          </select>
        </label>
        <label className="relative">
          <MapPin className="pointer-events-none absolute top-2.5 left-3 text-muted" size={16} />
          <select className="control appearance-none py-2 pr-8 pl-9 text-sm" value={branchFilter} onChange={(event) => setBranchFilter(event.target.value)}>
            <option value="">All branches</option>
            {branchChoices.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
        </label>
        <Button className="ml-auto" onClick={() => { setCreateForm(emptyCreate); setCreateOrgs([]); setCreating(true) }}>Create user</Button>
      </div>

      <div className="data-table">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="text-xs tracking-wide uppercase">
              <th className="px-4 py-3 font-medium">Name / email</th>
              <th className="px-4 py-3 font-medium">Organisations</th>
              <th className="px-4 py-3 font-medium">Branches</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td className="px-4 py-8 text-muted" colSpan={5}>{users.isLoading ? 'Loading users…' : 'No workspace users match these filters.'}</td></tr>
            ) : rows.map((user) => {
              const maps = mapsFor(user.id).filter((row) => !branchFilter || row.branches.includes(branchFilter))
              const roles = [...new Set(maps.flatMap((row) => row.roles))]
              return (
                <tr key={user.id} className="border-t border-line">
                  <td className="px-4 py-3">
                    <p className="font-semibold">{user.full_name}</p>
                    <p className="text-xs text-muted">{user.email}</p>
                    {user.is_active ? null : <p className="mt-1 text-xs font-medium text-danger">Inactive</p>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      {maps.length === 0 ? <span className="text-muted">—</span> : maps.map((row) => (
                        <span key={row.id} className="chip chip-org" title={row.organization_code}><Building2 size={12} />{row.organization_name}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      {maps.flatMap((row) => row.branches).length === 0 ? <span className="text-muted">—</span> : [...new Set(maps.flatMap((row) => row.branches))].map((name) => (
                        <span key={name} className="chip chip-branch">{name}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted">{roles.length ? roles.join(', ') : '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <button type="button" className="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-sm font-medium hover:bg-brand/10" onClick={() => openEdit(user)}>
                        <Pencil size={14} /> Edit
                      </button>
                      <button type="button" className="inline-flex items-center gap-1.5 rounded-lg border border-brand px-3 py-1.5 text-sm font-medium text-brand hover:bg-brand/10" onClick={() => openAssign(user)}>
                        Assign access
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <Modal title="Create user" wide open={creating} onClose={() => setCreating(false)}>
        <form className="grid gap-3" onSubmit={async (event) => {
          event.preventDefault()
          try {
            const created = await adminApi.createUser({
              full_name: createForm.full_name,
              email: createForm.email,
              password: createForm.password,
              phone: createForm.phone || undefined,
            })
            await saveOrganisations(created.id, createOrgs)
            setCreating(false)
            toast(createOrgs.length > 1 ? `User created in ${createOrgs.length} organisations` : 'Workspace user created')
            refresh()
          } catch (error) {
            toast(apiError(error), 'error')
          }
        }}>
          <Field label="Name" value={createForm.full_name} onChange={(event) => setCreateForm({ ...createForm, full_name: event.target.value })} required />
          <Field label="Email" type="email" value={createForm.email} onChange={(event) => setCreateForm({ ...createForm, email: event.target.value })} required />
          <Field label="Password" type="password" value={createForm.password} onChange={(event) => setCreateForm({ ...createForm, password: event.target.value })} required minLength={8} />
          <Field label="Phone" value={createForm.phone} onChange={(event) => setCreateForm({ ...createForm, phone: event.target.value })} />
          <OrgChecklist selected={createOrgs} onChange={setCreateOrgs} />
          <Button type="submit">Create user</Button>
        </form>
      </Modal>

      <Modal title="Edit user" open={editing !== null} onClose={() => setEditing(null)}>
        <form className="grid gap-3" onSubmit={async (event) => {
          event.preventDefault()
          if (!editing) return
          try {
            await adminApi.updateUser(editing.id, {
              full_name: editForm.full_name,
              email: editForm.email,
              phone: editForm.phone,
              is_active: editForm.is_active,
              ...(editForm.password ? { password: editForm.password } : {}),
            })
            setEditing(null)
            toast('User updated')
            refresh()
          } catch (error) {
            toast(apiError(error), 'error')
          }
        }}>
          <Field label="Name" value={editForm.full_name} onChange={(event) => setEditForm({ ...editForm, full_name: event.target.value })} required />
          <Field label="Email" type="email" value={editForm.email} onChange={(event) => setEditForm({ ...editForm, email: event.target.value })} required />
          <Field label="Phone" value={editForm.phone} onChange={(event) => setEditForm({ ...editForm, phone: event.target.value })} />
          <Field label="New password" type="password" value={editForm.password} minLength={8} placeholder="Leave blank to keep the current password" onChange={(event) => setEditForm({ ...editForm, password: event.target.value })} />
          <SelectField label="Status" value={editForm.is_active ? 'active' : 'inactive'} onChange={(event) => setEditForm({ ...editForm, is_active: event.target.value === 'active' })}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </SelectField>
          <Button type="submit">Save user</Button>
        </form>
      </Modal>

      <Modal title={assigning ? `Assign access · ${assigning.full_name}` : 'Assign access'} wide open={assigning !== null} onClose={() => setAssigning(null)}>
        <form className="space-y-4" onSubmit={async (event) => {
          event.preventDefault()
          if (!assigning || assignOrgs.length === 0) return
          try {
            await saveOrganisations(assigning.id, assignOrgs)
            setAssignOrgs([])
            toast(assignOrgs.length === 1 ? 'Organisation assigned' : `${assignOrgs.length} organisations assigned`)
            refresh()
          } catch (error) {
            toast(apiError(error), 'error')
          }
        }}>
          <CurrentAccess userId={assigning?.id ?? ''} rows={activeMaps} onRemove={async (row) => {
            try {
              await adminApi.unmapUser(row.organization_id, row.id)
              toast('Organisation removed')
              refresh()
            } catch (error) {
              toast(apiError(error), 'error')
            }
          }} />
          <OrgChecklist
            selected={assignOrgs}
            onChange={setAssignOrgs}
            disabledIds={activeMaps.filter((row) => row.user_id === assigning?.id).map((row) => row.organization_id)}
          />
          <Button type="submit" disabled={assignOrgs.length === 0}>
            {assignOrgs.length > 1 ? `Add ${assignOrgs.length} organisations` : 'Add organisation'}
          </Button>
        </form>
      </Modal>
    </div>
  )
}

function OrgChecklist({ selected, onChange, disabledIds = [] }: { selected: OrgPick[]; onChange: (next: OrgPick[]) => void; disabledIds?: string[] }) {
  const organizations = useQuery({ queryKey: ['admin-orgs'], queryFn: () => adminApi.organizations() })
  const items = organizations.data?.items ?? []
  return (
    <div>
      <p className="mb-1 text-sm text-muted">Organisations</p>
      <p className="mb-2 text-xs text-muted">Select every organisation this user should join. Each one can have its own role and branch.</p>
      <div className="max-h-72 space-y-1 overflow-y-auto rounded-lg border border-line p-2">
        {items.length === 0 ? <p className="px-2 py-3 text-sm text-muted">No organisations yet.</p> : items.map((organization) => {
          const picked = selected.find((item) => item.organization_id === organization.id)
          const already = disabledIds.includes(organization.id)
          return (
            <div key={organization.id} className="rounded-lg px-2 py-2">
              <label className="flex items-center gap-2 text-sm font-medium">
                <input
                  type="checkbox"
                  className="size-4 accent-brand"
                  checked={already || Boolean(picked)}
                  disabled={already}
                  onChange={() => {
                    if (already) return
                    if (picked) onChange(selected.filter((item) => item.organization_id !== organization.id))
                    else onChange([...selected, { organization_id: organization.id, role_id: '', branch_id: '' }])
                  }}
                />
                <Building2 size={14} className="text-brand" />
                {organization.display_name}
                {already ? <span className="text-xs font-normal text-muted">Already added</span> : null}
              </label>
              {picked ? (
                <OrgRoleBranch
                  pick={picked}
                  onChange={(next) => onChange(selected.map((item) => item.organization_id === next.organization_id ? next : item))}
                />
              ) : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function OrgRoleBranch({ pick, onChange }: { pick: OrgPick; onChange: (pick: OrgPick) => void }) {
  const roles = useQuery({ queryKey: ['admin-roles', pick.organization_id], queryFn: () => adminApi.roles(pick.organization_id) })
  const branches = useQuery({ queryKey: ['admin-branches', pick.organization_id], queryFn: () => adminApi.branches(pick.organization_id) })
  return (
    <div className="mt-2 grid gap-2 pl-6 sm:grid-cols-2">
      <SelectField label="Role" value={pick.role_id} onChange={(event) => onChange({ ...pick, role_id: event.target.value })}>
        <option value="">No role</option>
        {(roles.data?.items ?? []).map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}
      </SelectField>
      <SelectField label="Branch" value={pick.branch_id} onChange={(event) => onChange({ ...pick, branch_id: event.target.value })}>
        <option value="">No branch</option>
        {(branches.data ?? []).map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
      </SelectField>
    </div>
  )
}

function CurrentAccess({ userId, rows, onRemove }: { userId: string; rows: MembershipMap[]; onRemove: (row: MembershipMap) => void }) {
  const own = rows.filter((row) => row.user_id === userId)
  if (!userId) return null
  if (own.length === 0) return <p className="text-sm text-muted">This user is not in an organisation yet.</p>
  return (
    <ul className="space-y-2">
      {own.map((row) => (
        <li key={row.id} className="flex items-center justify-between gap-3 rounded-lg border border-line px-3 py-2 text-sm">
          <div>
            <p className="font-medium">{row.organization_name}</p>
            <p className="text-xs text-muted">{[row.roles.join(', ') || 'No role', row.branches.join(', ') || 'No branch'].join(' · ')}</p>
          </div>
          <button type="button" className="text-sm text-danger" onClick={() => onRemove(row)}>Remove</button>
        </li>
      ))}
    </ul>
  )
}
