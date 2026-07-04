# BimaSarathi — Build Plan (2 Hours)

Execution plan derived from `ARCHITECTURE.md`. Sequenced so a **fully working demo exists at the 60-minute mark** (all simulated), before any real browser automation is written.

**Product type:** web app (React UI + Supabase Realtime). Browser Use runs server-side on the orchestrator (local laptop for the demo). The user installs nothing.

---

## Repo layout (target)

```
Browser Use Hackathon/
├── db/
│   └── schema.sql              # tables + realtime + registry seed
├── web/                        # Vite + React + Tailwind
│   ├── .env.local              # VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
│   └── src/
│       ├── lib/supabase.ts
│       ├── App.tsx
│       └── components/{SearchForm,ResultsGrid,InsurerCard,SummaryBar}.tsx
├── orchestrator/               # Python FastAPI + Browser Use
│   ├── .env                    # SUPABASE_URL, SUPABASE_SERVICE_KEY, ANTHROPIC_API_KEY, DEMO_MODE
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app, POST /search
│   ├── orchestrator.py         # create run, seed rows, asyncio fan-out
│   ├── db.py                   # supabase-py client + row writers
│   ├── registry.py             # insurer seed list
│   └── adapters/
│       ├── base.py             # InsurerOutcome model + interface
│       ├── stub.py             # simulated (staggered → blocked)
│       └── sbi_life.py         # Browser Use live adapter
├── ARCHITECTURE.md
└── BUILD_PLAN.md
```

---

## Prerequisites (do before the timer starts)

- [ ] **Supabase project** — I can create + configure it via the Supabase MCP, or you point me at an existing one (need URL + anon key + service_role key).
- [ ] **LLM API key** for Browser Use — Anthropic (Claude) preferred. In `orchestrator/.env`.
- [ ] **Local runtimes** — Node 18+ and Python 3.11+ on the demo laptop.
- [ ] **`browser-use` installs** — `pip install browser-use && playwright install chromium`.

---

## Phase 1 — Supabase schema + seed · (0:00–0:15)
**Deliverable:** live DB with Realtime on.
- [ ] Apply `db/schema.sql`: `search_run`, `insurer_result`, `insurer_registry`.
- [ ] `alter publication supabase_realtime add table insurer_result`.
- [ ] Enable RLS; permissive `anon` read policy on both watched tables (orchestrator writes via service_role).
- [ ] Seed `insurer_registry` (~50 rows; flag **SBI Life** + 2–4 others as `live`, rest `stub`).

**Done when:** I can edit an `insurer_result` row in the dashboard and it's queryable.

## Phase 2 — Frontend + Realtime · (0:15–0:35)
**Deliverable:** live grid that reacts to row changes.
- [ ] `npm create vite@latest web -- --template react-ts`; add Tailwind + `@supabase/supabase-js`.
- [ ] `SearchForm` (claimant, deceased, PAN, DOB, optional policy no + mobile) → one button.
- [ ] `ResultsGrid` + `InsurerCard` (status pill) + `SummaryBar` (count found · total ₹).
- [ ] Subscribe: `supabase.channel().on('postgres_changes', {table:'insurer_result', filter:'run_id=eq.<id>'})`.

**Done when:** editing a row in the dashboard flips a card in the UI live. *(No orchestrator yet.)*

## Phase 3 — Orchestrator + stub fan-out · (0:35–1:00) ⭐ DEMO WORKS HERE
**Deliverable:** full end-to-end flow, 100% simulated.
- [ ] FastAPI `POST /search`: create `search_run`, seed one `insurer_result` per registry row (`queued`), return `run_id`.
- [ ] `asyncio` fan-out with `Semaphore(3)`.
- [ ] **Stubs only:** each staggered `queued → searching → blocked "adapter pending"`; SBI Life stub-scripts a `found ₹X` for a realistic visual.
- [ ] Wire `SearchForm` submit → `POST /search`.

**Done when:** submit → dozens of cards light up and resolve live; summary ticks up. **This is the safety net.**

## Phase 4 — First live Browser Use adapter (SBI Life) · (1:00–1:30)
**Deliverable:** one real `found ₹X`.
- [ ] `adapters/base.py`: `InsurerOutcome{status, amount_found, detail}` + `run(details)` interface.
- [ ] `adapters/sbi_life.py`: Browser Use `Agent` with the parameterized task template + structured output.
- [ ] Test standalone against `sbilife.co.in/unclaimed-amount-disclosure`, then wire behind the `live` flag.
- [ ] try/except → `error` on any failure (never crashes the fan-out).

**Done when:** SBI Life card resolves from a real page run.

## Phase 5 — More adapters / safety fallback · (1:30–1:45)
**Deliverable:** coverage or hardening.
- [ ] Clone template for 1–2 more (HDFC / Max / ICICI) **if** SBI was clean, else stop.
- [ ] `DEMO_MODE` env flag: when `true`, live adapters return scripted outcomes on the same code path.

**Done when:** `DEMO_MODE=true` reproduces the full flow with no network dependency.

## Phase 6 — Polish + Initiate claim + dry run · (1:45–2:00)
**Deliverable:** ship-ready.
- [ ] Status pill colors + staggered CSS transitions; summary-bar totals.
- [ ] **Initiate claim** on a `found` card → `claim_initiated` (open one pre-filled insurer form).
- [ ] End-to-end dry run with a seeded test identity; fix the one thing that breaks.

**Done when:** the 90-second demo script runs clean start to finish.

---

## Cut lines (if behind)
1. Extra live adapters → SBI Life only, rest simulated.
2. Real pre-filled form open → just flip status to `claim_initiated`.
3. **Never cut:** stubbed fan-out + Realtime grid + summary bar. That's the demo.

## Definition of done (demo)
Submit a test identity → grid fans out live → ≥1 real `found ₹X` (or `DEMO_MODE`) → summary shows "₹X across N insurers" → Initiate claim flips a card. All state persisted in Supabase, pushed via Realtime.
