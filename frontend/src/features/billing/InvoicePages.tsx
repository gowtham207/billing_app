import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'
import QRCode from 'qrcode'
import { useEffect, useMemo, useState, type ChangeEvent, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Button, Field, Modal, PageHeader, SelectField, StatusBadge, TextArea, useToast } from '@/components/common/ui'
import { useSession } from '@/hooks/session'
import { apiError } from '@/services/api'
import { billingService, invoiceService, paymentService } from '@/services/billing.service'
import { customerService } from '@/services/customer.service'
import { crmService } from '@/services/crm.service'
import { inventoryService, productService } from '@/services/inventory.service'
import { organizationService } from '@/services/organization.service'
import type { BillingSnapshot, GstLine, Invoice, PartyAddress } from '@/types/api'
import { readExtras } from '@/features/billing/extras'
import { downloadInvoicePdf } from '@/features/billing/pdf/invoicePdf'
import { buildTaxInvoice, TaxInvoiceSheet, type TaxInvoiceLine } from '@/features/billing/TaxInvoiceSheet'
import { paiseFields, previewGst } from '@/utils/gst'
import { formatInr, fromPaise, toPaise } from '@/utils/money'
import { upiPayUri } from '@/utils/upi'
import { whatsAppInvoiceUrl } from '@/utils/whatsapp'

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
  warehouse_id: string
}

function blankLine(): DraftLine {
  return { product_id: '', description: '', sku: '', hsn: '', quantity: '1', unit: '', unit_price: '0', discount: '0', gst_rate: 18, exempt: false, warehouse_id: '' }
}

export function InvoicesPage() {
  const session = useSession()
  const invoices = useQuery({ queryKey: ['invoices'], queryFn: () => invoiceService.list() })
  const customers = useQuery({ queryKey: ['customers-all'], queryFn: () => customerService.list({ page_size: 100 }) })
  const statuses = useQuery({ queryKey: ['statuses'], queryFn: crmService.statuses })
  const [customerId, setCustomerId] = useState('')
  const [status, setStatus] = useState('')
  const name = (id: string) => customers.data?.items.find((item) => item.id === id)
  const rows = (invoices.data?.items ?? []).filter((invoice) => (!customerId || invoice.customer_id === customerId) && (!status || invoice.status_id === status) && (!session.branchId || invoice.branch_id === session.branchId))
  return (
    <div>
      <PageHeader title="Invoices" subtitle="Posted invoices are not edited here. Cancel a posted invoice or issue a credit note.">
        {session.can('invoices.create') ? <Link to="/billing/invoices/new"><Button>Create invoice</Button></Link> : null}
      </PageHeader>
      <div className="mb-3 flex flex-wrap gap-2">
        <select className="control px-3 py-2 text-sm" value={customerId} onChange={(event) => setCustomerId(event.target.value)}>
          <option value="">All customers</option>
          {(customers.data?.items ?? []).map((customer) => <option key={customer.id} value={customer.id}>{customer.display_name}</option>)}
        </select>
        <select className="control px-3 py-2 text-sm" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          {(statuses.data?.items ?? []).map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>
      </div>
      <div className="data-table">
        <table className="min-w-full text-sm">
          <thead className="text-left text-muted"><tr>{['Invoice', 'Date', 'Customer', 'GSTIN', 'Subtotal', 'GST', 'Total', 'Paid', 'Balance', 'Status', ''].map((heading) => <th key={heading} className="px-2 py-2">{heading}</th>)}</tr></thead>
          <tbody>
            {rows.map((invoice) => {
              const customer = name(invoice.customer_id)
              const label = statuses.data?.items.find((item) => item.id === invoice.status_id)?.label ?? 'Draft'
              return (
                <tr key={invoice.id} className="border-t border-line">
                  <td className="px-2 py-2"><Link className="underline" to={`/billing/invoices/${invoice.id}`}>{invoice.invoice_no}</Link></td>
                  <td className="px-2 py-2">{invoice.invoice_date}</td>
                  <td className="px-2 py-2">{customer?.display_name}</td>
                  <td className="px-2 py-2">{customer?.tax_registration_no}</td>
                  <td className="px-2 py-2">{formatInr(invoice.subtotal)}</td>
                  <td className="px-2 py-2">{formatInr(invoice.tax_total)}</td>
                  <td className="px-2 py-2">{formatInr(invoice.grand_total)}</td>
                  <td className="px-2 py-2">{formatInr(invoice.amount_paid)}</td>
                  <td className="px-2 py-2">{formatInr(invoice.balance_due)}</td>
                  <td className="px-2 py-2"><StatusBadge value={label} /></td>
                  <td className="px-2 py-2"><ShareButton invoice={invoice} phone={customer?.phone} name={customer?.display_name} /></td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function InvoiceEditorPage() {
  const { id } = useParams()
  const isNew = !id || id === 'new'
  const session = useSession()
  const navigate = useNavigate()
  const toast = useToast()
  const existing = useQuery({ queryKey: ['invoice', id], enabled: !isNew, queryFn: () => invoiceService.get(id!) })
  const items = useQuery({ queryKey: ['invoice-items', id], enabled: !isNew, queryFn: () => invoiceService.items(id!) })
  const customers = useQuery({ queryKey: ['customers-all'], queryFn: () => customerService.list({ page_size: 100 }) })
  const products = useQuery({ queryKey: ['products-all'], queryFn: () => productService.list({ page_size: 100 }) })
  const warehouses = useQuery({ queryKey: ['warehouses'], queryFn: inventoryService.warehouses })
  const settings = useQuery({ queryKey: ['billing-settings'], queryFn: billingService.settings })
  const rates = useQuery({ queryKey: ['tax-rates'], queryFn: billingService.taxRates })
  const organization = useQuery({ queryKey: ['organization', session.organizationId], enabled: Boolean(session.organizationId), queryFn: () => organizationService.get(session.organizationId!) })
  const addresses = useQuery({ queryKey: ['org-addresses', session.organizationId], enabled: Boolean(session.organizationId), queryFn: () => organizationService.addresses(session.organizationId!) })
  const extras = session.organizationId ? readExtras(session.organizationId) : null
  const [from, setFrom] = useState<PartyAddress>(emptyParty())
  const [to, setTo] = useState<PartyAddress>(emptyParty())
  const [billTo, setBillTo] = useState<PartyAddress>(emptyParty())
  const [customerId, setCustomerId] = useState('')
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().slice(0, 10))
  const [dueDate, setDueDate] = useState('')
  const [reference, setReference] = useState('')
  const [salesOrderId, setSalesOrderId] = useState('')
  const [place, setPlace] = useState(extras?.placeOfSupply ?? '')
  const [terms, setTerms] = useState(String(settings.data?.default_payment_terms_days ?? ''))
  const [notes, setNotes] = useState('')
  const [shipping, setShipping] = useState('0')
  const [lines, setLines] = useState<DraftLine[]>([blankLine()])
  const [preview, setPreview] = useState(false)
  const locked = Boolean(existing.data?.issued_at)

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
    if (!existing.data || !items.data) return
    const snapshot = existing.data.billing_snapshot
    if (snapshot?.from) setFrom(snapshot.from)
    if (snapshot?.to) setTo(snapshot.to)
    if (snapshot?.bill_to) setBillTo(snapshot.bill_to)
    setCustomerId(existing.data.customer_id)
    setInvoiceDate(existing.data.invoice_date)
    setDueDate(existing.data.due_date ?? '')
    setNotes(existing.data.notes ?? '')
    setShipping(existing.data.shipping_amount)
    setReference(snapshot?.reference_no ?? '')
    setPlace(snapshot?.place_of_supply ?? '')
    setLines(items.data.map((item) => {
      const saved = snapshot?.lines?.find((line) => line.description === item.description)
      return {
        product_id: item.product_id ?? '',
        description: item.description,
        sku: saved?.sku ?? '',
        hsn: saved?.hsn ?? '',
        quantity: item.quantity,
        unit: saved?.unit ?? '',
        unit_price: item.unit_price,
        discount: item.discount_amount,
        gst_rate: saved?.gst_rate ?? 0,
        exempt: saved?.exempt ?? false,
        warehouse_id: item.warehouse_id ?? '',
      }
    }))
  }, [existing.data, items.data])

  const inclusive = Boolean(settings.data?.tax_inclusive_pricing)
  const computed = useMemo(() => lines.map((line) => {
    const split = previewGst({
      quantity: line.quantity || 0,
      unitPrice: line.unit_price || 0,
      discount: line.discount || 0,
      ratePercent: extras?.gstEnabled === false ? 0 : line.gst_rate,
      sellerState: from.state,
      buyerState: billTo.state || to.state,
      inclusive,
      exempt: line.exempt || extras?.gstEnabled === false,
    })
    return { line, split, money: paiseFields(split) }
  }), [lines, from.state, billTo.state, to.state, inclusive, extras?.gstEnabled])
  const totals = computed.reduce((sum, row) => ({
    taxable: sum.taxable + row.split.taxablePaise,
    discount: sum.discount + toPaise(row.line.discount),
    cgst: sum.cgst + row.split.cgstPaise,
    sgst: sum.sgst + row.split.sgstPaise,
    igst: sum.igst + row.split.igstPaise,
    total: sum.total + row.split.totalPaise,
  }), { taxable: 0, discount: 0, cgst: 0, sgst: 0, igst: 0, total: 0 })
  const grand = totals.total + toPaise(shipping)
  const treatment = computed.some((row) => row.split.treatment === 'inter') ? 'inter' : computed.every((row) => row.split.treatment === 'exempt') ? 'exempt' : 'intra'

  const snapshot = (): BillingSnapshot => ({
    from, to, bill_to: billTo, place_of_supply: place, reference_no: reference, payment_terms: terms, treatment,
    upi_id: extras?.upiEnabled ? extras.upiId : undefined,
    merchant_name: extras?.merchantName || from.name,
    lines: computed.map((row): GstLine => ({
      product_id: row.line.product_id || null,
      description: row.line.description,
      sku: row.line.sku,
      hsn: row.line.hsn,
      quantity: row.line.quantity,
      unit: row.line.unit,
      unit_price: row.line.unit_price,
      discount: row.line.discount,
      gst_rate: row.line.gst_rate,
      exempt: row.line.exempt,
      taxable: row.money.taxable,
      cgst: row.money.cgst,
      sgst: row.money.sgst,
      igst: row.money.igst,
      total: row.money.total,
      warehouse_id: row.line.warehouse_id || null,
    })),
  })

  const payload = () => ({
    customer_id: customerId,
    branch_id: session.branchId || null,
    sales_order_id: salesOrderId || null,
    invoice_date: invoiceDate,
    due_date: dueDate || null,
    shipping_amount: shipping || 0,
    notes: notes || null,
    billing_snapshot: snapshot(),
    items: computed.map((row) => ({
      product_id: row.line.product_id || null,
      description: row.line.description,
      quantity: row.line.quantity,
      unit_price: row.line.unit_price,
      discount_amount: row.line.discount || 0,
      tax_rate: row.line.exempt ? 0 : row.line.gst_rate,
      tax_amount: row.money.tax,
      warehouse_id: row.line.warehouse_id || null,
    })),
  })

  const save = useMutation({
    mutationFn: async (mode: 'draft' | 'confirm' | 'post') => {
      const body = payload()
      const invoice = !isNew && existing.data ? await invoiceService.update(existing.data.id, body) : await invoiceService.create(body)
      if (mode === 'draft') return invoice
      const approved = await invoiceService.approve(invoice.id)
      if (mode === 'confirm') return approved
      return invoiceService.post(approved.id)
    },
    onSuccess: (invoice) => {
      toast('Invoice saved. Totals shown after save come from the server.')
      navigate(`/billing/invoices/${invoice.id}`)
    },
    onError: (error) => toast(apiError(error), 'error'),
  })

  const chooseCustomer = async (nextId: string) => {
    setCustomerId(nextId)
    const customer = customers.data?.items.find((item) => item.id === nextId)
    if (!customer) return
    const saved = await customerService.addresses(nextId)
    const billing = saved.find((address) => address.address_type === 'billing') ?? saved[0]
    const shippingAddress = saved.find((address) => address.address_type === 'shipping') ?? billing
    const party = (address: typeof billing, name: string): PartyAddress => ({
      ...emptyParty(),
      name,
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
    const nextTo = party(shippingAddress, customer.display_name)
    setTo(nextTo)
    setBillTo(party(billing, customer.display_name))
  }

  const addLine = () => setLines([...lines, { ...blankLine(), gst_rate: Number(extras?.defaultRate || 18) }])
  const actions = (
    <div className="flex flex-col gap-2">
      <Button disabled={locked || save.isPending || !customerId} onClick={() => save.mutate('post')}>{save.isPending ? 'Saving…' : 'Generate invoice'}</Button>
      <Button variant="secondary" disabled={locked || save.isPending || !customerId} onClick={() => save.mutate('confirm')}>Save and confirm</Button>
      <Button variant="secondary" disabled={locked || save.isPending || !customerId} onClick={() => save.mutate('draft')}>Save draft</Button>
      <Button variant="ghost" onClick={() => navigate('/billing/invoices')}>Cancel</Button>
    </div>
  )

  return (
    <div className="space-y-4">
      <PageHeader title={isNew ? 'Create invoice' : existing.data?.invoice_no || 'Invoice'} subtitle="GST amounts are a preview. The stored total comes from the server when you save.">
        <Button variant="secondary" onClick={() => setPreview(true)}>Preview invoice</Button>
        <Button className="xl:hidden" variant="secondary" disabled={locked || save.isPending || !customerId} onClick={() => save.mutate('draft')}>Save draft</Button>
        <Button className="xl:hidden" disabled={locked || save.isPending || !customerId} onClick={() => save.mutate('post')}>Generate</Button>
      </PageHeader>
      {locked ? <p className="notice">This invoice is posted. Use cancel or a credit note instead of editing it.</p> : null}
      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_19rem]">
        <div className="min-w-0 space-y-4">
          <section className="panel p-4">
            <h2 className="mb-3 text-sm font-semibold">Invoice details</h2>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <SelectField label="Customer" value={customerId} onChange={(event) => chooseCustomer(event.target.value)}>
                <option value="">Select customer</option>
                {(customers.data?.items ?? []).map((customer) => <option key={customer.id} value={customer.id}>{customer.display_name}</option>)}
              </SelectField>
              <Field label="Invoice date" type="date" value={invoiceDate} onChange={(event) => setInvoiceDate(event.target.value)} />
              <Field label="Due date" type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
              <Field label="Payment terms (days)" value={terms} onChange={(event) => setTerms(event.target.value)} />
              <Field label="Reference number" value={reference} onChange={(event) => setReference(event.target.value)} />
              <Field label="Sales order reference" value={salesOrderId} onChange={(event) => setSalesOrderId(event.target.value)} />
              <Field label="Place of supply" value={place} onChange={(event) => setPlace(event.target.value)} />
              <Field label="Additional charges" value={shipping} onChange={(event) => setShipping(event.target.value)} />
            </div>
            <div className="mt-3"><TextArea label="Notes" value={notes} onChange={(event) => setNotes(event.target.value)} rows={2} /></div>
          </section>
          <section className="grid gap-4 lg:grid-cols-3">
            <PartyCard title="From" party={from} onChange={setFrom} />
            <PartyCard title="Ship to" party={to} onChange={setTo} />
            <PartyCard title="Bill to" party={billTo} onChange={setBillTo} extra={<Button className="px-2 py-1 text-xs" variant="secondary" onClick={() => setBillTo(to)}>Copy ship to</Button>} />
          </section>
          <section className="panel overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
              <div>
                <h2 className="text-sm font-semibold">Line items</h2>
                <p className="text-xs text-muted">{lines.length} {lines.length === 1 ? 'row' : 'rows'}</p>
              </div>
              <Button variant="secondary" onClick={addLine}><Plus size={16} /> Add row</Button>
            </div>
            <div className="data-table rounded-none border-0">
              <table className="min-w-[1080px] text-sm">
                <thead className="text-left text-xs tracking-wide uppercase">
                  <tr>{['Product', 'HSN', 'Qty', 'Unit', 'Price', 'Discount', 'GST', 'Taxable', 'CGST', 'SGST', 'IGST', 'Total', ''].map((heading) => <th key={heading} className={`px-3 py-2 font-medium ${['Taxable', 'CGST', 'SGST', 'IGST', 'Total', 'Price', 'Discount', 'Qty'].includes(heading) ? 'text-right' : ''}`}>{heading}</th>)}</tr>
                </thead>
                <tbody>
                  {computed.length === 0 ? (
                    <tr><td className="px-3 py-8 text-center text-muted" colSpan={13}>Add a product row to start this invoice.</td></tr>
                  ) : computed.map((row, index) => (
                    <tr key={index} className="align-top">
                      <td className="min-w-52 px-3 py-2">
                        <select className="control w-full px-2 py-1.5 text-sm" value={row.line.product_id} onChange={(event) => {
                          const product = products.data?.items.find((item) => item.id === event.target.value)
                          setLines(lines.map((line, lineIndex) => lineIndex === index ? { ...line, product_id: event.target.value, description: product?.name ?? line.description, sku: product?.sku ?? '', unit_price: product?.selling_price ?? line.unit_price, gst_rate: gstFromDescription(product?.description) } : line))
                        }}>
                          <option value="">Select product</option>
                          {(products.data?.items ?? []).map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
                        </select>
                        <input className="control mt-1.5 w-full px-2 py-1.5 text-sm" placeholder="Description" value={row.line.description} onChange={(event) => updateLine(index, { description: event.target.value })} />
                        {row.line.sku ? <p className="mt-1 text-xs text-muted">SKU {row.line.sku}</p> : null}
                      </td>
                      <td className="px-3 py-2"><input className="control w-24 px-2 py-1.5 text-sm" value={row.line.hsn} onChange={(event) => updateLine(index, { hsn: event.target.value })} /></td>
                      <td className="px-3 py-2"><input className="control w-20 px-2 py-1.5 text-right text-sm tabular-nums" value={row.line.quantity} onChange={(event) => updateLine(index, { quantity: event.target.value })} /></td>
                      <td className="px-3 py-2"><input className="control w-20 px-2 py-1.5 text-sm" value={row.line.unit} onChange={(event) => updateLine(index, { unit: event.target.value })} /></td>
                      <td className="px-3 py-2"><input className="control w-24 px-2 py-1.5 text-right text-sm tabular-nums" value={row.line.unit_price} onChange={(event) => updateLine(index, { unit_price: event.target.value })} /></td>
                      <td className="px-3 py-2"><input className="control w-20 px-2 py-1.5 text-right text-sm tabular-nums" value={row.line.discount} onChange={(event) => updateLine(index, { discount: event.target.value })} /></td>
                      <td className="px-3 py-2">
                        <select className="control w-28 px-2 py-1.5 text-sm" value={row.line.exempt ? 'exempt' : String(row.line.gst_rate)} onChange={(event) => updateLine(index, event.target.value === 'exempt' ? { exempt: true, gst_rate: 0 } : { exempt: false, gst_rate: Number(event.target.value) })}>
                          <option value="exempt">Exempt</option>
                          {(rates.data?.items ?? []).map((rate) => <option key={rate.id} value={rate.rate}>{rate.rate}%</option>)}
                          {['0', '5', '12', '18', '28'].map((rate) => <option key={rate} value={rate}>{rate}%</option>)}
                        </select>
                        <select className="control mt-1.5 w-28 px-2 py-1.5 text-sm" value={row.line.warehouse_id} onChange={(event) => updateLine(index, { warehouse_id: event.target.value })}>
                          <option value="">Warehouse</option>
                          {(warehouses.data?.items ?? []).map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>)}
                        </select>
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">{formatInr(row.money.taxable)}</td>
                      <td className="px-3 py-2 text-right text-muted tabular-nums">{formatInr(row.money.cgst)}</td>
                      <td className="px-3 py-2 text-right text-muted tabular-nums">{formatInr(row.money.sgst)}</td>
                      <td className="px-3 py-2 text-right text-muted tabular-nums">{formatInr(row.money.igst)}</td>
                      <td className="px-3 py-2 text-right font-medium tabular-nums">{formatInr(row.money.total)}</td>
                      <td className="px-3 py-2">
                        <button type="button" className="icon-button text-danger" aria-label="Remove row" onClick={() => setLines(lines.filter((_, lineIndex) => lineIndex !== index))}><Trash2 size={16} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
        <aside className="panel space-y-4 p-4 xl:sticky xl:top-4">
          <div>
            <p className="text-xs font-semibold tracking-wide text-muted uppercase">Summary</p>
            <p className="mt-1 text-sm">{treatment === 'intra' ? 'Intra-state · CGST + SGST' : treatment === 'inter' ? 'Inter-state · IGST' : 'Exempt'}</p>
          </div>
          <div className="space-y-2">
            <SummaryLine label="Taxable" value={formatInr(fromPaise(totals.taxable))} />
            <SummaryLine label="Discount" value={formatInr(fromPaise(totals.discount))} />
            <SummaryLine label="CGST" value={formatInr(fromPaise(totals.cgst))} />
            <SummaryLine label="SGST" value={formatInr(fromPaise(totals.sgst))} />
            <SummaryLine label="IGST" value={formatInr(fromPaise(totals.igst))} />
            <SummaryLine label="Additional charges" value={formatInr(shipping)} />
            <div className="flex items-end justify-between gap-3 border-t border-line pt-3">
              <span className="text-sm text-muted">Grand total</span>
              <span className="text-xl font-semibold tabular-nums">{formatInr(fromPaise(grand))}</span>
            </div>
          </div>
          {!customerId ? <p className="text-xs text-muted">Select a customer before saving.</p> : null}
          {actions}
        </aside>
      </div>
      <Modal title="Invoice preview" wide open={preview} onClose={() => setPreview(false)}>
        <TaxInvoiceSheet invoice={buildTaxInvoice({
          businessName: from.name,
          phone: from.phone,
          email: from.email,
          invoiceNo: existing.data?.invoice_no || 'Draft',
          invoiceDate,
          billToName: billTo.name || to.name,
          notes,
          shipping,
          lines: computed.map((row): TaxInvoiceLine => ({
            description: row.line.description,
            sku: row.line.sku,
            hsn: row.line.hsn,
            quantity: row.line.quantity,
            unit: row.line.unit,
            unitPrice: row.line.unit_price,
            discount: row.line.discount,
            gstRate: row.line.exempt ? 0 : row.line.gst_rate,
            cgst: row.money.cgst,
            sgst: row.money.sgst,
            igst: row.money.igst,
            total: row.money.total,
          })),
        })} />
      </Modal>
    </div>
  )

  function updateLine(index: number, patch: Partial<DraftLine>) {
    setLines(lines.map((line, lineIndex) => lineIndex === index ? { ...line, ...patch } : line))
  }
}

function gstFromDescription(description?: string | null) {
  const match = description?.match(/GST:\s*(\d+)/)
  return match ? Number(match[1]) : 18
}

function SummaryLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <span className="text-muted">{label}</span>
      <span className="tabular-nums">{value}</span>
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
        <div className="sm:col-span-2"><Field label="Address line 2" value={party.line2} onChange={set('line2')} /></div>
        <Field label="State" value={party.state} onChange={set('state')} />
        <Field label="Pincode" value={party.postal_code} onChange={set('postal_code')} />
        <div className="sm:col-span-2"><Field label="GSTIN" value={party.gstin} onChange={set('gstin')} /></div>
        <Field label="Phone" value={party.phone} onChange={set('phone')} />
        <Field label="Email" value={party.email} onChange={set('email')} />
      </div>
    </section>
  )
}

export function InvoiceDetailPage() {
  const { id = '' } = useParams()
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const invoice = useQuery({ queryKey: ['invoice', id], queryFn: () => invoiceService.get(id) })
  const items = useQuery({ queryKey: ['invoice-items', id], queryFn: () => invoiceService.items(id) })
  const customer = useQuery({ queryKey: ['customer', invoice.data?.customer_id], enabled: Boolean(invoice.data?.customer_id), queryFn: () => customerService.get(invoice.data!.customer_id) })
  const methods = useQuery({ queryKey: ['payment-methods'], queryFn: billingService.paymentMethods })
  const [qr, setQr] = useState('')
  const [amount, setAmount] = useState('')
  const data = invoice.data
  const extras = session.organizationId ? readExtras(session.organizationId) : null
  if (!data) return <p className="text-sm">Loading invoice…</p>
  const snapshot = data.billing_snapshot ?? {}
  const upiId = snapshot.upi_id || (extras?.upiEnabled ? extras.upiId : '')
  return (
    <div className="space-y-4">
      <PageHeader title={data.invoice_no} subtitle={`${data.invoice_date} · Balance ${formatInr(data.balance_due)}`}>
        {session.can('invoices.create') && !data.issued_at ? <Link to={`/billing/invoices/${data.id}/edit`}><Button variant="secondary">Edit draft</Button></Link> : null}
        <Button variant="secondary" onClick={() => downloadInvoicePdf(data, snapshot).catch((error) => toast(apiError(error), 'error'))}>Download PDF</Button>
        <Button variant="secondary" onClick={() => invoiceService.pdfBlob(data.id).then((blob) => window.open(URL.createObjectURL(blob))).catch((error) => toast(apiError(error), 'error'))}>Server PDF</Button>
        <Button variant="secondary" onClick={() => window.print()}>Print invoice</Button>
        <ShareButton invoice={data} phone={customer.data?.phone} name={customer.data?.display_name} />
        <Button onClick={async () => {
          if (!upiId) return toast('Add a UPI ID in Billing Settings first.', 'error')
          const uri = upiPayUri({ upiId, merchantName: snapshot.merchant_name || extras?.merchantName || snapshot.from?.name || 'Merchant', amount: String(data.balance_due || data.grand_total), invoiceNo: data.invoice_no })
          setQr(await QRCode.toDataURL(uri))
        }}>Generate UPI QR</Button>
        {session.can('invoices.cancel') ? <Button variant="danger" onClick={() => invoiceService.cancel(data.id).then(() => queryClient.invalidateQueries({ queryKey: ['invoice', id] })).catch((error) => toast(apiError(error), 'error'))}>Cancel invoice</Button> : null}
      </PageHeader>
      <div id="invoice-print">
        <TaxInvoiceSheet invoice={buildTaxInvoice({
          businessName: snapshot.from?.name || extras?.merchantName || 'Business',
          phone: snapshot.from?.phone,
          email: snapshot.from?.email,
          invoiceNo: data.invoice_no,
          invoiceDate: data.invoice_date,
          billToName: snapshot.bill_to?.name || customer.data?.display_name || 'Customer',
          notes: data.notes,
          shipping: data.shipping_amount,
          received: data.amount_paid,
          balance: data.balance_due,
          grandTotal: data.grand_total,
          lines: snapshot.lines?.length ? snapshot.lines.map((line) => ({
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
            gstRate: 0,
            cgst: '0',
            sgst: '0',
            igst: item.tax_amount,
            total: item.line_total,
          })),
        })} />
      </div>
      <p className="text-sm text-muted">A QR code does not confirm payment. Record the payment after you reconcile it.</p>
      {session.can('payments.create') ? (
        <form className="flex flex-wrap items-end gap-2" onSubmit={async (event) => {
          event.preventDefault()
          try {
            const payment = await paymentService.create({ customer_id: data.customer_id, amount, payment_method_id: methods.data?.items[0]?.id ?? null, branch_id: session.branchId })
            await paymentService.allocate(payment.id, data.id, amount)
            toast('Payment recorded')
            queryClient.invalidateQueries({ queryKey: ['invoice', id] })
          } catch (error) {
            toast(apiError(error), 'error')
          }
        }}>
          <Field label="Record payment" value={amount} onChange={(event) => setAmount(event.target.value)} required />
          <Button type="submit">Record payment</Button>
        </form>
      ) : null}
      <Modal title="UPI QR" open={Boolean(qr)} onClose={() => setQr('')}>
        <img src={qr} alt="UPI QR code" className="mx-auto h-56 w-56" />
        <p className="mt-2 text-center text-sm">{upiId}</p>
        <p className="text-center text-sm">Amount {formatInr(data.balance_due || data.grand_total)}</p>
        <Button className="mt-3" onClick={() => { const link = document.createElement('a'); link.href = qr; link.download = `${data.invoice_no}-upi.png`; link.click() }}>Download QR</Button>
      </Modal>
    </div>
  )
}

function ShareButton({ invoice, phone, name }: { invoice: Invoice; phone?: string | null; name?: string | null }) {
  const toast = useToast()
  return <Button variant="secondary" onClick={() => {
    try {
      const url = whatsAppInvoiceUrl({
        phone: phone || '',
        customerName: name || 'Customer',
        invoiceNo: invoice.invoice_no,
        invoiceDate: invoice.invoice_date,
        grandTotal: invoice.grand_total,
        amountPaid: invoice.amount_paid,
        balanceDue: invoice.balance_due || '0',
        invoiceUrl: `${window.location.origin}/billing/invoices/${invoice.id}`,
      })
      window.open(url, '_blank', 'noopener')
    } catch (error) {
      toast(apiError(error), 'error')
    }
  }}>Share on WhatsApp</Button>
}
