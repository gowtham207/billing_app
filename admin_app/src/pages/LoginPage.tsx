import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { apiError } from '@/api'
import { useSession } from '@/session'
import { Button, Field } from '@/ui'

export function LoginPage() {
  const session = useSession()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  if (session.accessToken && session.user) return <Navigate to="/" replace />
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setPending(true)
    setError('')
    try {
      await session.login(email, password)
    } catch (reason) {
      setError(apiError(reason))
    } finally {
      setPending(false)
    }
  }
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="hidden flex-col justify-between bg-navy p-10 text-white lg:flex">
        <div>
          <p className="text-lg font-semibold">PeakSuite</p>
          <p className="text-sm text-white/60">Technology Peak</p>
        </div>
        <div>
          <h1 className="max-w-md text-4xl font-semibold tracking-tight">Platform administration.</h1>
          <p className="mt-3 max-w-md text-white/70">Organizations, users, branches, roles, and permissions.</p>
        </div>
        <p className="text-sm text-white/50">PeakSuite by Technology Peak</p>
      </section>
      <section className="grid place-items-center bg-canvas p-6">
        <form className="panel w-full max-w-md space-y-4 p-6" onSubmit={submit}>
          <div className="lg:hidden">
            <p className="font-semibold">PeakSuite Admin</p>
            <p className="text-sm text-muted">Platform administration</p>
          </div>
          <h2 className="text-xl font-semibold">Sign in</h2>
          <Field label="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          <Field label="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          <Button className="w-full" type="submit" disabled={pending}>{pending ? 'Signing in…' : 'Sign in'}</Button>
        </form>
      </section>
    </div>
  )
}
