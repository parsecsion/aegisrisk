import pytest

from aegisrisk.core.models import MarketState, OrderType, Side, TimeInForce, TradeTicket


def test_ticket_validation() -> None:
    with pytest.raises(ValueError, match="lots must be positive"):
        TradeTicket(
            1, "ACC", "eurusd", Side.BUY, -1.0, 1.1, OrderType.MARKET, 10.0, TimeInForce.DAY
        )

    with pytest.raises(ValueError, match="price must be positive"):
        TradeTicket(
            1, "ACC", "eurusd", Side.BUY, 1.0, -1.1, OrderType.MARKET, 10.0, TimeInForce.DAY
        )

    with pytest.raises(ValueError, match="leverage must be positive"):
        TradeTicket(
            1, "ACC", "eurusd", Side.BUY, 1.0, 1.1, OrderType.MARKET, -10.0, TimeInForce.DAY
        )


def test_market_validation() -> None:
    with pytest.raises(ValueError, match="bid and ask must be positive"):
        MarketState("eurusd", -1.0, 1.0, 12.0, 10000.0, 0.0, 0.0)

    with pytest.raises(ValueError, match="account_balance cannot be negative"):
        MarketState("eurusd", 1.0, 1.1, 12.0, -100.0, 0.0, 0.0)

    with pytest.raises(ValueError, match="open_exposure cannot be negative"):
        MarketState("eurusd", 1.0, 1.1, 12.0, 10000.0, -100.0, 0.0)


def test_market_spread() -> None:
    market = MarketState("eurusd", 1.0990, 1.1010, 12.0, 10000.0, 0.0, 0.0)
    assert market.spread == pytest.approx(0.0020)
