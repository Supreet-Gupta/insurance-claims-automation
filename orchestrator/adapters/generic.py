"""Generic real adapter — a Browser Use agent driving a browser over CDP.

Two browser backends, chosen by env:
- BROWSERBASE (BROWSERBASE_API_KEY + BROWSERBASE_PROJECT_ID set): a hosted stealth
  browser. We create a session, hand its live-view URL to the UI (so the user watches
  the agent work in an iframe), and point browser-use at its CDP endpoint.
- cloakbrowser (fallback, local): a stealth Chromium we launch ourselves, exposing a
  CDP port. Headless in a container, visible windows locally.

Honest outcomes only: success (opened + filled + submitted) / failed (stopped before
submit: access denied / CAPTCHA / OTP / required field unfillable / no form).
"""
import asyncio
import os
import socket
import urllib.request
import zlib

import httpx
from browser_use import Agent, BrowserSession, ChatOpenAI

from .base import InsurerOutcome

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
HEADLESS = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"

BB_API_KEY = os.getenv("BROWSERBASE_API_KEY")
BB_PROJECT_ID = os.getenv("BROWSERBASE_PROJECT_ID")
BB_SOLVE_CAPTCHAS = os.getenv("BROWSERBASE_SOLVE_CAPTCHAS", "true").lower() == "true"
BB_PROXIES = os.getenv("BROWSERBASE_PROXIES", "false").lower() == "true"
USE_BROWSERBASE = bool(BB_API_KEY and BB_PROJECT_ID)
BB_BASE = "https://api.browserbase.com/v1"

TASK = """You are checking an insurer's PUBLIC 'unclaimed amount' disclosure page \
for money owed to a policyholder, using the details their nominee provided.

Insurer page: {url}
Fields this page tends to use: {fields_hint}

Details you have:
  name: {name}
  date of birth: {dob}
  PAN: {pan}{policy_line}

Steps:
1. Go to the page. If it doesn't load or you get 'access denied', that is status "failed".
2. Find the unclaimed-amount search form. It may not be obvious:
   - Scroll down; it is often below the fold.
   - It may be behind a tab, an accordion, or a toggle like 'Individual Policy' vs
     'Group Policy', or a 'Search' / 'Check now' button that reveals the fields. Click
     those to expose the form.
   Fill ONLY the fields it has, from the details above. Leave unknown fields blank.
   - Date of birth is given as YYYY-MM-DD. Try typing it as DD/MM/YYYY first (most
     Indian forms), then DD-MM-YYYY, then YYYY-MM-DD, until one is accepted.
   - If DOB is a calendar/date-picker widget, do NOT click the previous-month arrow
     dozens of times. Click the month/year header (or a year dropdown) to jump to a
     year-selection view, pick 1962 directly, then the month, then the day.
3. Submit the search (click the Search / Submit / Check button).

IMPORTANT: these details are test data and may not match any real policy. So an
error, 'no record found', 'invalid details/combination', or 'no data' shown AFTER you
fill the fields and click submit is STILL a success -- it means the form accepted your
input and processed it. We only care that the agent could open the page, fill the
fields, and submit.

Decide the outcome:
- status "success" if you reached the search form, filled the fields you have, and
  clicked submit -- regardless of what the site shows afterwards (a result, 'no record',
  'invalid combination', or nothing at all). If a rupee amount is actually shown, put it
  (digits only) in amount_found.
- status "failed" ONLY if you were stopped BEFORE submitting: the page won't open /
  'access denied', a CAPTCHA or OTP or login blocks submission, a REQUIRED field cannot
  be filled at all, or there is no search form on the page. Put the reason in detail.

Do NOT try to solve CAPTCHAs or bypass any bot protection. If blocked, report "failed".
Keep detail to one short sentence."""


def _build_task(details: dict, row: dict, fields_hint: str | None) -> str:
    policy = (details.get("policy_number") or "").strip()
    policy_line = f"\n  policy number: {policy}" if policy else ""
    return TASK.format(
        url=row.get("insurer_url") or "",
        fields_hint=fields_hint or "name / DOB / PAN / policy number",
        name=details.get("deceased_name") or "",
        dob=details.get("dob") or "",
        pan=details.get("pan") or "",
        policy_line=policy_line,
    )


async def _run_agent(task: str, session: BrowserSession) -> InsurerOutcome:
    agent = Agent(
        task=task,
        llm=ChatOpenAI(model=MODEL),
        browser_session=session,
        output_model_schema=InsurerOutcome,
        use_vision=True,
    )
    history = await agent.run(max_steps=14)
    parsed = getattr(history, "structured_output", None)
    if isinstance(parsed, InsurerOutcome):
        return parsed
    final = history.final_result() if hasattr(history, "final_result") else None
    if final:
        try:
            return InsurerOutcome.model_validate_json(final)
        except Exception:
            return InsurerOutcome(status="failed", detail=str(final)[:180])
    return InsurerOutcome(status="failed", detail="Agent returned no result")


# ---------------- Browserbase backend ----------------

async def _bb_create_session() -> tuple[str, str, str | None]:
    headers = {"X-BB-API-Key": BB_API_KEY, "Content-Type": "application/json"}
    body = {
        "projectId": BB_PROJECT_ID,
        "browserSettings": {"solveCaptchas": BB_SOLVE_CAPTCHAS},
        "proxies": BB_PROXIES,
        "keepAlive": False,
    }
    async with httpx.AsyncClient(timeout=40) as c:
        r = await c.post(f"{BB_BASE}/sessions", headers=headers, json=body)
        r.raise_for_status()
        s = r.json()
        sid = s["id"]
        connect_url = s.get("connectUrl") or (
            f"wss://connect.browserbase.com?apiKey={BB_API_KEY}&sessionId={sid}"
        )
        live_url = None
        try:
            d = (await c.get(f"{BB_BASE}/sessions/{sid}/debug", headers=headers)).json()
            live_url = d.get("debuggerFullscreenUrl")
            if not live_url and d.get("pages"):
                live_url = d["pages"][0].get("debuggerFullscreenUrl")
        except Exception:
            pass
    return sid, connect_url, live_url


async def _bb_release(sid: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            await c.post(
                f"{BB_BASE}/sessions/{sid}",
                headers={"X-BB-API-Key": BB_API_KEY, "Content-Type": "application/json"},
                json={"projectId": BB_PROJECT_ID, "status": "REQUEST_RELEASE"},
            )
    except Exception:
        pass


# ---------------- cloakbrowser backend (fallback) ----------------

def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


async def _wait_cdp(port: int, timeout_s: float = 25) -> bool:
    for _ in range(int(timeout_s * 2)):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2).read()
            return True
        except Exception:
            await asyncio.sleep(0.5)
    return False


# ---------------- entrypoint ----------------

async def run(details: dict, row: dict, fields_hint: str | None = None, live_view_cb=None) -> InsurerOutcome:
    task = _build_task(details, row, fields_hint)

    if USE_BROWSERBASE:
        sid, connect_url, live_url = await _bb_create_session()
        if live_url and live_view_cb:
            try:
                await live_view_cb(live_url)
            except Exception:
                pass
        session = BrowserSession(cdp_url=connect_url, is_local=False)
        try:
            return await _run_agent(task, session)
        finally:
            await _bb_release(sid)

    # cloakbrowser fallback
    import cloakbrowser

    port = _free_port()
    fingerprint = 10000 + (zlib.crc32((row.get("insurer_name") or "").encode()) % 89999)
    cloak = await cloakbrowser.launch_async(
        headless=HEADLESS,
        humanize=True,
        args=[f"--remote-debugging-port={port}", f"--fingerprint={fingerprint}"],
    )
    try:
        if not await _wait_cdp(port):
            return InsurerOutcome(status="failed", detail="Stealth browser CDP endpoint did not come up")
        session = BrowserSession(cdp_url=f"http://127.0.0.1:{port}", is_local=False)
        return await _run_agent(task, session)
    finally:
        try:
            await cloak.close()
        except Exception:
            pass
