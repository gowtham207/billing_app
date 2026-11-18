import type { PartyAddress } from '@/types/api'
import { amountInWords, fromPaise, toPaise } from '@/utils/money'

export const GST_DECLARATION = 'We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.'
export const GST_TERMS = 'Please make payment by the due date mentioned above.'
export const QUOTATION_DECLARATION = 'We declare that this quotation shows the actual price of the goods described and that all particulars are true and correct.'
export const QUOTATION_TERMS = 'This quotation is valid until the date mentioned above.'
export const ORDER_DECLARATION = 'We declare that this sales order shows the actual price of the goods described and that all particulars are true and correct.'
export const ORDER_TERMS = 'This sales order is confirmed for supply of the goods described above.'

export type TaxInvoiceLine = {
  description: string
  sku?: string
  hsn?: string
  quantity: string
  unit?: string
  unitPrice: string
  discount: string
  gstRate: number
  cgst: string
  sgst: string
  igst: string
  total: string
}

export type TaxInvoiceInput = {
  businessName: string
  seller?: Partial<PartyAddress>
  buyer?: Partial<PartyAddress>
  shipTo?: Partial<PartyAddress>
  invoiceNo: string
  invoiceDate: string
  dueDate?: string | null
  placeOfSupply?: string
  supplyType?: string
  notes?: string | null
  showDiscount?: boolean
  documentKind?: 'invoice' | 'quotation' | 'order'
  lines: TaxInvoiceLine[]
  shipping?: string
  grandTotal?: string
}

export type TaxInvoiceView = {
  businessName: string
  headerLines: string[]
  invoiceNo: string
  invoiceDate: string
  dueDate: string
  seller: string[]
  buyer: string[]
  shipTo: string[]
  placeOfSupply: string
  supplyType: string
  lines: { index: number; name: string; hsn: string; quantity: string; rate: string; discount: string; taxable: string }[]
  tableSubtotal: string
  taxableAmount: string
  discount: string
  gstRateLabel: string
  taxLines: { label: string; amount: string }[]
  totalGst: string
  totals: { label: string; amount: string; emphasize?: boolean }[]
  words: string
  declaration: string
  terms: string
  showDiscount: boolean
  documentTitle: string
  numberLabel: string
  dateLabel: string
  dueLabel: string
}

function money(paise: number) {
  return new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(paise / 100)
}

function prettyNumber(value: number) {
  if (!Number.isFinite(value)) return '0'
  const rounded = Math.round(value * 100) / 100
  return Number.isInteger(rounded) ? String(rounded) : String(rounded)
}

function rateLabel(rate: number) {
  const rounded = Math.round(rate * 100) / 100
  return Number.isInteger(rounded) ? String(rounded) : String(rounded)
}

function formatDate(value?: string | null) {
  if (!value) return '—'
  const date = new Date(`${value.slice(0, 10)}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-')
}

function wordsOf(value: string | number) {
  const core = amountInWords(value).replace(/ rupees(?: and .* paise)? only$/i, '').replace(/ only$/i, '')
  const titled = core.replace(/\b[a-z]+/g, (word) => (word === 'and' ? word : word.charAt(0).toUpperCase() + word.slice(1)))
  return `Rupees ${titled} Only.`
}

function partyLines(party: Partial<PartyAddress> | undefined, fallback: string) {
  const place = [party?.city, party?.district, party?.state].filter(Boolean).join(', ')
  const locality = [place, party?.postal_code].filter(Boolean).join(' – ')
  return [
    party?.name || fallback,
    party?.line1,
    party?.line2,
    locality,
    party?.gstin ? `GSTIN: ${party.gstin}` : '',
    party?.phone ? `Phone: ${party.phone}` : '',
    party?.email ? `Email: ${party.email}` : '',
  ].filter((line): line is string => Boolean(line && line.trim()))
}

export function buildTaxInvoice(input: TaxInvoiceInput): TaxInvoiceView {
  let discount = 0
  let taxable = 0
  let gst = 0
  const tax = new Map<number, { cgst: number; sgst: number; igst: number }>()
  const lines = input.lines.map((line, index) => {
    const discountPaise = toPaise(line.discount)
    const taxPaise = toPaise(line.cgst) + toPaise(line.sgst) + toPaise(line.igst)
    const taxablePaise = toPaise(line.total) - taxPaise
    discount += discountPaise
    taxable += taxablePaise
    gst += taxPaise
    const bucket = tax.get(line.gstRate) ?? { cgst: 0, sgst: 0, igst: 0 }
    bucket.cgst += toPaise(line.cgst)
    bucket.sgst += toPaise(line.sgst)
    bucket.igst += toPaise(line.igst)
    tax.set(line.gstRate, bucket)
    return {
      index: index + 1,
      name: line.description || 'Item',
      hsn: line.hsn || '—',
      quantity: prettyNumber(Number(line.quantity) || 0),
      rate: money(toPaise(line.unitPrice)),
      discount: money(discountPaise),
      taxable: money(taxablePaise),
    }
  })

  const shipping = toPaise(input.shipping)
  const exact = taxable + gst + shipping
  const grand = input.grandTotal !== undefined ? toPaise(input.grandTotal) : exact
  const rates = [...tax.keys()].filter((rate) => rate > 0)
  const taxLines: { label: string; amount: string }[] = []
  ;[...tax.entries()].filter(([, bucket]) => bucket.cgst || bucket.sgst || bucket.igst).sort((left, right) => left[0] - right[0]).forEach(([rate, bucket]) => {
    if (!rate) {
      taxLines.push({ label: 'GST', amount: money(bucket.cgst + bucket.sgst + bucket.igst) })
      return
    }
    if (bucket.cgst) taxLines.push({ label: `CGST @ ${rateLabel(rate / 2)}%`, amount: money(bucket.cgst) })
    if (bucket.sgst) taxLines.push({ label: `SGST @ ${rateLabel(rate / 2)}%`, amount: money(bucket.sgst) })
    if (bucket.igst) taxLines.push({ label: `IGST @ ${rateLabel(rate)}%`, amount: money(bucket.igst) })
  })
  const showDiscount = input.showDiscount !== false
  const totals: { label: string; amount: string; emphasize?: boolean }[] = [
    { label: 'Subtotal', amount: money(showDiscount ? taxable + discount : taxable) },
    ...(showDiscount ? [{ label: 'Discount', amount: money(discount) }, { label: 'Taxable value', amount: money(taxable) }] : []),
    ...taxLines.map((row) => ({ label: row.label.replace(' @ ', ' (').replace('%', '%)'), amount: row.amount })),
  ]
  if (shipping) totals.push({ label: 'Additional charges', amount: money(shipping) })
  totals.push({ label: 'Grand Total', amount: money(grand), emphasize: true })

  const seller = input.seller ?? {}
  const headerLines = partyLines({ ...seller, name: '', gstin: '', phone: '', email: '' }, '').filter((line) => line !== seller.name)
  if (seller.gstin || seller.phone) headerLines.push([seller.gstin ? `GSTIN: ${seller.gstin}` : '', seller.phone ? `Phone: ${seller.phone}` : ''].filter(Boolean).join(' | '))
  if (seller.email) headerLines.push(`Email: ${seller.email}`)

  return {
    businessName: (input.businessName || seller.name || 'Business').toUpperCase(),
    headerLines: [...new Set(headerLines)],
    invoiceNo: input.invoiceNo || 'Draft',
    invoiceDate: formatDate(input.invoiceDate),
    dueDate: formatDate(input.dueDate),
    seller: partyLines(seller, input.businessName || 'Seller'),
    buyer: partyLines(input.buyer, 'Buyer'),
    shipTo: partyLines(input.shipTo, input.buyer?.name || 'Ship to'),
    placeOfSupply: input.placeOfSupply || input.buyer?.state || input.shipTo?.state || '—',
    supplyType: input.supplyType || (taxLines.some((row) => row.label.startsWith('IGST')) ? 'Inter-state' : gst ? 'Intra-state' : 'Exempt'),
    lines,
    tableSubtotal: money(taxable),
    taxableAmount: money(taxable),
    discount: money(discount),
    gstRateLabel: rates.length === 1 ? `${rateLabel(rates[0])}%` : rates.length ? 'Multiple' : '0%',
    taxLines,
    totalGst: money(gst),
    totals,
    words: wordsOf(fromPaise(grand)),
    declaration: input.documentKind === 'quotation' ? QUOTATION_DECLARATION : input.documentKind === 'order' ? ORDER_DECLARATION : GST_DECLARATION,
    terms: input.notes?.trim() || (input.documentKind === 'quotation' ? QUOTATION_TERMS : input.documentKind === 'order' ? ORDER_TERMS : GST_TERMS),
    showDiscount,
    documentTitle: input.documentKind === 'quotation' ? 'QUOTATION' : input.documentKind === 'order' ? 'SALES ORDER' : 'TAX INVOICE',
    numberLabel: input.documentKind === 'quotation' ? 'Quotation No' : input.documentKind === 'order' ? 'Order No' : 'Invoice No',
    dateLabel: input.documentKind === 'quotation' ? 'Quotation Date' : input.documentKind === 'order' ? 'Order Date' : 'Invoice Date',
    dueLabel: input.documentKind === 'quotation' ? 'Valid Until' : 'Due Date',
  }
}

function Party({ title, lines }: { title: string; lines: string[] }) {
  return (
    <div className="gst-party">
      <h3>{title}</h3>
      {lines.map((line, index) => <p key={`${title}-${index}`} className={index === 0 ? 'name' : undefined}>{line}</p>)}
    </div>
  )
}

export function TaxInvoiceSheet({ invoice }: { invoice: TaxInvoiceView }) {
  const quotation = invoice.documentTitle === 'QUOTATION'
  const salesOrder = invoice.documentTitle === 'SALES ORDER'
  const watermark = quotation ? 'QUOTATION' : salesOrder ? 'SALES ORDER' : ''
  return (
    <article className={quotation ? 'gst-invoice is-quotation' : salesOrder ? 'gst-invoice is-order' : 'gst-invoice'}>
      <header className="gst-head">
        <div>
          <h1>{invoice.businessName}</h1>
          {invoice.headerLines.map((line) => <p key={line}>{line}</p>)}
        </div>
        <div className="gst-meta">
          <h2>{invoice.documentTitle}</h2>
          <p><strong>{invoice.numberLabel}:</strong> {invoice.invoiceNo}</p>
          <p><strong>{invoice.dateLabel}:</strong> {invoice.invoiceDate}</p>
          {invoice.dueDate !== '—' ? <p><strong>{invoice.dueLabel}:</strong> {invoice.dueDate}</p> : null}
        </div>
      </header>
      <section className="gst-parties">
        <Party title="FROM / SELLER" lines={invoice.seller} />
        <Party title="BUYER / BILL TO" lines={invoice.buyer} />
        <div className="gst-party">
          <h3>DELIVERY / SHIP TO</h3>
          {invoice.shipTo.map((line, index) => <p key={line} className={index === 0 ? 'name' : undefined}>{line}</p>)}
          <p>Place of Supply: {invoice.placeOfSupply}</p>
          <p>Supply Type: {invoice.supplyType}</p>
        </div>
      </section>
      <h3 className="gst-section-title mt-4">ITEM DETAILS</h3>
      <div className="overflow-x-auto">
        <table className="gst-grid min-w-[720px]">
          <thead>
            <tr>
              <th>S.No</th>
              <th>Description</th>
              <th>HSN/SAC</th>
              <th className="num">Qty</th>
              <th className="num">Rate (₹)</th>
              {invoice.showDiscount ? <th className="num">Discount (₹)</th> : null}
              <th className="num">Taxable Value (₹)</th>
            </tr>
          </thead>
          <tbody>
            {invoice.lines.length === 0 ? <tr><td colSpan={invoice.showDiscount ? 7 : 6}>No line items yet.</td></tr> : invoice.lines.map((line) => (
              <tr key={line.index} className={line.index % 2 === 0 ? 'alt' : undefined}>
                <td>{line.index}</td>
                <td>{line.name}</td>
                <td>{line.hsn}</td>
                <td className="num">{line.quantity}</td>
                <td className="num">{line.rate}</td>
                {invoice.showDiscount ? <td className="num">{line.discount}</td> : null}
                <td className="num">{line.taxable}</td>
              </tr>
            ))}
            <tr className="subtotal">
              <td colSpan={invoice.showDiscount ? 6 : 5}>Subtotal</td>
              <td className="num">{invoice.tableSubtotal}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <section className="gst-lower">
        <div className="gst-box">
          <h3 className="gst-section-title">TAX BREAKUP</h3>
          <p>Taxable Amount: ₹ {invoice.taxableAmount}</p>
          {invoice.showDiscount ? <p>Discount: ₹ {invoice.discount}</p> : null}
          <p>GST Rate: {invoice.gstRateLabel}</p>
          {invoice.taxLines.map((row) => <p key={row.label}>{row.label}: ₹ {row.amount}</p>)}
          <p><strong>Total GST: ₹ {invoice.totalGst}</strong></p>
        </div>
        <table className="gst-totals">
          <tbody>
            {invoice.totals.map((row) => (
              <tr key={row.label} className={row.emphasize ? 'grand' : undefined}>
                <td>{row.label}</td>
                <td className="num">₹ {row.amount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className="mt-4"><strong>Amount in Words:</strong> {invoice.words}</p>
      <section className="gst-box mt-3">
        <h3 className="gst-section-title">DECLARATION</h3>
        <p>{invoice.declaration}</p>
        <p className="mt-2"><strong>Terms:</strong> {invoice.terms}</p>
      </section>
      <section className="gst-sign">
        <div>
          <p className="font-semibold">Customer Signature</p>
          <div className="line">Received By</div>
        </div>
        <div>
          <p className="font-semibold">For {invoice.businessName}</p>
          <div className="line">Authorized Signatory</div>
        </div>
      </section>
      <p className="mt-4 text-sm">Thank you for your business!</p>
      {watermark ? <div className="gst-watermark" aria-hidden="true">{watermark}</div> : null}
    </article>
  )
}
