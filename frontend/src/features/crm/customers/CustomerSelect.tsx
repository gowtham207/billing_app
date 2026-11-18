import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { customerService } from '@/services/customer.service'
import type { Customer } from '@/types/api'

type CustomerSelectProps = {
  value: string
  onChange: (customerId: string) => void
  label?: string
  placeholder?: string
  required?: boolean
  disabled?: boolean
  allowEmpty?: boolean
  emptyLabel?: string
}

function detail(customer: Customer) {
  return [customer.customer_code, customer.phone, customer.tax_registration_no].filter(Boolean).join(' · ')
}

export function CustomerSelect({ value, onChange, label, placeholder = 'Search by name, phone, code, or GSTIN', required, disabled, allowEmpty, emptyLabel = 'All customers' }: CustomerSelectProps) {
  const box = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const selected = useQuery({ queryKey: ['customer', value], enabled: Boolean(value), queryFn: () => customerService.get(value) })
  const results = useQuery({
    queryKey: ['customers-search', query],
    enabled: open,
    queryFn: () => customerService.list({ q: query || undefined, page_size: 20 }),
  })
  const matches = results.data?.items ?? []

  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(text.trim()), 200)
    return () => window.clearTimeout(timer)
  }, [text])

  useEffect(() => {
    setActive(0)
  }, [query, open])

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (!box.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const pick = (customerId: string) => {
    onChange(customerId)
    setText('')
    setOpen(false)
  }

  const chooseActive = () => {
    if (allowEmpty && active === 0) {
      pick('')
      return
    }
    const customer = matches[allowEmpty ? active - 1 : active]
    if (customer) pick(customer.id)
  }

  return (
    <label className="block text-sm">
      {label ? <span className="mb-1 block text-muted">{label}</span> : null}
      <div className="relative" ref={box}>
        <input
          className="control w-full px-3 py-2"
          role="combobox"
          aria-expanded={open}
          aria-autocomplete="list"
          autoComplete="off"
          disabled={disabled}
          placeholder={value ? selected.data?.display_name || placeholder : placeholder}
          value={open ? text : selected.data?.display_name ?? ''}
          onFocus={() => {
            if (disabled) return
            setText('')
            setOpen(true)
          }}
          onChange={(event) => {
            setText(event.target.value)
            setOpen(true)
          }}
          onKeyDown={(event) => {
            const count = matches.length + (allowEmpty ? 1 : 0)
            if (event.key === 'ArrowDown') {
              event.preventDefault()
              setOpen(true)
              setActive((index) => Math.min(index + 1, Math.max(count - 1, 0)))
            } else if (event.key === 'ArrowUp') {
              event.preventDefault()
              setActive((index) => Math.max(index - 1, 0))
            } else if (event.key === 'Enter' && open) {
              event.preventDefault()
              chooseActive()
            } else if (event.key === 'Escape') {
              setOpen(false)
              setText('')
            }
          }}
        />
        {required ? <input className="sr-only" tabIndex={-1} value={value} required onChange={() => undefined} aria-hidden="true" /> : null}
        {open && !disabled ? (
          <ul className="panel absolute z-30 mt-1 max-h-64 w-full overflow-auto py-1 shadow-lg" role="listbox">
            {allowEmpty ? (
              <li>
                <button type="button" className={`block w-full px-3 py-2 text-left text-sm ${active === 0 ? 'bg-brand/10' : ''}`} onMouseDown={(event) => event.preventDefault()} onMouseEnter={() => setActive(0)} onClick={() => pick('')}>{emptyLabel}</button>
              </li>
            ) : null}
            {results.isLoading ? <li className="px-3 py-2 text-sm text-muted">Searching customers…</li> : null}
            {!results.isLoading && matches.length === 0 ? <li className="px-3 py-2 text-sm text-muted">No customers found</li> : null}
            {matches.map((customer, index) => {
              const position = allowEmpty ? index + 1 : index
              return (
                <li key={customer.id}>
                  <button type="button" className={`block w-full px-3 py-2 text-left ${position === active ? 'bg-brand/10' : ''}`} onMouseDown={(event) => event.preventDefault()} onMouseEnter={() => setActive(position)} onClick={() => pick(customer.id)}>
                    <span className="block text-sm font-medium">{customer.display_name}</span>
                    {detail(customer) ? <span className="block text-xs text-muted">{detail(customer)}</span> : null}
                  </button>
                </li>
              )
            })}
          </ul>
        ) : null}
      </div>
    </label>
  )
}
