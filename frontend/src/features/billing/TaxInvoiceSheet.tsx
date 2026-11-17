import { amountInWords, formatInr, fromPaise, toPaise } from '@/utils/money'

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
  phone?: string
  email?: string
  invoiceNo: string
  invoiceDate: string
  billToName: string
  notes?: string | null
  lines: TaxInvoiceLine[]
  shipping?: string
  received?: string
  balance?: string | null
  grandTotal?: string
}

export type TaxInvoiceView = {
  businessName: string
  phone: string
  email: string
  invoiceNo: string
  invoiceDate: string
  billToName: string
  lines: { index: number; name: string; code: string; hsn: string; quantity: string; unit: string; price: string; discount: string; gst: string; amount: string }[]
  totalQuantity: string
  totalDiscount: string
  totalGst: string
  totalAmount: string
  words: string
  terms: string
  summary: { label: string; amount: string; emphasize?: boolean }[]
}

function rupee(value: string | number) {
  return formatInr(value).replace('₹', '₹ ')
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

function invoiceWords(value: string | number) {
  return amountInWords(value).replace(/\b[a-z]+/g, (word) => (word === 'only' || word === 'and' ? word : word.charAt(0).toUpperCase() + word.slice(1)))
}

function invoiceDate(value: string) {
  const [year, month, day] = value.slice(0, 10).split('-')
  if (!year || !month || !day) return value || '—'
  return `${day}/${month}/${year}`
}

export function buildTaxInvoice(input: TaxInvoiceInput): TaxInvoiceView {
  let quantity = 0
  let discount = 0
  let gst = 0
  let amount = 0
  let subtotal = 0
  const tax = new Map<number, { cgst: number; sgst: number; igst: number }>()

  const lines = input.lines.map((line, index) => {
    const qty = Number(line.quantity) || 0
    const discountPaise = toPaise(line.discount)
    const cgst = toPaise(line.cgst)
    const sgst = toPaise(line.sgst)
    const igst = toPaise(line.igst)
    const taxPaise = cgst + sgst + igst
    const totalPaise = toPaise(line.total)
    const gross = Math.round((toPaise(line.quantity) / 100) * toPaise(line.unitPrice))
    const percent = gross > 0 ? (discountPaise / gross) * 100 : 0
    quantity += qty
    discount += discountPaise
    gst += taxPaise
    amount += totalPaise
    subtotal += toPaise(line.total) + discountPaise - taxPaise
    const bucket = tax.get(line.gstRate) ?? { cgst: 0, sgst: 0, igst: 0 }
    bucket.cgst += cgst
    bucket.sgst += sgst
    bucket.igst += igst
    tax.set(line.gstRate, bucket)
    return {
      index: index + 1,
      name: line.description || 'Item',
      code: line.sku || '',
      hsn: line.hsn || '',
      quantity: prettyNumber(qty),
      unit: line.unit || '-',
      price: rupee(line.unitPrice || 0),
      discount: `${rupee(fromPaise(discountPaise))} (${rateLabel(percent)}%)`,
      gst: `${rupee(fromPaise(taxPaise))} (${rateLabel(line.gstRate)}%)`,
      amount: rupee(fromPaise(totalPaise)),
    }
  })

  const shipping = toPaise(input.shipping)
  const exact = subtotal - discount + gst + shipping
  const total = input.grandTotal !== undefined ? toPaise(input.grandTotal) : Math.round(exact / 100) * 100
  const roundOff = total - exact
  const received = toPaise(input.received)
  const balance = input.balance !== undefined && input.balance !== null ? toPaise(input.balance) : total - received
  const summary: TaxInvoiceView['summary'] = [
    { label: 'Sub Total', amount: rupee(fromPaise(subtotal)) },
    { label: 'Discount', amount: rupee(fromPaise(discount)) },
  ]
  ;[...tax.entries()].filter(([, bucket]) => bucket.cgst || bucket.sgst || bucket.igst).sort((left, right) => left[0] - right[0]).forEach(([rate, bucket]) => {
    if (!rate) {
      summary.push({ label: 'GST', amount: rupee(fromPaise(bucket.cgst + bucket.sgst + bucket.igst)) })
      return
    }
    if (bucket.sgst) summary.push({ label: `SGST@${rateLabel(rate / 2)}%`, amount: rupee(fromPaise(bucket.sgst)) })
    if (bucket.cgst) summary.push({ label: `CGST@${rateLabel(rate / 2)}%`, amount: rupee(fromPaise(bucket.cgst)) })
    if (bucket.igst) summary.push({ label: `IGST@${rateLabel(rate)}%`, amount: rupee(fromPaise(bucket.igst)) })
  })
  if (shipping) summary.push({ label: 'Additional charges', amount: rupee(fromPaise(shipping)) })
  summary.push(
    { label: 'Round off', amount: rupee(fromPaise(roundOff)) },
    { label: 'Total', amount: rupee(fromPaise(total)), emphasize: true },
    { label: 'Received', amount: rupee(fromPaise(received)) },
    { label: 'Balance', amount: rupee(fromPaise(balance)) },
  )

  return {
    businessName: input.businessName || 'Business',
    phone: input.phone || '—',
    email: input.email || '—',
    invoiceNo: input.invoiceNo || 'Draft',
    invoiceDate: invoiceDate(input.invoiceDate),
    billToName: input.billToName || 'Customer',
    lines,
    totalQuantity: prettyNumber(quantity),
    totalDiscount: rupee(fromPaise(discount)),
    totalGst: rupee(fromPaise(gst)),
    totalAmount: rupee(fromPaise(amount)),
    words: invoiceWords(fromPaise(total)),
    terms: input.notes?.trim() || 'Thanks for doing business with us!',
    summary,
  }
}

export function TaxInvoiceSheet({ invoice }: { invoice: TaxInvoiceView }) {
  return (
    <div className="invoice-stage">
      <article className="invoice-sheet">
        <div className="invoice-ribbon">Premium</div>
        <div className="invoice-banner">TAX INVOICE</div>
        <h2 className="invoice-brand">{invoice.businessName}</h2>
        <p className="invoice-contact"><strong>Phone:</strong><br />{invoice.phone}</p>
        <p className="invoice-contact"><strong>Email:</strong><br />{invoice.email}</p>
        <hr className="invoice-rule" />
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="text-sm">
            <p><strong>Invoice No.:</strong> {invoice.invoiceNo}</p>
            <p className="mt-2"><strong>Date:</strong> <span className="ml-6">{invoice.invoiceDate}</span></p>
          </div>
          <div className="text-sm">
            <p><strong>Bill To:</strong></p>
            <p className="mt-2 text-base font-bold">{invoice.billToName}</p>
          </div>
        </div>
        <div className="mt-4 overflow-x-auto">
          <table className="invoice-grid min-w-[860px]">
            <thead>
              <tr>
                {['#', 'Item name', 'Item Code', 'HSN/SAC', 'Quantity', 'Unit', 'Price/Unit', 'Discount', 'GST', 'Amount'].map((heading) => <th key={heading}>{heading}</th>)}
              </tr>
            </thead>
            <tbody>
              {invoice.lines.length === 0 ? (
                <tr><td colSpan={10}>No line items yet.</td></tr>
              ) : invoice.lines.map((line) => (
                <tr key={line.index}>
                  <td>{line.index}</td>
                  <td className="name">{line.name}</td>
                  <td>{line.code}</td>
                  <td>{line.hsn}</td>
                  <td>{line.quantity}</td>
                  <td>{line.unit}</td>
                  <td className="amount">{line.price}</td>
                  <td className="amount">{line.discount}</td>
                  <td className="amount">{line.gst}</td>
                  <td className="amount">{line.amount}</td>
                </tr>
              ))}
              <tr className="total">
                <td />
                <td className="name">Total</td>
                <td />
                <td />
                <td>{invoice.totalQuantity}</td>
                <td />
                <td />
                <td className="amount">{invoice.totalDiscount}</td>
                <td className="amount">{invoice.totalGst}</td>
                <td className="amount">{invoice.totalAmount}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="mt-6 flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-sm text-sm">
            <p className="invoice-kicker">Invoice Amount In Words</p>
            <p className="mt-1">{invoice.words}</p>
            <p className="invoice-kicker mt-5">Terms And Conditions</p>
            <p className="mt-1">{invoice.terms}</p>
            <p className="mt-8">For : {invoice.businessName}</p>
            <div className="mt-10 w-48 border-t border-black pt-1 font-bold">Authorized Signatory</div>
          </div>
          <table className="invoice-summary">
            <tbody>
              {invoice.summary.map((row) => (
                <tr key={row.label} className={row.emphasize ? 'grand' : undefined}>
                  <td>{row.label}</td>
                  <td className="amount">{row.amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </div>
  )
}
