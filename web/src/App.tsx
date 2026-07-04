import { useCallback, useEffect, useRef, useState } from 'react'
import { supabase, ORCHESTRATOR_URL } from './lib/supabase'
import type { InsurerResult, SearchDetails } from './types'
import { SearchForm } from './components/SearchForm'
import { SummaryBar } from './components/SummaryBar'
import { ResultsGrid } from './components/ResultsGrid'

export default function App() {
  const [runId, setRunId] = useState<string | null>(null)
  const [results, setResults] = useState<InsurerResult[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const channelRef = useRef<ReturnType<typeof supabase.channel> | null>(null)

  const upsert = useCallback((row: InsurerResult) => {
    setResults((prev) => {
      const i = prev.findIndex((r) => r.id === row.id)
      if (i === -1) return [...prev, row]
      const next = prev.slice()
      next[i] = row
      return next
    })
  }, [])

  // Subscribe to realtime + hydrate whenever we have a run.
  useEffect(() => {
    if (!runId) return

    const channel = supabase
      .channel(`run:${runId}`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'insurer_result', filter: `run_id=eq.${runId}` },
        (payload) => upsert(payload.new as InsurerResult),
      )
      .subscribe()
    channelRef.current = channel

    // Hydrate any rows that already exist (seeded before subscribe).
    supabase
      .from('insurer_result')
      .select('*')
      .eq('run_id', runId)
      .then(({ data }) => {
        if (data) (data as InsurerResult[]).forEach(upsert)
      })

    return () => {
      supabase.removeChannel(channel)
      channelRef.current = null
    }
  }, [runId, upsert])

  const handleSubmit = async (details: SearchDetails, demo: boolean) => {
    setSubmitting(true)
    setError(null)
    setResults([])
    try {
      const res = await fetch(`${ORCHESTRATOR_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...details, demo }),
      })
      if (!res.ok) throw new Error(`Orchestrator returned ${res.status}`)
      const data = await res.json()
      setRunId(data.run_id)
    } catch (e) {
      setError(
        `Could not reach the orchestrator at ${ORCHESTRATOR_URL}. Is it running? (${
          e instanceof Error ? e.message : e
        })`,
      )
    } finally {
      setSubmitting(false)
    }
  }

  const reset = () => {
    setRunId(null)
    setResults([])
    setError(null)
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">बीमा</span>
          <div>
            <h1>BimaSarathi</h1>
            <p className="tagline">Find unclaimed insurance left behind for you</p>
          </div>
        </div>
        {runId && (
          <button className="ghost-btn" onClick={reset}>
            New search
          </button>
        )}
      </header>

      {error && <div className="banner error">{error}</div>}

      {!runId ? (
        <SearchForm onSubmit={handleSubmit} submitting={submitting} />
      ) : (
        <main className="results">
          <SummaryBar results={results} />
          <ResultsGrid results={results} runId={runId} />
        </main>
      )}

      <footer className="foot">
        Prototype · results stream live from Supabase
        {runId ? ` · ${results.length} insurers in this run` : ''}
      </footer>
    </div>
  )
}
