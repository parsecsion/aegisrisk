from tradeguard.core.models import MarketState, TradeTicket
from tradeguard.engine.fuzzifier import (
    _exposure_level,
    _sentiment_level,
    _spread_level,
    _volatility_level,
    fuzzify,
)


def test_volatility_buckets() -> None:
    assert _volatility_level(10.0) == "low"
    assert _volatility_level(20.0) == "medium"
    assert _volatility_level(40.0) == "high"
    assert _volatility_level(80.0) == "extreme"


def test_spread_buckets() -> None:
    # mid = 1.1000, 1 pip = 0.0001, rel = 0.0001 / 1.1 = 0.00009 -> tight
    assert _spread_level(1.09995, 1.10005) == "tight"

    # mid = 1.1000, 3 pips = 0.0003, rel = 0.0003 / 1.1 = 0.00027 -> normal
    assert _spread_level(1.09985, 1.10015) == "normal"

    # mid = 1.1000, 5 pips = 0.0005, rel -> wide
    assert _spread_level(1.09975, 1.10025) == "wide"


def test_exposure_buckets() -> None:
    assert _exposure_level(100.0, 1000.0) == "low"  # 10%
    assert _exposure_level(300.0, 1000.0) == "elevated"  # 30%
    assert _exposure_level(600.0, 1000.0) == "critical"  # 60%


def test_sentiment_buckets() -> None:
    assert _sentiment_level(-0.5) == "negative"
    assert _sentiment_level(0.0) == "neutral"
    assert _sentiment_level(0.5) == "positive"


def test_fuzzify(base_ticket: TradeTicket, base_market: MarketState) -> None:
    base_market.volatility = 40.0  # high
    base_market.bid = 1.09995
    base_market.ask = 1.10005  # tight
    base_market.open_exposure = 100.0
    base_market.account_balance = 1000.0  # low
    base_market.news_sentiment = -0.6  # negative

    result = fuzzify(base_ticket, base_market, "europe")

    assert result.volatility_level == "high"
    assert result.spread_level == "tight"
    assert result.exposure_level == "low"
    assert result.sentiment_level == "negative"
    assert result.session == "europe"

    assert result.as_dict() == {
        "volatility_level": "high",
        "spread_level": "tight",
        "exposure_level": "low",
        "sentiment_level": "negative",
        "session": "europe",
    }
