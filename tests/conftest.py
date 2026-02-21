from __future__ import annotations

import pytest

from aegisrisk.core.models import MarketState, OrderType, Side, TimeInForce, TradeTicket


@pytest.fixture
def base_ticket() -> TradeTicket:
    return TradeTicket(
        ticket_id=1,
        account_id="ACC-0001",
        symbol="eurusd",
        side=Side.BUY,
        lots=0.05,
        price=1.1000,
        order_type=OrderType.MARKET,
        leverage=10.0,
        time_in_force=TimeInForce.DAY,
    )


@pytest.fixture
def base_market() -> MarketState:
    return MarketState(
        symbol="eurusd",
        bid=1.0999,
        ask=1.1001,
        volatility=12.0,
        account_balance=10000.0,
        open_exposure=1000.0,
        news_sentiment=0.0,
    )
