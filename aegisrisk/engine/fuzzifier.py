from __future__ import annotations

from dataclasses import dataclass

from aegisrisk.core.models import MarketState, TradeTicket


@dataclass(slots=True)
class FuzzyFacts:
    """
    Fuzzified view of the numeric state, ready to assert into Prolog.
    All values are lowercase Prolog-safe atoms.
    """

    volatility_level: str
    spread_level: str
    exposure_level: str
    sentiment_level: str
    session: str

    def as_dict(self) -> dict[str, str]:
        return {
            "volatility_level": self.volatility_level,
            "spread_level": self.spread_level,
            "exposure_level": self.exposure_level,
            "sentiment_level": self.sentiment_level,
            "session": self.session,
        }


def _volatility_level(volatility_pct: float) -> str:
    """
    Map numeric volatility (percent) to a fuzzy bucket.
    """
    if volatility_pct < 15.0:
        return "low"
    if volatility_pct < 30.0:
        return "medium"
    if volatility_pct < 60.0:
        return "high"
    return "extreme"


def _spread_level(bid: float, ask: float) -> str:
    """
    Map spread to fuzzy buckets based on relative width vs. mid price.
    """
    mid = (bid + ask) / 2.0
    if mid <= 0.0:
        return "normal"
    spread = ask - bid
    rel = spread / mid
    if rel <= 0.0001:
        return "tight"
    if rel <= 0.0003:
        return "normal"
    return "wide"


def _exposure_level(open_exposure: float, balance: float) -> str:
    """
    Fuzzify exposure vs. account balance into low / elevated / critical.
    """
    if balance <= 0.0:
        return "critical"
    ratio = open_exposure / balance
    if ratio < 0.2:
        return "low"
    if ratio < 0.5:
        return "elevated"
    return "critical"


def _sentiment_level(sentiment: float) -> str:
    """
    Fuzzify sentiment from numeric scale [-1.0, 1.0].
    """
    if sentiment <= -0.4:
        return "negative"
    if sentiment >= 0.4:
        return "positive"
    return "neutral"


def fuzzify(ticket: TradeTicket, market: MarketState, session: str) -> FuzzyFacts:
    """
    Compute all fuzzy buckets from the given ticket + market snapshot.

    `session` should already be a lowercase Prolog-safe atom
    (e.g. 'asia', 'europe', 'us', 'rollover').
    """
    vol_level = _volatility_level(market.volatility)
    spread_level = _spread_level(market.bid, market.ask)
    exp_level = _exposure_level(market.open_exposure, market.account_balance)
    sent_level = _sentiment_level(market.news_sentiment)

    return FuzzyFacts(
        volatility_level=vol_level,
        spread_level=spread_level,
        exposure_level=exp_level,
        sentiment_level=sent_level,
        session=session,
    )
