from __future__ import annotations

import argparse
import sys
import time
from typing import NoReturn

from tradeguard.core.models import Decision
from tradeguard.engine.bridge import PrologBridge
from tradeguard.engine.fuzzifier import fuzzify
from tradeguard.simulator.generator import generate_snapshot
from tradeguard.utils.logger import log_decision


def _run_loop(iterations: int | None, sleep_seconds: float) -> None:
    bridge = PrologBridge()
    counter = 1

    try:
        while True:
            snapshot = generate_snapshot(counter)
            fuzzy = fuzzify(snapshot.ticket, snapshot.market, snapshot.session)
            decision: Decision = bridge.evaluate(
                snapshot.ticket,
                snapshot.market,
                fuzzy.as_dict(),
                account_tier=snapshot.account_tier,
            )

            log_decision(snapshot.ticket, snapshot.market, decision)

            counter += 1
            if iterations is not None and counter > iterations:
                break
            time.sleep(sleep_seconds)
    except KeyboardInterrupt:
        print("\nShutting down TradeGuard main loop gracefully.", file=sys.stderr)


def main(argv: list[str] | None = None) -> NoReturn:
    parser = argparse.ArgumentParser(description="TradeGuard pre-trade risk engine demo")
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Number of iterations to run (default: infinite loop)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds to sleep between evaluations (default: 1.0)",
    )
    args = parser.parse_args(argv)

    _run_loop(args.iterations, args.interval)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
