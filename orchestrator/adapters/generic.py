"""Generic real adapter — a Browser Use agent driving a CLOAKBROWSER stealth
Chromium over CDP.

Instead of browser-use spawning its own vanilla Playwright Chromium (which the
insurer WAFs flag instantly -> 'access denied'), we launch a cloakbrowser stealth
browser that exposes a CDP endpoint, then point browser-use at it via cdp_url.
We keep all the agent logic; we gain the anti-detection layer.

Each insurer gets its own stealth browser with a distinct fingerprint.
Honest outcomes only: success (search submitted) / failed (CAPTCHA/OTP/error).
"""
import asyncio
import os
import socket
import urllib.request
import zlib

import cloakbrowser
from browser_use import Agent, BrowserSession, ChatOpenAI

from .base import InsurerOutcome

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
HEADLESS = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"

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


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


async def _wait_cdp(port: int, timeout_s: float = 25) -> bool:
    deadline = timeout_s * 2
    for _ in range(int(deadline)):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2).read()
            return True
        except Exception:
            await asyncio.sleep(0.5)
    return False


async def run(details: dict, row: dict, fields_hint: str | None = None) -> InsurerOutcome:
    policy = (details.get("policy_number") or "").strip()
    policy_line = f"\n  policy number: {policy}" if policy else ""
    task = TASK.format(
        url=row.get("insurer_url") or "",
        fields_hint=fields_hint or "name / DOB / PAN / policy number",
        name=details.get("deceased_name") or "",
        dob=details.get("dob") or "",
        pan=details.get("pan") or "",
        policy_line=policy_line,
    )

    port = _free_port()
    # Distinct, stable fingerprint per insurer so sites can't correlate our agents.
    fingerprint = 10000 + (zlib.crc32((row.get("insurer_name") or "").encode()) % 89999)

    cloak = await cloakbrowser.launch_async(
        headless=HEADLESS,
        humanize=True,  # human-like mouse/keyboard/scroll
        args=[f"--remote-debugging-port={port}", f"--fingerprint={fingerprint}"],
    )
    try:
        if not await _wait_cdp(port):
            return InsurerOutcome(status="failed", detail="Stealth browser CDP endpoint did not come up")

        session = BrowserSession(cdp_url=f"http://127.0.0.1:{port}", is_local=False)
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
    finally:
        try:
            await cloak.close()  # we own the stealth browser's lifecycle
        except Exception:
            pass
