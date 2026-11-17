import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Button, DataTable, Field, PageHeader, StatusBadge, useToast } from '@/components/common/ui'
import { useSession } from '@/hooks/session'
import { accessService, reportService } from '@/services/dashboard.service'
import { apiError } from '@/services/api'
import { documentService, paymentService } from '@/services/billing.service'
import { customerService } from '@/services/customer.service'
import { organizationService } from '@/services/organization.service'
import { formatInr } from '@/utils/money'

const reports = ['sales', 'purchases', 'inventory', 'stock-movement', 'customer-ledger', 'supplier-ledger', 'outstanding', 'expenses', 'tax', 'profit-loss']

function textStatus(row: Record<string, unknown>) {
  for (const key of ['status_label', 'status', 'document_status', 'payment_status']) {
    const value = row[key]
    if (typeof value === 'string' && value) return value
  }
  return ''
}

export function DocumentPage({ title, path, createPath, action }: { title: string; path: string; createPath?: string; action?: string }) {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: [path], queryFn: () => documentService.list(path) })
  const customers = useQuery({ queryKey: ['customers-all'], queryFn: () => customerService.list({ page_size: 100 }) })
  const [customerId, setCustomerId] = useState('')
  const [description, setDescription] = useState('Item')
  const [quantity, setQuantity] = useState('1')
  const [price, setPrice] = useState('0')
  const rows = query.data?.items ?? []
  return (
    <div>
      <PageHeader title={title} />
      {createPath ? (
        <form className="mb-4 grid gap-2 panel p-4 md:grid-cols-5" onSubmit={async (event) => {
          event.preventDefault()
          try {
            await documentService.create(createPath, {
              customer_id: customerId,
              branch_id: session.branchId,
              items: [{ description, quantity, unit_price: price, discount_amount: 0, tax_rate: 0, tax_amount: 0 }],
            })
            queryClient.invalidateQueries({ queryKey: [path] })
          } catch (error) {
            toast(apiError(error), 'error')
          }
        }}>
          <select className="control px-2 py-2 text-sm" value={customerId} onChange={(event) => setCustomerId(event.target.value)} required>
            <option value="">Customer</option>
            {(customers.data?.items ?? []).map((customer) => <option key={customer.id} value={customer.id}>{customer.display_name}</option>)}
          </select>
          <input className="control px-2 py-2 text-sm" value={description} onChange={(event) => setDescription(event.target.value)} />
          <input className="control px-2 py-2 text-sm" value={quantity} onChange={(event) => setQuantity(event.target.value)} />
          <input className="control px-2 py-2 text-sm" value={price} onChange={(event) => setPrice(event.target.value)} />
          <Button type="submit">Create</Button>
        </form>
      ) : null}
      <DataTable
        rows={rows}
        empty="No records yet."
        rowKey={(row) => String(row.id)}
        columns={[
          { key: 'number', label: 'Number', render: (row) => String(row.quotation_no ?? row.order_no ?? row.credit_note_no ?? row.payment_no ?? row.expense_no ?? row.po_number ?? row.invoice_no ?? row.id) },
          { key: 'date', label: 'Date', render: (row) => String(row.document_date ?? row.order_date ?? row.quotation_date ?? row.created_at ?? '—') },
          { key: 'amount', label: 'Amount', render: (row) => formatInr(String(row.grand_total ?? row.amount ?? '')) },
          { key: 'status', label: 'Status', render: (row) => textStatus(row) ? <StatusBadge value={textStatus(row)} /> : '—' },
          { key: 'action', label: '', render: (row) => action ? <Button variant="secondary" onClick={() => documentService.action(`${path}/${row.id}/${action}`).then(() => queryClient.invalidateQueries({ queryKey: [path] })).catch((error) => toast(apiError(error), 'error'))}>{action}</Button> : null },
        ]}
      />
    </div>
  )
}

export function PaymentsPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: ['payments'], queryFn: () => paymentService.list() })
  const customers = useQuery({ queryKey: ['customers-all'], queryFn: () => customerService.list({ page_size: 100 }) })
  const [customerId, setCustomerId] = useState('')
  const [amount, setAmount] = useState('')
  return (
    <div>
      <PageHeader title="Payments" />
      <form className="mb-4 flex flex-wrap gap-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await paymentService.create({ customer_id: customerId, amount, branch_id: session.branchId })
          setAmount('')
          queryClient.invalidateQueries({ queryKey: ['payments'] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <select className="control px-2 py-2 text-sm" value={customerId} onChange={(event) => setCustomerId(event.target.value)} required>
          <option value="">Customer</option>
          {(customers.data?.items ?? []).map((customer) => <option key={customer.id} value={customer.id}>{customer.display_name}</option>)}
        </select>
        <input className="control px-2 py-2 text-sm" placeholder="Amount" value={amount} onChange={(event) => setAmount(event.target.value)} required />
        <Button type="submit">Record payment</Button>
      </form>
      <DataTable
        rows={query.data?.items ?? []}
        empty="No payments yet."
        rowKey={(payment) => payment.id}
        columns={[
          { key: 'payment_no', label: 'Payment', render: (payment) => payment.payment_no },
          { key: 'payment_date', label: 'Date', render: (payment) => payment.payment_date },
          { key: 'amount', label: 'Amount', render: (payment) => formatInr(payment.amount) },
          { key: 'reference_no', label: 'Reference', render: (payment) => payment.reference_no || '—' },
          { key: 'payment_status', label: 'Status', render: (payment) => <StatusBadge value={payment.payment_status} /> },
        ]}
      />
    </div>
  )
}

export function PurchasingPage() {
  return <DocumentPage title="Purchasing" path="/purchases/orders" />
}

export function ExpensesPage() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const categories = useQuery({ queryKey: ['expense-categories'], queryFn: () => documentService.list('/expenses/categories') })
  const expenses = useQuery({ queryKey: ['expenses'], queryFn: () => documentService.list('/expenses') })
  const [name, setName] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [amount, setAmount] = useState('')
  return (
    <div>
      <PageHeader title="Expenses" />
      <form className="mb-3 flex gap-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await documentService.create('/expenses/categories', { name })
          setName('')
          queryClient.invalidateQueries({ queryKey: ['expense-categories'] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <Field label="New category" value={name} onChange={(event) => setName(event.target.value)} />
        <Button className="self-end" type="submit">Add category</Button>
      </form>
      <form className="mb-4 flex flex-wrap gap-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await documentService.create('/expenses', { category_id: categoryId, amount, tax_amount: 0 })
          queryClient.invalidateQueries({ queryKey: ['expenses'] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <select className="control px-2 py-2 text-sm" value={categoryId} onChange={(event) => setCategoryId(event.target.value)} required>
          <option value="">Category</option>
          {(categories.data?.items ?? []).map((item) => <option key={String(item.id)} value={String(item.id)}>{String(item.name)}</option>)}
        </select>
        <input className="control px-2 py-2 text-sm" placeholder="Amount" value={amount} onChange={(event) => setAmount(event.target.value)} required />
        <Button type="submit">Add expense</Button>
      </form>
      <h2 className="mb-2 font-medium">Categories</h2>
      <DataTable
        rows={categories.data?.items ?? []}
        empty="No expense categories yet."
        rowKey={(item) => String(item.id)}
        columns={[{ key: 'name', label: 'Category', render: (item) => String(item.name ?? '') }]}
      />
      <h2 className="mt-4 mb-2 font-medium">Expenses</h2>
      <DataTable
        rows={expenses.data?.items ?? []}
        empty="No expenses yet."
        rowKey={(item) => String(item.id)}
        columns={[
          { key: 'expense_no', label: 'Expense', render: (item) => String(item.expense_no ?? item.id) },
          { key: 'amount', label: 'Amount', render: (item) => formatInr(String(item.amount ?? '')) },
          { key: 'status', label: 'Status', render: (item) => textStatus(item) ? <StatusBadge value={textStatus(item)} /> : '—' },
          { key: 'action', label: '', render: (item) => <Button variant="secondary" onClick={() => documentService.action(`/expenses/${item.id}/submit`).then(() => queryClient.invalidateQueries({ queryKey: ['expenses'] })).catch((error) => toast(apiError(error), 'error'))}>Submit</Button> },
        ]}
      />
    </div>
  )
}

export function ReportsPage() {
  const [name, setName] = useState('sales')
  const query = useQuery({ queryKey: ['report', name], queryFn: () => reportService.run(name) })
  const toast = useToast()
  const rows = query.data ?? []
  return (
    <div>
      <PageHeader title="Reports">
        <Button variant="secondary" onClick={() => reportService.download(name, 'csv').then(saveBlob(`${name}.csv`)).catch((error) => toast(apiError(error), 'error'))}>Export CSV</Button>
      </PageHeader>
      <select className="mb-3 control px-3 py-2 text-sm" value={name} onChange={(event) => setName(event.target.value)}>
        {reports.map((report) => <option key={report} value={report}>{report}</option>)}
      </select>
      <DataTable
        rows={rows}
        empty="This report has no rows."
        rowKey={(_, index) => String(index)}
        columns={(rows[0] ? Object.keys(rows[0]) : ['result']).map((key) => ({
          key,
          label: key.replaceAll('_', ' '),
          render: (row: Record<string, unknown>) => {
            const value = row[key]
            if (value == null || value === '') return '—'
            if (key.toLowerCase().includes('status')) return <StatusBadge value={String(value)} />
            return String(value)
          },
        }))}
      />
    </div>
  )
}

export function OrganizationSettingsPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const branches = useQuery({
    queryKey: ['branches', session.organizationId],
    enabled: Boolean(session.organizationId),
    queryFn: () => organizationService.branches(session.organizationId!),
  })
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  return (
    <div className="space-y-4">
      <PageHeader title="Organizations" subtitle="Organizations available to this account." />
      <DataTable
        rows={session.organizations}
        empty="No organizations are assigned to this account."
        rowKey={(org) => org.id}
        columns={[
          { key: 'display_name', label: 'Name', render: (org) => org.display_name },
          { key: 'code', label: 'Code', render: (org) => org.code },
          { key: 'status', label: 'Status', render: (org) => <StatusBadge value={org.status} /> },
          { key: 'member_status', label: 'Membership', render: (org) => <StatusBadge value={org.member_status} /> },
        ]}
      />
      <PageHeader title="Branches" subtitle="Branches for the organization selected in the header." />
      <form className="flex flex-wrap gap-2" onSubmit={async (event) => {
        event.preventDefault()
        if (!session.organizationId) return
        try {
          await organizationService.createBranch(session.organizationId, { name, code })
          setName('')
          setCode('')
          toast('Branch created')
          queryClient.invalidateQueries({ queryKey: ['branches', session.organizationId] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <Field label="Branch name" value={name} onChange={(event) => setName(event.target.value)} required />
        <Field label="Branch code" value={code} onChange={(event) => setCode(event.target.value)} required />
        <Button className="self-end" type="submit">Add branch</Button>
      </form>
      <DataTable
        rows={branches.data ?? []}
        empty="No branches yet."
        rowKey={(branch) => branch.id}
        columns={[
          { key: 'code', label: 'Code', render: (branch) => branch.code },
          { key: 'name', label: 'Name', render: (branch) => branch.name },
          { key: 'phone', label: 'Phone', render: (branch) => branch.phone || '—' },
          { key: 'email', label: 'Email', render: (branch) => branch.email || '—' },
          { key: 'is_head_office', label: 'Head office', render: (branch) => branch.is_head_office ? 'Yes' : 'No' },
          { key: 'is_active', label: 'Status', render: (branch) => <StatusBadge value={branch.is_active ? 'Active' : 'Inactive'} /> },
        ]}
      />
    </div>
  )
}

export function UsersPage() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const members = useQuery({ queryKey: ['members'], queryFn: accessService.members })
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  return (
    <div>
      <PageHeader title="Users" />
      <form className="mb-4 flex flex-wrap gap-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await accessService.invite(email, name)
          setEmail('')
          setName('')
          queryClient.invalidateQueries({ queryKey: ['members'] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <Field label="Name" value={name} onChange={(event) => setName(event.target.value)} />
        <Field label="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        <Button className="self-end" type="submit">Invite user</Button>
      </form>
      <DataTable
        rows={members.data?.items ?? []}
        empty="No users yet."
        rowKey={(member) => member.id}
        columns={[
          { key: 'user_id', label: 'User', render: (member) => member.user_id },
          { key: 'joined_at', label: 'Joined', render: (member) => member.joined_at || '—' },
          { key: 'member_status', label: 'Status', render: (member) => <StatusBadge value={member.member_status} /> },
          { key: 'action', label: '', render: (member) => <Button variant="secondary" onClick={() => accessService.setStatus(member.id, member.member_status === 'active' ? 'disabled' : 'active').then(() => queryClient.invalidateQueries({ queryKey: ['members'] })).catch((error) => toast(apiError(error), 'error'))}>{member.member_status === 'active' ? 'Disable' : 'Activate'}</Button> },
        ]}
      />
    </div>
  )
}

export function RolesPage() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const roles = useQuery({ queryKey: ['roles'], queryFn: accessService.roles })
  const permissions = useQuery({ queryKey: ['permissions'], queryFn: accessService.permissions })
  const [selected, setSelected] = useState('')
  const assigned = useQuery({ queryKey: ['role-permissions', selected], enabled: Boolean(selected), queryFn: () => accessService.rolePermissions(selected) })
  const [name, setName] = useState('')
  const [key, setKey] = useState('')
  const ids = new Set(assigned.data?.permission_ids ?? [])
  return (
    <div className="space-y-4">
      <PageHeader title="Roles" />
      <form className="flex flex-wrap gap-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await accessService.createRole({ name, role_key: key })
          setName('')
          setKey('')
          queryClient.invalidateQueries({ queryKey: ['roles'] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <Field label="Role name" value={name} onChange={(event) => setName(event.target.value)} required />
        <Field label="Role key" value={key} onChange={(event) => setKey(event.target.value)} required />
        <Button className="self-end" type="submit">Add role</Button>
      </form>
      <DataTable
        rows={roles.data?.items ?? []}
        empty="No roles yet."
        rowKey={(role) => role.id}
        columns={[
          { key: 'name', label: 'Role', render: (role) => <button className="font-medium text-brand" onClick={() => setSelected(role.id)}>{role.name}</button> },
          { key: 'role_key', label: 'Key', render: (role) => role.role_key },
          { key: 'description', label: 'Description', render: (role) => role.description || '—' },
          { key: 'is_system', label: 'Type', render: (role) => <StatusBadge value={role.is_system ? 'System' : 'Custom'} /> },
        ]}
      />
      <PageHeader title="Permissions" subtitle={selected ? 'Assigned permissions for the selected role.' : 'Select a role to edit its permissions.'} />
      <DataTable
        rows={selected ? (permissions.data ?? []) : []}
        empty={selected ? 'No permissions are defined.' : 'Select a role from the table above.'}
        rowKey={(permission) => permission.id}
        columns={[
          { key: 'assigned', label: 'Assigned', render: (permission) => <input type="checkbox" checked={ids.has(permission.id)} onChange={async (event) => {
            const next = new Set(ids)
            if (event.target.checked) next.add(permission.id)
            else next.delete(permission.id)
            try {
              await accessService.setRolePermissions(selected, [...next])
              queryClient.invalidateQueries({ queryKey: ['role-permissions', selected] })
            } catch (error) {
              toast(apiError(error), 'error')
            }
          }} /> },
          { key: 'module_key', label: 'Module', render: (permission) => permission.module_key },
          { key: 'permission_key', label: 'Permission', render: (permission) => permission.permission_key },
          { key: 'description', label: 'Description', render: (permission) => permission.description || '—' },
        ]}
      />
    </div>
  )
}

function saveBlob(filename: string) {
  return (blob: Blob) => {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  }
}
