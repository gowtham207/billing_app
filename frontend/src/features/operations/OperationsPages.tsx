import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Button, ConfirmDialog, DataTable, Field, Modal, PageHeader, SelectField, StatusBadge, TextArea, useToast } from '@/components/common/ui'
import { useSession } from '@/hooks/session'
import { accessService, reportService } from '@/services/dashboard.service'
import { api, apiError } from '@/services/api'
import { documentService, invoiceService, paymentService } from '@/services/billing.service'
import { crmService } from '@/services/crm.service'
import { customerService } from '@/services/customer.service'
import { organizationService } from '@/services/organization.service'
import { formatInr, toPaise } from '@/utils/money'
import { blankCustomer, CustomerFormFields, saveCustomer } from '@/features/crm/customers/customerForm'
import { CustomerSelect } from '@/features/crm/customers/CustomerSelect'

const reports = [
  ['sales', 'Sales'],
  ['purchases', 'Purchases'],
  ['inventory', 'Inventory'],
  ['stock-movement', 'Stock movement'],
  ['customer-ledger', 'Customer ledger'],
  ['supplier-ledger', 'Supplier ledger'],
  ['outstanding', 'Outstanding'],
  ['expenses', 'Expenses'],
  ['tax', 'Tax'],
  ['profit-loss', 'Profit and loss'],
] as const

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
          <CustomerSelect value={customerId} onChange={setCustomerId} required placeholder="Search customer" />
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
  const invoices = useQuery({ queryKey: ['invoices-for-payment'], queryFn: () => invoiceService.list(1, 100) })
  const statuses = useQuery({ queryKey: ['statuses'], queryFn: crmService.statuses })
  const [customerId, setCustomerId] = useState('')
  const [invoiceId, setInvoiceId] = useState('')
  const [amount, setAmount] = useState('')
  const cancelledIds = new Set((statuses.data?.items ?? []).filter((status) => status.status_key === 'cancelled' || status.status_key === 'canceled').map((status) => status.id))
  const openInvoices = (invoices.data?.items ?? []).filter((invoice) => invoice.customer_id === customerId && Number(invoice.balance_due ?? 0) > 0 && (invoice.status_id == null || !cancelledIds.has(invoice.status_id)))
  const [customerOpen, setCustomerOpen] = useState(false)
  const [newCustomer, setNewCustomer] = useState(blankCustomer())
  const [savingCustomer, setSavingCustomer] = useState(false)
  return (
    <div>
      <PageHeader title="Payments" subtitle="Record a receipt against a customer. Add the customer here if they are not in the list yet." />
      <form className="panel mb-4 grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1.2fr)_12rem_auto]" onSubmit={async (event) => {
        event.preventDefault()
        try {
          const payment = await paymentService.create({ customer_id: customerId, amount, branch_id: session.branchId })
          if (invoiceId) await paymentService.allocate(payment.id, invoiceId, amount)
          setAmount('')
          setInvoiceId('')
          toast('Payment recorded')
          queryClient.invalidateQueries({ queryKey: ['payments'] })
          queryClient.invalidateQueries({ queryKey: ['invoices-for-payment'] })
          queryClient.invalidateQueries({ queryKey: ['invoice-payments'] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <div className="relative">
          <CustomerSelect label="Customer" value={customerId} onChange={(nextId) => { setCustomerId(nextId); setInvoiceId('') }} required />
          {session.can('customers.create') ? <button type="button" className="absolute top-0 right-0 text-xs font-medium text-brand" onClick={() => { setNewCustomer(blankCustomer()); setCustomerOpen(true) }}>New customer</button> : null}
        </div>
        <SelectField label="Invoice" value={invoiceId} onChange={(event) => setInvoiceId(event.target.value)} disabled={!customerId}>
          <option value="">{customerId ? 'Select invoice' : 'Choose a customer first'}</option>
          {openInvoices.map((invoice) => <option key={invoice.id} value={invoice.id}>{invoice.invoice_no} · {formatInr(invoice.balance_due)}</option>)}
        </SelectField>
        <Field label="Amount" type="number" min="0" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} required />
        <div className="flex items-end"><Button type="submit">Record payment</Button></div>
      </form>
      <Modal title="New customer" open={customerOpen} onClose={() => setCustomerOpen(false)}>
        <CustomerFormFields
          form={newCustomer}
          onChange={setNewCustomer}
          pending={savingCustomer}
          submitLabel="Create customer"
          onSubmit={async (event) => {
            event.preventDefault()
            setSavingCustomer(true)
            try {
              const customer = await saveCustomer(newCustomer)
              setCustomerId(customer.id)
              setCustomerOpen(false)
              setNewCustomer(blankCustomer())
              toast('Customer created')
              queryClient.setQueryData(['customers-all'], (current: { items: { id: string }[]; total: number } | undefined) => {
                if (!current || current.items.some((item) => item.id === customer.id)) return current
                return { ...current, items: [customer, ...current.items], total: current.total + 1 }
              })
              queryClient.invalidateQueries({ queryKey: ['customers-all'] })
              queryClient.invalidateQueries({ queryKey: ['customers'] })
            } catch (error) {
              toast(apiError(error), 'error')
            } finally {
              setSavingCustomer(false)
            }
          }}
        />
      </Modal>
      <DataTable
        rows={query.data?.items ?? []}
        empty="No payments yet."
        rowKey={(payment) => payment.id}
        columns={[
          { key: 'payment_no', label: 'Payment', render: (payment) => payment.payment_no },
          { key: 'payment_date', label: 'Date', render: (payment) => payment.payment_date },
          { key: 'customer', label: 'Customer', render: (payment) => payment.customer_name || customers.data?.items.find((customer) => customer.id === payment.customer_id)?.display_name || '—' },
          { key: 'invoice', label: 'Invoice', render: (payment) => (payment.invoices ?? []).length ? (payment.invoices ?? []).map((invoice) => <Link key={invoice.id} className="mr-2 text-brand underline" to={`/billing/invoices/${invoice.id}`}>{invoice.invoice_no}</Link>) : '—' },
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

type ExpenseDraft = {
  id: string
  categoryId: string
  expenseDate: string
  vendor: string
  description: string
  amount: string
  tax: string
}

function blankExpense(): ExpenseDraft {
  return { id: '', categoryId: '', expenseDate: new Date().toISOString().slice(0, 10), vendor: '', description: '', amount: '', tax: '0' }
}

function expenseDate(value: unknown) {
  const [year, month, day] = String(value ?? '').slice(0, 10).split('-')
  return year && month && day ? `${day}/${month}/${year}` : '—'
}

export function ExpensesPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const categories = useQuery({ queryKey: ['expense-categories'], queryFn: () => documentService.list('/expenses/categories', 1, 100) })
  const expenses = useQuery({ queryKey: ['expenses'], queryFn: () => documentService.list('/expenses', 1, 100) })
  const statuses = useQuery({ queryKey: ['statuses'], queryFn: crmService.statuses })
  const [categoryName, setCategoryName] = useState('')
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [draft, setDraft] = useState<ExpenseDraft | null>(null)
  const [rejectId, setRejectId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const categoryNameOf = (id: unknown) => String(categories.data?.items.find((item) => item.id === id)?.name ?? '—')
  const statusOf = (id: unknown) => statuses.data?.items.find((item) => item.id === id)
  const statusKeyOf = (item: Record<string, unknown>) => (item.status_id ? statusOf(item.status_id)?.status_key ?? '' : 'draft')
  const rows = (expenses.data?.items ?? []).filter((item) => {
    const statusKey = statusKeyOf(item)
    const haystack = `${item.expense_no ?? ''} ${item.vendor_name ?? ''} ${item.description ?? ''} ${categoryNameOf(item.category_id)}`.toLowerCase()
    return (!categoryFilter || item.category_id === categoryFilter) && (!statusFilter || statusKey === statusFilter) && (!search.trim() || haystack.includes(search.trim().toLowerCase()))
  })
  const totalOf = (item: Record<string, unknown>) => toPaise(String(item.amount ?? 0)) + toPaise(String(item.tax_amount ?? 0))
  const sumWhere = (status: string | null) => rows
    .filter((item) => (status ? statusKeyOf(item) === status : true))
    .reduce((sum, item) => sum + totalOf(item), 0)
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['expenses'] })

  const saveExpense = async (event: FormEvent) => {
    event.preventDefault()
    if (!draft) return
    setSaving(true)
    const body = {
      category_id: draft.categoryId,
      branch_id: session.branchId,
      expense_date: draft.expenseDate,
      amount: draft.amount,
      tax_amount: draft.tax || 0,
      vendor_name: draft.vendor || null,
      description: draft.description || null,
    }
    try {
      if (draft.id) await api.put(`/expenses/${draft.id}`, body)
      else await documentService.create('/expenses', body)
      setDraft(null)
      toast(draft.id ? 'Expense updated' : 'Expense recorded')
      refresh()
    } catch (error) {
      toast(apiError(error), 'error')
    } finally {
      setSaving(false)
    }
  }

  const move = async (id: string, action: 'submit' | 'approve' | 'reject' | 'pay', message: string) => {
    try {
      await documentService.action(`/expenses/${id}/${action}`)
      toast(message)
      refresh()
    } catch (error) {
      toast(apiError(error), 'error')
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Expenses" subtitle="Record a draft, submit it for approval, then mark it paid when the money goes out.">
        <Button onClick={() => setDraft(blankExpense())} disabled={(categories.data?.items.length ?? 0) === 0}>Record expense</Button>
      </PageHeader>
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ['Recorded', formatInr(sumWhere(null) / 100), `${rows.length} shown`],
          ['Draft', formatInr(sumWhere('draft') / 100), 'Not submitted'],
          ['Submitted', formatInr(sumWhere('submitted') / 100), 'Waiting for approval'],
          ['Paid', formatInr(sumWhere('paid') / 100), 'Settled'],
        ].map(([label, value, hint]) => (
          <article key={label} className="panel p-4">
            <p className="text-xs font-semibold tracking-wide text-muted uppercase">{label}</p>
            <p className="mt-2 text-2xl font-semibold tabular-nums">{value}</p>
            <p className="mt-1 text-xs text-muted">{hint}</p>
          </article>
        ))}
      </section>
      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_18rem]">
        <section className="panel overflow-hidden">
          <div className="flex flex-wrap items-center gap-2 border-b border-line px-4 py-3">
            <input className="control min-w-48 flex-1 px-3 py-2 text-sm" placeholder="Search number, vendor, or description" value={search} onChange={(event) => setSearch(event.target.value)} />
            <select className="control px-3 py-2 text-sm" value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}>
              <option value="">All categories</option>
              {(categories.data?.items ?? []).map((item) => <option key={String(item.id)} value={String(item.id)}>{String(item.name)}</option>)}
            </select>
            <select className="control px-3 py-2 text-sm" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">All statuses</option>
              {['draft', 'submitted', 'approved', 'rejected', 'paid'].map((status) => <option key={status} value={status}>{status[0].toUpperCase() + status.slice(1)}</option>)}
            </select>
          </div>
          <div className="data-table rounded-none border-0">
            <table className="min-w-[980px] text-left text-sm">
              <thead className="text-xs tracking-wide text-muted uppercase">
                <tr>
                  {['Expense', 'Date', 'Category', 'Vendor', 'Description'].map((heading) => <th key={heading} className="px-3 py-2 font-medium">{heading}</th>)}
                  {['Amount', 'Tax', 'Total'].map((heading) => <th key={heading} className="px-3 py-2 text-right font-medium">{heading}</th>)}
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {expenses.isLoading ? <tr><td className="px-3 py-8 text-center text-muted" colSpan={10}>Loading expenses…</td></tr> : expenses.isError ? <tr><td className="px-3 py-8 text-center text-danger" colSpan={10}>{apiError(expenses.error)}</td></tr> : rows.length === 0 ? <tr><td className="px-3 py-8 text-center text-muted" colSpan={10}>No expense data found</td></tr> : rows.map((item) => {
                  const resolved = item.status_id ? statusOf(item.status_id) : { status_key: 'draft', label: 'Draft' }
                  const statusKey = statusKeyOf(item)
                  const statusLabel = resolved?.label ?? (statuses.isLoading ? '…' : 'Unknown')
                  return (
                    <tr key={String(item.id)} className="border-t border-line">
                      <td className="px-3 py-2 font-medium">{String(item.expense_no ?? '—')}</td>
                      <td className="px-3 py-2 whitespace-nowrap">{expenseDate(item.expense_date)}</td>
                      <td className="px-3 py-2">{categoryNameOf(item.category_id)}</td>
                      <td className="px-3 py-2">{String(item.vendor_name || '—')}</td>
                      <td className="max-w-56 truncate px-3 py-2 text-muted">{String(item.description || '—')}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{formatInr(String(item.amount ?? 0))}</td>
                      <td className="px-3 py-2 text-right tabular-nums">{formatInr(String(item.tax_amount ?? 0))}</td>
                      <td className="px-3 py-2 text-right font-medium tabular-nums">{formatInr(totalOf(item) / 100)}</td>
                      <td className="px-3 py-2"><StatusBadge value={statusLabel} /></td>
                      <td className="px-3 py-2">
                        <div className="flex justify-end gap-1">
                          {statusKey === 'draft' ? <Button variant="ghost" onClick={() => setDraft({ id: String(item.id), categoryId: String(item.category_id ?? ''), expenseDate: String(item.expense_date ?? '').slice(0, 10), vendor: String(item.vendor_name ?? ''), description: String(item.description ?? ''), amount: String(item.amount ?? ''), tax: String(item.tax_amount ?? '0') })}>Edit</Button> : null}
                          {statusKey === 'draft' ? <Button variant="secondary" onClick={() => move(String(item.id), 'submit', 'Expense submitted')}>Submit</Button> : null}
                          {statusKey === 'submitted' ? <Button variant="secondary" onClick={() => move(String(item.id), 'approve', 'Expense approved')}>Approve</Button> : null}
                          {statusKey === 'submitted' ? <Button variant="ghost" onClick={() => setRejectId(String(item.id))}>Reject</Button> : null}
                          {statusKey === 'approved' ? <Button variant="secondary" onClick={() => move(String(item.id), 'pay', 'Expense marked paid')}>Mark paid</Button> : null}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>
        <section className="panel p-4">
          <h2 className="text-sm font-semibold">Categories</h2>
          <p className="mt-1 text-xs text-muted">Every expense belongs to one category.</p>
          <ul className="mt-3 space-y-2">
            {(categories.data?.items ?? []).length === 0 ? <li className="rounded-lg border border-dashed border-line px-3 py-4 text-sm text-muted">No categories yet. Add one before recording an expense.</li> : (categories.data?.items ?? []).map((item) => {
              const count = (expenses.data?.items ?? []).filter((expense) => expense.category_id === item.id).length
              return (
                <li key={String(item.id)} className="flex items-center justify-between rounded-lg border border-line px-3 py-2 text-sm">
                  <span className="font-medium">{String(item.name)}</span>
                  <span className="text-xs text-muted">{count}</span>
                </li>
              )
            })}
          </ul>
          <form className="mt-4 space-y-2" onSubmit={async (event) => {
            event.preventDefault()
            try {
              await documentService.create('/expenses/categories', { name: categoryName })
              setCategoryName('')
              toast('Category added')
              queryClient.invalidateQueries({ queryKey: ['expense-categories'] })
            } catch (error) {
              toast(apiError(error), 'error')
            }
          }}>
            <Field label="New category" value={categoryName} onChange={(event) => setCategoryName(event.target.value)} required />
            <Button className="w-full" type="submit" variant="secondary">Add category</Button>
          </form>
        </section>
      </div>
      <Modal title={draft?.id ? 'Edit expense' : 'Record expense'} open={draft !== null} onClose={() => setDraft(null)}>
        {draft ? (
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={saveExpense}>
            <SelectField label="Category" value={draft.categoryId} onChange={(event) => setDraft({ ...draft, categoryId: event.target.value })} required>
              <option value="">Select category</option>
              {(categories.data?.items ?? []).map((item) => <option key={String(item.id)} value={String(item.id)}>{String(item.name)}</option>)}
            </SelectField>
            <Field label="Date" type="date" value={draft.expenseDate} onChange={(event) => setDraft({ ...draft, expenseDate: event.target.value })} required />
            <Field label="Vendor" value={draft.vendor} onChange={(event) => setDraft({ ...draft, vendor: event.target.value })} />
            <Field label="Amount" type="number" min="0" step="0.01" value={draft.amount} onChange={(event) => setDraft({ ...draft, amount: event.target.value })} required />
            <Field label="Tax" type="number" min="0" step="0.01" value={draft.tax} onChange={(event) => setDraft({ ...draft, tax: event.target.value })} />
            <div className="flex items-end justify-between rounded-lg border border-line px-3 py-2 text-sm">
              <span className="text-muted">Total</span>
              <span className="font-semibold tabular-nums">{formatInr((toPaise(draft.amount) + toPaise(draft.tax)) / 100)}</span>
            </div>
            <div className="sm:col-span-2"><TextArea label="Description" rows={3} value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} /></div>
            <div className="sm:col-span-2 flex justify-end gap-2">
              <Button type="button" variant="secondary" onClick={() => setDraft(null)}>Close</Button>
              <Button type="submit" disabled={saving}>{saving ? 'Saving…' : draft.id ? 'Save changes' : 'Save draft'}</Button>
            </div>
          </form>
        ) : null}
      </Modal>
      <ConfirmDialog
        open={rejectId !== null}
        title="Reject expense"
        message="Reject this expense? It will stay on the register with a rejected status."
        confirmLabel="Reject expense"
        dismissLabel="Keep it"
        onClose={() => setRejectId(null)}
        onConfirm={() => {
          if (!rejectId) return
          const id = rejectId
          setRejectId(null)
          move(id, 'reject', 'Expense rejected')
        }}
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
      <PageHeader title="Reports" subtitle="Every report can be saved as a CSV or an Excel file.">
        <Button variant="secondary" onClick={() => reportService.download(name, 'csv').then(saveBlob(`${name}.csv`)).catch((error) => toast(apiError(error), 'error'))}>Export CSV</Button>
        <Button variant="secondary" onClick={() => reportService.download(name, 'xlsx').then(saveBlob(`${name}.xlsx`)).catch((error) => toast(apiError(error), 'error'))}>Export Excel</Button>
      </PageHeader>
      <select className="mb-3 control px-3 py-2 text-sm" value={name} onChange={(event) => setName(event.target.value)}>
        {reports.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
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
