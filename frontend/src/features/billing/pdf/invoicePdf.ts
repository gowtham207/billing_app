import { jsPDF } from 'jspdf'
import type { BillingSnapshot, Invoice } from '@/types/api'
import { buildTaxInvoice, type TaxInvoiceView } from '@/features/billing/TaxInvoiceSheet'

const NAVY: [number, number, number] = [16, 42, 67]
const INK: [number, number, number] = [30, 41, 59]
const MUTED: [number, number, number] = [100, 116, 139]
const LINE: [number, number, number] = [226, 232, 240]

function wrapped(doc: jsPDF, lines: string[], x: number, y: number, width: number, size = 8) {
  doc.setFontSize(size)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...INK)
  const text = doc.splitTextToSize(lines.join('\n'), width)
  doc.text(text, x, y)
  return y + text.length * (size * 0.42)
}

function drawSheet(doc: jsPDF, view: TaxInvoiceView) {
  const left = 12
  const width = 186
  doc.setTextColor(...NAVY)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(16)
  doc.text(view.businessName, left, 16)
  doc.text(view.documentTitle, left + width, 16, { align: 'right' })
  let y = wrapped(doc, view.headerLines, left, 22, 110, 8)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(...INK)
  doc.text(`${view.numberLabel}: ${view.invoiceNo}`, left + width, 22, { align: 'right' })
  doc.text(`${view.dateLabel}: ${view.invoiceDate}`, left + width, 27, { align: 'right' })
  doc.text(`${view.dueLabel}: ${view.dueDate}`, left + width, 32, { align: 'right' })
  y = Math.max(y, 38) + 2

  const boxW = width / 3
  const partyBlocks = [
    ['FROM / SELLER', view.seller],
    ['BUYER / BILL TO', view.buyer],
    ['DELIVERY / SHIP TO', [...view.shipTo, `Place of Supply: ${view.placeOfSupply}`, `Supply Type: ${view.supplyType}`]],
  ]
  const blockHeight = 34
  doc.setDrawColor(...LINE)
  doc.setFillColor(248, 250, 252)
  doc.rect(left, y, width, blockHeight, 'FD')
  partyBlocks.forEach((block, index) => {
    const x = left + index * boxW
    if (index) doc.line(x, y, x, y + blockHeight)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8)
    doc.setTextColor(...NAVY)
    doc.text(String(block[0]), x + 2, y + 5)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(...INK)
    doc.setFontSize(7.5)
    const body = doc.splitTextToSize((block[1] as string[]).join('\n'), boxW - 4)
    doc.text(body.slice(0, 7), x + 2, y + 10)
  })
  y += blockHeight + 7

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  doc.setTextColor(...NAVY)
  doc.text('ITEM DETAILS', left, y)
  y += 2
  const columns = view.showDiscount ? [12, 52, 22, 14, 24, 26, 36] : [14, 70, 24, 16, 28, 34]
  const headers = view.showDiscount ? ['S.No', 'Description', 'HSN/SAC', 'Qty', 'Rate', 'Discount', 'Taxable'] : ['S.No', 'Description', 'HSN/SAC', 'Qty', 'Rate', 'Taxable']
  const paintHeader = () => {
    doc.setFillColor(...NAVY)
    doc.rect(left, y, width, 7, 'F')
    doc.setTextColor(255, 255, 255)
    doc.setFontSize(7.5)
    let x = left
    headers.forEach((header, index) => {
      doc.text(header, x + 1.5, y + 4.6)
      x += columns[index]
    })
    y += 7
  }
  paintHeader()
  const paintRow = (cells: string[], fill?: [number, number, number]) => {
    if (y > 250) {
      doc.addPage()
      y = 16
      paintHeader()
    }
    if (fill) {
      doc.setFillColor(...fill)
      doc.rect(left, y, width, 6.5, 'F')
    }
    doc.setTextColor(...INK)
    doc.setFont('helvetica', fill ? 'bold' : 'normal')
    doc.setFontSize(8)
    let x = left
    cells.forEach((cell, index) => {
      doc.text(String(cell), x + 1.5, y + 4.4, { maxWidth: columns[index] - 2 })
      x += columns[index]
    })
    y += 6.5
  }
  const cells = (line: TaxInvoiceView['lines'][number]) => view.showDiscount
    ? [String(line.index), line.name, line.hsn, line.quantity, line.rate, line.discount, line.taxable]
    : [String(line.index), line.name, line.hsn, line.quantity, line.rate, line.taxable]
  if (view.lines.length === 0) paintRow(view.showDiscount ? ['', 'No line items yet', '', '', '', '', ''] : ['', 'No line items yet', '', '', '', ''])
  view.lines.forEach((line, index) => paintRow(cells(line), index % 2 ? [248, 250, 252] : undefined))
  paintRow(view.showDiscount ? ['', 'Subtotal', '', '', '', '', view.tableSubtotal] : ['', 'Subtotal', '', '', '', view.tableSubtotal], [241, 245, 249])
  y += 6

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  doc.setTextColor(...NAVY)
  doc.text('TAX BREAKUP', left, y)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(...INK)
  const breakup = [
    `Taxable Amount: Rs. ${view.taxableAmount}`,
    ...(view.showDiscount ? [`Discount: Rs. ${view.discount}`] : []),
    `GST Rate: ${view.gstRateLabel}`,
    ...view.taxLines.map((row) => `${row.label}: Rs. ${row.amount}`),
    `Total GST: Rs. ${view.totalGst}`,
  ]
  doc.text(breakup, left, y + 5)
  let totalsY = y
  view.totals.forEach((row) => {
    if (row.emphasize) {
      doc.setFillColor(231, 246, 244)
      doc.rect(118, totalsY - 4, 80, 8, 'F')
      doc.setTextColor(15, 118, 110)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(11)
    } else {
      doc.setTextColor(...INK)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9)
    }
    doc.text(row.label, 120, totalsY)
    doc.text(`Rs. ${row.amount}`, 196, totalsY, { align: 'right' })
    totalsY += row.emphasize ? 10 : 6
  })
  y = Math.max(y + 6 + breakup.length * 4, totalsY) + 4
  doc.setTextColor(...INK)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  doc.text('Amount in Words:', left, y)
  doc.setFont('helvetica', 'normal')
  doc.text(view.words, left + 34, y)
  y += 6
  doc.setFillColor(248, 250, 252)
  doc.setDrawColor(...LINE)
  const declaration = doc.splitTextToSize(view.declaration, width - 6)
  const terms = doc.splitTextToSize(`Terms: ${view.terms}`, width - 6)
  const boxHeight = 10 + (declaration.length + terms.length) * 4
  doc.rect(left, y, width, boxHeight, 'FD')
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...NAVY)
  doc.text('DECLARATION', left + 3, y + 5)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...INK)
  doc.text(declaration, left + 3, y + 10)
  doc.setFont('helvetica', 'bold')
  doc.text(terms, left + 3, y + 12 + declaration.length * 4)
  y += boxHeight + 10
  doc.setFont('helvetica', 'bold')
  doc.text('Customer Signature', left, y)
  doc.text(`For ${view.businessName}`, 120, y)
  y += 16
  doc.setDrawColor(51, 65, 85)
  doc.line(left, y, left + 55, y)
  doc.line(120, y, 175, y)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(...MUTED)
  doc.text('Received By', left, y + 4)
  doc.text('Authorized Signatory', 120, y + 4)
  doc.setTextColor(...INK)
  doc.text('Thank you for your business!', left, y + 12)
}

export async function downloadInvoicePdf(invoice: Invoice, snapshot: BillingSnapshot) {
  const view = buildTaxInvoice({
    businessName: snapshot.from?.name || snapshot.merchant_name || 'Business',
    seller: snapshot.from,
    buyer: snapshot.bill_to,
    shipTo: snapshot.to,
    invoiceNo: invoice.invoice_no,
    invoiceDate: invoice.invoice_date,
    dueDate: invoice.due_date,
    placeOfSupply: snapshot.place_of_supply || snapshot.bill_to?.state,
    supplyType: snapshot.treatment === 'inter' ? 'Inter-state' : snapshot.treatment === 'exempt' ? 'Exempt' : 'Intra-state',
    showDiscount: snapshot.show_discount !== false,
    notes: invoice.notes,
    shipping: invoice.shipping_amount,
    grandTotal: invoice.grand_total,
    lines: (snapshot.lines ?? []).map((line) => ({
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
    })),
  })
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  drawSheet(doc, view)
  doc.save(`${invoice.invoice_no}.pdf`)
}

export function downloadSheetPdf(view: TaxInvoiceView, filename: string) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  drawSheet(doc, view)
  doc.save(filename)
}
