import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { adminApi, apiError, type AdminAccount } from '@/api'
import { useSession } from '@/session'
import { Button, DataTable, Field, PageHeader, StatusBadge, useToast } from '@/ui'

export function AdminsPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [q, setQ] = useState('')
  const [form, setForm] = useState({ full_name: '', email: '', password: '' })
  const query = useQuery({ queryKey: ['admin-accounts', q], queryFn: () => adminApi.admins(q) })
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['admin-accounts'] })
  return (
    <div className="space-y-4">
      <PageHeader title="Administrators" subtitle="These accounts sign in only to this console. They are not workspace users." />
      <form className="panel grid gap-3 p-4 md:grid-cols-4" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await adminApi.createAdmin(form)
          setForm({ full_name: '', email: '', password: '' })
          toast('Administrator created')
          refresh()
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <Field label="Name" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} required />
        <Field label="Email" type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
        <Field label="Password" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required minLength={8} />
        <Button className="self-end" type="submit">Add administrator</Button>
      </form>
      <input className="control w-full max-w-sm px-3 py-2 text-sm" placeholder="Search administrators" value={q} onChange={(event) => setQ(event.target.value)} />
      <DataTable
        rows={query.data ?? []}
        empty={query.isLoading ? 'Loading administrators…' : 'No administrators yet.'}
        rowKey={(admin) => admin.id}
        columns={[
          { key: 'full_name', label: 'Name', render: (admin: AdminAccount) => admin.full_name },
          { key: 'email', label: 'Email', render: (admin) => admin.email },
          { key: 'status', label: 'Status', render: (admin) => <StatusBadge value={admin.is_active ? 'Active' : 'Inactive'} /> },
          { key: 'last_login_at', label: 'Last login', render: (admin) => admin.last_login_at ? admin.last_login_at.slice(0, 16).replace('T', ' ') : '—' },
          { key: 'action', label: '', render: (admin) => admin.id === session.user?.id ? <span className="text-xs text-muted">You</span> : <Button variant="ghost" onClick={() => adminApi.updateAdmin(admin.id, { is_active: !admin.is_active }).then(refresh).catch((error) => toast(apiError(error), 'error'))}>{admin.is_active ? 'Disable' : 'Activate'}</Button> },
        ]}
      />
    </div>
  )
}
