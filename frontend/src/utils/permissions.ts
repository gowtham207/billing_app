const WRITE_ALIASES: Record<string, string> = {
  'customers.create': 'crm.write',
  'customers.update': 'crm.write',
  'customers.delete': 'crm.write',
  'products.create': 'inventory.write',
  'products.update': 'inventory.write',
  'products.delete': 'inventory.write',
  'invoices.create': 'billing.write',
  'invoices.post': 'billing.write',
  'invoices.cancel': 'billing.write',
  'payments.create': 'billing.write',
  'reports.view': 'reports.read',
  'settings.write': 'settings.write',
  'access.manage': 'access.manage',
  'workflows.manage': 'workflows.manage',
}

export function allows(input: { permissions: string[]; roles: string[]; platformAdmin: boolean }, permission: string): boolean {
  if (input.platformAdmin || input.roles.includes('owner')) return true
  const key = WRITE_ALIASES[permission] ?? permission
  return input.permissions.includes(key)
}
