export type Status =
  | 'queued'
  | 'searching'
  | 'success'
  | 'failed'
  | 'blocked'
  | 'pending'
  | 'claim_initiated'

export interface InsurerResult {
  id: string
  run_id: string
  insurer_name: string
  insurer_url: string | null
  adapter_type: 'live' | 'stub' | null
  status: Status
  amount_found: number | null
  detail: string | null
  updated_at: string
}

export interface SearchDetails {
  claimant_name: string
  deceased_name: string
  pan: string
  dob: string
  policy_number?: string
  mobile?: string
}
