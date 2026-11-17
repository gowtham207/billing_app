import { jsPDF } from 'jspdf'
import type { BillingSnapshot, Invoice } from '@/types/api'
import { buildTaxInvoice, type TaxInvoiceView } from '@/features/billing/TaxInvoiceSheet'

const PURPLE: [number, number, number] = [91, 70, 224]

function drawSheet(doc: jsPDF, view: TaxInvoiceView) {
  const left = 12
  const width = 186
  doc.setFillColor(...PURPLE)
  doc.roundedRect(left, 12, 58, 12, 1.4, 1.4, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(13)
  doc.setTextColor(255, 255, 255)
  doc.text('TAX INVOICE', left + 4, 20)
  doc.setTextColor(...PURPLE)
  doc.setFontSize(18)
  doc.text(view.businessName, left, 34)
  doc.setTextColor(31, 36, 48)
  doc.setFontSize(10)
  doc.setFont('helvetica', 'bold')
  doc.text('Phone:', left, 42)
  doc.setFont('helvetica', 'normal')
  doc.text(view.phone, left, 47)
  doc.setFont('helvetica', 'bold')
  doc.text('Email:', left, 54)
  doc.setFont('helvetica', 'normal')
  doc.text(view.email, left, 59)
  doc.setDrawColor(...PURPLE)
  doc.setLineWidth(0.6)
  doc.line(left, 64, left + width, 64)

  doc.setFont('helvetica', 'bold')
  doc.text(`Invoice No.: ${view.invoiceNo}`, left, 72)
  doc.text('Date:', left, 78)
  doc.setFont('helvetica', 'normal')
  doc.text(view.invoiceDate, left + 28, 78)
  doc.setFont('helvetica', 'bold')
  doc.text('Bill To:', 110, 72)
  doc.setFontSize(12)
  doc.text(view.billToName, 110, 79)

  const columns = [8, 34, 18, 16, 16, 12, 20, 22, 22, 18]
  const headers = ['#', 'Item name', 'Item Code', 'HSN/SAC', 'Quantity', 'Unit', 'Price/Unit', 'Discount', 'GST', 'Amount']
  let y = 88
  const rowHeight = 8
  const paintHeader = () => {
    doc.setFillColor(...PURPLE)
    doc.rect(left, y, width, rowHeight, 'F')
    doc.setTextColor(255, 255, 255)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(7)
    let x = left
    headers.forEach((header, index) => {
      doc.text(header, x + 1, y + 5.2, { maxWidth: columns[index] - 1.5 })
      x += columns[index]
    })
    y += rowHeight
  }
  paintHeader()

  const paintCells = (cells: string[], fill: boolean) => {
    if (y > 250) {
      doc.addPage()
      y = 16
      paintHeader()
    }
    if (fill) {
      doc.setFillColor(...PURPLE)
      doc.rect(left, y, width, rowHeight, 'F')
      doc.setTextColor(255, 255, 255)
    } else {
      doc.setTextColor(31, 36, 48)
    }
    doc.setFont('helvetica', fill ? 'bold' : 'normal')
    doc.setFontSize(7)
    let x = left
    cells.forEach((cell, index) => {
      doc.text(String(cell), x + 1, y + 5.2, { maxWidth: columns[index] - 1.5 })
      x += columns[index]
    })
    y += rowHeight
  }

  if (view.lines.length === 0) paintCells(['', 'No line items yet', '', '', '', '', '', '', '', ''], false)
  view.lines.forEach((line) => paintCells([String(line.index), line.name, line.code, line.hsn, line.quantity, line.unit, line.price, line.discount, line.gst, line.amount], false))
  paintCells(['', 'Total', '', '', view.totalQuantity, '', '', view.totalDiscount, view.totalGst, view.totalAmount], true)

  y += 8
  if (y > 230) {
    doc.addPage()
    y = 16
  }
  doc.setTextColor(...PURPLE)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.text('Invoice Amount In Words', left, y)
  doc.setTextColor(31, 36, 48)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  const words = doc.splitTextToSize(view.words, 100)
  doc.text(words, left, y + 6)
  const termsY = y + 8 + words.length * 4
  doc.setTextColor(...PURPLE)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.text('Terms And Conditions', left, termsY)
  doc.setTextColor(31, 36, 48)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  const terms = doc.splitTextToSize(view.terms, 100)
  doc.text(terms, left, termsY + 6)
  const signY = termsY + 12 + terms.length * 4
  doc.text(`For : ${view.businessName}`, left, signY)
  doc.line(left, signY + 16, left + 48, signY + 16)
  doc.setFont('helvetica', 'bold')
  doc.text('Authorized Signatory', left, signY + 21)

  let summaryY = y
  view.summary.forEach((row) => {
    if (row.emphasize) {
      doc.setFillColor(...PURPLE)
      doc.rect(118, summaryY - 4, 80, 7, 'F')
      doc.setTextColor(255, 255, 255)
    } else {
      doc.setDrawColor(217, 214, 234)
      doc.rect(118, summaryY - 4, 80, 7)
      doc.setTextColor(31, 36, 48)
    }
    doc.setFont('helvetica', row.emphasize ? 'bold' : 'normal')
    doc.setFontSize(8)
    doc.text(row.label, 120, summaryY)
    doc.text(row.amount, 196, summaryY, { align: 'right' })
    summaryY += 7
  })
}

export async function downloadInvoicePdf(invoice: Invoice, snapshot: BillingSnapshot) {
  const view = buildTaxInvoice({
    businessName: snapshot.from?.name || snapshot.merchant_name || 'Business',
    phone: snapshot.from?.phone,
    email: snapshot.from?.email,
    invoiceNo: invoice.invoice_no,
    invoiceDate: invoice.invoice_date,
    billToName: snapshot.bill_to?.name || snapshot.to?.name || 'Customer',
    notes: invoice.notes,
    shipping: invoice.shipping_amount,
    received: invoice.amount_paid,
    balance: invoice.balance_due,
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
