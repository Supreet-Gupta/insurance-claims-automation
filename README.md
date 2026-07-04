# BimaSarathi

**An AI agent that finds unclaimed insurance money left behind for a nominee.**

When someone passes away, their family often doesn't know *which* insurer holds a
policy — let alone the policy number. Meanwhile thousands of crores in maturity and
death benefits sit unclaimed across dozens of Indian insurers, each with its own
"unclaimed amount" disclosure page. BimaSarathi takes a nominee's details once, then
sends browser agents to search every insurer's page **in parallel**, streaming back —
live — where the search went through, where it was blocked, and where money was found.

> Built for the **Browser Use Hackathon**. It's a working prototype, and it's honest
> about what's real vs. demo (see [Status & limitations](#status--limitations)).

**Live demo:** https://bimasarathi-web-production.up.railway.app

---

## What it does

1. You enter the deceased policyholder's details once (name, PAN, DOB, optional policy no.).
2. The app fans out across insurers' unclaimed-amount pages.
3. Each insurer resolves live in a grid: `queued → searching → success / failed / pending`.
4. A **live panel** on the right shows the agent's actual browser as it works each site —
   you watch it open the real insurer page, fill the form, and submit.

Two ways to run a search:

- **"Run sample demo"** — a scripted showcase with fictional data (~90% success). No
  browser, no LLM. This is clearly labelled and is *not* real search results.
- **"Search across all insurers"** — the real thing. Live AI browser agents drive the
  actual insurer sites and report their **honest** outcome. Insurers we haven't wired
  up yet show as `pending`.

Success criterion for a real search: the agent **opened the page, filled the fields,
and submitted**. Because the demo data is fictional, a "no record found" after a
successful submit still counts as success — the agent did its job.

---

## How it works

```
        Web UI (React + Supabase Realtime)
              │  submit details            ▲ live status + live-view URL
              ▼                            │  (Supabase Realtime)
        Orchestrator (FastAPI, asyncio fan-out)
              │  one agent per insurer
              ▼
        Browser Use agent  ──drives──▶  Browserbase (hosted stealth browser)
                                          └─ live-view iframe shown in the UI
              │                        (or cloakbrowser stealth Chromium, local fallback)
              ▼
        writes results → Supabase Postgres → Realtime → UI
```

- **Browser layer:** each insurer gets its own browser session. In production we use
  **Browserbase** (hosted, stealthy, and it gives an embeddable **live view** of the
  session). Browser Use connects to it over CDP. If Browserbase isn't configured, it
  automatically falls back to **cloakbrowser** — a local stealth Chromium — over CDP.
  Both defeat the WAF/bot-detection that blocks a vanilla headless browser.
- **The agent:** [Browser Use](https://github.com/browser-use/browser-use) + an OpenAI
  model. No hand-written selectors — one task prompt adapts to each insurer's form.
- **Realtime:** every status change (and the live-view URL) is written to Supabase and
  pushed to the browser instantly. No polling, no websockets to manage.

## Tech stack

| Layer | Tech |
|---|---|
| Web UI | Vite + React + TypeScript, `@supabase/supabase-js` |
| DB + Realtime | Supabase (Postgres + Realtime) |
| Orchestrator | Python, FastAPI, asyncio |
| Browser agent | Browser Use + OpenAI (`gpt-5-mini`) |
| Browser | Browserbase (hosted) · cloakbrowser (local fallback) |
| Hosting | Railway (two services, Docker) |

---

## Status & limitations (read this before judging results)

This is a prototype. It's built to be **honest**, so:

- **Real vs. demo.** Demo mode is scripted theatre. Only "Search across all insurers"
  runs real agents.
- **Coverage.** A curated set of insurers is "live" (wired for real search); the rest
  show `pending`. All ~37 have verified reference URLs in the DB.
- **CAPTCHA / OTP.** Some insurer pages require a CAPTCHA or OTP. We do **not** solve or
  bypass these — those searches honestly report `failed`. (Browserbase offers CAPTCHA
  solving as a paid add-on; off by default in this repo's settings beyond the flag.)
- **The policy-number paradox.** A nominee who doesn't know the insurer usually doesn't
  have the policy number — which is exactly what some forms require. Those fail honestly.
- **Geo-IP.** Browserbase runs from the US/EU. Some Indian portals may behave differently
  from a non-India IP; enable `BROWSERBASE_PROXIES=true` (India residential, paid) if so.
- **Automated access & ToS.** This hits public disclosure pages with a real nominee's own
  details. Some portals' terms restrict automated access — fine for a prototype, a real
  constraint for production. Don't use this to hammer sites or evade protections.

---

## Run it locally

**Prereqs:** Node 18+, Python 3.11+, a Supabase project, an OpenAI API key.
(Optional: a Browserbase account for the hosted live-view browser.)

```bash
# 1. Backend (FastAPI + agent)
cd orchestrator
cp .env.example .env          # fill in your keys (see below)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# using the local cloakbrowser fallback? install its Chromium once:
python -m cloakbrowser install
uvicorn main:app --host 127.0.0.1 --port 8000

# 2. Frontend (in another terminal)
cd web
cp .env.local.example .env.local   # fill in Supabase URL/key + orchestrator URL
npm install
npm run dev                        # http://localhost:5173
```

You'll also need the database schema. The tables are `search_run`, `insurer_result`
(Realtime enabled), and `insurer_registry`. See `ARCHITECTURE.md` for the schema, and
seed `insurer_registry` with the insurers you want to search.

### Configuration

`orchestrator/.env` (see `orchestrator/.env.example`):

| Var | What |
|---|---|
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | your Supabase project |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | the LLM (default `gpt-5-mini`) |
| `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` | optional; enables hosted browser + live view |
| `BROWSERBASE_SOLVE_CAPTCHAS`, `BROWSERBASE_PROXIES` | Browserbase options |
| `BROWSER_HEADLESS` | cloakbrowser fallback: `false` = visible windows locally |
| `REAL_CONCURRENCY` | how many insurers run at once (Browserbase free tier = 1) |

`web/.env.local` (see `web/.env.local.example`): `VITE_SUPABASE_URL`,
`VITE_SUPABASE_ANON_KEY`, `VITE_ORCHESTRATOR_URL`.

## Deploy

Deployed on Railway as two Docker services (backend `orchestrator/`, frontend `web/`).
Full step-by-step in **[DEPLOY.md](./DEPLOY.md)**.

---

## Using / forking this

Yes — clone or fork it. To run your own instance you need:

1. Your own **Supabase** project (create the schema, enable Realtime on `insurer_result`).
2. An **OpenAI** API key.
3. Optionally a **Browserbase** account for the hosted browser + live view (otherwise it
   uses the local cloakbrowser fallback).

It's wired for Indian insurers, but the adapter is generic (URL + a task prompt), so you
can point it at any set of "search this page for me" targets by editing the registry.

**Please use it responsibly** — for legitimate unclaimed-amount lookups with the
claimant's own details, not for scraping at scale or evading site protections.

## Repo structure

```
web/           React frontend (Vite)
orchestrator/  FastAPI orchestrator + Browser Use agent (adapters/)
ARCHITECTURE.md  design + data model
BUILD_PLAN.md    how it was built
DEPLOY.md        Railway deployment guide
```

## License

No formal license yet — it's a hackathon prototype shared for reference. If you plan to
build on it, add a license first (e.g. MIT).

## Credits

Built with [Browser Use](https://github.com/browser-use/browser-use),
[cloakbrowser](https://cloakbrowser.dev), [Browserbase](https://browserbase.com), and
[Supabase](https://supabase.com), for the Browser Use Hackathon.
