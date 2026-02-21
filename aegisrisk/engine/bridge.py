from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyswip import Prolog  # type: ignore[import]

from aegisrisk.core.models import Decision, DecisionStatus, MarketState, TradeTicket


@dataclass(slots=True)
class PrologBridge:
    """
    Thin wrapper around PySwip to talk to the SWI‑Prolog knowledge base.
    All financial / risk logic lives in `rules.pl`; this class only
    manages facts and queries plus fail-safe error handling.
    """

    _prolog: Prolog
    _initialized: bool

    def __init__(self) -> None:
        self._prolog = Prolog()
        self._initialized = False
        try:
            kb_path = Path(__file__).resolve().parent.parent / "knowledge_base" / "rules.pl"
            self._prolog.consult(str(kb_path))
            self._initialized = True
        except Exception:
            # Leave `_initialized` as False; evaluation will fail safe to reject.
            self._initialized = False

    # --- Public API -----------------------------------------------------

    def evaluate(
        self,
        ticket: TradeTicket,
        market: MarketState,
        fuzzy_facts: dict[str, str],
        account_tier: str = "retail_standard",
    ) -> Decision:
        """
        Evaluate a trade by asserting the given snapshot into Prolog and
        querying `evaluate_trade(Status, Reason)`.

        On any error or missing decision, returns a REJECT decision.
        """
        if not self._initialized:
            return Decision(
                status="reject",
                reason="Prolog engine not initialized or rules file could not be loaded",
            )

        try:
            self._clear_facts()
            self._assert_ticket(ticket)
            self._assert_market_and_state(market, fuzzy_facts)
            self._assert_account_tier(account_tier)

            results = list(self._prolog.query("evaluate_trade(Status, Reason)", maxresult=1))
            if not results:
                return Decision(
                    status="reject",
                    reason="Engine error or no decision from Prolog",
                )

            row: dict[str, Any] = results[0]
            status_str = str(row.get("Status", "reject"))
            reason = str(row.get("Reason", "No reason returned from Prolog"))

            if status_str not in ("approve", "reject"):
                return Decision(
                    status="reject",
                    reason=f"Unexpected status from Prolog: {status_str!r}",
                )

            # At this point, status_str is validated as either "approve" or "reject".
            status: DecisionStatus = "approve" if status_str == "approve" else "reject"
            return Decision(status=status, reason=reason)

        except Exception as exc:  # noqa: BLE001
            return Decision(
                status="reject",
                reason=f"Prolog evaluation error: {exc}",
            )

    # --- Internal helpers -----------------------------------------------

    def _clear_facts(self) -> None:
        """
        Remove all previously asserted dynamic facts so each evaluation
        runs on a fresh knowledge base snapshot.
        """
        predicates = [
            "ticket(_,_,_,_,_)",
            "market(_,_,_,_)",
            "order_type(_)",
            "time_in_force(_)",
            "session(_)",
            "spread_value(_)",
            "volatility_value(_)",
            "bid_value(_)",
            "ask_value(_)",
            "price_value(_)",
            "open_exposure_value(_)",
            "news_sentiment_value(_)",
            "exposure_level(_)",
            "sentiment_level(_)",
            "account_tier(_)",
        ]
        for pred in predicates:
            list(self._prolog.query(f"retractall({pred})"))

    def _atom(self, value: str) -> str:
        """
        Coerce a Python string into a Prolog atom representation.
        Assumes the value is already lowercase and Prolog-safe.
        """
        return value.lower()

    def _assert_ticket(self, ticket: TradeTicket) -> None:
        symbol_atom = self._atom(ticket.symbol)
        side_atom = self._atom(ticket.side.value)
        order_type_atom = self._atom(ticket.order_type.value)
        tif_atom = self._atom(ticket.time_in_force.value)

        self._prolog.assertz(
            f"ticket({ticket.ticket_id}, {symbol_atom}, {side_atom}, "
            f"{float(ticket.lots)}, {float(ticket.leverage)})"
        )
        self._prolog.assertz(f"order_type({order_type_atom})")
        self._prolog.assertz(f"time_in_force({tif_atom})")
        self._prolog.assertz(f"price_value({float(ticket.price)})")

    def _assert_market_and_state(self, market: MarketState, fuzzy_facts: dict[str, str]) -> None:
        symbol_atom = self._atom(market.symbol)
        vol_level = self._atom(fuzzy_facts["volatility_level"])
        spread_level = self._atom(fuzzy_facts["spread_level"])
        exposure_level = self._atom(fuzzy_facts["exposure_level"])
        sentiment_level = self._atom(fuzzy_facts["sentiment_level"])
        session_atom = self._atom(fuzzy_facts["session"])

        self._prolog.assertz(
            f"market({symbol_atom}, {float(market.account_balance)}, {vol_level}, {spread_level})"
        )
        self._prolog.assertz(f"session({session_atom})")

        self._prolog.assertz(f"bid_value({float(market.bid)})")
        self._prolog.assertz(f"ask_value({float(market.ask)})")
        self._prolog.assertz(f"volatility_value({float(market.volatility)})")
        self._prolog.assertz(f"spread_value({float(market.spread)})")
        self._prolog.assertz(f"open_exposure_value({float(market.open_exposure)})")
        self._prolog.assertz(f"news_sentiment_value({float(market.news_sentiment)})")

        self._prolog.assertz(f"exposure_level({exposure_level})")
        self._prolog.assertz(f"sentiment_level({sentiment_level})")

    def _assert_account_tier(self, account_tier: str) -> None:
        """Assert the account tier for tier-based risk limits."""
        tier_atom = self._atom(account_tier)
        self._prolog.assertz(f"account_tier({tier_atom})")
