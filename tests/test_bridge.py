"""
Integration tests ensuring Python models properly align with Prolog rules.
"""

import pytest

from aegisrisk.core.models import MarketState, OrderType, Side, TimeInForce, TradeTicket
from aegisrisk.engine.bridge import PrologBridge
from aegisrisk.engine.fuzzifier import fuzzify


@pytest.fixture
def bridge() -> PrologBridge:
    return PrologBridge()


def test_bridge_initialization(bridge: PrologBridge) -> None:
    assert bridge._initialized is True


def test_approve_standard_trade(
    bridge: PrologBridge, base_ticket: TradeTicket, base_market: MarketState
) -> None:
    """A standard vanilla trade on a major pair during valid session should approve."""
    fuzzy = fuzzify(base_ticket, base_market, "us")
    decision = bridge.evaluate(base_ticket, base_market, fuzzy.as_dict())

    assert decision.status == "approve"
    assert "All checks passed" in decision.reason


def test_reject_blacklisted_symbol(
    bridge: PrologBridge, base_ticket: TradeTicket, base_market: MarketState
) -> None:
    base_ticket.symbol = "tsla"
    base_market.symbol = "tsla"

    fuzzy = fuzzify(base_ticket, base_market, "us")
    decision = bridge.evaluate(base_ticket, base_market, fuzzy.as_dict())

    assert decision.status == "reject"
    assert decision.reason == "Instrument is blacklisted"


def test_reject_restricted_session(
    bridge: PrologBridge, base_ticket: TradeTicket, base_market: MarketState
) -> None:
    fuzzy = fuzzify(base_ticket, base_market, "rollover")  # rollover is restricted
    decision = bridge.evaluate(base_ticket, base_market, fuzzy.as_dict())

    assert decision.status == "reject"
    assert decision.reason == "Trading is blocked during restricted session"


def test_reject_leverage_limit(
    bridge: PrologBridge, base_ticket: TradeTicket, base_market: MarketState
) -> None:
    base_ticket.symbol = "usdzar"  # exotic, limit 20
    base_market.symbol = "usdzar"
    base_ticket.leverage = 30.0  # exceeds 20

    fuzzy = fuzzify(base_ticket, base_market, "us")
    decision = bridge.evaluate(base_ticket, base_market, fuzzy.as_dict())

    assert decision.status == "reject"
    assert decision.reason == "Leverage exceeds hard limit"


def test_reject_limit_order_with_ioc(
    bridge: PrologBridge, base_ticket: TradeTicket, base_market: MarketState
) -> None:
    base_ticket.order_type = OrderType.LIMIT
    base_ticket.time_in_force = TimeInForce.IOC

    fuzzy = fuzzify(base_ticket, base_market, "us")
    decision = bridge.evaluate(base_ticket, base_market, fuzzy.as_dict())

    assert decision.status == "reject"
    assert decision.reason == "IOC not allowed for limit orders"


def test_cleanup_between_evaluations(
    bridge: PrologBridge, base_ticket: TradeTicket, base_market: MarketState
) -> None:
    """
    Ensure the Prolog state correctly cleans up facts so sequential
    evaluations do not pollute each other.
    """
    # 1. Reject trade
    bad_ticket = TradeTicket(
        ticket_id=1,
        account_id="ACC",
        symbol="tsla",
        side=Side.BUY,
        lots=1.0,
        price=250.0,
        order_type=OrderType.MARKET,
        leverage=10.0,
        time_in_force=TimeInForce.DAY,
    )
    bad_market = MarketState("tsla", 249.9, 250.1, 40.0, 10000.0, 0.0, 0.0)
    fuzzy = fuzzify(bad_ticket, bad_market, "us")

    decision1 = bridge.evaluate(bad_ticket, bad_market, fuzzy.as_dict())
    assert decision1.status == "reject"

    # 2. Good trade right after uses completely fresh KB
    fuzzy2 = fuzzify(base_ticket, base_market, "us")
    decision2 = bridge.evaluate(base_ticket, base_market, fuzzy2.as_dict())
    assert decision2.status == "approve"
