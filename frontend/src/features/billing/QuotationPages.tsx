import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useState, type ChangeEvent, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Button, ConfirmDialog, Field, Modal, PageHeader, StatusBadge, TextArea, useToast } from '@/components/common/ui'
import { blankCustomer, CustomerFormFields, saveCustomer } from '@/features/crm/customers/customerForm'
import { CustomerSelect } from '@/features/crm/customers/CustomerSelect'
import { readExtras } from '@/features/billing/extras'
import { downloadSheet, printSheet } from '@/features/billing/printSheet'
import { buildTaxInvoice, TaxInvoiceSheet, type TaxInvoiceLine } from '@/features/billing/TaxInvoiceSheet'
import { useSession } from '@/hooks/session'
import { apiError } from '@/services/api'
import { billingService, quotationService } from '@/services/billing.service'
import { crmService } from '@/services/crm.service'
import { customerService } from '@/services/customer.service'
import { productService } from '@/services/inventory.service'
import { organizationService } from '@/services/organization.service'
import type { PartyAddress } from '@/types/api'
import { paiseFields, previewGst } from '@/utils/gst'
import { formatInr, fromPaise, toPaise } from '@/utils/money'

const NOTE_MARK = '\n[[peaksuite-quote]]\n'
const emptyParty = (): PartyAddress => ({ name: '', line1: '', line2: '', city: '', district: '', state: '', postal_code: '', country: 'IN', gstin: '', phone: '', email: '' })

type DraftLine = {
  product_id: string
  description: string
  sku: string
  hsn: string
  quantity: string
  unit: string
  unit_price: string
  discount: string
  gst_rate: number
  exempt: boolean
}

type QuoteSheet = {
  from: PartyAddress
  to: PartyAddress
  bill_to: PartyAddress
  place: string
  treatment: string
  lines: Array<DraftLine & { cgst: string; sgst: string; igst: string; total: string }>
}

function blankLine(rate = 18): DraftLine {
  return { product_id: '', description: '', sku: '', hsn: '', quantity: '1', unit: '', unit_price: '0', discount: '0', gst_rate: rate, exempt: false }
}

function packNotes(text: string, sheet: QuoteSheet) {
  return `${text}${NOTE_MARK}${JSON.stringify(sheet)}`
}

function unpackNotes(raw: string | null | undefined) {
  const value = raw ?? ''
  const index = value.indexOf(NOTE_MARK)
  if (index < 0) return { text: value, sheet: null as QuoteSheet | null }
  try {
    return { text: value.slice(0, index), sheet: JSON.parse(value.slice(index + NOTE_MARK.length)) as QuoteSheet }
  } catch {
    return { text: value, sheet: null as QuoteSheet | null }
  }
}

function gstFromDescription(description?: string | null) {
  const match = description?.match(/GST:\s*(\d+)/)
  return match ? Number(match[1]) : 18
}

function laterDate(days: number) {
  const date = new Date()
  date.setDate(date.getDate() + (days || 15))
  return date.toISOString().slice(0, 10)
}

export function QuotationsPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const quotations = useQuery({ queryKey: ['quotations'], queryFn: () => quotationService.list() })
  const customers = useQuery({ queryKey: ['customers-all'], queryFn: () => customerService.list({ page_size: 100 }) })
  const statuses = useQuery({ queryKey: ['statuses'], queryFn: crmService.statuses })
  const [customerId, setCustomerId] = useState('')
  const [pendingDelete, setPendingDelete] = useState<{ id: string; number: string } | null>(null)
  const rows = (quotations.data?.items ?? []).filter((item) => (!customerId || item.customer_id === customerId) && (!session.branchId || item.branch_id === session.branchId))
  return (
    <div>
      <PageHeader title="Quotations" subtitle="A quotation uses the same GST sheet as an invoice. Discount follows the invoice discount in Billing settings.">
        {session.can('quotations.create') ? <Link to="/billing/quotations/new"><Button>Create quotation</Button></Link> : null}
      </PageHeader>
      <div className="mb-3">
        <div className="max-w-xs">
          <CustomerSelect value={customerId} onChange={setCustomerId} allowEmpty emptyLabel="All customers" placeholder="Search customers" />
        </div>
      </div>
      <div className="data-table">
        <table className="min-w-full text-left text-sm">
          <thead className="text-muted"><tr>{['Quotation', 'Date', 'Valid until', 'Customer', 'Discount', 'GST', 'Total', 'Status', ''].map((heading) => <th key={heading} className="px-3 py-2 font-medium">{heading}</th>)}</tr></thead>
          <tbody>
            {quotations.isLoading ? <tr><td className="px-3 py-8 text-center text-muted" colSpan={9}>Loading quotations…</td></tr> : rows.length === 0 ? <tr><td className="px-3 py-8 text-center text-muted" colSpan={9}>No quotation data found</td></tr> : rows.map((item) => (
              <tr key={item.id} className="border-t border-line">
                <td className="px-3 py-2"><Link className="underline" to={`/billing/quotations/${item.id}`}>{item.quotation_no}</Link></td>
                <td className="px-3 py-2">{item.quotation_date}</td>
                <td className="px-3 py-2">{item.valid_until || '—'}</td>
                <td className="px-3 py-2">{customers.data?.items.find((customer) => customer.id === item.customer_id)?.display_name ?? '—'}</td>
                <td className="px-3 py-2 tabular-nums">{formatInr(item.discount_total)}</td>
                <td className="px-3 py-2 tabular-nums">{formatInr(item.tax_total)}</td>
                <td className="px-3 py-2 font-medium tabular-nums">{formatInr(item.grand_total)}</td>
                <td className="px-3 py-2"><StatusBadge value={statuses.data?.items.find((status) => status.id === item.status_id)?.label ?? 'Draft'} /></td>
                <td className="px-3 py-2">{session.can('quotations.create') ? <Button variant="danger" className="px-2 py-1 text-xs" onClick={() => setPendingDelete({ id: item.id, number: item.quotation_no })}>Delete</Button> : null}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete quotation"
        message={pendingDelete ? `Delete ${pendingDelete.number}? The quotation is removed. A sales order created from it stays in the list.` : ''}
        confirmLabel="Delete quotation"
        dismissLabel="Keep quotation"
        onClose={() => setPendingDelete(null)}
        onConfirm={() => {
          if (!pendingDelete) return
          const target = pendingDelete
          setPendingDelete(null)
          quotationService.remove(target.id).then(() => {
            toast('Quotation deleted')
            queryClient.invalidateQueries({ queryKey: ['quotations'] })
          }).catch((error) => toast(apiError(error), 'error'))
        }}
      />
    </div>
  )
}

export function QuotationEditorPage() {
  const { id } = useParams()
  const isNew = !id
  const session = useSession()
  const navigate = useNavigate()
  const toast = useToast()
  const existing = useQuery({ queryKey: ['quotation', id], enabled: !isNew, queryFn: () => quotationService.get(id!) })
  const savedItems = useQuery({ queryKey: ['quotation-items', id], enabled: !isNew, queryFn: () => quotationService.items(id!) })
  const customers = useQuery({ queryKey: ['customers-all'], queryFn: () => customerService.list({ page_size: 100 }) })
  const products = useQuery({ queryKey: ['products-all'], queryFn: () => productService.list({ page_size: 100 }) })
  const rates = useQuery({ queryKey: ['tax-rates'], queryFn: billingService.taxRates })
  const settings = useQuery({ queryKey: ['billing-settings'], queryFn: billingService.settings })
  const organization = useQuery({ queryKey: ['organization', session.organizationId], enabled: Boolean(session.organizationId), queryFn: () => organizationService.get(session.organizationId!) })
  const addresses = useQuery({ queryKey: ['org-addresses', session.organizationId], enabled: Boolean(session.organizationId), queryFn: () => organizationService.addresses(session.organizationId!) })
  const statuses = useQuery({ queryKey: ['statuses'], queryFn: crmService.statuses })
  const extras = session.organizationId ? readExtras(session.organizationId) : null
  const showDiscount = extras?.discountEnabled !== false
  const [from, setFrom] = useState<PartyAddress>(emptyParty())
  const [to, setTo] = useState<PartyAddress>(emptyParty())
  const [billTo, setBillTo] = useState<PartyAddress>(emptyParty())
  const [customerId, setCustomerId] = useState('')
  const [quotationDate, setQuotationDate] = useState(new Date().toISOString().slice(0, 10))
  const [validUntil, setValidUntil] = useState(laterDate(15))
  const [place, setPlace] = useState(extras?.placeOfSupply ?? '')
  const [notes, setNotes] = useState('')
  const [lines, setLines] = useState<DraftLine[]>([blankLine(Number(extras?.defaultRate || 18))])
  const [preview, setPreview] = useState(false)
  const [loaded, setLoaded] = useState(isNew)
  const [customerOpen, setCustomerOpen] = useState(false)
  const [newCustomer, setNewCustomer] = useState(blankCustomer())
  const [savingCustomer, setSavingCustomer] = useState(false)
  const queryClient = useQueryClient()
  const statusKey = statuses.data?.items.find((item) => item.id === existing.data?.status_id)?.status_key ?? 'draft'
  const locked = !isNew && statusKey !== 'draft'

  useEffect(() => {
    const registered = addresses.data?.find((address) => address.is_default) ?? addresses.data?.[0]
    if (!organization.data || from.name) return
    setFrom({
      ...emptyParty(),
      name: organization.data.display_name,
      line1: registered?.line1 ?? '',
      line2: registered?.line2 ?? '',
      city: registered?.city ?? '',
      state: registered?.state_region ?? '',
      postal_code: registered?.postal_code ?? '',
      country: registered?.country_code ?? 'IN',
      gstin: organization.data.tax_registration_no ?? '',
      phone: organization.data.phone ?? '',
      email: organization.data.email ?? '',
    })
  }, [organization.data, addresses.data, from.name])

  useEffect(() => {
    if (isNew || !existing.data || !savedItems.data || loaded) return
    const unpacked = unpackNotes(existing.data.notes)
    if (unpacked.sheet) {
      setFrom(unpacked.sheet.from)
      setTo(unpacked.sheet.to)
      setBillTo(unpacked.sheet.bill_to)
      setPlace(unpacked.sheet.place)
      setLines(unpacked.sheet.lines.map(({ cgst: _cgst, sgst: _sgst, igst: _igst, total: _total, ...line }) => line))
    } else {
      setLines(savedItems.data.map((item) => ({
        product_id: item.product_id ?? '',
        description: item.description,
        sku: '',
        hsn: '',
        quantity: item.quantity,
        unit: '',
        unit_price: item.unit_price,
        discount: item.discount_amount,
        gst_rate: Number(item.tax_rate) || 0,
        exempt: Number(item.tax_rate) === 0,
      })))
    }
    setNotes(unpacked.text)
    setCustomerId(existing.data.customer_id)
    setQuotationDate(existing.data.quotation_date)
    setValidUntil(existing.data.valid_until ?? existing.data.quotation_date)
    setLoaded(true)
  }, [existing.data, savedItems.data, isNew, loaded])

  const inclusive = Boolean(settings.data?.tax_inclusive_pricing)
  const computed = useMemo(() => lines.map((line) => {
    const split = previewGst({
      quantity: line.quantity || 0,
      unitPrice: line.unit_price || 0,
      discount: showDiscount ? line.discount || 0 : 0,
      ratePercent: extras?.gstEnabled === false ? 0 : line.gst_rate,
      sellerState: from.state,
      buyerState: billTo.state || to.state,
      inclusive,
      exempt: line.exempt || extras?.gstEnabled === false,
    })
    return { line, split, money: paiseFields(split) }
  }), [lines, from.state, billTo.state, to.state, inclusive, extras?.gstEnabled, showDiscount])
  const totals = computed.reduce((sum, row) => ({
    taxable: sum.taxable + row.split.taxablePaise,
    discount: sum.discount + (showDiscount ? toPaise(row.line.discount) : 0),
    cgst: sum.cgst + row.split.cgstPaise,
    sgst: sum.sgst + row.split.sgstPaise,
    igst: sum.igst + row.split.igstPaise,
    total: sum.total + row.split.totalPaise,
  }), { taxable: 0, discount: 0, cgst: 0, sgst: 0, igst: 0, total: 0 })
  const treatment = computed.some((row) => row.split.treatment === 'inter') ? 'inter' : computed.every((row) => row.split.treatment === 'exempt') ? 'exempt' : 'intra'
  const discountFor = (quantity: string, price: string) => {
    if (!showDiscount) return '0'
    const amount = (Number(quantity) || 0) * (Number(price) || 0) * (Number(extras?.defaultDiscount) || 0) / 100
    return amount ? amount.toFixed(2) : '0'
  }
  const sheet = (): QuoteSheet => ({
    from, to, bill_to: billTo, place, treatment,
    lines: computed.map((row) => ({ ...row.line, discount: showDiscount ? row.line.discount : '0', cgst: row.money.cgst, sgst: row.money.sgst, igst: row.money.igst, total: row.money.total })),
  })
  const view = buildTaxInvoice({
    documentKind: 'quotation',
    businessName: from.name,
    seller: from,
    buyer: billTo,
    shipTo: to,
    invoiceNo: existing.data?.quotation_no || 'Draft',
    invoiceDate: quotationDate,
    dueDate: validUntil,
    placeOfSupply: place || billTo.state,
    supplyType: treatment === 'inter' ? 'Inter-state' : treatment === 'exempt' ? 'Exempt' : 'Intra-state',
    showDiscount,
    notes,
    grandTotal: fromPaise(totals.total),
    lines: computed.map((row): TaxInvoiceLine => ({
      description: row.line.description,
      sku: row.line.sku,
      hsn: row.line.hsn,
      quantity: row.line.quantity,
      unit: row.line.unit,
      unitPrice: row.line.unit_price,
      discount: showDiscount ? row.line.discount : '0',
      gstRate: row.line.exempt ? 0 : row.line.gst_rate,
      cgst: row.money.cgst,
      sgst: row.money.sgst,
      igst: row.money.igst,
      total: row.money.total,
    })),
  })

  const save = useMutation({
    mutationFn: async (send: boolean) => {
      const body = {
        customer_id: customerId,
        branch_id: session.branchId,
        quotation_no: existing.data?.quotation_no,
        quotation_date: quotationDate,
        valid_until: validUntil || null,
        notes: packNotes(notes, sheet()),
        items: computed.filter((row) => row.line.description.trim()).map((row) => ({
          product_id: row.line.product_id || null,
          description: row.line.description,
          quantity: row.line.quantity,
          unit_price: row.line.unit_price,
          discount_amount: showDiscount ? row.line.discount || 0 : 0,
          tax_rate: row.line.exempt ? 0 : row.line.gst_rate,
          tax_amount: row.money.tax,
        })),
      }
      if (body.items.length === 0) throw new Error('Add at least one line with a description.')
      const saved = existing.data ? await quotationService.update(existing.data.id, body) : await quotationService.create(body)
      return send ? quotationService.send(saved.id) : saved
    },
    onSuccess: (saved) => {
      toast('Quotation saved')
      queryClient.invalidateQueries({ queryKey: ['quotations'] })
      navigate(`/billing/quotations/${saved.id}`)
    },
    onError: (error) => toast(error instanceof Error && error.message.startsWith('Add at least') ? error.message : apiError(error), 'error'),
  })

  const chooseCustomer = async (nextId: string) => {
    setCustomerId(nextId)
    const customer = customers.data?.items.find((item) => item.id === nextId)
    if (!customer) return
    const saved = await customerService.addresses(nextId)
    const billing = saved.find((address) => address.address_type === 'billing') ?? saved[0]
    const shipping = saved.find((address) => address.address_type === 'shipping') ?? billing
    const party = (address: typeof billing): PartyAddress => ({
      ...emptyParty(),
      name: customer.display_name,
      line1: address?.line1 ?? '',
      line2: address?.line2 ?? '',
      city: address?.city ?? '',
      state: address?.state_region ?? '',
      postal_code: address?.postal_code ?? '',
      country: address?.country_code ?? 'IN',
      gstin: customer.tax_registration_no ?? '',
      phone: customer.phone ?? '',
      email: customer.email ?? '',
    })
    setTo(party(shipping))
    setBillTo(party(billing))
    if (!place && billing?.state_region) setPlace(billing.state_region)
  }

  if (!loaded) return <p className="text-sm text-muted">Loading quotation…</p>

  return (
    <div className="space-y-4">
      <PageHeader title={isNew ? 'Create quotation' : existing.data?.quotation_no || 'Quotation'} subtitle="The printed quotation uses the invoice sheet, including tax, discount, declaration, and terms.">
        <Button variant="secondary" onClick={() => setPreview(true)}>Preview quotation</Button>
      </PageHeader>
      {locked ? <p className="notice">This quotation is no longer a draft. Open it from the list to send, accept, or convert it.</p> : null}
      <section className="panel p-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="relative">
            <CustomerSelect label="Customer" value={customerId} onChange={chooseCustomer} disabled={locked} />
            {session.can('customers.create') && !locked ? <button type="button" className="absolute top-0 right-0 text-xs font-medium text-brand" onClick={() => { setNewCustomer(blankCustomer()); setCustomerOpen(true) }}>New customer</button> : null}
          </div>
          <Field label="Quotation date" type="date" value={quotationDate} disabled={locked} onChange={(event) => setQuotationDate(event.target.value)} />
          <Field label="Valid until" type="date" value={validUntil} disabled={locked} onChange={(event) => setValidUntil(event.target.value)} />
          <Field label="Place of supply" value={place} disabled={locked} onChange={(event) => setPlace(event.target.value)} />
        </div>
        <div className="mt-3"><TextArea label="Terms" value={notes} disabled={locked} onChange={(event) => setNotes(event.target.value)} rows={2} /></div>
      </section>
      <section className="grid gap-4 lg:grid-cols-3">
        <PartyCard title="From" party={from} onChange={setFrom} />
        <PartyCard title="Ship to" party={to} onChange={setTo} />
        <PartyCard title="Bill to" party={billTo} onChange={setBillTo} extra={<Button className="px-2 py-1 text-xs" variant="secondary" onClick={() => setBillTo(to)}>Copy ship to</Button>} />
      </section>
      <section className="panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <h2 className="text-sm font-semibold">Line items</h2>
          {!locked ? <Button variant="secondary" onClick={() => setLines([...lines, blankLine(Number(extras?.defaultRate || 18))])}><Plus size={16} /> Add row</Button> : null}
        </div>
        <div className="data-table rounded-none border-0">
          <table className="min-w-[980px] text-sm">
            <thead className="text-left text-xs tracking-wide uppercase">
              <tr>{['Product', 'HSN', 'Qty', 'Unit', 'Price', ...(showDiscount ? ['Discount'] : []), 'GST', 'Taxable', 'CGST', 'SGST', 'IGST', 'Total', ''].map((heading) => <th key={heading} className={`px-3 py-2 font-medium ${['Qty', 'Price', 'Discount', 'Taxable', 'CGST', 'SGST', 'IGST', 'Total'].includes(heading) ? 'text-right' : ''}`}>{heading}</th>)}</tr>
            </thead>
            <tbody>
              {computed.map((row, index) => (
                <tr key={index} className="align-top">
                  <td className="min-w-52 px-3 py-2">
                    <select className="control w-full px-2 py-1.5 text-sm" value={row.line.product_id} disabled={locked} onChange={(event) => {
                      const product = products.data?.items.find((item) => item.id === event.target.value)
                      const price = product?.selling_price ?? row.line.unit_price
                      setLines(lines.map((line, lineIndex) => lineIndex === index ? { ...line, product_id: event.target.value, description: product?.name ?? line.description, sku: product?.sku ?? '', unit_price: price, discount: discountFor(line.quantity, price), gst_rate: gstFromDescription(product?.description) } : line))
                    }}>
                      <option value="">Select product</option>
                      {(products.data?.items ?? []).map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
                    </select>
                    <input className="control mt-1.5 w-full px-2 py-1.5 text-sm" placeholder="Description" value={row.line.description} disabled={locked} onChange={(event) => updateLine(index, { description: event.target.value })} />
                  </td>
                  <td className="px-3 py-2"><input className="control w-24 px-2 py-1.5 text-sm" value={row.line.hsn} disabled={locked} onChange={(event) => updateLine(index, { hsn: event.target.value })} /></td>
                  <td className="px-3 py-2"><input className="control w-20 px-2 py-1.5 text-right text-sm" value={row.line.quantity} disabled={locked} onChange={(event) => updateLine(index, { quantity: event.target.value })} /></td>
                  <td className="px-3 py-2"><input className="control w-20 px-2 py-1.5 text-sm" value={row.line.unit} disabled={locked} onChange={(event) => updateLine(index, { unit: event.target.value })} /></td>
                  <td className="px-3 py-2"><input className="control w-24 px-2 py-1.5 text-right text-sm" value={row.line.unit_price} disabled={locked} onChange={(event) => updateLine(index, { unit_price: event.target.value })} /></td>
                  {showDiscount ? <td className="px-3 py-2"><input className="control w-20 px-2 py-1.5 text-right text-sm" value={row.line.discount} disabled={locked} onChange={(event) => updateLine(index, { discount: event.target.value })} /></td> : null}
                  <td className="px-3 py-2">
                    <select className="control w-28 px-2 py-1.5 text-sm" value={row.line.exempt ? 'exempt' : String(row.line.gst_rate)} disabled={locked} onChange={(event) => updateLine(index, event.target.value === 'exempt' ? { exempt: true, gst_rate: 0 } : { exempt: false, gst_rate: Number(event.target.value) })}>
                      <option value="exempt">Exempt</option>
                      {(rates.data?.items ?? []).map((rate) => <option key={rate.id} value={rate.rate}>{rate.rate}%</option>)}
                      {['0', '5', '12', '18', '28'].map((rate) => <option key={rate} value={rate}>{rate}%</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">{formatInr(row.money.taxable)}</td>
                  <td className="px-3 py-2 text-right text-muted tabular-nums">{formatInr(row.money.cgst)}</td>
                  <td className="px-3 py-2 text-right text-muted tabular-nums">{formatInr(row.money.sgst)}</td>
                  <td className="px-3 py-2 text-right text-muted tabular-nums">{formatInr(row.money.igst)}</td>
                  <td className="px-3 py-2 text-right font-medium tabular-nums">{formatInr(row.money.total)}</td>
                  <td className="px-3 py-2">{locked ? null : <button type="button" className="icon-button text-danger" aria-label="Remove row" onClick={() => setLines(lines.filter((_, lineIndex) => lineIndex !== index))}><Trash2 size={16} /></button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel flex flex-wrap items-end justify-between gap-4 p-4">
        <div className="space-y-1 text-sm">
          <p>Taxable {formatInr(fromPaise(totals.taxable))}</p>
          {showDiscount ? <p>Discount {formatInr(fromPaise(totals.discount))}</p> : null}
          <p className="text-lg font-semibold">Grand total {formatInr(fromPaise(totals.total))}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="ghost" onClick={() => navigate('/billing/quotations')}>Cancel</Button>
          <Button variant="secondary" disabled={locked || save.isPending || !customerId} onClick={() => save.mutate(false)}>Save draft</Button>
          <Button disabled={locked || save.isPending || !customerId} onClick={() => save.mutate(true)}>Save and send</Button>
        </div>
      </section>
      <Modal title="New customer" open={customerOpen} onClose={() => setCustomerOpen(false)}>
        <CustomerFormFields form={newCustomer} onChange={setNewCustomer} pending={savingCustomer} submitLabel="Create customer" onSubmit={async (event) => {
          event.preventDefault()
          setSavingCustomer(true)
          try {
            const customer = await saveCustomer(newCustomer)
            setCustomerId(customer.id)
            const party: PartyAddress = { ...emptyParty(), name: newCustomer.display_name, line1: newCustomer.line1, city: newCustomer.city, state: newCustomer.state_region, postal_code: newCustomer.postal_code, gstin: newCustomer.tax_registration_no, phone: newCustomer.phone, email: newCustomer.email }
            const shipping: PartyAddress = { ...party, line1: newCustomer.shipping_line1 || newCustomer.line1 }
            setBillTo(party)
            setTo(shipping)
            if (!place && newCustomer.state_region) setPlace(newCustomer.state_region)
            setCustomerOpen(false)
            toast('Customer created')
            queryClient.setQueryData(['customers-all'], (current: { items: { id: string }[]; total: number } | undefined) => {
              if (!current || current.items.some((item) => item.id === customer.id)) return current
              return { ...current, items: [customer, ...current.items], total: current.total + 1 }
            })
            queryClient.invalidateQueries({ queryKey: ['customers-all'] })
          } catch (error) {
            toast(apiError(error), 'error')
          } finally {
            setSavingCustomer(false)
          }
        }} />
      </Modal>
      <Modal title="Quotation preview" wide open={preview} onClose={() => setPreview(false)}>
        <TaxInvoiceSheet invoice={view} />
      </Modal>
    </div>
  )

  function updateLine(index: number, patch: Partial<DraftLine>) {
    setLines(lines.map((line, lineIndex) => lineIndex === index ? { ...line, ...patch } : line))
  }
}

export function QuotationDetailPage() {
  const { id = '' } = useParams()
  const session = useSession()
  const navigate = useNavigate()
  const toast = useToast()
  const queryClient = useQueryClient()
  const quotation = useQuery({ queryKey: ['quotation', id], queryFn: () => quotationService.get(id) })
  const items = useQuery({ queryKey: ['quotation-items', id], queryFn: () => quotationService.items(id) })
  const statuses = useQuery({ queryKey: ['statuses'], queryFn: crmService.statuses })
  const [rejecting, setRejecting] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const data = quotation.data
  const extras = session.organizationId ? readExtras(session.organizationId) : null
  if (!data) return <p className="text-sm text-muted">Loading quotation…</p>
  const unpacked = unpackNotes(data.notes)
  const status = statuses.data?.items.find((item) => item.id === data.status_id)
  const statusKey = status?.status_key ?? 'draft'
  const sheet = unpacked.sheet
  const view = buildTaxInvoice({
    documentKind: 'quotation',
    businessName: sheet?.from.name || extras?.merchantName || 'Business',
    seller: sheet?.from,
    buyer: sheet?.bill_to,
    shipTo: sheet?.to,
    invoiceNo: data.quotation_no,
    invoiceDate: data.quotation_date,
    dueDate: data.valid_until,
    placeOfSupply: sheet?.place || sheet?.bill_to.state,
    supplyType: sheet?.treatment === 'inter' ? 'Inter-state' : sheet?.treatment === 'exempt' ? 'Exempt' : 'Intra-state',
    showDiscount: extras?.discountEnabled !== false,
    notes: unpacked.text,
    grandTotal: data.grand_total,
    lines: sheet?.lines.length ? sheet.lines.map((line) => ({
      description: line.description,
      sku: line.sku,
      hsn: line.hsn,
      quantity: line.quantity,
      unit: line.unit,
      unitPrice: line.unit_price,
      discount: line.discount,
      gstRate: line.exempt ? 0 : line.gst_rate,
      cgst: line.cgst,
      sgst: line.sgst,
      igst: line.igst,
      total: line.total,
    })) : (items.data ?? []).map((item) => ({
      description: item.description,
      quantity: item.quantity,
      unitPrice: item.unit_price,
      discount: item.discount_amount,
      gstRate: Number(item.tax_rate) || 0,
      cgst: '0',
      sgst: '0',
      igst: '0',
      total: item.line_total,
    })),
  })
  const run = async (action: 'send' | 'accept' | 'convert', message: string) => {
    try {
      if (action === 'convert') {
        const order = await quotationService.convert(data.id)
        toast(`Sales order ${order.order_no} created`)
        navigate(`/billing/orders/${order.id}`)
        return
      }
      await (action === 'send' ? quotationService.send(data.id) : quotationService.accept(data.id))
      toast(message)
      queryClient.invalidateQueries({ queryKey: ['quotation', id] })
      queryClient.invalidateQueries({ queryKey: ['quotations'] })
    } catch (error) {
      toast(apiError(error), 'error')
    }
  }
  return (
    <div className="space-y-4">
      <PageHeader title={data.quotation_no} subtitle={`${data.quotation_date} · ${status?.label ?? 'Draft'} · ${formatInr(data.grand_total)}`}>
        {statusKey === 'draft' ? <Link to={`/billing/quotations/${data.id}/edit`}><Button variant="secondary">Edit draft</Button></Link> : null}
        {statusKey === 'draft' ? <Button onClick={() => run('send', 'Quotation sent')}>Send</Button> : null}
        {statusKey === 'sent' ? <Button onClick={() => run('accept', 'Quotation accepted')}>Accept</Button> : null}
        {statusKey === 'sent' ? <Button variant="danger" onClick={() => setRejecting(true)}>Reject</Button> : null}
        {statusKey === 'sent' || statusKey === 'accepted' ? <Button variant="secondary" onClick={() => run('convert', 'Converted')}>Convert to order</Button> : null}
        {session.can('quotations.create') ? <Button variant="danger" onClick={() => setDeleting(true)}>Delete</Button> : null}
        <Button variant="secondary" onClick={() => downloadSheet(data.quotation_no).catch((error) => toast(apiError(error), 'error'))}>Download PDF</Button>
        <Button variant="secondary" onClick={() => printSheet(data.quotation_no)}>Print quotation</Button>
      </PageHeader>
      <div id="invoice-print"><TaxInvoiceSheet invoice={view} /></div>
      <ConfirmDialog
        open={deleting}
        title="Delete quotation"
        message={`Delete ${data.quotation_no}? The quotation is removed. A sales order created from it stays in the list.`}
        confirmLabel="Delete quotation"
        dismissLabel="Keep quotation"
        onClose={() => setDeleting(false)}
        onConfirm={() => {
          setDeleting(false)
          quotationService.remove(data.id).then(() => {
            toast('Quotation deleted')
            queryClient.invalidateQueries({ queryKey: ['quotations'] })
            navigate('/billing/quotations')
          }).catch((error) => toast(apiError(error), 'error'))
        }}
      />
      <ConfirmDialog
        open={rejecting}
        title="Reject quotation"
        message={`Reject ${data.quotation_no}? It stays in the list with a rejected status.`}
        confirmLabel="Reject quotation"
        dismissLabel="Keep quotation"
        onClose={() => setRejecting(false)}
        onConfirm={() => {
          setRejecting(false)
          quotationService.reject(data.id).then(() => {
            toast('Quotation rejected')
            queryClient.invalidateQueries({ queryKey: ['quotation', id] })
          }).catch((error) => toast(apiError(error), 'error'))
        }}
      />
    </div>
  )
}

function PartyCard({ title, party, onChange, extra }: { title: string; party: PartyAddress; onChange: (party: PartyAddress) => void; extra?: ReactNode }) {
  const set = (key: keyof PartyAddress) => (event: ChangeEvent<HTMLInputElement>) => onChange({ ...party, [key]: event.target.value })
  return (
    <section className="panel p-4">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-semibold tracking-wide text-muted uppercase">{title}</p>
          <p className="mt-0.5 text-sm font-medium">{party.name || 'Add a name'}</p>
        </div>
        {extra}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <div className="sm:col-span-2"><Field label="Name" value={party.name} onChange={set('name')} /></div>
        <div className="sm:col-span-2"><Field label="Address" value={party.line1} onChange={set('line1')} /></div>
        <Field label="State" value={party.state} onChange={set('state')} />
        <Field label="Pincode" value={party.postal_code} onChange={set('postal_code')} />
        <div className="sm:col-span-2"><Field label="GSTIN" value={party.gstin} onChange={set('gstin')} /></div>
        <Field label="Phone" value={party.phone} onChange={set('phone')} />
        <Field label="Email" value={party.email} onChange={set('email')} />
      </div>
    </section>
  )
}
