"""FastAPI entrypoint. POST /search kicks off a fan-out and returns a run_id the
UI subscribes to via Supabase Realtime.

The `demo` flag decides the mode:
  demo=true  -> scripted showcase (sample-data button)
  demo=false -> real Browser Use agents for built insurers; rest pending
"""
import asyncio
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db
from orchestrator import run_search

app = FastAPI(title="BimaSarathi Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchIn(BaseModel):
    claimant_name: str
    deceased_name: str
    pan: Optional[str] = None
    dob: Optional[str] = None
    policy_number: Optional[str] = None
    mobile: Optional[str] = None
    demo: bool = False


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/search")
async def search(body: SearchIn):
    details = body.model_dump()
    demo = bool(details.pop("demo", False))

    run_id = await db.create_run(details)
    registry = await db.fetch_registry()
    seeded = await db.seed_results(run_id, registry)
    hints = {r["insurer_name"]: r.get("fields_hint") for r in registry}

    asyncio.create_task(run_search(run_id, details, seeded, demo, hints))

    built = sum(1 for r in registry if r.get("adapter_type") == "live")
    return {"run_id": run_id, "insurers": len(seeded), "demo": demo, "built_adapters": built}
