export type BillingExtras = {
  upiId: string
  merchantName: string
  upiEnabled: boolean
  pan: string
  gstEnabled: boolean
  defaultRate: string
  logoDataUrl: string
  placeOfSupply: string
}

const empty: BillingExtras = {
  upiId: '',
  merchantName: '',
  upiEnabled: false,
  pan: '',
  gstEnabled: true,
  defaultRate: '18',
  logoDataUrl: '',
  placeOfSupply: '',
}

export function readExtras(organizationId: string): BillingExtras {
  const raw = localStorage.getItem(`billing.extras.${organizationId}`)
  return raw ? { ...empty, ...JSON.parse(raw) } : empty
}

export function writeExtras(organizationId: string, extras: BillingExtras) {
  localStorage.setItem(`billing.extras.${organizationId}`, JSON.stringify(extras))
}
