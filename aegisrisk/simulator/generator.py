from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass

from tradeguard.core.models import MarketState, OrderType, Side, TimeInForce, TradeTicket

_SYMBOLS: tuple[str, ...] = (
    "eurusd",
    "gbpusd",
    "usdjpy",
    "xauusd",
    "tsla",
    "usdzar",
)


def _base_price(symbol: str) -> float:
    bases = {
        "eurusd": 1.10,
        "gbpusd": 1.25,
        "usdjpy": 150.0,
        "xauusd": 2000.0,
        "tsla": 250.0,
        "usdzar": 18.0,
    }
    return bases.get(symbol, 1.0)


def _random_account_tier(rng: random.Random) -> str:
    tiers: tuple[tuple[str, float], ...] = (
        ("retail_standard", 0.5),
        ("prop_funded_eval_1", 0.3),
        ("prop_funded_pro", 0.2),
    )
    r = rng.random()
    acc = 0.0
    for name, prob in tiers:
        acc += prob
        if r <= acc:
            return name
    return "retail_standard"


def _random_session(rng: random.Random) -> str:
    # Simple session model with low probability of rollover.
    sessions: tuple[tuple[str, float], ...] = (
        ("asia", 0.3),
        ("europe", 0.3),
        ("us", 0.3),
        ("rollover", 0.1),
    )
    r = rng.random()
    acc = 0.0
    for name, prob in sessions:
        acc += prob
        if r <= acc:
            return name
    return "us"


@dataclass(slots=True)
class SimulationSnapshot:
    ticket: TradeTicket
    market: MarketState
    session: str
    account_tier: str


def _choose(rng: random.Random, items: Iterable[str]) -> str:
    seq = tuple(items)
    return rng.choice(seq)


def generate_snapshot(counter: int, rng: random.Random | None = None) -> SimulationSnapshot:
    """
    Generate a self-consistent TradeTicket + MarketState + session triple.
    """
    rng = rng or random.Random()

    symbol = _choose(rng, _SYMBOLS)
    side = Side.BUY if rng.random() < 0.5 else Side.SELL
    order_type = OrderType.MARKET if rng.random() < 0.6 else OrderType.LIMIT
    tif = rng.choice((TimeInForce.DAY, TimeInForce.GTC, TimeInForce.IOC, TimeInForce.FOK))

    lots = max(0.01, rng.lognormvariate(0.0, 1.0))  # skew towards small tickets
    lots = min(lots, 60.0)

    base = _base_price(symbol)
    # Price is near base with some noise.
    price = base * (1.0 + rng.uniform(-0.01, 0.01))

    leverage = rng.choice((5.0, 10.0, 20.0, 30.0, 40.0, 60.0))

    ticket = TradeTicket(
        ticket_id=counter,
        account_id=f"ACC-{1 + (counter % 10):04d}",
        symbol=symbol,
        side=side,
        lots=round(lots, 2),
        price=round(price, 5),
        order_type=order_type,
        leverage=leverage,
        time_in_force=tif,
    )

    # Market state
    mid = base * (1.0 + rng.uniform(-0.02, 0.02))
    # Spread scales with price magnitude.
    spread_bp = rng.uniform(0.5, 4.0)  # basis points
    spread = mid * spread_bp / 10_000.0
    bid = mid - spread / 2.0
    ask = mid + spread / 2.0

    volatility = rng.uniform(5.0, 100.0)
    balance = rng.uniform(500.0, 50_000.0)
    open_exposure = rng.uniform(0.0, balance * 0.9)
    news_sentiment = rng.uniform(-1.0, 1.0)

    market = MarketState(
        symbol=symbol,
        bid=round(bid, 5),
        ask=round(ask, 5),
        volatility=volatility,
        account_balance=balance,
        open_exposure=open_exposure,
        news_sentiment=news_sentiment,
    )

    session = _random_session(rng)
    account_tier = _random_account_tier(rng)
    return SimulationSnapshot(
        ticket=ticket, market=market, session=session, account_tier=account_tier
    )
