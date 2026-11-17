export const tokens = {
  brand: '#2563EB',
  navy: '#102A43',
  electric: '#3B82F6',
  cyan: '#38BDF8',
  canvas: '#F8FAFC',
  surface: '#FFFFFF',
  ink: '#0F172A',
  muted: '#64748B',
  line: '#E2E8F0',
  success: '#16A34A',
  warning: '#F59E0B',
  danger: '#DC2626',
} as const

export type StatusTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

const tones: [StatusTone, string[]][] = [
  ['danger', ['unpaid', 'inactive', 'cancelled', 'canceled', 'cancel', 'lost', 'rejected', 'disabled', 'archived', 'failed', 'overdue', 'void']],
  ['success', ['active', 'won', 'posted', 'paid', 'converted', 'completed', 'approved', 'confirmed', 'delivered', 'received']],
  ['warning', ['low stock', 'low', 'pending', 'draft', 'qualified', 'suspended', 'proposal', 'submitted', 'partial', 'due', 'hold']],
  ['info', ['new', 'open', 'sent', 'issued', 'progress', 'processing']],
]

export function statusTone(value: string | null | undefined): StatusTone {
  const key = (value ?? '').toLowerCase()
  const match = tones.find(([, words]) => words.some((word) => key.includes(word)))
  return match?.[0] ?? 'neutral'
}
