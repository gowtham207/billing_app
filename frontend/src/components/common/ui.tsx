import { X } from 'lucide-react'
import { createContext, useContext, useState, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'
import { statusTone, type StatusTone } from '@/styles/tokens'

const ToastContext = createContext<(message: string, tone?: 'ok' | 'error') => void>(() => undefined)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<{ id: number; message: string; tone: 'ok' | 'error' }[]>([])
  const push = (message: string, tone: 'ok' | 'error' = 'ok') => {
    const id = Date.now()
    setToasts((current) => [...current, { id, message, tone }])
    window.setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 4000)
  }
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="fixed right-4 bottom-4 z-50 flex w-80 flex-col gap-2">
        {toasts.map((toast) => (
          <div key={toast.id} className={`rounded-lg px-3 py-2 text-sm text-white ${toast.tone === 'error' ? 'bg-danger' : 'bg-navy'}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}

export function Button({ variant = 'primary', className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' | 'ghost' }) {
  const styles = {
    primary: 'bg-brand text-white hover:bg-electric',
    secondary: 'control text-ink hover:bg-brand/10',
    danger: 'bg-danger text-white hover:opacity-90',
    ghost: 'text-ink hover:bg-brand/10',
  }
  return <button className={`inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`} {...props} />
}

export function Field({ label, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-muted">{label}</span>
      <input className="control w-full px-3 py-2" {...props} />
    </label>
  )
}

export function TextArea({ label, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-muted">{label}</span>
      <textarea className="control w-full px-3 py-2" {...props} />
    </label>
  )
}

export function SelectField({ label, children, ...props }: SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-muted">{label}</span>
      <select className="control w-full px-3 py-2" {...props}>{children}</select>
    </label>
  )
}

export function Modal({ title, open, onClose, children, wide = false }: { title: string; open: boolean; onClose: () => void; children: ReactNode; wide?: boolean }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-navy/40 p-4">
      <div className={`panel my-8 w-full ${wide ? 'max-w-6xl' : 'max-w-3xl'}`}>
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <h2 className="text-base font-semibold">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}

export function ConfirmDialog({ open, title, message, onConfirm, onClose, confirmLabel = 'Confirm', dismissLabel = 'Cancel' }: { open: boolean; title: string; message: string; onConfirm: () => void; onClose: () => void; confirmLabel?: string; dismissLabel?: string }) {
  return (
    <Modal title={title} open={open} onClose={onClose}>
      <p className="text-sm text-muted">{message}</p>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>{dismissLabel}</Button>
        <Button variant="danger" onClick={onConfirm}>{confirmLabel}</Button>
      </div>
    </Modal>
  )
}

export function PageHeader({ title, subtitle, children }: { title: string; subtitle?: string; children?: ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold">{title}</h1>
        {subtitle ? <p className="mt-1 max-w-3xl text-sm text-muted">{subtitle}</p> : null}
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  )
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="rounded-xl border border-dashed border-line p-8 text-center"><p className="font-medium">{title}</p><p className="mt-1 text-sm text-muted">{detail}</p></div>
}

export function Skeleton() {
  return <div className="h-24 animate-pulse rounded-xl bg-line" />
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`panel p-4 ${className}`}>{children}</section>
}

export function StatusBadge({ value, children }: { value?: string | null; children?: ReactNode }) {
  const label = children ?? value ?? 'Unknown'
  const tone: StatusTone = statusTone(typeof label === 'string' ? label : value)
  return <span className={`status status-${tone}`}>{label}</span>
}

export function DataTable<T>({ columns, rows, empty, rowKey }: {
  columns: { key: string; label: string; render?: (row: T) => ReactNode }[]
  rows: T[]
  empty: string
  rowKey: (row: T, index: number) => string
}) {
  return (
    <div className="data-table">
      <table className="min-w-full text-left text-sm">
        <thead className="text-muted">
          <tr>{columns.map((column) => <th key={column.key} className="px-3 py-2 font-medium">{column.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td className="px-3 py-6 text-muted" colSpan={Math.max(columns.length, 1)}>{empty}</td></tr>
          ) : rows.map((row, index) => (
            <tr key={rowKey(row, index)} className="border-t border-line">
              {columns.map((column) => <td key={column.key} className="px-3 py-2 align-middle">{column.render ? column.render(row) : '—'}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
