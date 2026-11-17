import { DndContext, PointerSensor, useDraggable, useDroppable, useSensor, useSensors, type DragEndEvent } from '@dnd-kit/core'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Button, DataTable, Field, Modal, PageHeader, SelectField, StatusBadge, useToast } from '@/components/common/ui'
import { useSession } from '@/hooks/session'
import { apiError } from '@/services/api'
import { crmService } from '@/services/crm.service'
import type { Lead, StatusDefinition } from '@/types/api'
import { formatInr, fromPaise, toPaise } from '@/utils/money'

export function KanbanPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [q, setQ] = useState('')
  const [source, setSource] = useState('')
  const [assignee, setAssignee] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Lead | null>(null)
  const [stageOpen, setStageOpen] = useState(false)
  const [form, setForm] = useState({ contact_name: '', company_name: '', phone: '', estimated_value: '', source_id: '' })
  const [stage, setStage] = useState({ label: '', status_key: '' })
  const leads = useQuery({ queryKey: ['leads', q], queryFn: () => crmService.leads({ q, page_size: 100 }) })
  const statuses = useQuery({ queryKey: ['statuses'], queryFn: crmService.statuses })
  const groups = useQuery({ queryKey: ['status-groups'], queryFn: crmService.groups })
  const sources = useQuery({ queryKey: ['lead-sources'], queryFn: crmService.sources })
  const leadGroup = groups.data?.items.find((group) => group.module_key === 'crm' && group.entity_key === 'lead')
  const columns = (statuses.data?.items ?? []).filter((item) => item.status_group_id === leadGroup?.id && item.is_active).sort((a, b) => a.sort_order - b.sort_order)
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }))
  const visible = useMemo(() => (leads.data?.items ?? []).filter((lead) => {
    if (source && lead.source_id !== source) return false
    if (assignee && lead.assigned_to !== assignee) return false
    return true
  }), [leads.data, source, assignee])

  const move = useMutation({
    mutationFn: async ({ lead, status }: { lead: Lead; status: StatusDefinition }) => {
      const updated = await crmService.leadStatus(lead.id, status.status_key)
      await crmService.createActivity({
        activity_type: 'note',
        subject: `Lead moved to ${status.label}`,
        description: `${lead.contact_name} changed stage to ${status.label}.`,
        lead_id: lead.id,
      })
      return updated
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leads'] }),
    onError: (error) => toast(apiError(error), 'error'),
  })

  const onDragEnd = (event: DragEndEvent) => {
    const status = columns.find((column) => column.id === event.over?.id)
    const lead = visible.find((item) => item.id === event.active.id)
    if (!status || !lead || lead.status_id === status.id) return
    move.mutate({ lead, status })
  }

  const saveLead = async () => {
    const body = {
      lead_code: `LD-${Date.now().toString().slice(-6)}`,
      contact_name: form.contact_name,
      company_name: form.company_name || null,
      phone: form.phone || null,
      estimated_value: form.estimated_value || null,
      source_id: form.source_id || null,
      branch_id: session.branchId || null,
    }
    try {
      if (editing) await crmService.updateLead(editing.id, body)
      else await crmService.createLead(body)
      toast('Lead saved')
      setOpen(false)
      queryClient.invalidateQueries({ queryKey: ['leads'] })
    } catch (error) {
      toast(apiError(error), 'error')
    }
  }

  return (
    <div>
      <PageHeader title="CRM Kanban" subtitle="Columns come from the lead statuses stored for this organization.">
        {session.can('crm.write') ? <Button onClick={() => { setEditing(null); setForm({ contact_name: '', company_name: '', phone: '', estimated_value: '', source_id: '' }); setOpen(true) }}>Add lead</Button> : null}
        {session.can('workflows.manage') ? <Button variant="secondary" onClick={() => setStageOpen(true)}>Add stage</Button> : null}
      </PageHeader>
      <div className="mb-3 flex flex-wrap gap-2">
        <input className="control px-3 py-2 text-sm" placeholder="Search leads" value={q} onChange={(event) => setQ(event.target.value)} />
        <select className="control px-3 py-2 text-sm" value={source} onChange={(event) => setSource(event.target.value)}>
          <option value="">All sources</option>
          {(sources.data?.items ?? []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        <input className="control px-3 py-2 text-sm" placeholder="Filter by assigned user id" value={assignee} onChange={(event) => setAssignee(event.target.value)} />
      </div>
      <DndContext sensors={sensors} onDragEnd={onDragEnd}>
        <div className="flex gap-3 overflow-x-auto pb-4">
          {columns.map((column) => {
            const cards = visible.filter((lead) => lead.status_id === column.id)
            const value = cards.reduce((sum, lead) => sum + toPaise(lead.estimated_value), 0)
            return <Column key={column.id} column={column} count={cards.length} value={formatInr(fromPaise(value))} leads={cards} onEdit={(lead) => { setEditing(lead); setForm({ contact_name: lead.contact_name, company_name: lead.company_name ?? '', phone: lead.phone ?? '', estimated_value: lead.estimated_value ?? '', source_id: lead.source_id ?? '' }); setOpen(true) }} />
          })}
        </div>
      </DndContext>
      <Modal title={editing ? 'Edit lead' : 'Add lead'} open={open} onClose={() => setOpen(false)}>
        <div className="grid gap-3">
          <Field label="Lead name" value={form.contact_name} onChange={(event) => setForm({ ...form, contact_name: event.target.value })} />
          <Field label="Company" value={form.company_name} onChange={(event) => setForm({ ...form, company_name: event.target.value })} />
          <Field label="Mobile" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
          <Field label="Expected value" value={form.estimated_value} onChange={(event) => setForm({ ...form, estimated_value: event.target.value })} />
          <SelectField label="Source" value={form.source_id} onChange={(event) => setForm({ ...form, source_id: event.target.value })}>
            <option value="">None</option>
            {(sources.data?.items ?? []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </SelectField>
          <Button onClick={saveLead}>Save lead</Button>
        </div>
      </Modal>
      <Modal title="Add pipeline stage" open={stageOpen} onClose={() => setStageOpen(false)}>
        <div className="grid gap-3">
          <Field label="Label" value={stage.label} onChange={(event) => setStage({ ...stage, label: event.target.value })} />
          <Field label="Status key" value={stage.status_key} onChange={(event) => setStage({ ...stage, status_key: event.target.value })} />
          <Button onClick={async () => {
            if (!leadGroup) return toast('Lead status group was not found', 'error')
            try {
              await crmService.createStatus({ status_group_id: leadGroup.id, status_key: stage.status_key, label: stage.label, sort_order: columns.length + 1 })
              toast('Stage added')
              setStageOpen(false)
              queryClient.invalidateQueries({ queryKey: ['statuses'] })
            } catch (error) {
              toast(apiError(error), 'error')
            }
          }}>Save stage</Button>
        </div>
      </Modal>
    </div>
  )
}

function Column({ column, leads, count, value, onEdit }: { column: StatusDefinition; leads: Lead[]; count: number; value: string; onEdit: (lead: Lead) => void }) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id })
  return (
    <div ref={setNodeRef} className={`w-[min(18rem,82vw)] shrink-0 rounded-xl border p-3 ${isOver ? 'border-brand bg-brand/10' : 'border-line bg-canvas'}`}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <StatusBadge value={column.label} />
        <span className="status status-neutral">{count}</span>
      </div>
      <p className="mb-3 text-xs text-muted">{value}</p>
      <div className="space-y-2">{leads.map((lead) => <Card key={lead.id} lead={lead} stage={column.label} onEdit={onEdit} />)}</div>
    </div>
  )
}

function Card({ lead, stage, onEdit }: { lead: Lead; stage: string; onEdit: (lead: Lead) => void }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: lead.id })
  const style = transform ? { transform: `translate(${transform.x}px, ${transform.y}px)` } : undefined
  return (
    <article ref={setNodeRef} style={style} {...listeners} {...attributes} className="panel cursor-grab p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <p className="font-medium">{lead.contact_name}</p>
        <StatusBadge value={stage} />
      </div>
      <p className="text-muted">{lead.company_name || 'No company'}</p>
      <p>{lead.phone || 'No mobile'}</p>
      <p>{formatInr(lead.estimated_value)}</p>
      <p className="text-xs text-muted">Assigned: {lead.assigned_to || 'Unassigned'}</p>
      <button className="mt-2 text-xs underline" onPointerDown={(event) => event.stopPropagation()} onClick={() => onEdit(lead)}>Edit lead</button>
    </article>
  )
}

export function LeadsPage() {
  return <KanbanPage />
}

export function OpportunitiesPage() {
  const query = useQuery({ queryKey: ['opportunities'], queryFn: () => crmService.opportunities({}) })
  const toast = useToast()
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  return (
    <div>
      <PageHeader title="Opportunities" />
      <form className="mb-4 flex flex-wrap gap-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await crmService.createOpportunity({ opportunity_code: `OP-${Date.now().toString().slice(-6)}`, title, expected_value: 0 })
          setTitle('')
          queryClient.invalidateQueries({ queryKey: ['opportunities'] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <input className="control px-3 py-2 text-sm" placeholder="Opportunity title" value={title} onChange={(event) => setTitle(event.target.value)} required />
        <Button type="submit">Add opportunity</Button>
      </form>
      <DataTable
        rows={query.data?.items ?? []}
        empty="No opportunities yet."
        rowKey={(item) => item.id}
        columns={[
          { key: 'opportunity_code', label: 'Code', render: (item) => item.opportunity_code },
          { key: 'title', label: 'Title', render: (item) => item.title },
          { key: 'expected_value', label: 'Expected value', render: (item) => formatInr(item.expected_value) },
          { key: 'probability', label: 'Probability', render: (item) => item.probability || '—' },
          { key: 'expected_close_date', label: 'Close date', render: (item) => item.expected_close_date || '—' },
        ]}
      />
    </div>
  )
}

export function ActivitiesPage() {
  const query = useQuery({ queryKey: ['activities'], queryFn: () => crmService.activities({}) })
  const toast = useToast()
  const queryClient = useQueryClient()
  const [subject, setSubject] = useState('')
  return (
    <div>
      <PageHeader title="Activities" />
      <form className="mb-4 flex gap-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await crmService.createActivity({ activity_type: 'task', subject })
          setSubject('')
          queryClient.invalidateQueries({ queryKey: ['activities'] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <input className="control px-3 py-2 text-sm" placeholder="Task subject" value={subject} onChange={(event) => setSubject(event.target.value)} required />
        <Button type="submit">Add activity</Button>
      </form>
      <DataTable
        rows={query.data?.items ?? []}
        empty="No activities yet."
        rowKey={(item) => item.id}
        columns={[
          { key: 'activity_type', label: 'Type', render: (item) => item.activity_type },
          { key: 'subject', label: 'Subject', render: (item) => item.subject },
          { key: 'due_at', label: 'Due', render: (item) => item.due_at || '—' },
          { key: 'assigned_to', label: 'Assigned', render: (item) => item.assigned_to || '—' },
          { key: 'status', label: 'Status', render: (item) => item.completed_at ? <StatusBadge value="Completed" /> : <Button variant="secondary" onClick={() => crmService.completeActivity(item.id).then(() => queryClient.invalidateQueries({ queryKey: ['activities'] })).catch((error) => toast(apiError(error), 'error'))}>Complete</Button> },
        ]}
      />
    </div>
  )
}
