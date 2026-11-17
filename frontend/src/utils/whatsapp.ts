import { formatInr } from '@/utils/money'

export function whatsAppInvoiceUrl(input: {
  phone: string
  customerName: string
  invoiceNo: string
  invoiceDate: string
  grandTotal: string
  amountPaid: string
  balanceDue: string
  invoiceUrl?: string
}): string {
  const digits = input.phone.replace(/\D/g, '')
  const withCountry = digits.length === 10 ? `91${digits}` : digits
  if (withCountry.length < 11 || withCountry.length > 15) {
    throw new Error('Enter a valid mobile number before sharing on WhatsApp.')
  }
  const link = input.invoiceUrl ? `\n\nPlease find your invoice here: ${input.invoiceUrl}` : ''
  const text = `Hello ${input.customerName},\n\nYour invoice ${input.invoiceNo} dated ${input.invoiceDate} has been generated.\n\nInvoice Amount: ${formatInr(input.grandTotal)}\nPaid Amount: ${formatInr(input.amountPaid)}\nBalance Due: ${formatInr(input.balanceDue)}${link}\n\nThank you for your business!`
  return `https://wa.me/${withCountry}?text=${encodeURIComponent(text)}`
}
