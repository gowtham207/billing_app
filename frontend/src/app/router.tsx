import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { useSession } from '@/hooks/session'
import { LoginPage, needsOrganizationChoice, SelectOrganizationPage } from '@/features/auth/AuthPages'
import { BillingHomePage, BillingSettingsPage } from '@/features/billing/BillingSettingsPage'
import { InvoiceDetailPage, InvoiceEditorPage, InvoicesPage } from '@/features/billing/InvoicePages'
import { ActivitiesPage, KanbanPage, OpportunitiesPage } from '@/features/crm/kanban/KanbanPage'
import { CustomerDetailPage, CustomersPage } from '@/features/crm/customers/CustomersPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { CategoriesPage, MovementsPage, ProductDetailPage, ProductsPage, SimpleCatalogPage, StockPage } from '@/features/inventory/InventoryPages'
import { DocumentPage, ExpensesPage, OrganizationSettingsPage, PaymentsPage, PurchasingPage, ReportsPage, RolesPage, UsersPage } from '@/features/operations/OperationsPages'

function Guard({ children }: { children: ReactNode }) {
  const session = useSession()
  if (!session.ready) return <p className="grid min-h-screen place-items-center bg-canvas text-sm text-muted">Loading session…</p>
  if (!session.accessToken) return <Navigate to="/login" replace />
  if (needsOrganizationChoice(session.organizations, session.organizationId)) return <Navigate to="/select-organization" replace />
  return children
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<Navigate to="/login" replace />} />
      <Route path="/select-organization" element={<SelectOrganizationPage />} />
      <Route element={<Guard><AppShell /></Guard>}>
        <Route index element={<DashboardPage />} />
        <Route path="crm/customers" element={<CustomersPage />} />
        <Route path="crm/customers/:id" element={<CustomerDetailPage />} />
        <Route path="crm/leads" element={<KanbanPage />} />
        <Route path="crm/opportunities" element={<OpportunitiesPage />} />
        <Route path="crm/activities" element={<ActivitiesPage />} />
        <Route path="crm/kanban" element={<KanbanPage />} />
        <Route path="inventory/products" element={<ProductsPage />} />
        <Route path="inventory/products/:id" element={<ProductDetailPage />} />
        <Route path="inventory/categories" element={<CategoriesPage />} />
        <Route path="inventory/brands" element={<SimpleCatalogPage title="Brands" kind="brands" />} />
        <Route path="inventory/units" element={<SimpleCatalogPage title="Units" kind="units" />} />
        <Route path="inventory/warehouses" element={<SimpleCatalogPage title="Warehouses" kind="warehouses" />} />
        <Route path="inventory/stock" element={<StockPage />} />
        <Route path="inventory/movements" element={<MovementsPage />} />
        <Route path="billing" element={<BillingHomePage />} />
        <Route path="billing/quotations" element={<DocumentPage title="Quotations" path="/billing/quotations" createPath="/billing/quotations" action="send" />} />
        <Route path="billing/orders" element={<DocumentPage title="Sales orders" path="/billing/orders" createPath="/billing/orders" action="confirm" />} />
        <Route path="billing/invoices" element={<InvoicesPage />} />
        <Route path="billing/invoices/new" element={<InvoiceEditorPage />} />
        <Route path="billing/invoices/:id/edit" element={<InvoiceEditorPage />} />
        <Route path="billing/invoices/:id" element={<InvoiceDetailPage />} />
        <Route path="billing/payments" element={<PaymentsPage />} />
        <Route path="billing/credit-notes" element={<DocumentPage title="Credit notes" path="/billing/credit-notes" />} />
        <Route path="billing/settings" element={<BillingSettingsPage />} />
        <Route path="purchasing" element={<PurchasingPage />} />
        <Route path="expenses" element={<ExpensesPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="settings/organization" element={<OrganizationSettingsPage />} />
        <Route path="settings/users" element={<UsersPage />} />
        <Route path="settings/roles" element={<RolesPage />} />
      </Route>
    </Routes>
  )
}
