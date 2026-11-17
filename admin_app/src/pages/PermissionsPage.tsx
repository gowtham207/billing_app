import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { adminApi, apiError, type Permission } from '@/api'
import { Button, DataTable, Field, PageHeader, useToast } from '@/ui'

export function PermissionsPage() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [q, setQ] = useState('')
  const [form, setForm] = useState({ permission_key: '', module_key: '', description: '' })
  const query = useQuery({ queryKey: ['admin-permissions', q], queryFn: () => adminApi.permissions(q) })
  return (
    <div className="space-y-4">
      <PageHeader title="Permissions" subtitle="Keys that roles can grant inside an organization." />
      <form className="panel grid gap-3 p-4 md:grid-cols-4" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await adminApi.createPermission(form)
          setForm({ permission_key: '', module_key: '', description: '' })
          toast('Permission created')
          queryClient.invalidateQueries({ queryKey: ['admin-permissions'] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <Field label="Permission key" value={form.permission_key} onChange={(event) => setForm({ ...form, permission_key: event.target.value })} required />
        <Field label="Module" value={form.module_key} onChange={(event) => setForm({ ...form, module_key: event.target.value })} required />
        <Field label="Description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
        <Button className="self-end" type="submit">Add permission</Button>
      </form>
      <input className="control w-full max-w-sm px-3 py-2 text-sm" placeholder="Search key or description" value={q} onChange={(event) => setQ(event.target.value)} />
      <DataTable
        rows={query.data ?? []}
        empty={query.isLoading ? 'Loading permissions…' : 'No permissions yet.'}
        rowKey={(item: Permission) => item.id}
        columns={[
          { key: 'module_key', label: 'Module', render: (item) => item.module_key },
          { key: 'permission_key', label: 'Permission', render: (item) => item.permission_key },
          { key: 'description', label: 'Description', render: (item) => item.description || '—' },
          { key: 'action', label: '', render: (item) => <Button variant="ghost" onClick={() => adminApi.deletePermission(item.id).then(() => queryClient.invalidateQueries({ queryKey: ['admin-permissions'] })).catch((error) => toast(apiError(error), 'error'))}>Delete</Button> },
        ]}
      />
    </div>
  )
}
