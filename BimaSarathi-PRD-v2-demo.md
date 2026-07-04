# BimaSarathi — PRD v2.0 (Demo Build)

**Unclaimed Insurance Discovery Agent for Nominees**
Version 2.0 | July 2026 | Build target: working prototype in ~3 hours
Stack: Supabase (DB + Realtime) · Playwright (browser agent) · lightweight web UI

---

## 0. What changed from v1.0 (read this first)

v1.0 specified a 10-layer "Agent Operating System" spanning Temporal, Kafka, ClickHouse, Neo4j, Weaviate, a 6-model Grok router, payments, RBAC/ABAC, and 5-phase GTM. None of that is needed to demo the core idea, and most of it is undemoable in the available time.

**The core idea, stated plainly:** a nominee doesn't know which insurer holds their deceased relative's policy. They enter identifying details once. The agent searches across insurers' unclaimed-amount pages in parallel and shows, in realtime, where money was found and where a claim was initiated.

v2.0 builds *only* that, for a curated subset of insurers, honestly labelling what is automated vs pending.

---

## 1. Ground truth about the target portals (verified)

The Bima Bharosa page (`/Home/UnclaimedAmount`) is a **directory of outbound links**, not a search interface. It lists:

- 25 life insurers
- 26 general insurers
- 6 health insurers

Each entry links to that insurer's **own** unclaimed-amount page. There is **no unified search endpoint**. Consequences:

- Each insurer is a separate adapter. No shared schema, no shared auth.
- Page types vary: (a) live search forms (policy no. / name / DOB), (b) static disclosure tables or PDFs you filter locally, (c) OTP-gated forms.
- OTP-gated pages are blocked for a deceased policyholder — treat as manual.
- CAPTCHA-gated pages are out of scope for the demo — do not attempt to solve them.

**Design implication:** the product is a registry of per-insurer adapters behind one orchestrator. For the demo, 3–5 adapters are real; the rest are declared "pending" and rendered as queued.

---

## 2. Scope

### In scope (demo)
- One UI form capturing claimant + policyholder details.
- Orchestrator that fans out across a curated insurer list.
- 3–5 **real** Playwright adapters against insurer unclaimed-amount pages that have plain public search forms (no CAPTCHA/OTP).
- Supabase persistence + Realtime pushing per-insurer status to the UI live.
- Status states surfaced per insurer: `queued → searching → found (₹amount) / not_found / blocked → claim_initiated`.

### Out of scope (demo) — say so if asked
- All 57 insurers automated.
- CAPTCHA solving; OTP handling; deceased-mobile SIM reactivation.
- Actual end-to-end claim settlement (filed → paid). Demo stops at "claim initiated / form pre-filled."
- Payments, fraud graph, IRDAI compliance tooling, multi-model LLM routing, Temporal/Kafka/Neo4j/ClickHouse.
- Auth/RBAC. Single-user demo.

---

## 3. Architecture (thin)

```
[Web UI]  --submit details-->  [Orchestrator API]
   ^                                  |
   | Supabase Realtime                | spawns N adapter tasks
   |                                  v
[Supabase Postgres] <--writes--  [Playwright adapters]  (1 per insurer)
                                       |  real: 3-5 insurers
                                       |  stub: the rest (status=pending)
```

Components:
| Component | Tech | Job |
|---|---|---|
| UI | React (Vite) or plain HTML+JS | Capture details; subscribe to Supabase Realtime; render live status grid |
| Orchestrator | Node or Python (FastAPI) | Create a `search_run`, enqueue one `insurer_result` row per insurer, launch adapters concurrently |
| Adapters | Playwright | Per-insurer scripts. Navigate, fill form, read result, write status back to Supabase |
| DB + Realtime | Supabase | Store runs/results; push row changes to UI |

No queue infra needed for the demo — run adapters with bounded concurrency (e.g. `Promise.all` over a pool of ~5, or `asyncio.gather`). Supabase Realtime replaces Kafka/websockets.

---

## 4. Data model (Supabase)

```sql
create table search_run (
  id uuid primary key default gen_random_uuid(),
  claimant_name text,
  deceased_name text,
  pan text,
  dob date,
  policy_number text,        -- optional
  mobile text,               -- optional
  created_at timestamptz default now(),
  status text default 'running'  -- running | done
);

create table insurer_result (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references search_run(id),
  insurer_name text,
  insurer_url text,
  adapter_type text,         -- 'live' | 'stub'
  status text default 'queued',
  -- queued | searching | found | not_found | blocked | claim_initiated | error
  amount_found numeric,      -- nullable
  detail text,               -- e.g. 'OTP required', 'no public form', error msg
  updated_at timestamptz default now()
);
```

Enable Realtime on `insurer_result`. The UI subscribes with `run_id=eq.<id>` and renders one card/row per insurer, updating on every change.

---

## 5. UX flow

1. **Input screen.** Fields: claimant name, deceased name, PAN, DOB, policy number (optional), mobile (optional). One button: **Search across insurers**.
2. **Live results grid.** On submit, immediately render every insurer as a card in `queued` state, then watch them flip live:
   - grey `queued` → blue `searching` → green `found ₹X` / neutral `not found` / amber `blocked (OTP/CAPTCHA)` → green `claim initiated`.
3. **Summary bar.** Running totals: *N insurers searched · M with unclaimed amounts · ₹T total discovered.*
4. **Per-card action.** For `found`, a **Initiate claim** button that (demo) flips status to `claim_initiated` and, where the insurer has a claim/refund form, opens it pre-filled. For `blocked`, show the manual next step.

The realtime flip is the demo's whole visual payload. Make the state transitions visible and slightly staggered.

---

## 6. Insurer adapter strategy

### Architecture decision: hardcode the five, behind an adapter interface

**Decision:** each insurer gets a hand-written, selector-based Playwright adapter. No LLM in the fill loop for the demo. (high confidence at this scope)

Rationale — the five unclaimed-amount pages were inspected and are heterogeneous, fixed, low-churn targets (IRDAI-mandated disclosure pages that rarely redesign). For a small static set, deterministic adapters are faster (~5–15s/run vs 20–60s for an LLM agent), free per run, debuggable, and reliable on stage. An adaptive LLM agent adds nondeterminism to a deterministic problem and does **not** help with the one genuinely hard part (bot detection), which is a browser-fingerprint problem, not a "what do I fill" problem.

**But** write every adapter behind one interface so an LLM-driven generic adapter can be dropped in later for the long tail / as a fallback when a hardcoded selector breaks (the v3 "Skyvern-style" path). Build the interface now; do not build the adaptive adapter now.

```
Adapter interface:
  run(details) -> { status, amount_found, detail }
    details = { deceased_name, dob, pan, policy_number? }
    status  ∈ found | not_found | blocked | error
```

Registry entry: `{ insurer_name, url, type: 'deterministic' | 'generic_llm', run }`. Orchestrator and UI are adapter-agnostic.

Each `run`: write `searching` → navigate (real, non-headless browser context) → fill the fields this insurer accepts → submit → parse result → write `found`/`not_found`/`blocked`/`error` + `amount_found` + `detail`. Wrap in try/catch; any failure writes `error` with the message and never crashes the run.

### The five (verified where noted — inspect the DOM in hour 1 before coding each)

| Insurer | Unclaimed-amount URL | Fields required | Notes |
|---|---|---|---|
| **SBI Life** | `sbilife.co.in/unclaimed-amount-disclosure` | **min 2 of** {name, policy no, DOB, PAN} | Loosest form; searchable on name+DOB+PAN with no policy number. **Build and demo this first.** |
| **ICICI Prudential** | `customer.iciciprulife.com/csr/unclaimedAmountAuthentication.htm` | policy no / DOB / PAN (via an "authentication" webflow step) | Spring webflow — expect a multi-step flow, not a single form submit. |
| **HDFC Life** | (inspect — under hdfclife.com customer service / unclaimed) | TBD (inspect) | Not yet inspected; assume bespoke. |
| **Max Life** | (inspect — under maxlifeinsurance.com) | TBD (inspect) | Not yet inspected; assume bespoke. |
| **LIC** | `merchant.licindia.in/LICEPS/portlets/visitor/unclaimedPolicyDues/UnclaimedPolicyDuesController.jpf` | policy no + name + DOB + PAN (**all four**) | Legacy JSP portlet. **Active bot detection** (blocked automated access on inspection). Effectively needs the policy number. Highest-value insurer but hardest path — budget for it failing live; keep it hardcoded but be ready to present it as the "needs stealth context / v3" case. |

Everything beyond these five registers in the UI as `queued → blocked` with an honest `detail` ("adapter pending"), so the fan-out reads visually without fabricating results.

---

## 7. 3-hour build plan

| Time | Task |
|---|---|
| 0:00–0:20 | Supabase project: create tables, enable Realtime on `insurer_result`, grab keys |
| 0:20–0:35 | Scaffold UI (Vite React or single HTML), form + empty results grid, Realtime subscription wired |
| 0:35–1:20 | Probe candidate insurer pages; write 3 real Playwright adapters; confirm they return a parseable result |
| 1:20–1:50 | Orchestrator: create run, seed `insurer_result` rows for full insurer list, run live adapters concurrently, resolve stubs to `blocked` |
| 1:50–2:20 | UI polish: status pills, staggered transitions, summary bar (count + total ₹) |
| 2:20–2:40 | `Initiate claim` action → `claim_initiated`; open pre-filled form for one insurer that has one |
| 2:40–3:00 | End-to-end dry run, seed a realistic test identity, fix the one thing that breaks on stage |

If an adapter fights you past ~15 min, demote it to stub and move on. Three working live adapters is enough to sell the concept.

---

## 8. Demo script (90 seconds)

1. "Nominee doesn't know where the policy is." Enter details, hit search.
2. Grid lights up: dozens of insurers flip to `searching` at once.
3. Live adapters resolve — one or two hit `found ₹X`, others `not found`, OTP ones `blocked`.
4. Summary bar ticks up to "₹X discovered across N insurers."
5. Click **Initiate claim** on a `found` card → `claim_initiated`, pre-filled form opens.
6. Close: "Every result is written to Supabase in realtime; adding an insurer is adding one adapter."

Lead with the fan-out visual, not the plumbing.

---

## 9. Honest caveats (know these before someone asks)

- **Coverage.** 3 of 57 insurers are real in the demo. Say so; don't imply full coverage.
- **ToS / automated access.** Some insurer and government portals prohibit automated access in their terms. This is fine for a prototype hitting public disclosure pages with a real nominee's own details, but it's a real constraint for production and worth naming. Do **not** solve CAPTCHAs or evade bot detection for the demo.
- **OTP for deceased policyholder.** Genuinely unsolved and out of scope. The `blocked` state is the honest answer, not a bug to hide.
- **Static-disclosure pages.** Some "unclaimed amount" pages are downloadable lists, not search forms — a different adapter pattern (download + local filter). Skip for the demo unless one is trivially parseable.
- **Realtime, not agentic-AI.** This prototype is browser automation + realtime DB. There is no LLM in the loop yet. If the pitch needs "agent," the honest version is: the LLM layer (adaptive form-filling for portals that change layout) is the v3 addition, not what's demoed here.
- **The policy-number paradox.** A nominee who doesn't know which insurer holds the policy almost certainly doesn't have the policy number. That is exactly the identifier LIC's form requires. So the discovery flow only truly works on insurers that accept name+DOB+PAN (e.g. SBI Life). Lead the demo with those; treat policy-number-gated insurers as a known limitation.
- **LIC bot detection is real, not theoretical.** LIC's unclaimed portal blocked automated access on inspection. It is the highest-value insurer and the hardest to automate. Do not stake the live demo on LIC resolving; show SBI Life as the working case and LIC as the "stealth-context, v3" case.

---

## 10. What v3 would add (post-demo, not now)
- LLM-driven adaptive adapters (handle layout changes / unseen forms) instead of hand-written selectors.
- More insurer adapters, prioritised by unclaimed-amount volume.
- OTP relay flow where a living claimant's own mobile is usable.
- Claim-status monitoring after initiation.
- Auth + multi-user + audit trail.
