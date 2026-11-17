export function upiPayUri(input: { upiId: string; merchantName: string; amount: string; invoiceNo: string }): string {
  const query = [
    ['pa', input.upiId.trim()],
    ['pn', input.merchantName.trim() || 'Merchant'],
    ['am', Number(input.amount).toFixed(2)],
    ['cu', 'INR'],
    ['tn', input.invoiceNo],
  ]
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
    .join('&')
  return `upi://pay?${query}`
}
