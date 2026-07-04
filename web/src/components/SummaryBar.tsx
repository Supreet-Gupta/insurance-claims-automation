import type { InsurerResult } from '../types'

const RESOLVED = new Set(['success', 'failed', 'blocked', 'pending', 'claim_initiated'])

export function SummaryBar({ results }: { results: InsurerResult[] }) {
  const total = results.length
  const resolved = results.filter((r) => RESOLVED.has(r.status)).length
  const successful = results.filter((r) => r.status === 'success' || r.status === 'claim_initiated')
  const issues = results.filter((r) => r.status === 'failed' || r.status === 'blocked')
  const pending = results.filter((r) => r.status === 'pending').length
  const amount = successful.reduce((s, r) => s + (Number(r.amount_found) || 0), 0)
  const pct = total ? Math.round((resolved / total) * 100) : 0

  const rupee = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)

  return (
    <div className="summary">
      <div className="summary-stats">
        <Stat label="Submitted successfully" value={String(successful.length)} highlight={successful.length > 0} />
        <Stat label="Failed / blocked" value={String(issues.length)} />
        <Stat label="Total discovered" value={amount > 0 ? rupee : '—'} highlight={amount > 0} big />
      </div>
      <div className="progress">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      {pending > 0 && (
        <p className="summary-note">{pending} insurers pending — no adapter built yet.</p>
      )}
    </div>
  )
}

function Stat({
  label,
  value,
  highlight,
  big,
}: {
  label: string
  value: string
  highlight?: boolean
  big?: boolean
}) {
  return (
    <div className={`stat ${highlight ? 'hl' : ''} ${big ? 'big' : ''}`}>
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}
