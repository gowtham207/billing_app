import { jsPDF } from 'jspdf'
import QRCode from 'qrcode'
import type { BillingSnapshot, Invoice, PartyAddress } from '@/types/api'
import { amountInWords, formatInr, toPaise } from '@/utils/money'
import { upiPayUri } from '@/utils/upi'

function linesOf(address?: PartyAddress) {
  if (!address) return ['—']
  return [address.name, address.line1, address.line2, [address.city, address.district, address.state, address.postal_code].filter(Boolean).join(', '), address.gstin && `GSTIN ${address.gstin}`, address.phone, address.email].filter(Boolean) as string[]
}

export async function downloadInvoicePdf(invoice: Invoice, snapshot: BillingSnapshot, logo?: string) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  const rows = snapshot.lines ?? []
  let y = 16
  if (logo) {
    try { doc.addImage(logo, 'PNG', 14, 12, 22, 22); y = 18 } catch { y = 16 }
  }
  doc.setFontSize(16)
  doc.text(snapshot.from?.name || 'Tax invoice', logo ? 42 : 14, y)
  doc.setFontSize(10)
  linesOf(snapshot.from).forEach((line, index) => doc.text(line, logo ? 42 : 14, y + 6 + index * 4))
  doc.text(`Invoice ${invoice.invoice_no}`, 140, 18)
  doc.text(`Date ${invoice.invoice_date}`, 140, 24)
  doc.text(`Due ${invoice.due_date || '—'}`, 140, 30)
  doc.text(`Place of supply ${snapshot.place_of_supply || '—'}`, 140, 36)
  y = 58
  doc.setFontSize(11)
  doc.text('To address', 14, y)
  doc.text('Bill to address', 110, y)
  doc.setFontSize(10)
  linesOf(snapshot.to).forEach((line, index) => doc.text(line, 14, y + 6 + index * 4))
  linesOf(snapshot.bill_to).forEach((line, index) => doc.text(line, 110, y + 6 + index * 4))
  y = 96
  const headers = ['Item', 'HSN', 'Qty', 'Price', 'Disc', 'Taxable', 'CGST', 'SGST', 'IGST', 'Total']
  doc.setFontSize(8)
  headers.forEach((header, index) => doc.text(header, 14 + index * 19, y))
  y += 5
  rows.forEach((row) => {
    if (y > 250) {
      doc.addPage()
      y = 20
    }
    const cells = [row.description, row.hsn || '—', row.quantity, formatInr(row.unit_price), formatInr(row.discount), formatInr(row.taxable), formatInr(row.cgst), formatInr(row.sgst), formatInr(row.igst), formatInr(row.total)]
    cells.forEach((cell, index) => doc.text(String(cell).slice(0, 16), 14 + index * 19, y))
    y += 5
  })
  y += 4
  doc.setFontSize(10)
  ;[
    `Subtotal ${formatInr(invoice.subtotal)}`,
    `Discount ${formatInr(invoice.discount_total)}`,
    `Tax ${formatInr(invoice.tax_total)}`,
    `Grand total ${formatInr(invoice.grand_total)}`,
    `Paid ${formatInr(invoice.amount_paid)}`,
    `Balance ${formatInr(invoice.balance_due)}`,
    amountInWords(invoice.grand_total),
  ].forEach((line) => { doc.text(line, 14, y); y += 5 })
  if (snapshot.upi_id && toPaise(invoice.balance_due) > 0) {
    const uri = upiPayUri({ upiId: snapshot.upi_id, merchantName: snapshot.merchant_name || snapshot.from?.name || 'Merchant', amount: String(invoice.balance_due), invoiceNo: invoice.invoice_no })
    const image = await QRCode.toDataURL(uri)
    doc.addImage(image, 'PNG', 150, Math.min(y, 230), 36, 36)
    doc.text(`UPI ${snapshot.upi_id}`, 150, Math.min(y, 230) + 40)
  }
  doc.text('Terms: Payment is confirmed only after it is recorded against this invoice.', 14, 275)
  const pages = doc.getNumberOfPages()
  for (let page = 1; page <= pages; page += 1) {
    doc.setPage(page)
    doc.setFontSize(8)
    doc.text(`Page ${page} of ${pages}`, 180, 290)
  }
  doc.save(`${invoice.invoice_no}.pdf`)
}
