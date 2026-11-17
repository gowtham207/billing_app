import { fromPaise, toPaise } from '@/utils/money'

export type GstSplit = {
  taxablePaise: number
  cgstPaise: number
  sgstPaise: number
  igstPaise: number
  taxPaise: number
  totalPaise: number
  treatment: 'intra' | 'inter' | 'exempt'
}

function sameState(seller: string, buyer: string): boolean {
  const left = seller.trim().toLowerCase()
  const right = buyer.trim().toLowerCase()
  return left.length > 0 && left === right
}

export function previewGst(input: {
  quantity: string | number
  unitPrice: string | number
  discount: string | number
  ratePercent: number
  sellerState: string
  buyerState: string
  inclusive: boolean
  exempt: boolean
}): GstSplit {
  const gross = toPaise(input.quantity) / 100 * toPaise(input.unitPrice) - toPaise(input.discount)
  const grossPaise = Math.round(gross)
  if (input.exempt || input.ratePercent <= 0) {
    return { taxablePaise: grossPaise, cgstPaise: 0, sgstPaise: 0, igstPaise: 0, taxPaise: 0, totalPaise: grossPaise, treatment: 'exempt' }
  }
  const rate = input.ratePercent
  let taxable = grossPaise
  let tax = 0
  if (input.inclusive) {
    taxable = Math.round(grossPaise * 10000 / (10000 + Math.round(rate * 100)))
    tax = grossPaise - taxable
  } else {
    tax = Math.round(grossPaise * rate / 100)
  }
  const intra = sameState(input.sellerState, input.buyerState)
  if (intra) {
    const cgst = Math.floor(tax / 2)
    return {
      taxablePaise: taxable,
      cgstPaise: cgst,
      sgstPaise: tax - cgst,
      igstPaise: 0,
      taxPaise: tax,
      totalPaise: input.inclusive ? grossPaise : taxable + tax,
      treatment: 'intra',
    }
  }
  return {
    taxablePaise: taxable,
    cgstPaise: 0,
    sgstPaise: 0,
    igstPaise: tax,
    taxPaise: tax,
    totalPaise: input.inclusive ? grossPaise : taxable + tax,
    treatment: 'inter',
  }
}

export function paiseFields(split: GstSplit) {
  return {
    taxable: fromPaise(split.taxablePaise),
    cgst: fromPaise(split.cgstPaise),
    sgst: fromPaise(split.sgstPaise),
    igst: fromPaise(split.igstPaise),
    tax: fromPaise(split.taxPaise),
    total: fromPaise(split.totalPaise),
  }
}
