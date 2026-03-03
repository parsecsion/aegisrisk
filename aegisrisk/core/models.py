from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class TimeInForce(str, Enum):
    DAY = "day"
    GTC = "gtc"  # good till cancelled
    IOC = "ioc"  # immediate or cancel
    FOK = "fok"  # fill or kill


DecisionStatus = Literal["approve", "reject"]


@dataclass
class TradeTicket:
    """
    Immutable description of an incoming trade request.
    """

    ticket_id: int
    account_id: str
    symbol: str
    side: Side
    lots: float
    price: float
    order_type: OrderType
    leverage: float
    time_in_force: TimeInForce

@dataclass
class MarketState:
    """
    Snapshot of market and account state relevant for pre-trade checks.
    """

    symbol: str
    bid: float
    ask: float
    volatility: float  # e.g. annualized volatility in percent
    account_balance: float
    open_exposure: float  # notional exposure across open positions
    news_sentiment: float  # simple scale, e.g. -1.0 (very negative) to 1.0 (very positive)
    @property
    def spread(self) -> float:
        return self.ask - self.bid


@dataclass(frozen=True)
class Decision:
    """
    Deterministic output of the Prolog knowledge base.
    """

    status: DecisionStatus
    reason: str
