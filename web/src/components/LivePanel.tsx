import type { InsurerResult } from '../types'

function domain(url: string | null) {
  if (!url) return ''
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return ''
  }
}

export function LivePanel({ results }: { results: InsurerResult[] }) {
  // Free tier = 1 concurrent, so there's exactly one live session at a time.
  const active = results.find((r) => r.status === 'searching' && r.live_view_url)

  return (
    <aside className="live-panel">
      <div className="live-panel-head">
        <span className={`live-dot ${active ? 'on' : ''}`} />
        {active ? (
          <div className="live-meta">
            <span className="live-label">Now searching</span>
            <strong>{active.insurer_name}</strong>
            <span className="live-domain">{domain(active.insurer_url)}</span>
          </div>
        ) : (
          <div className="live-meta">
            <span className="live-label">Live agent view</span>
            <strong>Waiting for the next insurer…</strong>
          </div>
        )}
      </div>

      {active && active.live_view_url ? (
        <iframe
          key={active.id}
          className="live-frame"
          src={active.live_view_url}
          title={`${active.insurer_name} live`}
          sandbox="allow-scripts allow-same-origin"
        />
      ) : (
        <div className="live-empty">
          The agent's browser appears here while it searches each insurer, one at a time.
        </div>
      )}
    </aside>
  )
}
