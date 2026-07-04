# Deploying BimaSarathi to Railway

This is a **monorepo with two services**. Deploy them as **two Railway services from the
same GitHub repo**, each with its own Root Directory. Deploy the backend first (the
frontend needs the backend's URL baked in at build time).

> Copy the secret values from your local `orchestrator/.env` and `web/.env.local`.
> Do NOT commit them — this repo is public.

---

## 1. Backend service (orchestrator)

Heads-up: this runs a headless Chromium (cloakbrowser). It needs memory — budget
~1 GB per concurrent agent. On Railway, use a plan with enough RAM and keep
`REAL_CONCURRENCY` low (2, or 1 if you hit out-of-memory).

1. In your Railway project, create a service from the GitHub repo
   `Supreet-Gupta/insurance-claims-automation` (or reuse the existing failed one).
2. **Settings → Source → Root Directory:** `orchestrator`
   (Railway will then build using `orchestrator/Dockerfile` automatically.)
3. **Variables** (Settings → Variables):
   ```
   SUPABASE_URL=<from orchestrator/.env>
   SUPABASE_ANON_KEY=<from orchestrator/.env>
   OPENAI_API_KEY=<from orchestrator/.env>
   OPENAI_MODEL=gpt-5-mini
   BROWSER_HEADLESS=true
   REAL_CONCURRENCY=2
   ```
   (`BROWSER_HEADLESS` and `REAL_CONCURRENCY` also default in the Dockerfile.)
4. Deploy. First build is slow (installs Chromium + browser-use, ~few min).
5. **Settings → Networking → Generate Domain.** Copy the public URL, e.g.
   `https://insurance-claims-automation-production.up.railway.app`.
6. Sanity check: open `<backend-url>/health` → should return `{"ok":true}`.

## 2. Frontend service (web)

1. Add a **second service** from the same repo.
2. **Settings → Source → Root Directory:** `web`
   (builds using `web/Dockerfile`.)
3. **Variables** — Vite bakes these at build time, so they must be set BEFORE the build:
   ```
   VITE_SUPABASE_URL=<from web/.env.local>
   VITE_SUPABASE_ANON_KEY=<from web/.env.local>
   VITE_ORCHESTRATOR_URL=<the backend public URL from step 1.5>
   ```
4. Deploy, then **Generate Domain** for the frontend. That URL is your live app.

## 3. Use it

Open the frontend URL. "Run sample demo" works instantly. "Search across all insurers"
runs the real stealth agents **headless** on the server (no visible windows online —
that part is local-only), streaming Success/Failed/Pending live via Supabase Realtime.

---

## Troubleshooting

- **Backend build fails on Chromium libs:** a system lib may be missing for your base
  image; add it to the `apt-get install` line in `orchestrator/Dockerfile`.
- **Out of memory / agent crashes:** lower `REAL_CONCURRENCY` to 1, or upgrade the plan.
- **Frontend can't reach backend (CORS/next to nothing happens):** confirm
  `VITE_ORCHESTRATOR_URL` is the backend's **https** domain and that you rebuilt the
  frontend after setting it (Vite bakes it at build time).
- **`/health` works but searches 500:** check `OPENAI_API_KEY` and the Supabase vars on
  the backend service.
