# BimaSarathi

Unclaimed-insurance discovery agent for nominees. Enter a deceased policyholder's
details once; agents fan out across insurers' unclaimed-amount pages in parallel;
results stream back live. Web app (React + Supabase Realtime) with a Python
orchestrator that drives **Browser Use** agents server-side.

See `ARCHITECTURE.md` for the design and `BUILD_PLAN.md` for the build phases.

## Run it (two processes)

**1. Orchestrator** (FastAPI, port 8000)
```bash
cd orchestrator
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**2. Web app** (Vite, port 5173)
```bash
cd web
npm run dev
```

Open http://localhost:5173 → "Use sample identity" → "Search across all insurers".

## Two modes (chosen per search, not a global flag)

- **Real search** — the "Search across all insurers" button (enter real data).
  Runs live **Browser Use** agents on the 5 built insurers (SBI Life, HDFC Life,
  ICICI Pru, Max Life, LIC) and shows their actual **success / failed** state.
  Every other insurer shows **pending** (no adapter built). Needs `OPENAI_API_KEY`.
  Visible Chrome windows drive the sites (`BROWSER_HEADLESS=false`). Real outcomes
  are mostly `failed` (CAPTCHA/access-denied) — that's the truth, not a bug.
- **Sample demo** — the "Run sample demo" button. Scripted showcase with fictional
  data: ~90% success / ~10% blocked. Clearly not real results. No browser, no LLM.

Card links: built insurers point to their own verified unclaimed-amount page;
everything else points to the IRDAI Bima Bharosa unclaimed directory.

Tunables in `orchestrator/.env`: `OPENAI_MODEL`, `BROWSER_HEADLESS`, `REAL_CONCURRENCY`.

## Stack
- **Supabase** — Postgres + Realtime (project `bimasarathi`, region ap-south-1)
- **Web** — Vite + React + TypeScript, `@supabase/supabase-js`
- **Orchestrator** — FastAPI + asyncio fan-out
- **Agents** — `browser-use` 0.13 + OpenAI, structured output → `{status, amount, detail}`
