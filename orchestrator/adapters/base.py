"""The outcome every real adapter returns.

A real Browser Use run reports one of two honest states:
  - success: it reached a result — the search/application was submitted and a
    response came back (whether or not money was found). amount_found is set if
    a rupee figure was shown.
  - failed:  it could not complete — CAPTCHA, OTP, login wall, access denied, or
    an error. detail says why.
"""
from typing import Literal, Optional

from pydantic import BaseModel

Status = Literal["success", "failed"]


class InsurerOutcome(BaseModel):
    status: Status
    amount_found: Optional[float] = None
    detail: Optional[str] = None
