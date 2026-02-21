from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

from aegisrisk.core.models import Decision, MarketState, TradeTicket


def _default_log_path() -> Path:
    return Path(__file__).resolve().parent.parent / "audit_log.txt"


def _color_codes() -> tuple[str, str, str, str]:
    """
    Return (green, red, yellow, reset) ANSI codes.
    If the terminal does not support ANSI codes, fall back to empty strings.
    """
    # Basic heuristic: modern terminals generally support ANSI; we still
    # allow callers to disable colors by redirecting stdout to a file.
    if not sys.stdout.isatty():
        return "", "", "", ""

    green = "\033[92m"
    red = "\033[91m"
    yellow = "\033[93m"
    reset = "\033[0m"
    return green, red, yellow, reset


def _format_console_line(ticket: TradeTicket, market: MarketState, decision: Decision) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f"[{ts}] ticket={ticket.ticket_id} "
        f"{ticket.side.value.upper()} {ticket.lots:.2f} {ticket.symbol.upper()} "
        f"@ {ticket.price:.5f} "
        f"status={decision.status.upper()} "
        f"reason={decision.reason}"
    )


def _format_audit_record(ticket: TradeTicket, market: MarketState, decision: Decision) -> str:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": ticket.ticket_id,
        "account_id": ticket.account_id,
        "symbol": ticket.symbol,
        "side": ticket.side.value,
        "lots": ticket.lots,
        "price": ticket.price,
        "order_type": ticket.order_type.value,
        "leverage": ticket.leverage,
        "time_in_force": ticket.time_in_force.value,
        "bid": market.bid,
        "ask": market.ask,
        "volatility": market.volatility,
        "account_balance": market.account_balance,
        "open_exposure": market.open_exposure,
        "news_sentiment": market.news_sentiment,
        "decision_status": decision.status,
        "decision_reason": decision.reason,
    }
    return json.dumps(record, separators=(",", ":"))


def _write_line(line: str, file: TextIO) -> None:
    file.write(line + "\n")
    file.flush()


def log_decision(
    ticket: TradeTicket,
    market: MarketState,
    decision: Decision,
    *,
    log_path: Path | None = None,
) -> None:
    """
    Print a colorized summary to stdout and append a structured line to
    `audit_log.txt` (JSONL format).
    """
    green, red, yellow, reset = _color_codes()
    console_line = _format_console_line(ticket, market, decision)

    if decision.status == "approve":
        color = green
    elif decision.status == "reject":
        color = red
    else:
        color = yellow

    print(f"{color}{console_line}{reset}")

    path = log_path or _default_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        _write_line(_format_audit_record(ticket, market, decision), f)
