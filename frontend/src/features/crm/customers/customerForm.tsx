import type { FormEvent } from 'react'
import { Button, Field, SelectField, TextArea } from '@/components/common/ui'
import { customerService } from '@/services/customer.service'

export type CustomerForm = {
  display_name: string
  customer_code: string
  customer_type: 'individual' | 'business'
  email: string
  phone: string
  alternate_phone: string
  tax_registration_no: string
  pan: string
  line1: string
  shipping_line1: string
  state_region: string
  district: string
  city: string
  postal_code: string
  notes: string
  is_active: boolean
}

export function blankCustomer(): CustomerForm {
  return {
    display_name: '',
    customer_code: '',
    customer_type: 'business',
    email: '',
    phone: '',
    alternate_phone: '',
    tax_registration_no: '',
    pan: '',
    line1: '',
    shipping_line1: '',
    state_region: '',
    district: '',
    city: '',
    postal_code: '',
    notes: '',
    is_active: true,
  }
}

export async function saveCustomer(form: CustomerForm, editingId?: string) {
  const body = {
    customer_code: form.customer_code || `CUS-${Date.now().toString().slice(-6)}`,
    customer_type: form.customer_type,
    display_name: form.display_name,
    email: form.email || null,
    phone: form.phone || null,
    tax_registration_no: form.tax_registration_no || null,
    is_active: form.is_active,
  }
  const customer = editingId ? await customerService.update(editingId, body) : await customerService.create(body)
  if (form.line1) await customerService.addAddress(customer.id, addressBody(customer.id, 'billing', form.line1, form))
  if (form.shipping_line1) await customerService.addAddress(customer.id, addressBody(customer.id, 'shipping', form.shipping_line1, form))
  const note = [form.notes, form.pan && `PAN: ${form.pan}`, form.alternate_phone && `Alternate phone: ${form.alternate_phone}`, form.district && `District: ${form.district}`].filter(Boolean).join('\n')
  if (note) await customerService.addNote(customer.id, note)
  return customer
}

function addressBody(customerId: string, addressType: string, line1: string, form: CustomerForm) {
  return { customer_id: customerId, address_type: addressType, line1, city: form.city || null, state_region: form.state_region || null, postal_code: form.postal_code || null, country_code: 'IN' }
}

export function CustomerFormFields({ form, onChange, onSubmit, pending, submitLabel }: {
  form: CustomerForm
  onChange: (form: CustomerForm) => void
  onSubmit: (event: FormEvent) => void
  pending?: boolean
  submitLabel: string
}) {
  return (
    <form className="grid gap-3 md:grid-cols-2" onSubmit={onSubmit}>
      <Field label="Customer name" value={form.display_name} onChange={(event) => onChange({ ...form, display_name: event.target.value })} required />
      <Field label="Customer code" value={form.customer_code} placeholder="Auto-generated if empty" onChange={(event) => onChange({ ...form, customer_code: event.target.value })} />
      <SelectField label="Customer type" value={form.customer_type} onChange={(event) => onChange({ ...form, customer_type: event.target.value as CustomerForm['customer_type'] })}>
        <option value="individual">Individual</option>
        <option value="business">Business</option>
      </SelectField>
      <Field label="Email" type="email" value={form.email} onChange={(event) => onChange({ ...form, email: event.target.value })} />
      <Field label="Mobile number" value={form.phone} onChange={(event) => onChange({ ...form, phone: event.target.value })} />
      <Field label="Alternate mobile number" value={form.alternate_phone} onChange={(event) => onChange({ ...form, alternate_phone: event.target.value })} />
      <Field label="GSTIN" value={form.tax_registration_no} onChange={(event) => onChange({ ...form, tax_registration_no: event.target.value })} />
      <Field label="PAN" value={form.pan} onChange={(event) => onChange({ ...form, pan: event.target.value })} />
      <Field label="Billing address" value={form.line1} onChange={(event) => onChange({ ...form, line1: event.target.value })} />
      <Field label="Shipping address" value={form.shipping_line1} onChange={(event) => onChange({ ...form, shipping_line1: event.target.value })} />
      <Field label="State" value={form.state_region} onChange={(event) => onChange({ ...form, state_region: event.target.value })} />
      <Field label="District" value={form.district} onChange={(event) => onChange({ ...form, district: event.target.value })} />
      <Field label="City" value={form.city} onChange={(event) => onChange({ ...form, city: event.target.value })} />
      <Field label="Pincode" value={form.postal_code} onChange={(event) => onChange({ ...form, postal_code: event.target.value })} />
      <SelectField label="Status" value={form.is_active ? 'active' : 'inactive'} onChange={(event) => onChange({ ...form, is_active: event.target.value === 'active' })}>
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
      </SelectField>
      <div className="md:col-span-2"><TextArea label="Notes" value={form.notes} onChange={(event) => onChange({ ...form, notes: event.target.value })} /></div>
      <div className="md:col-span-2 flex justify-end"><Button type="submit" disabled={pending}>{pending ? 'Saving…' : submitLabel}</Button></div>
    </form>
  )
}
