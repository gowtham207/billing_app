export function toPaise(value: string | number | null | undefined): number {
  if (value === null || value === undefined || value === '') return 0
  const raw = String(value).trim().replace(/,/g, '')
  const negative = raw.startsWith('-')
  const [whole, fraction = ''] = raw.replace('-', '').split('.')
  const paise = Number(whole || '0') * 100 + Number((fraction + '00').slice(0, 2))
  return negative ? -paise : paise
}

export function fromPaise(paise: number): string {
  const sign = paise < 0 ? '-' : ''
  const absolute = Math.abs(Math.round(paise))
  return `${sign}${Math.floor(absolute / 100)}.${String(absolute % 100).padStart(2, '0')}`
}

export function formatInr(value: string | number | null | undefined): string {
  const amount = toPaise(value) / 100
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount)
}

const ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
const TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']

function belowThousand(value: number): string {
  const hundred = Math.floor(value / 100)
  const rest = value % 100
  const parts: string[] = []
  if (hundred) parts.push(`${ONES[hundred]} hundred`)
  if (rest < 20) parts.push(ONES[rest])
  else parts.push(`${TENS[Math.floor(rest / 10)]}${ONES[rest % 10] ? ` ${ONES[rest % 10]}` : ''}`)
  return parts.filter(Boolean).join(' ')
}

export function amountInWords(value: string | number): string {
  const paise = Math.abs(toPaise(value))
  const rupees = Math.floor(paise / 100)
  const coins = paise % 100
  if (rupees === 0 && coins === 0) return 'Zero rupees only'
  const scales = [
    { value: 10000000, name: 'crore' },
    { value: 100000, name: 'lakh' },
    { value: 1000, name: 'thousand' },
  ]
  let remaining = rupees
  const words: string[] = []
  for (const scale of scales) {
    const count = Math.floor(remaining / scale.value)
    if (count) {
      words.push(`${belowThousand(count)} ${scale.name}`)
      remaining %= scale.value
    }
  }
  if (remaining) words.push(belowThousand(remaining))
  const rupeeWords = words.join(' ') || 'zero'
  const coinWords = coins ? ` and ${belowThousand(coins)} paise` : ''
  return `${rupeeWords.charAt(0).toUpperCase()}${rupeeWords.slice(1)} rupees${coinWords} only`
}
