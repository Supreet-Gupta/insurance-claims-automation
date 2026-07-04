"""Demo-mode scripted outcomes. Used ONLY when the user runs the sample demo.
About 90% of insurers resolve to `success` (with a plausible unclaimed amount),
~10% to `blocked`. Deterministic per index so the demo is stable.

This is clearly the showcase path, not real search. Real mode never calls this.
"""
import asyncio
import random


def demo_outcome(index: int, insurer_name: str) -> tuple[str, float | None, str]:
    """Return (status, amount_found, detail) for the demo showcase."""
    # ~10% blocked (indices 4, 13, 22, 31 over ~37 insurers)
    if index % 9 == 4:
        return ("blocked", None, "Blocked — CAPTCHA / OTP required")

    # Deterministic, varied, plausible rupee amounts (₹8k … ~₹1.1L).
    amount = 8000 + ((index * 7919) % 130) * 800
    return ("success", float(amount), "Unclaimed amount located · application submitted")


async def demo_delay(status: str) -> None:
    """Stagger resolution so the grid fills progressively, found ones last."""
    base = random.uniform(3.0, 6.0) if status == "success" else random.uniform(1.0, 3.0)
    await asyncio.sleep(base)
