"""Fail-closed permissions for the zero-outlay research pilot.

Changing environment variables cannot grant payment, publishing, or spending
authority. A future budget increase needs a separately reviewed owner approval.
"""
from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path


class PolicyDenied(RuntimeError):
    pass


class Action(str, Enum):
    RESEARCH = "research"
    PUBLIC_FEED = "public_feed"
    LOCAL_PRODUCT = "local_product"
    MODEL = "model"
    PUBLISH = "publish"
    PAYMENT = "payment"
    NOTIFY = "notify"


HARD_MONTHLY_BUDGET_EUR = Decimal("0")
HARD_MAX_RUNS_PER_DAY = 4
HARD_MAX_FAILURES = 3


def bounded_int(name: str, default: int, low: int, high: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        raise PolicyDenied(f"Invalid {name}") from None
    if not low <= value <= high:
        raise PolicyDenied(f"{name} outside allowed limits")
    return value


def authorize(action: Action, *, data_dir: Path | None = None,
              cost_eur: Decimal = Decimal("0")) -> None:
    try:
        configured = Decimal(os.getenv("MONTHLY_BUDGET_EUR", "0"))
        proposed = Decimal(cost_eur)
    except (InvalidOperation, TypeError, ValueError):
        raise PolicyDenied("Invalid budget") from None
    if not configured.is_finite() or configured != HARD_MONTHLY_BUDGET_EUR:
        raise PolicyDenied("Owner-approved budget is EUR 0; environment cannot raise it")
    if not proposed.is_finite() or proposed != 0:
        raise PolicyDenied("Zero-outlay policy forbids this cost")
    if os.getenv("AI_CEO_SHUTDOWN", "false").lower() not in ("false", "0", "no"):
        raise PolicyDenied("Shutdown switch is active")
    if data_dir is not None and (data_dir / "STOP").exists():
        raise PolicyDenied("Shutdown file is present")
    if os.getenv("PAYMENTS_ENABLED", "false").lower() not in ("false", "0", "no"):
        raise PolicyDenied("Payments are blocked pending secure onboarding and readiness review")
    if not isinstance(action, Action) or action not in {
        Action.RESEARCH, Action.PUBLIC_FEED, Action.LOCAL_PRODUCT,
    }:
        raise PolicyDenied("This action is outside the research pilot permissions")
