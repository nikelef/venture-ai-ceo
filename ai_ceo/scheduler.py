"""Bounded foreground scheduler; no installed or cloud schedule is implied."""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from ai_ceo.policy import Action, PolicyDenied, authorize
from ai_ceo.worker import main as run_once


def run(runs: int, interval: int, *, sleep=time.sleep, worker=run_once) -> int:
    if type(runs) is not int or not 1 <= runs <= 4 or type(interval) is not int or not 60 <= interval <= 86400:
        raise ValueError("Scheduler limits: 1-4 runs, 60-86400 seconds between runs")
    import os
    directory = Path(os.getenv("AI_CEO_DATA_DIR", "./data"))
    for index in range(runs):
        authorize(Action.RESEARCH, data_dir=directory)
        result = worker([])
        if result:
            return result  # No automatic retries or runaway crash loop.
        if index < runs - 1:
            remaining = interval
            while remaining:
                step = min(remaining, 1)
                sleep(step)
                remaining -= step
                authorize(Action.RESEARCH, data_dir=directory)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--interval-seconds", type=int, default=3600)
    args = parser.parse_args()
    try:
        return run(args.runs, args.interval_seconds)
    except (ValueError, PolicyDenied) as exc:
        print(f"SAFE STOP: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
