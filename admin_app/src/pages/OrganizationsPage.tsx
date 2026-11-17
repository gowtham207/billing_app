import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { adminApi, apiError, type Organization } from '@/api'
import { Button, DataTable, Field, Modal, PageHeader, StatusBadge, useToast } from '@/ui'

const blank = { legal_name: '', display_name: '', code: '', email: '', phone: '', owner_email: '', owner_name: '' }

export function OrganizationsPage() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(blank)
  const [notice, setNotice] = useState('')
  const query = useQuery({ queryKey: ['admin-orgs', q], queryFn: () => adminApi.organizations(q) })
  const set = (key: keyof typeof blank) => (value: string) => setForm((current) => ({ ...current, [key]: value }))
  return (
    <div>
      <PageHeader title="Organizations" subtitle="Create and manage every tenant.">
        <Button onClick={() => { setForm(blank); setNotice(''); setOpen(true) }}>New organization</Button>
      </PageHeader>
      <input className="control mb-3 w-full max-w-sm px-3 py-2 text-sm" placeholder="Search name, code, or email" value={q} onChange={(event) => setQ(event.target.value)} />
      <DataTable
        rows={query.data?.items ?? []}
        empty={query.isLoading ? 'Loading organizations…' : 'No organizations yet.'}
        rowKey={(org) => org.id}
        columns={[
          { key: 'display_name', label: 'Name', render: (org: Organization) => <Link className="font-medium text-brand" to={`/organizations/${org.id}`}>{org.display_name}</Link> },
          { key: 'code', label: 'Code', render: (org) => org.code },
          { key: 'legal_name', label: 'Legal name', render: (org) => org.legal_name },
          { key: 'email', label: 'Email', render: (org) => org.email || '—' },
          { key: 'status', label: 'Status', render: (org) => <StatusBadge value={org.status} /> },
        ]}
      />
      <Modal title="New organization" open={open} onClose={() => setOpen(false)}>
        <form className="grid gap-3" onSubmit={async (event) => {
          event.preventDefault()
          try {
            const created = await adminApi.createOrganization(Object.fromEntries(Object.entries(form).filter(([, value]) => value)))
            setNotice(created.temporary_owner_password ? `Temporary owner password: ${created.temporary_owner_password}` : 'Organization created.')
            toast('Organization created')
            queryClient.invalidateQueries({ queryKey: ['admin-orgs'] })
            setOpen(false)
          } catch (error) {
            toast(apiError(error), 'error')
          }
        }}>
          <Field label="Legal name" value={form.legal_name} onChange={(event) => set('legal_name')(event.target.value)} required />
          <Field label="Display name" value={form.display_name} onChange={(event) => set('display_name')(event.target.value)} />
          <Field label="Code" value={form.code} onChange={(event) => set('code')(event.target.value)} />
          <Field label="Email" type="email" value={form.email} onChange={(event) => set('email')(event.target.value)} />
          <Field label="Phone" value={form.phone} onChange={(event) => set('phone')(event.target.value)} />
          <Field label="Owner email" type="email" value={form.owner_email} onChange={(event) => set('owner_email')(event.target.value)} required />
          <Field label="Owner name" value={form.owner_name} onChange={(event) => set('owner_name')(event.target.value)} required />
          <Button type="submit">Create organization</Button>
        </form>
      </Modal>
      {notice ? <p className="notice mt-3">{notice}</p> : null}
    </div>
  )
}
