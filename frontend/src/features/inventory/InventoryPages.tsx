import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Button, DataTable, Field, Modal, PageHeader, SelectField, StatusBadge, TextArea, useToast } from '@/components/common/ui'
import { useSession } from '@/hooks/session'
import { apiError } from '@/services/api'
import { categoryService, inventoryService, productService } from '@/services/inventory.service'
import type { Category, Product } from '@/types/api'
import { formatInr } from '@/utils/money'

export function CategoriesPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Category | null>(null)
  const [form, setForm] = useState({ name: '', parent_id: '', description: '', is_active: true })
  const query = useQuery({ queryKey: ['categories', q], queryFn: () => categoryService.list(q) })
  const items = query.data?.items ?? []
  const save = useMutation({
    mutationFn: () => {
      const body = { name: form.name, parent_id: form.parent_id || null, description: form.description || null, is_active: form.is_active }
      return editing ? categoryService.update(editing.id, body) : categoryService.create(body)
    },
    onSuccess: async (category) => {
      const file = (document.getElementById('category-image') as HTMLInputElement | null)?.files?.[0]
      if (file) await inventoryService.upload('product_category', category.id, file)
      toast('Category saved')
      setOpen(false)
      queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
    onError: (error) => toast(apiError(error), 'error'),
  })
  return (
    <div>
      <PageHeader title="Categories" subtitle="Category code and image are not columns. The image is uploaded as an attachment after the category is saved.">
        {session.can('products.create') ? <Button onClick={() => { setEditing(null); setForm({ name: '', parent_id: '', description: '', is_active: true }); setOpen(true) }}>Add category</Button> : null}
      </PageHeader>
      <input className="mb-3 control px-3 py-2 text-sm" placeholder="Search category" value={q} onChange={(event) => setQ(event.target.value)} />
      <DataTable
        rows={items}
        empty="No categories yet."
        rowKey={(category) => category.id}
        columns={[
          { key: 'name', label: 'Name', render: (category) => category.name },
          { key: 'parent', label: 'Parent', render: (category) => items.find((item) => item.id === category.parent_id)?.name || '—' },
          { key: 'description', label: 'Description', render: (category) => category.description || '—' },
          { key: 'status', label: 'Status', render: (category) => <StatusBadge value={category.is_active ? 'Active' : 'Inactive'} /> },
          { key: 'action', label: '', render: (category) => session.can('products.update') ? <span className="flex gap-1"><Button variant="ghost" onClick={() => openEdit(category)}>Edit</Button><Button variant="ghost" onClick={() => categoryService.remove(category.id).then(() => queryClient.invalidateQueries({ queryKey: ['categories'] })).catch((error) => toast(apiError(error), 'error'))}>Delete</Button></span> : null },
        ]}
      />
      <Modal title={editing ? 'Edit category' : 'Add category'} open={open} onClose={() => setOpen(false)}>
        <form className="grid gap-3" onSubmit={(event) => { event.preventDefault(); save.mutate() }}>
          <Field label="Category name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          <SelectField label="Parent category" value={form.parent_id} onChange={(event) => setForm({ ...form, parent_id: event.target.value })}>
            <option value="">None</option>
            {items.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </SelectField>
          <TextArea label="Description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          <label className="text-sm">Image<input id="category-image" className="mt-1 block" type="file" accept="image/*" /></label>
          <SelectField label="Status" value={form.is_active ? 'active' : 'inactive'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'active' })}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </SelectField>
          <Button type="submit">Save category</Button>
        </form>
      </Modal>
    </div>
  )

  function openEdit(category: Category) {
    setEditing(category)
    setForm({ name: category.name, parent_id: category.parent_id ?? '', description: category.description ?? '', is_active: category.is_active })
    setOpen(true)
  }
}

export function ProductsPage() {
  const session = useSession()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [q, setQ] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [open, setOpen] = useState(false)
  const categories = useQuery({ queryKey: ['categories'], queryFn: () => categoryService.list() })
  const brands = useQuery({ queryKey: ['brands'], queryFn: inventoryService.brands })
  const units = useQuery({ queryKey: ['units'], queryFn: inventoryService.units })
  const products = useQuery({ queryKey: ['products', q, categoryId], queryFn: () => productService.list({ q, category_id: categoryId || undefined }) })
  const stock = useQuery({ queryKey: ['stock'], queryFn: inventoryService.stock })
  const [form, setForm] = useState(blankProduct())
  const save = useMutation({
    mutationFn: async () => {
      const body = {
        name: form.name,
        sku: form.sku,
        barcode: form.barcode || null,
        category_id: form.category_id || null,
        brand_id: form.brand_id || null,
        unit_id: form.unit_id,
        description: [form.description, form.hsn && `HSN: ${form.hsn}`, form.mrp && `MRP: ${form.mrp}`, form.gst && `GST: ${form.gst}%`].filter(Boolean).join('\n'),
        purchase_price: form.purchase_price || 0,
        selling_price: form.selling_price || 0,
        reorder_level: form.minimum_stock || 0,
        is_active: form.is_active,
        product_type: 'stock',
        track_inventory: true,
      }
      const product = form.id ? await productService.update(form.id, body) : await productService.create(body)
      const file = (document.getElementById('product-image') as HTMLInputElement | null)?.files?.[0]
      if (file) await inventoryService.upload('product', product.id, file)
      if (!form.id && form.opening_stock && form.warehouse_id) {
        await inventoryService.opening({ warehouse_id: form.warehouse_id, lines: [{ product_id: product.id, quantity: form.opening_stock, unit_cost: form.purchase_price || '0' }] })
      }
      return product
    },
    onSuccess: () => { toast('Product saved'); setOpen(false); queryClient.invalidateQueries({ queryKey: ['products'] }) },
    onError: (error) => toast(apiError(error), 'error'),
  })
  const warehouses = useQuery({ queryKey: ['warehouses'], queryFn: inventoryService.warehouses })
  return (
    <div>
      <PageHeader title="Products" subtitle="HSN, MRP, and GST are kept in the product description. Opening stock is posted through the stock API.">
        {session.can('products.create') ? <Button onClick={() => { setForm(blankProduct(units.data?.items[0]?.id)); setOpen(true) }}>Add product</Button> : null}
      </PageHeader>
      <div className="mb-3 flex flex-wrap gap-2">
        <input className="control px-3 py-2 text-sm" placeholder="Search products" value={q} onChange={(event) => setQ(event.target.value)} />
        <select className="control px-3 py-2 text-sm" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
          <option value="">All categories</option>
          {(categories.data?.items ?? []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </div>
      <div className="data-table">
        <table className="min-w-full text-sm">
          <thead className="text-muted"><tr>{['Name', 'SKU', 'Barcode', 'Price', 'Reorder', 'Status', ''].map((heading) => <th key={heading} className="px-3 py-2 text-left">{heading}</th>)}</tr></thead>
          <tbody>
            {(products.data?.items ?? []).map((product) => {
              const available = stockLevel(stock.data, product.id)
              const low = available !== null && available <= Number(product.reorder_level)
              return (
                <tr key={product.id} className="border-t border-line">
                  <td className="px-3 py-2"><Link className="text-brand underline" to={`/inventory/products/${product.id}`}>{product.name}</Link>{low ? <span className="ml-2"><StatusBadge value="Low stock" /></span> : null}</td>
                  <td className="px-3 py-2">{product.sku}</td>
                  <td className="px-3 py-2">{product.barcode}</td>
                  <td className="px-3 py-2">{formatInr(product.selling_price)}</td>
                  <td className="px-3 py-2">{available ?? '—'} / min {product.reorder_level}</td>
                  <td className="px-3 py-2"><StatusBadge value={product.is_active ? 'Active' : 'Inactive'} /></td>
                  <td className="px-3 py-2">{session.can('products.update') ? <Button variant="ghost" onClick={() => { setForm({ ...blankProduct(), ...product, description: product.description ?? '', barcode: product.barcode ?? '', category_id: product.category_id ?? '', brand_id: product.brand_id ?? '', hsn: '', mrp: '', gst: '', opening_stock: '', minimum_stock: product.reorder_level, purchase_price: product.purchase_price, selling_price: product.selling_price, warehouse_id: '' }); setOpen(true) }}>Edit</Button> : null}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <Modal title={form.id ? 'Edit product' : 'Add product'} open={open} onClose={() => setOpen(false)}>
        <form className="grid gap-3 md:grid-cols-2" onSubmit={(event) => { event.preventDefault(); save.mutate() }}>
          <Field label="Product name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          <Field label="SKU" value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} required />
          <Field label="Barcode" value={form.barcode} onChange={(event) => setForm({ ...form, barcode: event.target.value })} />
          <SelectField label="Category" value={form.category_id} onChange={(event) => setForm({ ...form, category_id: event.target.value })}>
            <option value="">None</option>
            {(categories.data?.items ?? []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </SelectField>
          <SelectField label="Brand" value={form.brand_id} onChange={(event) => setForm({ ...form, brand_id: event.target.value })}>
            <option value="">None</option>
            {(brands.data?.items ?? []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </SelectField>
          <SelectField label="Unit" value={form.unit_id} onChange={(event) => setForm({ ...form, unit_id: event.target.value })} required>
            <option value="">Select unit</option>
            {(units.data?.items ?? []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </SelectField>
          <Field label="HSN code" value={form.hsn} onChange={(event) => setForm({ ...form, hsn: event.target.value })} />
          <Field label="Purchase price" value={form.purchase_price} onChange={(event) => setForm({ ...form, purchase_price: event.target.value })} />
          <Field label="Selling price" value={form.selling_price} onChange={(event) => setForm({ ...form, selling_price: event.target.value })} />
          <Field label="MRP" value={form.mrp} onChange={(event) => setForm({ ...form, mrp: event.target.value })} />
          <Field label="GST percentage" value={form.gst} onChange={(event) => setForm({ ...form, gst: event.target.value })} />
          <Field label="Opening stock" value={form.opening_stock} onChange={(event) => setForm({ ...form, opening_stock: event.target.value })} />
          <SelectField label="Warehouse for opening stock" value={form.warehouse_id} onChange={(event) => setForm({ ...form, warehouse_id: event.target.value })}>
            <option value="">Select warehouse</option>
            {(warehouses.data?.items ?? []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </SelectField>
          <Field label="Minimum stock" value={form.minimum_stock} onChange={(event) => setForm({ ...form, minimum_stock: event.target.value })} />
          <div className="md:col-span-2"><TextArea label="Product description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></div>
          <label className="text-sm">Product image<input id="product-image" className="mt-1 block" type="file" accept="image/*" /></label>
          <SelectField label="Status" value={form.is_active ? 'active' : 'inactive'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'active' })}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </SelectField>
          <div className="md:col-span-2"><Button type="submit">Save product</Button></div>
        </form>
      </Modal>
    </div>
  )
}

function blankProduct(unitId = ''): ProductForm {
  return { id: '', name: '', sku: '', barcode: '', category_id: '', brand_id: '', unit_id: unitId, description: '', hsn: '', purchase_price: '', selling_price: '', mrp: '', gst: '', opening_stock: '', minimum_stock: '', warehouse_id: '', is_active: true }
}

type ProductForm = {
  id: string
  name: string
  sku: string
  barcode: string
  category_id: string
  brand_id: string
  unit_id: string
  description: string
  hsn: string
  purchase_price: string
  selling_price: string
  mrp: string
  gst: string
  opening_stock: string
  minimum_stock: string
  warehouse_id: string
  is_active: boolean
}

function stockLevel(payload: unknown, productId: string): number | null {
  const items = Array.isArray(payload) ? payload : (payload as { items?: Record<string, unknown>[] } | null)?.items ?? []
  const match = items.find((row) => String(row.product_id) === productId)
  if (!match) return null
  return Number(match.quantity_available ?? match.quantity ?? 0)
}

export function ProductDetailPage() {
  const { id = '' } = useParams()
  const product = useQuery({ queryKey: ['product', id], queryFn: () => productService.get(id) })
  const variants = useQuery({ queryKey: ['variants', id], queryFn: () => productService.variants(id) })
  const toast = useToast()
  const queryClient = useQueryClient()
  const [variant, setVariant] = useState({ variant_name: '', variant_sku: '' })
  const data = product.data
  if (!data) return <p className="text-sm">Loading product…</p>
  return (
    <div>
      <PageHeader title={data.name} subtitle={data.sku} />
      <p>Barcode: {data.barcode || '—'}</p>
      <p>Selling price: {formatInr(data.selling_price)}</p>
      <p className="whitespace-pre-wrap">{data.description}</p>
      <h2 className="mt-4 mb-2 font-medium">Variants</h2>
      <DataTable
        rows={variants.data ?? []}
        empty="No variants yet."
        rowKey={(item) => item.id}
        columns={[
          { key: 'variant_sku', label: 'SKU', render: (item) => item.variant_sku },
          { key: 'variant_name', label: 'Name', render: (item) => item.variant_name },
        ]}
      />
      <form className="flex flex-wrap gap-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          await productService.addVariant(id, { product_id: id, ...variant })
          setVariant({ variant_name: '', variant_sku: '' })
          queryClient.invalidateQueries({ queryKey: ['variants', id] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <input className="control px-3 py-2 text-sm" placeholder="Variant name" value={variant.variant_name} onChange={(event) => setVariant({ ...variant, variant_name: event.target.value })} required />
        <input className="control px-3 py-2 text-sm" placeholder="Variant SKU" value={variant.variant_sku} onChange={(event) => setVariant({ ...variant, variant_sku: event.target.value })} required />
        <Button type="submit">Add variant</Button>
      </form>
    </div>
  )
}

export function SimpleCatalogPage({ title, kind }: { title: string; kind: 'brands' | 'units' | 'warehouses' }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: [kind],
    queryFn: () => kind === 'brands' ? inventoryService.brands() : kind === 'units' ? inventoryService.units() : inventoryService.warehouses(),
  })
  const [name, setName] = useState('')
  const [extra, setExtra] = useState('')
  return (
    <div>
      <PageHeader title={title} />
      <form className="mb-4 flex flex-wrap gap-2" onSubmit={async (event) => {
        event.preventDefault()
        try {
          if (kind === 'brands') await inventoryService.createBrand(name)
          if (kind === 'units') await inventoryService.createUnit({ name, symbol: extra || name.slice(0, 3) })
          if (kind === 'warehouses') await inventoryService.createWarehouse({ name, code: extra || name.slice(0, 6).toUpperCase() })
          setName('')
          setExtra('')
          queryClient.invalidateQueries({ queryKey: [kind] })
        } catch (error) {
          toast(apiError(error), 'error')
        }
      }}>
        <Field label="Name" value={name} onChange={(event) => setName(event.target.value)} required />
        {kind !== 'brands' ? <Field label={kind === 'units' ? 'Symbol' : 'Code'} value={extra} onChange={(event) => setExtra(event.target.value)} /> : null}
        <Button className="self-end" type="submit">Add</Button>
      </form>
      <DataTable
        rows={query.data?.items ?? []}
        empty={`No ${title.toLowerCase()} yet.`}
        rowKey={(item) => item.id}
        columns={[
          { key: 'name', label: 'Name', render: (item) => item.name },
          { key: 'detail', label: kind === 'units' ? 'Symbol' : kind === 'warehouses' ? 'Code' : 'Detail', render: (item) => 'symbol' in item && typeof item.symbol === 'string' ? item.symbol : 'code' in item && typeof item.code === 'string' ? item.code : '—' },
          { key: 'status', label: 'Status', render: (item) => 'is_active' in item ? <StatusBadge value={item.is_active ? 'Active' : 'Inactive'} /> : '—' },
          { key: 'action', label: '', render: (item) => <Button variant="ghost" onClick={() => {
            const action = kind === 'brands' ? inventoryService.deleteBrand(item.id) : kind === 'units' ? inventoryService.deleteUnit(item.id) : inventoryService.deleteWarehouse(item.id)
            action.then(() => queryClient.invalidateQueries({ queryKey: [kind] })).catch((error) => toast(apiError(error), 'error'))
          }}>Delete</Button> },
        ]}
      />
    </div>
  )
}

export function StockPage() {
  const stock = useQuery({ queryKey: ['stock'], queryFn: inventoryService.stock })
  const low = useQuery({ queryKey: ['low-stock-page'], queryFn: inventoryService.lowStock })
  return (
    <div className="space-y-4">
      <PageHeader title="Stock Management" />
      <h2 className="font-medium">Low stock</h2>
      <RecordTable rows={asRows(low.data)} empty="No products are at or below their reorder level." />
      <h2 className="font-medium">Balances</h2>
      <RecordTable rows={asRows(stock.data)} empty="No stock balances yet. Add opening stock from a product." />
    </div>
  )
}

export function MovementsPage() {
  const query = useQuery({ queryKey: ['movements'], queryFn: inventoryService.movements })
  return (
    <div>
      <PageHeader title="Stock Movements" />
      <RecordTable rows={asRows(query.data)} empty="No stock movements yet." />
    </div>
  )
}

function asRows(payload: unknown): Record<string, unknown>[] {
  if (Array.isArray(payload)) return payload as Record<string, unknown>[]
  const items = (payload as { items?: Record<string, unknown>[] } | null)?.items
  return items ?? []
}

function RecordTable({ rows, empty }: { rows: Record<string, unknown>[]; empty: string }) {
  if (rows.length === 0) return <p className="text-sm text-muted">{empty}</p>
  const columns = Object.keys(rows[0]).slice(0, 8)
  return (
    <div className="data-table">
      <table className="min-w-full text-sm">
        <thead className="text-left text-muted"><tr>{columns.map((column) => <th key={column} className="px-3 py-2">{column}</th>)}</tr></thead>
        <tbody>{rows.map((row, index) => <tr key={index} className="border-t border-line">{columns.map((column) => <td key={column} className="px-3 py-2">{String(row[column] ?? '')}</td>)}</tr>)}</tbody>
      </table>
    </div>
  )
}

export function productLabel(product: Product) {
  return `${product.name} (${product.sku})`
}
