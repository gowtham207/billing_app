import { useQuery } from '@tanstack/react-query'
import { Building2, Boxes, GitBranch, Receipt, Users } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { BrandLockup } from '@/components/brand/BrandMark'
import { Button, Field, StatusBadge, useToast } from '@/components/common/ui'
import { useSession } from '@/hooks/session'
import { apiError } from '@/services/api'
import { organizationService } from '@/services/organization.service'
import type { Membership } from '@/types/api'

export function LoginPage() {
  const session = useSession()
  const navigate = useNavigate()
  const toast = useToast()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  if (session.accessToken) return <Navigate to={needsWorkspaceChoice(session) ? '/select-organization' : '/'} replace />
  return (
    <AuthCard title="Sign in" subtitle="Use your work email to open the workspace.">
      <form className="space-y-3" onSubmit={async (event) => {
        event.preventDefault()
        try {
          const profile = await session.login(email, password)
          navigate(needsOrganizationChoice(profile.organizations, profile.organization_id) ? '/select-organization' : '/')
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <Field label="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        <Field label="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        <Button className="w-full" type="submit">Sign in</Button>
      </form>
    </AuthCard>
  )
}

export function needsOrganizationChoice(organizations: Membership[], organizationId: string | null) {
  const active = organizations.filter((organization) => organization.member_status === 'active')
  return active.length > 1 && !organizationId
}

export function needsWorkspaceChoice(session: { organizations: Membership[]; organizationId: string | null; branchChosen: boolean }) {
  return needsOrganizationChoice(session.organizations, session.organizationId) || (Boolean(session.organizationId) && !session.branchChosen)
}

export function SelectOrganizationPage() {
  const session = useSession()
  const navigate = useNavigate()
  const toast = useToast()
  const [pending, setPending] = useState('')
  const [changingOrganization, setChangingOrganization] = useState(false)
  const choosingOrganization = changingOrganization || needsOrganizationChoice(session.organizations, session.organizationId)
  const branches = useQuery({
    queryKey: ['branches', session.organizationId],
    enabled: Boolean(session.organizationId) && !choosingOrganization,
    queryFn: () => organizationService.branches(session.organizationId!),
  })
  useEffect(() => {
    if (choosingOrganization || !branches.data || session.branchChosen) return
    if (branches.data.length === 0) session.skipBranch()
    if (branches.data.length === 1) session.setBranchId(branches.data[0].id)
  }, [branches.data, choosingOrganization, session])
  if (!session.ready) return <p className="grid min-h-screen place-items-center bg-canvas text-sm text-muted">Loading session…</p>
  if (!session.accessToken) return <Navigate to="/login" replace />
  if (!needsWorkspaceChoice(session)) return <Navigate to="/" replace />
  const activeOrganizations = session.organizations.filter((organization) => organization.member_status === 'active')
  const currentOrganization = activeOrganizations.find((organization) => organization.id === session.organizationId)
  return (
    <AuthCard
      title={choosingOrganization ? 'Choose an organization' : 'Choose a branch'}
      subtitle={choosingOrganization ? 'This account belongs to more than one organization.' : `Select the branch for ${currentOrganization?.display_name || 'this organization'}.`}
    >
      {choosingOrganization ? (
        <div className="space-y-2">
          {session.organizations.map((organization) => {
            const selectable = organization.member_status === 'active'
            return (
              <button
                key={organization.id}
                type="button"
                disabled={!selectable || pending === organization.id}
                className="flex w-full items-center gap-3 rounded-xl border border-line px-3 py-3 text-left hover:bg-brand/10 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={async () => {
                  setPending(organization.id)
                  try {
                    await session.switchOrganization(organization.id)
                    setChangingOrganization(false)
                  } catch (error) {
                    toast(apiError(error), 'error')
                  } finally {
                    setPending('')
                  }
                }}
              >
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-brand/10 text-brand"><Building2 size={18} /></span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">{organization.display_name}</span>
                  <span className="block truncate text-xs text-muted">{organization.code}</span>
                </span>
                <StatusBadge value={organization.member_status} />
              </button>
            )
          })}
        </div>
      ) : (
        <div className="space-y-2">
          {branches.isLoading ? <p className="text-sm text-muted">Loading branches…</p> : null}
          {(branches.data ?? []).map((branch) => (
            <button
              key={branch.id}
              type="button"
              className="flex w-full items-center gap-3 rounded-xl border border-line px-3 py-3 text-left hover:bg-brand/10"
              onClick={() => {
                session.setBranchId(branch.id)
                navigate('/')
              }}
            >
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-brand/10 text-brand"><GitBranch size={18} /></span>
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium">{branch.name}</span>
                <span className="block truncate text-xs text-muted">{branch.code}</span>
              </span>
            </button>
          ))}
          {activeOrganizations.length > 1 ? <Button className="w-full" variant="secondary" onClick={() => setChangingOrganization(true)}>Change organization</Button> : null}
        </div>
      )}
      <Button className="mt-4 w-full" variant="ghost" onClick={() => session.logout().then(() => navigate('/login'))}>Sign out</Button>
    </AuthCard>
  )
}

function AuthCard({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,0.9fr)_minmax(22rem,1fr)]">
      <aside className="hidden flex-col justify-between bg-sidebar px-10 py-12 text-white lg:flex">
        <BrandLockup tone="light" />
        <div className="max-w-md">
          <p className="text-3xl leading-tight font-semibold tracking-tight">One Platform. Every Business Operation.</p>
          <ul className="mt-8 space-y-4 text-sm text-white/75">
            <li className="flex items-center gap-3"><Users size={16} className="text-cyan" /> CRM pipeline and customer records</li>
            <li className="flex items-center gap-3"><Boxes size={16} className="text-cyan" /> Inventory, stock, and warehouses</li>
            <li className="flex items-center gap-3"><Receipt size={16} className="text-cyan" /> Billing, payments, and reports</li>
          </ul>
        </div>
        <p className="text-xs text-white/50">PeakSuite by Technology Peak</p>
      </aside>
      <div className="flex items-center justify-center bg-canvas p-4 sm:p-8">
        <div className="panel w-full max-w-md p-6 sm:p-8">
          <div className="mb-6 lg:hidden">
            <BrandLockup />
            <p className="mt-3 text-sm text-muted">One Platform. Every Business Operation.</p>
          </div>
          <h1 className="text-xl font-semibold">{title}</h1>
          <p className="mt-1 mb-5 text-sm text-muted">{subtitle}</p>
          {children}
        </div>
      </div>
    </div>
  )
}
