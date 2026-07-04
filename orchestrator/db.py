"""Supabase access layer. Sync supabase-py wrapped in threads so it never
blocks the asyncio event loop.

Writes retry on transient connection drops: a real adapter can run for 1-2
minutes, during which Supabase's keep-alive HTTP connection may be closed
server-side. The next write then fails with 'Server disconnected'. Retrying
re-establishes the connection, so a slow agent never loses its result.
"""
import asyncio
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_client: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_ANON_KEY"],
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _run(fn, attempts: int = 4):
    """Run a sync supabase call off-thread, retrying transient failures."""
    last = None
    for i in range(attempts):
        try:
            return await asyncio.to_thread(fn)
        except Exception as e:  # includes httpx RemoteProtocolError on idle drops
            last = e
            if i < attempts - 1:
                await asyncio.sleep(0.4 * (i + 1))
    raise last


async def create_run(details: dict) -> str:
    payload = {
        "claimant_name": details.get("claimant_name") or None,
        "deceased_name": details.get("deceased_name") or None,
        "pan": details.get("pan") or None,
        "dob": details.get("dob") or None,            # empty string -> NULL (date column)
        "policy_number": details.get("policy_number") or None,
        "mobile": details.get("mobile") or None,
        "status": "running",
    }

    def _do():
        return _client.table("search_run").insert(payload).execute().data[0]["id"]

    return await _run(_do)


async def fetch_registry() -> list[dict]:
    def _do():
        return (
            _client.table("insurer_registry")
            .select("*")
            .order("sort_order")
            .execute()
            .data
        )

    return await _run(_do)


async def seed_results(run_id: str, registry: list[dict]) -> list[dict]:
    rows = [
        {
            "run_id": run_id,
            "insurer_name": r["insurer_name"],
            "insurer_url": r.get("insurer_url"),
            "adapter_type": r.get("adapter_type", "stub"),
            "status": "queued",
        }
        for r in registry
    ]

    def _do():
        return _client.table("insurer_result").insert(rows).execute().data

    return await _run(_do)


async def update_result(result_id: str, **fields) -> None:
    fields["updated_at"] = _now()

    def _do():
        _client.table("insurer_result").update(fields).eq("id", result_id).execute()

    try:
        await _run(_do)
    except Exception:
        # Never let a status write kill the fan-out; log and move on.
        import logging

        logging.getLogger("uvicorn.error").warning(
            "update_result failed for %s after retries", result_id
        )


async def mark_run_done(run_id: str) -> None:
    def _do():
        _client.table("search_run").update({"status": "done"}).eq("id", run_id).execute()

    try:
        await _run(_do)
    except Exception:
        pass
