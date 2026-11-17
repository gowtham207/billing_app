import type { ReactElement } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, DataTable, PageHeader, Skeleton } from '@/components/common/ui'
import { dashboardService } from '@/services/dashboard.service'
import { formatInr } from '@/utils/money'

export function DashboardPage() {
  const overview = useQuery({ queryKey: ['overview'], queryFn: dashboardService.overview })
  const sales = useQuery({ queryKey: ['sales-summary'], queryFn: dashboardService.sales })
  const outstanding = useQuery({ queryKey: ['outstanding'], queryFn: dashboardService.outstanding })
  const customers = useQuery({ queryKey: ['customer-summary'], queryFn: dashboardService.customers })
  const inventory = useQuery({ queryKey: ['inventory-summary'], queryFn: dashboardService.inventory })
  const chart = useQuery({ queryKey: ['sales-chart'], queryFn: dashboardService.salesChart })
  const invoices = useQuery({ queryKey: ['recent-invoices'], queryFn: dashboardService.recentInvoices })
  const recentCustomers = useQuery({ queryKey: ['recent-customers'], queryFn: dashboardService.recentCustomers })
  const activities = useQuery({ queryKey: ['recent-activities'], queryFn: dashboardService.recentActivities })
  const products = useQuery({ queryKey: ['top-products'], queryFn: dashboardService.topProducts })
  const low = useQuery({ queryKey: ['low-stock'], queryFn: dashboardService.lowStock })
  const loading = overview.isLoading
  const points = (chart.data ?? []).map((row) => ({
    label: String((row as { day?: string; period?: string }).day ?? (row as { period?: string }).period ?? ''),
    total: Number((row as { amount?: number; total?: number }).amount ?? (row as { total?: number }).total ?? 0),
  }))

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Sales, collections, customers, and stock for the selected organization." />
      {loading ? <Skeleton /> : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <Metric label="Total sales" value={formatInr(sales.data?.total ?? overview.data?.revenue ?? 0)} to="/billing" />
          <Metric label="Total invoices" value={String(sales.data?.count ?? 0)} to="/billing/invoices" />
          <Metric label="Pending payments" value={formatInr(outstanding.data?.outstanding ?? overview.data?.outstanding ?? 0)} to="/billing/payments" tone="warning" />
          <Metric label="Total customers" value={String(customers.data?.customers ?? overview.data?.customers ?? 0)} to="/crm/customers" />
          <Metric label="Total products" value={String(inventory.data?.products ?? overview.data?.products ?? 0)} to="/inventory/products" />
          <Metric label="Low stock products" value={String(inventory.data?.low_stock ?? low.data?.length ?? 0)} to="/inventory/stock" tone="warning" />
        </div>
      )}
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Card>
          <h2 className="mb-3 font-medium">Monthly revenue</h2>
          <ChartFrame empty={points.length === 0} emptyLabel="No revenue recorded yet">
            <BarChart data={points}><CartesianGrid strokeDasharray="3 3" stroke="var(--line)" /><XAxis dataKey="label" tick={axisTick} /><YAxis tick={axisTick} /><Tooltip contentStyle={tooltipStyle} /><Bar dataKey="total" fill="var(--brand)" radius={4} /></BarChart>
          </ChartFrame>
        </Card>
        <Card>
          <h2 className="mb-3 font-medium">Sales trend</h2>
          <ChartFrame empty={points.length === 0} emptyLabel="No sales trend yet">
            <LineChart data={points}><CartesianGrid strokeDasharray="3 3" stroke="var(--line)" /><XAxis dataKey="label" tick={axisTick} /><YAxis tick={axisTick} /><Tooltip contentStyle={tooltipStyle} /><Line dataKey="total" stroke="var(--cyan)" strokeWidth={2} dot={false} /></LineChart>
          </ChartFrame>
        </Card>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-2 font-medium">Recent invoices</h2>
          <SimpleList rows={(invoices.data ?? []).map((invoice) => ({ label: `${invoice.invoice_no} · ${formatInr(invoice.grand_total)}`, to: `/billing/invoices/${invoice.id}` }))} empty="No invoices yet" />
        </Card>
        <Card>
          <h2 className="mb-2 font-medium">Recent customers</h2>
          <SimpleList rows={(recentCustomers.data ?? []).map((customer) => ({ label: customer.display_name, to: `/crm/customers/${customer.id}` }))} empty="No customers yet" />
        </Card>
        <Card>
          <h2 className="mb-2 font-medium">Recent activities</h2>
          <SimpleList rows={(activities.data ?? []).map((activity) => ({ label: activity.subject, to: '/crm/activities' }))} empty="No activities yet" />
        </Card>
        <Card>
          <h2 className="mb-2 font-medium">Top-selling products</h2>
          <SimpleList rows={(products.data ?? []).map((row) => ({ label: String(row.name ?? row.product_name ?? row.sku ?? 'Product'), to: typeof row.product_id === 'string' ? `/inventory/products/${row.product_id}` : typeof row.id === 'string' ? `/inventory/products/${row.id}` : '/inventory/products' }))} empty="No posted sales yet" />
        </Card>
      </div>
    </div>
  )
}

const axisTick = { fill: 'var(--muted)', fontSize: 12 }
const tooltipStyle = { background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: 8, color: 'var(--ink)' }

function Metric({ label, value, to, tone = 'brand' }: { label: string; value: string; to: string; tone?: 'brand' | 'warning' }) {
  return (
    <Link to={to} className={`panel block border-l-4 p-4 hover:bg-brand/5 ${tone === 'warning' ? 'border-l-warning' : 'border-l-brand'}`}>
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight">{value}</p>
    </Link>
  )
}

function ChartFrame({ empty, emptyLabel, children }: { empty: boolean; emptyLabel: string; children: ReactElement }) {
  if (empty) return <div className="flex h-64 items-center justify-center text-sm text-muted">{emptyLabel}</div>
  return <div className="h-64"><ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer></div>
}

function SimpleList({ rows, empty }: { rows: { label: string; to: string }[]; empty: string }) {
  return (
    <DataTable
      rows={rows.slice(0, 8)}
      empty={empty}
      rowKey={(row) => row.label}
      columns={[{ key: 'label', label: 'Record', render: (row) => <Link className="text-brand" to={row.to}>{row.label}</Link> }]}
    />
  )
}
