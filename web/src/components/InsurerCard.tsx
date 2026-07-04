import { useState } from 'react'
import { supabase, REFERENCE_DIRECTORY_URL } from '../lib/supabase'
import type { InsurerResult, Status } from '../types'

const PILL: Record<Status, { label: string; cls: string }> = {
  queued: { label: 'Queued', cls: 'queued' },
  searching: { label: 'Searching…', cls: 'searching' },
  success: { label: 'Success', cls: 'success' },
  failed: { label: 'Failed', cls: 'failed' },
  blocked: { label: 'Blocked', cls: 'blocked' },
  pending: { label: 'Pending', cls: 'pending' },
  claim_initiated: { label: 'Claim submitted', cls: 'success' },
}

const rupee = (n: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n)

function domain(url: string | null) {
  if (!url) return ''
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return ''
  }
}

export function InsurerCard({ result: r }: { result: InsurerResult }) {
  const [busy, setBusy] = useState(false)
  const pill = PILL[r.status]

  // Built insurers link to their own verified reference page; everything else
  // points at the official IRDAI unclaimed-amounts directory (never a guess).
  const referenceUrl =
    r.adapter_type === 'live' && r.insurer_url ? r.insurer_url : REFERENCE_DIRECTORY_URL

  const hasAmount = r.amount_found != null
  const isWin = r.status === 'success' || r.status === 'claim_initiated'

  const initiateClaim = async () => {
    setBusy(true)
    await supabase
      .from('insurer_result')
      .update({
        status: 'claim_initiated',
        detail: 'Claim form opened on insurer site',
        updated_at: new Date().toISOString(),
      })
      .eq('id', r.id)
    window.open(referenceUrl, '_blank', 'noopener')
    setBusy(false)
  }

  return (
    <div className={`insurer-card status-${pill.cls}`}>
      <div className="card-head">
        <div className="card-name">
          <strong>{r.insurer_name}</strong>
          <a className="card-domain" href={referenceUrl} target="_blank" rel="noopener noreferrer">
            {domain(r.insurer_url)} ↗
          </a>
        </div>
        <span className={`pill ${pill.cls}`}>
          {r.status === 'searching' && <span className="dot-pulse" />}
          {pill.label}
        </span>
      </div>

      {isWin && hasAmount && <div className="amount">{rupee(Number(r.amount_found))}</div>}

      {r.detail && !(isWin && hasAmount) && <div className="card-detail">{r.detail}</div>}

      {r.status === 'success' && hasAmount && (
        <button className="claim-btn" onClick={initiateClaim} disabled={busy}>
          {busy ? 'Opening…' : 'Initiate claim →'}
        </button>
      )}
    </div>
  )
}
