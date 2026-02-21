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


@dataclass(slots=True)
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

    def __post_init__(self) -> None:
        if self.lots <= 0:
            raise ValueError("lots must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.leverage <= 0:
            raise ValueError("leverage must be positive")


@dataclass(slots=True)
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

    def __post_init__(self) -> None:
        if self.bid <= 0 or self.ask <= 0:
            raise ValueError("bid and ask must be positive")
        if self.account_balance < 0:
            raise ValueError("account_balance cannot be negative")
        if self.open_exposure < 0:
            raise ValueError("open_exposure cannot be negative")

    @property
    def spread(self) -> float:
        return self.ask - self.bid


@dataclass(slots=True, frozen=True)
class Decision:
    """
    Deterministic output of the Prolog knowledge base.
    """

    status: DecisionStatus
    reason: str
