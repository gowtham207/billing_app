export type Page<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

export type User = {
  id: string
  email: string
  full_name: string
  phone: string | null
  is_platform_admin: boolean
  is_active: boolean
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  organization_id: string | null
  user?: User
}

export type Membership = {
  id: string
  code: string
  legal_name?: string
  display_name: string
  status: string
  member_status: string
}

export type MeResponse = {
  user: User
  organization_id: string | null
  organizations: Membership[]
  roles: string[]
  permissions: string[]
}

export type Address = {
  id: string
  address_type: 'billing' | 'shipping' | 'registered' | 'other'
  line1: string
  line2: string | null
  city: string | null
  state_region: string | null
  postal_code: string | null
  country_code: string
  is_default?: boolean
}

export type PartyAddress = {
  name: string
  line1: string
  line2: string
  city: string
  district: string
  state: string
  postal_code: string
  country: string
  gstin: string
  phone: string
  email: string
}

export type Customer = {
  id: string
  customer_code: string
  customer_type: 'individual' | 'business'
  display_name: string
  legal_name: string | null
  email: string | null
  phone: string | null
  tax_registration_no: string | null
  credit_limit: string
  opening_balance: string
  is_active: boolean
}

export type Lead = {
  id: string
  lead_code: string
  company_name: string | null
  contact_name: string
  email: string | null
  phone: string | null
  source_id: string | null
  status_id: string | null
  estimated_value: string | null
  assigned_to: string | null
  created_at: string
}

export type Opportunity = {
  id: string
  opportunity_code: string
  title: string
  customer_id: string | null
  stage_id: string | null
  expected_value: string
  probability: string | null
  expected_close_date: string | null
  owner_user_id: string | null
}

export type Activity = {
  id: string
  activity_type: string
  subject: string
  description: string | null
  customer_id: string | null
  lead_id: string | null
  due_at: string | null
  completed_at: string | null
  assigned_to: string | null
  created_at: string
}

export type StatusDefinition = {
  id: string
  status_group_id: string
  status_key: string
  label: string
  sort_order: number
  is_initial: boolean
  is_final: boolean
  color: string | null
  is_active: boolean
}

export type StatusGroup = {
  id: string
  module_key: string
  entity_key: string
  name: string
}

export type Category = {
  id: string
  parent_id: string | null
  name: string
  description: string | null
  is_active: boolean
}

export type Brand = { id: string; name: string }
export type Unit = { id: string; name: string; symbol: string; decimal_places: number }
export type Warehouse = { id: string; code: string; name: string; address: string | null; is_active: boolean; branch_id: string | null }

export type Product = {
  id: string
  category_id: string | null
  brand_id: string | null
  unit_id: string
  product_type: 'stock' | 'service' | 'non_stock'
  sku: string
  barcode: string | null
  name: string
  description: string | null
  purchase_price: string
  selling_price: string
  reorder_level: string
  track_inventory: boolean
  is_active: boolean
  category?: { id: string; name: string; parent_id: string | null } | null
}

export type TaxRate = {
  id: string
  tax_code: string
  name: string
  rate: string
  is_active: boolean
}

export type BillingSettings = {
  organization_id: string
  default_currency: string
  tax_inclusive_pricing: boolean
  allow_partial_payment: boolean
  allow_overpayment: boolean
  default_payment_terms_days: number
  default_due_days: number
  decimal_places: number
  rounding_method: 'half_up' | 'half_even' | 'up' | 'down'
}

export type Organization = {
  id: string
  code: string
  legal_name: string
  display_name: string
  email: string | null
  phone: string | null
  website: string | null
  tax_registration_no: string | null
  default_currency: string
  timezone: string
  status: string
}

export type Branch = {
  id: string
  code: string
  name: string
  email: string | null
  phone: string | null
  is_head_office: boolean
  is_active: boolean
}

export type Invoice = {
  id: string
  branch_id: string | null
  customer_id: string
  sales_order_id: string | null
  invoice_no: string
  invoice_date: string
  due_date: string | null
  status_id: string | null
  currency: string
  subtotal: string
  discount_total: string
  tax_total: string
  shipping_amount: string
  grand_total: string
  amount_paid: string
  balance_due: string | null
  billing_snapshot: BillingSnapshot | null
  notes: string | null
  issued_at: string | null
}

export type InvoiceItem = {
  id: string
  invoice_id: string
  product_id: string | null
  description: string
  quantity: string
  unit_price: string
  discount_amount: string
  tax_amount: string
  line_total: string
  warehouse_id: string | null
}

export type GstLine = {
  product_id: string | null
  description: string
  sku: string
  hsn: string
  quantity: string
  unit: string
  unit_price: string
  discount: string
  gst_rate: number
  exempt: boolean
  taxable: string
  cgst: string
  sgst: string
  igst: string
  total: string
  warehouse_id: string | null
}

export type BillingSnapshot = {
  from?: PartyAddress
  to?: PartyAddress
  bill_to?: PartyAddress
  place_of_supply?: string
  reference_no?: string
  payment_terms?: string
  treatment?: 'intra' | 'inter' | 'exempt'
  lines?: GstLine[]
  upi_id?: string
  merchant_name?: string
}

export type Payment = {
  id: string
  customer_id: string | null
  payment_no: string
  payment_date: string
  amount: string
  payment_status: string
  reference_no: string | null
  notes: string | null
}

export type Role = {
  id: string
  role_key: string
  name: string
  description: string | null
  is_system: boolean
}

export type Permission = {
  id: string
  permission_key: string
  module_key: string
  description: string | null
}

export type Member = {
  id: string
  user_id: string
  member_status: string
  joined_at: string | null
}

export type NotificationItem = {
  id: string
  title?: string
  body?: string
  message?: string
  is_read: boolean
  created_at: string
}
