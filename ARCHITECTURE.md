# BimaSarathi — Architecture (2-Hour Build)

**Unclaimed Insurance Discovery Agent for Nominees**
Build target: working, demoable prototype in **2 hours**.
Stack: **Supabase** (Postgres + Realtime) · **Browser Use** (agentic browser) · **Vite + React** UI · **Python asyncio** orchestrator.

> This doc defines the architecture from scratch. It ignores the PRD's build mechanics (hand-written Playwright selector adapters) and replaces them with **Browser Use LLM agents** — theme-fit for the hackathon, and far faster to author per-insurer (a task prompt, not a selector map). The product idea is unchanged: a nominee enters details once; agents fan out across insurers' unclaimed-amount pages in parallel; results stream back live.

---

## 1. Design principles (why the architecture looks like this)

1. **Demo-safe by 60 minutes.** The entire end-to-end flow — form → fan-out → live grid → summary — works with **zero real browser automation** first (all insurers stubbed/simulated). Real Browser Use adapters are then swapped in as time allows. You always have something to show.
2. **Everything runs on the presenter's laptop.** No deploy step in the critical path. Frontend on `localhost:5173`, orchestrator on `localhost:8000`, Supabase in the cloud. (Vercel deploy is a stretch goal, not a dependency.)
3. **Supabase Realtime is the whole magic trick.** The visual payload is dozens of insurer cards flipping `queued → searching → found ₹X` live. That's a Postgres row-change subscription — no websockets, no queue infra.
4. **The agent replaces the adapter.** One generic Browser Use task template, parameterized per insurer (URL + accepted fields). Adding an insurer = adding one registry row, not writing code.
5. **Honesty is a state, not a bug.** `blocked` (OTP/CAPTCHA/bot-detection) and `pending` (no adapter yet) are first-class statuses shown in the UI.

---

## 2. Component architecture

```
        ┌────────────────────────┐
        │   Web UI (Vite+React)   │   localhost:5173
        │  • input form           │
        │  • live results grid    │◄──────────────┐
        │  • summary bar          │               │ Supabase Realtime
        └───────────┬────────────┘               │ (row changes on
                    │ POST /search                │  insurer_result)
                    ▼                             │
        ┌────────────────────────┐        ┌───────┴──────────┐
        │  Orchestrator (Python)  │──────► │  Supabase        │
        │  FastAPI + asyncio      │ writes │  • Postgres      │
        │  • create search_run    │        │  • Realtime ON   │
        │  • seed N insurer rows  │◄────── │  • insurer_result│
        │  • fan out (Semaphore)  │  reads │  • search_run    │
        └───────────┬────────────┘        │  • insurer_reg   │
                    │ spawns tasks         └──────────────────┘
        ┌───────────┴────────────┐
        │  Per-insurer tasks      │
        │  ┌──────────────────┐   │
        │  │ Browser Use Agent│   │  LIVE  (SBI Life, +1-2 more)
        │  │ (LLM + Chromium) │   │  navigate → fill → read → return
        │  └──────────────────┘   │
        │  ┌──────────────────┐   │
        │  │ Stub / Simulated │   │  PENDING (the long tail)
        │  │ staggered delay  │   │  → blocked "adapter pending"
        │  └──────────────────┘   │
        └────────────────────────┘
```

**Data flow, two paths:**
- **Submit path (HTTP):** UI `POST /search` → orchestrator creates `search_run`, seeds one `insurer_result` per insurer (all `queued`), returns `run_id`.
- **Result path (Realtime):** each task updates its `insurer_result` row → Supabase pushes the change → UI card flips instantly. The UI never polls.

---

## 3. Tech stack & rationale

| Layer | Choice | Why (for a 2-hour vibecode build) |
|---|---|---|
| UI | **Vite + React + TypeScript + Tailwind** | Instant scaffold, `@supabase/supabase-js` has a 3-line Realtime subscription. Tailwind = fast status-pill styling. |
| DB + Realtime | **Supabase** | Managed Postgres + Realtime out of the box. Replaces Kafka + websockets + a backend DB with one dashboard. |
| Orchestrator | **Python + FastAPI + asyncio** | Same language as Browser Use, so no cross-process bridge. `asyncio.Semaphore` gives bounded concurrency for free — no queue. |
| Browser agent | **Browser Use** (`browser-use`) + Claude (Sonnet) | LLM-driven form-filling: one task template works across heterogeneous insurer forms. No per-site selector code. Structured output → `{status, amount, detail}`. |
| Persistence client | **supabase-py** | Orchestrator writes row updates directly; RLS kept permissive for the single-user demo. |

**Why Browser Use over hardcoded Playwright (the PRD's choice):** the PRD is right that deterministic adapters are faster *per run* and more reliable on stage — but they cost ~15 min of DOM archaeology *each*, and we have 2 hours for the whole product. A Browser Use agent turns "write an adapter" into "write a sentence," so we can cover more insurers and adapt to layout differences for free. Trade-off accepted: slower (20–40s/run) and nondeterministic — mitigated by the **simulation fallback** (§6) so the on-stage visual never depends on a live site behaving.

---

## 4. Data model (Supabase)

```sql
-- One search a nominee kicks off.
create table search_run (
  id            uuid primary key default gen_random_uuid(),
  claimant_name text,
  deceased_name text,
  pan           text,
  dob           date,
  policy_number text,          -- optional (most nominees won't have it)
  mobile        text,          -- optional
  status        text default 'running',   -- running | done
  created_at    timestamptz default now()
);

-- One row per insurer per run. This is the table the UI watches.
create table insurer_result (
  id            uuid primary key default gen_random_uuid(),
  run_id        uuid references search_run(id) on delete cascade,
  insurer_name  text,
  insurer_url   text,
  adapter_type  text,          -- 'live' | 'stub'
  status        text default 'queued',
  -- queued | searching | found | not_found | blocked | claim_initiated | error
  amount_found  numeric,       -- nullable
  detail        text,          -- 'OTP required', 'adapter pending', error msg…
  updated_at    timestamptz default now()
);

-- Static seed: the insurer directory (name, URL, whether a live adapter exists).
create table insurer_registry (
  id            uuid primary key default gen_random_uuid(),
  insurer_name  text unique,
  insurer_url   text,
  adapter_type  text default 'stub',   -- flip 3-5 rows to 'live'
  fields_hint   text                   -- e.g. 'name+dob+pan (min 2)'
);

alter publication supabase_realtime add table insurer_result;   -- enable Realtime
```

**RLS:** for the demo, enable RLS then add permissive `anon` read policy on `insurer_result`/`search_run`; orchestrator writes with the **service_role** key (bypasses RLS). Single-user, no auth.

---

## 5. Browser Use agent design

One reusable task template, filled per insurer from the registry. Structured output enforced via a Pydantic model so the orchestrator gets clean data.

```python
# Pseudocode — the shape, not the final code
class InsurerOutcome(BaseModel):
    status: Literal["found", "not_found", "blocked", "error"]
    amount_found: float | None
    detail: str

TASK = """
Go to {url}. This is an insurer's 'unclaimed amount' disclosure page.
Search for unclaimed policy money belonging to this person:
  name: {deceased_name}   DOB: {dob}   PAN: {pan}   policy no: {policy_number}
Fill only the fields the form accepts ({fields_hint}). Submit.
- If a matching unclaimed amount is shown, return status=found with the ₹ amount.
- If the form says no records, return status=not_found.
- If blocked by OTP, CAPTCHA, or login, return status=blocked with the reason.
Do not attempt to solve CAPTCHAs or bypass bot detection.
"""
```

**Per-task lifecycle** (each writes its own row):
`searching` → run agent → parse `InsurerOutcome` → `found`/`not_found`/`blocked`/`error` (+ `amount_found`, `detail`). Wrapped in try/except: any exception writes `error` and never kills the fan-out.

**Adapter roster for the demo (lead with SBI Life):**

| Insurer | Adapter | Note |
|---|---|---|
| **SBI Life** | **live** | Loosest form (name + DOB + PAN, no policy no). **Build & demo first.** |
| HDFC Life / Max Life / ICICI Pru | live *if time* | Clone the SBI task template. |
| LIC | stub | Active bot detection + needs policy number → present as the "v3 stealth" case. |
| ~50 others | stub | Seeded as `queued → blocked "adapter pending"` for the fan-out visual. |

---

## 6. Demo safety: simulation fallback

A `DEMO_MODE` env flag on the orchestrator. When `true`, **live** adapters are replaced by a scripted outcome (e.g. SBI Life → `found ₹47,300` after an ~8s staggered delay) instead of hitting the real site. Same code path, same Realtime writes — the audience sees an identical flow. This means a flaky venue network or a mid-pitch layout change on an insurer site **cannot** break the demo. Run live if the dry-run passed; flip to `DEMO_MODE` if it didn't.

Stub insurers always resolve on a staggered timer to `blocked` — this is what makes "dozens of cards light up at once" read visually without fabricating `found` results.

---

## 7. Two-hour build plan

The ordering guarantees a working demo at the **60-minute** mark, before any real browser code exists.

| Time | Task | Milestone |
|---|---|---|
| **0:00–0:15** | Supabase: create project, run §4 SQL, enable Realtime on `insurer_result`, seed `insurer_registry` (~50 rows, 3–5 flagged `live`). Copy URL + anon + service keys. | DB live |
| **0:15–0:35** | Vite React app: input form + results grid + summary bar. Wire `supabase.channel().on('postgres_changes')`. Test against **manually inserted rows** — watch a card flip by editing a row in the Supabase dashboard. | **Realtime visibly works** |
| **0:35–1:00** | FastAPI `POST /search`: create `search_run`, seed `insurer_result` rows from registry, `asyncio` fan-out. Implement **stubs only** — staggered `queued→searching→blocked`. | **Full end-to-end demo works, 100% simulated** |
| **1:00–1:30** | First real Browser Use adapter (SBI Life): task template + `InsurerOutcome` structured output. Test standalone, then wire into the fan-out behind the `live` flag. | First real `found ₹X` |
| **1:30–1:45** | Add 1–2 more live adapters (clone template) *or* stop and harden. Add `DEMO_MODE` simulation fallback (§6). | Coverage / safety |
| **1:45–2:00** | UI polish: status pill colors, staggered CSS transitions, summary bar totals, **Initiate claim** button → `claim_initiated` (opens pre-filled form for one insurer). End-to-end dry run with a seeded test identity; fix the one thing that breaks. | Ship |

**Cut lines (if behind):** drop extra live adapters → SBI Life only, rest simulated. Drop `Initiate claim` real form-open → just flip status. Never cut: the stubbed fan-out + Realtime grid (that's the demo).

---

## 8. Non-goals (unchanged from PRD — state them if asked)

CAPTCHA solving · OTP for a deceased policyholder · end-to-end claim settlement (we stop at "claim initiated") · all 57 insurers automated · auth/RBAC · payments/fraud-graph/compliance tooling. The `blocked` state is the honest answer for OTP/bot-detected portals, not a defect to hide.

---

## 9. What changes for production (post-demo)

- Move the orchestrator + Browser Use off the laptop → **Browser Use Cloud** or a container with hosted Chromium, triggered by a Supabase Edge Function on `search_run` insert (fully decouples UI from orchestrator; no local HTTP).
- Add auth (Supabase Auth) + RLS scoped per user + an audit trail.
- Expand the live-adapter roster, prioritized by unclaimed-amount volume; add OTP relay where a living claimant's own mobile is usable; add claim-status monitoring after initiation.
```
