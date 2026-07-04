"""One generic Browser Use adapter, parameterized per insurer from the registry
row (URL + field hints). This is the real thing: an LLM agent drives Chrome on
the insurer's actual unclaimed-amount page and reports what really happened.

Honest outcomes only:
  - success: the search form was submitted and a result came back.
  - failed:  CAPTCHA / OTP / login / access-denied / error stopped it.
"""
import os

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
2. Find the unclaimed-amount search form. Fill ONLY the fields it has, from the
   details above. Leave unknown fields blank.
3. Submit the search.

Decide the outcome:
- You reached a result page (a record, an amount, OR a clear 'no records found')
  -> status "success". If a rupee amount is shown, put it (digits only) in amount_found.
- A CAPTCHA, OTP, login, or 'access denied' blocks you, or the page errors
  -> status "failed", with the reason in detail.

Do NOT try to solve CAPTCHAs or bypass any bot protection. If blocked, report "failed".
Keep detail to one short sentence."""


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

    session = BrowserSession(headless=HEADLESS, channel="chrome")
    agent = Agent(
        task=task,
        llm=ChatOpenAI(model=MODEL),
        browser_session=session,
        output_model_schema=InsurerOutcome,
        use_vision=True,
    )
    try:
        history = await agent.run(max_steps=14)
    finally:
        try:
            await session.kill()
        except Exception:
            pass

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
