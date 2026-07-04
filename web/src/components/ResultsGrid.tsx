import type { InsurerResult, Status } from '../types'
import { InsurerCard } from './InsurerCard'

const RANK: Record<Status, number> = {
  claim_initiated: 0,
  success: 1,
  searching: 2,
  failed: 3,
  blocked: 4,
  queued: 5,
  pending: 6,
}

export function ResultsGrid({ results }: { results: InsurerResult[]; runId: string }) {
  const sorted = [...results].sort((a, b) => {
    const r = RANK[a.status] - RANK[b.status]
    return r !== 0 ? r : a.insurer_name.localeCompare(b.insurer_name)
  })

  return (
    <div className="grid">
      {sorted.map((r) => (
        <InsurerCard key={r.id} result={r} />
      ))}
      {results.length === 0 && <div className="empty">Queuing insurers…</div>}
    </div>
  )
}
