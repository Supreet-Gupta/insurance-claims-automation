import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL as string
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

export const supabase = createClient(url, anonKey, {
  realtime: { params: { eventsPerSecond: 20 } },
})

export const ORCHESTRATOR_URL =
  (import.meta.env.VITE_ORCHESTRATOR_URL as string) || 'http://localhost:8000'

// IRDAI's official unclaimed-amounts directory — the reference page for any
// insurer we haven't built a specific adapter for.
export const REFERENCE_DIRECTORY_URL =
  'https://bimabharosa.irdai.gov.in/Home/UnclaimedAmount'
