import { useState } from 'react'
import type { SearchDetails } from '../types'

interface Props {
  onSubmit: (details: SearchDetails, demo: boolean) => void
  submitting: boolean
}

const SAMPLE: SearchDetails = {
  claimant_name: 'Priya Sharma',
  deceased_name: 'Rajesh Sharma',
  pan: 'ABCPS1234K',
  dob: '1962-08-14',
  policy_number: '',
  mobile: '',
}

export function SearchForm({ onSubmit, submitting }: Props) {
  const [d, setD] = useState<SearchDetails>({
    claimant_name: '',
    deceased_name: '',
    pan: '',
    dob: '',
    policy_number: '',
    mobile: '',
  })

  const set = (k: keyof SearchDetails) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setD((prev) => ({ ...prev, [k]: e.target.value }))

  const valid = d.claimant_name && d.deceased_name && (d.pan || d.dob || d.policy_number)

  const runReal = (e: React.FormEvent) => {
    e.preventDefault()
    if (valid) onSubmit(d, false)
  }
  const runDemo = () => onSubmit(SAMPLE, true)

  return (
    <main className="form-wrap">
      <form className="card form" onSubmit={runReal}>
        <div className="form-intro">
          <h2>Whose policy are we looking for?</h2>
          <p>
            Enter the details of the person who passed away. We run real browser agents
            against each insurer's unclaimed-amount page and show, honestly, where the
            search went through and where it was blocked.
          </p>
        </div>

        <div className="grid2">
          <label>
            Your name (nominee)
            <input value={d.claimant_name} onChange={set('claimant_name')} placeholder="e.g. Priya Sharma" />
          </label>
          <label>
            Policyholder's name
            <input value={d.deceased_name} onChange={set('deceased_name')} placeholder="e.g. Rajesh Sharma" />
          </label>
          <label>
            Policyholder's PAN
            <input value={d.pan} onChange={set('pan')} placeholder="ABCPS1234K" />
          </label>
          <label>
            Date of birth
            <input type="date" value={d.dob} onChange={set('dob')} />
          </label>
          <label>
            Policy number <span className="opt">optional</span>
            <input value={d.policy_number} onChange={set('policy_number')} placeholder="if you have it" />
          </label>
          <label>
            Mobile <span className="opt">optional</span>
            <input value={d.mobile} onChange={set('mobile')} placeholder="registered mobile" />
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" className="primary-btn" disabled={!valid || submitting}>
            {submitting ? 'Starting…' : 'Search across all insurers'}
          </button>
          <button type="button" className="ghost-btn" onClick={runDemo} disabled={submitting}>
            Run sample demo →
          </button>
        </div>

        <p className="mode-note">
          <strong>Real search</strong> runs live agents on the 5 insurers we've built
          (SBI Life, HDFC Life, ICICI Pru, Max Life, LIC); the rest show as <em>pending</em>.
          <br />
          <strong>Sample demo</strong> is a scripted showcase with fictional data, clearly not real results.
        </p>
        {!valid && (
          <p className="hint">
            For a real search: enter both names plus PAN, DOB, or a policy number. Or try the sample demo.
          </p>
        )}
      </form>
    </main>
  )
}
