import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

const SHEET_WIDTH = 794

function mountSheet(source: HTMLElement) {
  const host = document.createElement('div')
  host.setAttribute('aria-hidden', 'true')
  host.style.position = 'fixed'
  host.style.left = '-12000px'
  host.style.top = '0'
  host.style.width = `${SHEET_WIDTH}px`
  host.style.background = '#ffffff'
  host.style.zIndex = '-1'
  host.innerHTML = source.innerHTML
  document.body.appendChild(host)
  return host
}

export async function downloadSheet(filename: string) {
  const source = document.getElementById('invoice-print')
  if (!source) return
  const host = mountSheet(source)
  try {
    if (document.fonts?.ready) await document.fonts.ready
    const canvas = await html2canvas(host, {
      scale: 3,
      backgroundColor: '#ffffff',
      useCORS: true,
      width: SHEET_WIDTH,
      windowWidth: 1280,
      scrollX: 0,
      scrollY: 0,
    })
    const pdf = new jsPDF({ unit: 'mm', format: 'a4', compress: true })
    const margin = 8
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const usableWidth = pageWidth - margin * 2
    const usableHeight = pageHeight - margin * 2
    const sliceHeight = Math.max(1, Math.floor((canvas.width * usableHeight) / usableWidth))
    let offset = 0
    let page = 0
    while (offset < canvas.height) {
      const height = Math.min(sliceHeight, canvas.height - offset)
      const slice = document.createElement('canvas')
      slice.width = canvas.width
      slice.height = height
      const context = slice.getContext('2d')
      if (!context) break
      context.fillStyle = '#ffffff'
      context.fillRect(0, 0, slice.width, slice.height)
      context.drawImage(canvas, 0, offset, canvas.width, height, 0, 0, canvas.width, height)
      if (page > 0) pdf.addPage()
      const heightMm = (height * usableWidth) / canvas.width
      pdf.addImage(slice.toDataURL('image/png'), 'PNG', margin, margin, usableWidth, heightMm)
      offset += height
      page += 1
    }
    pdf.save(filename.endsWith('.pdf') ? filename : `${filename}.pdf`)
  } finally {
    host.remove()
  }
}

export function printSheet(title: string) {
  const source = document.getElementById('invoice-print')
  if (!source) return
  const frame = document.createElement('iframe')
  frame.setAttribute('title', title)
  frame.style.position = 'fixed'
  frame.style.left = '-12000px'
  frame.style.top = '0'
  frame.style.width = `${SHEET_WIDTH}px`
  frame.style.height = '1123px'
  frame.style.border = '0'
  document.body.appendChild(frame)
  const doc = frame.contentDocument
  const win = frame.contentWindow
  if (!doc || !win) {
    frame.remove()
    return
  }
  const styles = [...document.querySelectorAll('link[rel="stylesheet"], style')].map((node) => node.outerHTML).join('')
  doc.open()
  doc.write(`<!DOCTYPE html><html><head><title>${title}</title>${styles}<style>@page{size:A4;margin:10mm}html,body{width:${SHEET_WIDTH}px;margin:0;background:#fff}</style></head><body>${source.innerHTML}</body></html>`)
  doc.close()
  window.setTimeout(() => {
    win.focus()
    win.print()
    window.setTimeout(() => frame.remove(), 1000)
  }, 400)
}
