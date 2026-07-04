"""Fan-out engine with two honest modes.

- demo=True  -> scripted showcase (90% success / 10% blocked). No browser, no LLM.
- demo=False -> REAL: insurers with a built adapter (adapter_type='live') are
  driven by a Browser Use agent and report their actual success/failed state;
  every other insurer is marked 'pending' (no adapter built yet). Nothing faked.
"""
import asyncio
import os
import random

import db
from adapters import generic
from adapters.stub import demo_delay, demo_outcome

REAL_CONCURRENCY = int(os.getenv("REAL_CONCURRENCY", "2"))


async def run_search(
    run_id: str,
    details: dict,
    seeded_rows: list[dict],
    demo: bool,
    hints: dict[str, str],
) -> None:
    sem = asyncio.Semaphore(REAL_CONCURRENCY)  # gates only real browser agents
    # return_exceptions=True: one insurer blowing up can never abort the others.
    try:
        await asyncio.gather(
            *(
                _run_one(details, row, idx, demo, sem, hints)
                for idx, row in enumerate(seeded_rows)
            ),
            return_exceptions=True,
        )
    finally:
        await db.mark_run_done(run_id)


async def _run_one(details, row, idx, demo, sem, hints) -> None:
    result_id = row["id"]
    name = row["insurer_name"]

    if demo:
        await _run_demo(result_id, idx, name)
    elif row.get("adapter_type") == "live":
        await _run_real(details, row, result_id, name, sem, hints)
    else:
        # Real mode, no adapter built for this insurer — say so honestly.
        await db.update_result(result_id, status="pending", detail="Adapter not built yet")


async def _run_demo(result_id, idx, name) -> None:
    await asyncio.sleep(idx * 0.05 + random.uniform(0, 0.3))
    await db.update_result(result_id, status="searching")
    status, amount, detail = demo_outcome(idx, name)
    await demo_delay(status)
    await db.update_result(result_id, status=status, amount_found=amount, detail=detail)


async def _run_real(details, row, result_id, name, sem, hints) -> None:
    await db.update_result(result_id, status="searching")
    try:
        async with sem:
            outcome = await generic.run(details, row, hints.get(name))
        await db.update_result(
            result_id,
            status=outcome.status,          # 'success' | 'failed'
            amount_found=outcome.amount_found,
            detail=outcome.detail,
        )
    except Exception as e:  # an adapter must never kill the fan-out
        await db.update_result(result_id, status="failed", detail=f"Agent error: {str(e)[:160]}")
