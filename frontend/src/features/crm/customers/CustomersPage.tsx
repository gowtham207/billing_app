import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Button, ConfirmDialog, Field, Modal, PageHeader, SelectField, StatusBadge, TextArea, useToast } from '@/components/common/ui'
import { useSession } from '@/hooks/session'
import { apiError } from '@/services/api'
import { customerService } from '@/services/customer.service'
import type { Address, Customer } from '@/types/api'
import { formatInr } from '@/utils/money'

type CustomerForm = {
  display_name: string
  customer_code: string
  customer_type: 'individual' | 'business'
  email: string
  phone: string
  alternate_phone: string
  tax_registration_no: string
  pan: string
  line1: string
  shipping_line1: string
  state_region: string
  district: string
  city: string
  postal_code: string
  notes: string
  is_active: boolean
}

const blank = (): CustomerForm => ({
  display_name: '',
  customer_code: '',
  customer_type: 'business',
  email: '',
  phone: '',
  alternate_phone: '',
  tax_registration_no: '',
  pan: '',
  line1: '',
  shipping_line1: '',
  state_region: '',
  district: '',
  city: '',
  postal_code: '',
  notes: '',
  is_active: true,
})

export function CustomersPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Customer | null>(null)
  const [form, setForm] = useState<CustomerForm>(blank())
  const [removeId, setRemoveId] = useState<string | null>(null)
  const customers = useQuery({
    queryKey: ['customers', q, status, page],
    queryFn: () => customerService.list({ q, page, page_size: 20, is_active: status === '' ? undefined : status === 'active' }),
  })
  const save = useMutation({
    mutationFn: async () => {
      const code = form.customer_code || `CUS-${Date.now().toString().slice(-6)}`
      const body = {
        customer_code: code,
        customer_type: form.customer_type,
        display_name: form.display_name,
        email: form.email || null,
        phone: form.phone || null,
        tax_registration_no: form.tax_registration_no || null,
        is_active: form.is_active,
      }
      const customer = editing ? await customerService.update(editing.id, body) : await customerService.create(body)
      if (form.line1) await customerService.addAddress(customer.id, addressBody(customer.id, 'billing', form.line1, form))
      if (form.shipping_line1) await customerService.addAddress(customer.id, addressBody(customer.id, 'shipping', form.shipping_line1, form))
      if (form.notes) await customerService.addNote(customer.id, [form.notes, form.pan && `PAN: ${form.pan}`, form.alternate_phone && `Alternate phone: ${form.alternate_phone}`, form.district && `District: ${form.district}`].filter(Boolean).join('\n'))
      return customer
    },
    onSuccess: () => {
      toast('Customer saved')
      setOpen(false)
      queryClient.invalidateQueries({ queryKey: ['customers'] })
    },
    onError: (error) => toast(apiError(error), 'error'),
  })

  const rows = customers.data?.items ?? []
  return (
    <div>
      <PageHeader title="Customers" subtitle="GSTIN is stored as the customer tax registration number. PAN, alternate phone, and district are saved on the customer note because those columns are not in the API.">
        {session.can('customers.create') ? <Button onClick={() => { setEditing(null); setForm(blank()); setOpen(true) }}>Add customer</Button> : null}
        <Button variant="secondary" onClick={() => exportCustomers(rows)}>Export customers</Button>
      </PageHeader>
      <div className="mb-3 flex flex-wrap gap-2">
        <input className="control px-3 py-2 text-sm" placeholder="Search customers" value={q} onChange={(event) => { setQ(event.target.value); setPage(1) }} />
        <select className="control px-3 py-2 text-sm" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>
      <div className="data-table">
        <table className="min-w-full text-left text-sm">
          <thead className="text-muted"><tr>{['Name', 'Code', 'Email', 'Mobile', 'GSTIN', 'Type', 'Status', ''].map((heading) => <th key={heading} className="px-3 py-2 font-medium">{heading}</th>)}</tr></thead>
          <tbody>
            {rows.map((customer) => (
              <tr key={customer.id} className="border-t border-line">
                <td className="px-3 py-2"><Link className="text-brand underline" to={`/crm/customers/${customer.id}`}>{customer.display_name}</Link></td>
                <td className="px-3 py-2">{customer.customer_code}</td>
                <td className="px-3 py-2">{customer.email}</td>
                <td className="px-3 py-2">{customer.phone}</td>
                <td className="px-3 py-2">{customer.tax_registration_no}</td>
                <td className="px-3 py-2">{customer.customer_type}</td>
                <td className="px-3 py-2"><StatusBadge value={customer.is_active ? 'Active' : 'Inactive'} /></td>
                <td className="px-3 py-2 text-right">
                  {session.can('customers.update') ? <Button variant="ghost" onClick={() => { setEditing(customer); setForm({ ...blank(), ...customer, customer_type: customer.customer_type, email: customer.email ?? '', phone: customer.phone ?? '', tax_registration_no: customer.tax_registration_no ?? '' }); setOpen(true) }}>Edit</Button> : null}
                  {session.can('customers.delete') ? <Button variant="ghost" onClick={() => setRemoveId(customer.id)}>Delete</Button> : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 ? <p className="p-6 text-sm text-muted">No customers match this search.</p> : null}
      </div>
      <div className="mt-3 flex items-center justify-between text-sm">
        <span>{customers.data?.total ?? 0} customers</span>
        <div className="flex gap-2">
          <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>Previous</Button>
          <Button variant="secondary" disabled={(customers.data?.page ?? 1) * (customers.data?.page_size ?? 20) >= (customers.data?.total ?? 0)} onClick={() => setPage((value) => value + 1)}>Next</Button>
        </div>
      </div>
      <Modal title={editing ? 'Edit customer' : 'Add customer'} open={open} onClose={() => setOpen(false)}>
        <form className="grid gap-3 md:grid-cols-2" onSubmit={(event) => { event.preventDefault(); save.mutate() }}>
          <Field label="Customer name" value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} required />
          <Field label="Customer code" value={form.customer_code} placeholder="Auto-generated if empty" onChange={(event) => setForm({ ...form, customer_code: event.target.value })} />
          <SelectField label="Customer type" value={form.customer_type} onChange={(event) => setForm({ ...form, customer_type: event.target.value as CustomerForm['customer_type'] })}>
            <option value="individual">Individual</option>
            <option value="business">Business</option>
          </SelectField>
          <Field label="Email" type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          <Field label="Mobile number" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
          <Field label="Alternate mobile number" value={form.alternate_phone} onChange={(event) => setForm({ ...form, alternate_phone: event.target.value })} />
          <Field label="GSTIN" value={form.tax_registration_no} onChange={(event) => setForm({ ...form, tax_registration_no: event.target.value })} />
          <Field label="PAN" value={form.pan} onChange={(event) => setForm({ ...form, pan: event.target.value })} />
          <Field label="Billing address" value={form.line1} onChange={(event) => setForm({ ...form, line1: event.target.value })} />
          <Field label="Shipping address" value={form.shipping_line1} onChange={(event) => setForm({ ...form, shipping_line1: event.target.value })} />
          <Field label="State" value={form.state_region} onChange={(event) => setForm({ ...form, state_region: event.target.value })} />
          <Field label="District" value={form.district} onChange={(event) => setForm({ ...form, district: event.target.value })} />
          <Field label="City" value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} />
          <Field label="Pincode" value={form.postal_code} onChange={(event) => setForm({ ...form, postal_code: event.target.value })} />
          <SelectField label="Status" value={form.is_active ? 'active' : 'inactive'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'active' })}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </SelectField>
          <div className="md:col-span-2"><TextArea label="Notes" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} /></div>
          <div className="md:col-span-2 flex justify-end"><Button type="submit" disabled={save.isPending}>Save customer</Button></div>
        </form>
      </Modal>
      <ConfirmDialog open={Boolean(removeId)} title="Delete customer" message="This removes the customer when the server allows it." onClose={() => setRemoveId(null)} onConfirm={() => {
        if (!removeId) return
        customerService.remove(removeId).then(() => { toast('Customer deleted'); queryClient.invalidateQueries({ queryKey: ['customers'] }) }).catch((error) => toast(apiError(error), 'error')).finally(() => setRemoveId(null))
      }} />
    </div>
  )
}

function addressBody(customerId: string, addressType: string, line1: string, form: CustomerForm) {
  return { customer_id: customerId, address_type: addressType, line1, city: form.city || null, state_region: form.state_region || null, postal_code: form.postal_code || null, country_code: 'IN' }
}

function exportCustomers(rows: Customer[]) {
  const header = ['name', 'code', 'email', 'phone', 'gstin', 'type', 'status']
  const lines = rows.map((row) => [row.display_name, row.customer_code, row.email ?? '', row.phone ?? '', row.tax_registration_no ?? '', row.customer_type, row.is_active ? 'active' : 'inactive'].join(','))
  const blob = new Blob([[header.join(','), ...lines].join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'customers.csv'
  link.click()
  URL.revokeObjectURL(url)
}

export function CustomerDetailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const customer = useQuery({ queryKey: ['customer', id], queryFn: () => customerService.get(id) })
  const addresses = useQuery({ queryKey: ['customer-addresses', id], queryFn: () => customerService.addresses(id) })
  const notes = useQuery({ queryKey: ['customer-notes', id], queryFn: () => customerService.notes(id) })
  const outstanding = useQuery({ queryKey: ['customer-outstanding', id], queryFn: () => customerService.outstanding(id) })
  const data = customer.data
  const addressText = useMemo(() => (addresses.data ?? []).map(formatAddress).join(' | '), [addresses.data])
  if (!data) return <p className="text-sm text-muted">Loading customer…</p>
  return (
    <div>
      <PageHeader title={data.display_name} subtitle={data.customer_code}>
        <Button variant="secondary" onClick={() => navigate('/crm/customers')}>Back</Button>
      </PageHeader>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="panel p-4">
          <p>Email: {data.email || '—'}</p>
          <p>Mobile: {data.phone || '—'}</p>
          <p>GSTIN: {data.tax_registration_no || '—'}</p>
          <p>Type: {data.customer_type}</p>
          <p className="mt-2">Status <StatusBadge value={data.is_active ? 'Active' : 'Inactive'} /></p>
          <p>Outstanding: {formatInr(String(outstanding.data?.outstanding ?? data.opening_balance))}</p>
          <p className="mt-2">Addresses: {addressText || 'No saved addresses'}</p>
        </div>
        <div className="panel p-4">
          <h2 className="mb-2 font-medium">Notes</h2>
          {(notes.data ?? []).map((note) => <p key={note.id} className="mb-2 text-sm">{note.note}</p>)}
          {(notes.data ?? []).length === 0 ? <p className="text-sm text-muted">No notes</p> : null}
        </div>
      </div>
    </div>
  )
}

function formatAddress(address: Address) {
  return [address.address_type, address.line1, address.city, address.state_region, address.postal_code].filter(Boolean).join(', ')
}
