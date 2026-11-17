import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { adminApi } from '@/api'
import { PageHeader } from '@/ui'

const cards = [
  { key: 'organizations', label: 'Organizations', to: '/organizations' },
  { key: 'users', label: 'Users', to: '/users' },
  { key: 'permissions', label: 'Permissions', to: '/permissions' },
] as const

export function HomePage() {
  const organizations = useQuery({ queryKey: ['admin-orgs'], queryFn: () => adminApi.organizations() })
  const users = useQuery({ queryKey: ['admin-users'], queryFn: () => adminApi.users() })
  const permissions = useQuery({ queryKey: ['admin-permissions'], queryFn: () => adminApi.permissions() })
  const totals = {
    organizations: organizations.data?.total ?? 0,
    users: users.data?.total ?? 0,
    permissions: permissions.data?.length ?? 0,
  }
  return (
    <div>
      <PageHeader title="Overview" subtitle="Platform records for PeakSuite." />
      <div className="grid gap-3 sm:grid-cols-3">
        {cards.map((card) => (
          <Link key={card.key} to={card.to} className="panel border-l-4 border-l-brand p-4">
            <p className="text-sm text-muted">{card.label}</p>
            <p className="mt-2 text-2xl font-semibold tabular-nums">{totals[card.key]}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
