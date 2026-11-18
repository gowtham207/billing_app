import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Button, DataTable, Field, PageHeader, SelectField, useToast } from '@/components/common/ui'
import { readExtras, writeExtras, type BillingExtras } from '@/features/billing/extras'
import { useSession } from '@/hooks/session'
import { apiError } from '@/services/api'
import { billingService } from '@/services/billing.service'
import { organizationService } from '@/services/organization.service'

const STANDARD_RATES = [0, 5, 12, 18, 28]

export function BillingSettingsPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const settings = useQuery({ queryKey: ['billing-settings'], queryFn: billingService.settings })
  const rates = useQuery({ queryKey: ['tax-rates'], queryFn: billingService.taxRates })
  const organization = useQuery({ queryKey: ['organization', session.organizationId], enabled: Boolean(session.organizationId), queryFn: () => organizationService.get(session.organizationId!) })
  const addresses = useQuery({ queryKey: ['org-addresses', session.organizationId], enabled: Boolean(session.organizationId), queryFn: () => organizationService.addresses(session.organizationId!) })
  const [company, setCompany] = useState({ legal_name: '', display_name: '', email: '', phone: '', website: '', tax_registration_no: '', line1: '', line2: '', city: '', state_region: '', postal_code: '', country_code: 'IN' })
  const [billing, setBilling] = useState<{ tax_inclusive_pricing: boolean; default_due_days: number; default_payment_terms_days: number; rounding_method: 'half_up' | 'half_even' | 'up' | 'down' }>({ tax_inclusive_pricing: false, default_due_days: 0, default_payment_terms_days: 0, rounding_method: 'half_up' })
  const [extras, setExtras] = useState<BillingExtras | null>(null)
  const address = addresses.data?.find((item) => item.address_type === 'billing') ?? addresses.data?.[0]

  useEffect(() => {
    if (!organization.data) return
    setCompany({
      legal_name: organization.data.legal_name,
      display_name: organization.data.display_name,
      email: organization.data.email ?? '',
      phone: organization.data.phone ?? '',
      website: organization.data.website ?? '',
      tax_registration_no: organization.data.tax_registration_no ?? '',
      line1: address?.line1 ?? '',
      line2: address?.line2 ?? '',
      city: address?.city ?? '',
      state_region: address?.state_region ?? '',
      postal_code: address?.postal_code ?? '',
      country_code: address?.country_code ?? 'IN',
    })
  }, [organization.data, address])
  useEffect(() => {
    if (!settings.data) return
    setBilling({
      tax_inclusive_pricing: settings.data.tax_inclusive_pricing,
      default_due_days: settings.data.default_due_days,
      default_payment_terms_days: settings.data.default_payment_terms_days,
      rounding_method: settings.data.rounding_method,
    })
  }, [settings.data])
  useEffect(() => {
    if (session.organizationId) setExtras(readExtras(session.organizationId))
  }, [session.organizationId])

  const save = useMutation({
    mutationFn: async () => {
      if (!session.organizationId || !extras) return
      await organizationService.update(session.organizationId, {
        legal_name: company.legal_name,
        display_name: company.display_name,
        email: company.email || null,
        phone: company.phone || null,
        website: company.website || null,
        tax_registration_no: company.tax_registration_no || null,
      })
      const addressBody = { address_type: 'billing' as const, line1: company.line1 || 'Address', line2: company.line2 || null, city: company.city || null, state_region: company.state_region || null, postal_code: company.postal_code || null, country_code: company.country_code || 'IN', is_default: true }
      if (address) await organizationService.updateAddress(address.id, addressBody)
      else await organizationService.createAddress(session.organizationId, addressBody)
      await billingService.updateSettings(billing)
      writeExtras(session.organizationId, extras)
    },
    onSuccess: () => {
      toast('Billing settings saved')
      queryClient.invalidateQueries({ queryKey: ['organization'] })
      queryClient.invalidateQueries({ queryKey: ['billing-settings'] })
    },
    onError: (error) => toast(apiError(error), 'error'),
  })

  if (!extras) return null
  return (
    <div className="space-y-4">
      <PageHeader title="Billing settings" subtitle="Company profile, address, tax rates, and invoice defaults are saved through the API. UPI ID, PAN, and logo stay in this browser because the billing settings API does not have those fields yet." />
      <form className="grid gap-4" onSubmit={(event) => { event.preventDefault(); save.mutate() }}>
        <section className="grid gap-3 panel p-4 md:grid-cols-2">
          <h2 className="md:col-span-2 font-medium">Company / from address</h2>
          <Field label="Company name" value={company.display_name} onChange={(event) => setCompany({ ...company, display_name: event.target.value })} />
          <Field label="Legal name" value={company.legal_name} onChange={(event) => setCompany({ ...company, legal_name: event.target.value })} />
          <Field label="Address line 1" value={company.line1} onChange={(event) => setCompany({ ...company, line1: event.target.value })} />
          <Field label="Address line 2" value={company.line2} onChange={(event) => setCompany({ ...company, line2: event.target.value })} />
          <Field label="City" value={company.city} onChange={(event) => setCompany({ ...company, city: event.target.value })} />
          <Field label="State" value={company.state_region} onChange={(event) => setCompany({ ...company, state_region: event.target.value })} />
          <Field label="Country" value={company.country_code} onChange={(event) => setCompany({ ...company, country_code: event.target.value })} />
          <Field label="Pincode" value={company.postal_code} onChange={(event) => setCompany({ ...company, postal_code: event.target.value })} />
          <Field label="GSTIN" value={company.tax_registration_no} onChange={(event) => setCompany({ ...company, tax_registration_no: event.target.value })} />
          <Field label="PAN" value={extras.pan} onChange={(event) => setExtras({ ...extras, pan: event.target.value })} />
          <Field label="Email" value={company.email} onChange={(event) => setCompany({ ...company, email: event.target.value })} />
          <Field label="Phone" value={company.phone} onChange={(event) => setCompany({ ...company, phone: event.target.value })} />
          <Field label="Website" value={company.website} onChange={(event) => setCompany({ ...company, website: event.target.value })} />
          <label className="text-sm">Company logo<input className="mt-1 block" type="file" accept="image/*" onChange={(event) => {
            const file = event.target.files?.[0]
            if (!file) return
            const reader = new FileReader()
            reader.onload = () => setExtras({ ...extras, logoDataUrl: String(reader.result) })
            reader.readAsDataURL(file)
          }} /></label>
        </section>
        <section className="grid gap-3 panel p-4 md:grid-cols-2">
          <h2 className="md:col-span-2 font-medium">GST configuration</h2>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={extras.gstEnabled} onChange={(event) => setExtras({ ...extras, gstEnabled: event.target.checked })} /> GST enabled</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={billing.tax_inclusive_pricing} onChange={(event) => setBilling({ ...billing, tax_inclusive_pricing: event.target.checked })} /> GST inclusive pricing</label>
          <div className="md:col-span-2 grid gap-3 rounded-lg border border-line p-3 md:grid-cols-2">
            <h3 className="md:col-span-2 text-sm font-medium">Invoice discount</h3>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={extras.discountEnabled} onChange={(event) => setExtras({ ...extras, discountEnabled: event.target.checked })} /> Show discount on invoices and quotations</label>
            <Field label="Default discount (%)" type="number" min="0" max="100" step="0.01" value={extras.defaultDiscount} disabled={!extras.discountEnabled} onChange={(event) => setExtras({ ...extras, defaultDiscount: event.target.value })} />
            <p className="md:col-span-2 text-xs text-muted">Choosing a product fills the line discount from this percent. Turn the option off to hide the discount column on the invoice and quotation.</p>
          </div>
          <SelectField label="Default GST rate" value={extras.defaultRate} onChange={(event) => setExtras({ ...extras, defaultRate: event.target.value })}>
            {STANDARD_RATES.map((rate) => <option key={rate} value={rate}>{rate}%</option>)}
          </SelectField>
          <Field label="Default place of supply" value={extras.placeOfSupply} onChange={(event) => setExtras({ ...extras, placeOfSupply: event.target.value })} />
          <Field label="Payment terms days" type="number" value={billing.default_payment_terms_days} onChange={(event) => setBilling({ ...billing, default_payment_terms_days: Number(event.target.value) })} />
          <Field label="Default due days" type="number" value={billing.default_due_days} onChange={(event) => setBilling({ ...billing, default_due_days: Number(event.target.value) })} />
          <div className="md:col-span-2">
            <p className="mb-2 text-sm text-muted">Intra-state invoices split the rate into CGST and SGST. Inter-state invoices use IGST only. Existing rates:</p>
            <DataTable
              rows={rates.data?.items ?? []}
              empty="No tax rates yet."
              rowKey={(rate) => rate.id}
              columns={[
                { key: 'tax_code', label: 'Code', render: (rate) => rate.tax_code },
                { key: 'name', label: 'Name', render: (rate) => rate.name },
                { key: 'rate', label: 'Rate', render: (rate) => `${rate.rate}%` },
              ]}
            />
            <div className="flex flex-wrap gap-2">
              {STANDARD_RATES.map((rate) => <Button key={rate} type="button" variant="secondary" onClick={() => billingService.createTaxRate({ tax_code: `GST${rate}`, name: `GST ${rate}%`, rate }).then(() => queryClient.invalidateQueries({ queryKey: ['tax-rates'] })).catch((error) => toast(apiError(error), 'error'))}>Add {rate}%</Button>)}
            </div>
          </div>
        </section>
        <section className="grid gap-3 panel p-4 md:grid-cols-2">
          <h2 className="md:col-span-2 font-medium">UPI</h2>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={extras.upiEnabled} onChange={(event) => setExtras({ ...extras, upiEnabled: event.target.checked })} /> UPI payment enabled</label>
          <Field label="UPI ID" value={extras.upiId} onChange={(event) => setExtras({ ...extras, upiId: event.target.value })} />
          <Field label="Merchant name" value={extras.merchantName} onChange={(event) => setExtras({ ...extras, merchantName: event.target.value })} />
        </section>
        <Button type="submit" disabled={!session.can('settings.write') || save.isPending}>Save settings</Button>
      </form>
    </div>
  )
}

export function BillingHomePage() {
  const invoices = useQuery({ queryKey: ['invoices'], queryFn: () => import('@/services/billing.service').then((module) => module.invoiceService.list()) })
  const total = (invoices.data?.items ?? []).reduce((sum, invoice) => sum + Number(invoice.grand_total), 0)
  const balance = (invoices.data?.items ?? []).reduce((sum, invoice) => sum + Number(invoice.balance_due ?? 0), 0)
  return (
    <div>
      <PageHeader title="Billing dashboard" />
      <div className="grid gap-3 md:grid-cols-3">
        <article className="panel p-4"><p className="text-sm text-muted">Invoices</p><p className="text-2xl font-semibold">{invoices.data?.total ?? 0}</p></article>
        <article className="panel p-4"><p className="text-sm text-muted">Listed total</p><p className="text-2xl font-semibold">{total.toFixed(2)}</p></article>
        <article className="panel p-4"><p className="text-sm text-muted">Listed balance</p><p className="text-2xl font-semibold">{balance.toFixed(2)}</p></article>
      </div>
    </div>
  )
}
