% AegisRisk Knowledge Base (SWI-Prolog)
%
% Facts asserted by Python (via PySwip):
%   ticket(TicketId, Symbol, Side, Lots, Leverage).
%   market(Symbol, Balance, VolatilityLevel, SpreadLevel).
%   order_type(market|limit).  time_in_force(day|gtc|ioc|fok).
%   session(asia|europe|us|rollover).
%   spread_value/1, volatility_value/1, bid_value/1, ask_value/1, price_value/1.
%   open_exposure_value/1, news_sentiment_value/1.
%   exposure_level(low|elevated|critical).  sentiment_level(negative|neutral|positive).
%   account_tier/1 (e.g. retail_standard, prop_funded_pro).

:- dynamic ticket/5.
:- dynamic market/4.
:- dynamic order_type/1.
:- dynamic time_in_force/1.
:- dynamic session/1.
:- dynamic spread_value/1.
:- dynamic volatility_value/1.
:- dynamic bid_value/1.
:- dynamic ask_value/1.
:- dynamic price_value/1.
:- dynamic open_exposure_value/1.
:- dynamic news_sentiment_value/1.
:- dynamic exposure_level/1.
:- dynamic sentiment_level/1.
:- dynamic account_tier/1.

% =============================================================================
% STATIC KNOWLEDGE BASE: The Financial Universe (~80 facts)
% =============================================================================

% --- Category 1: Asset Profiles & Specifications ---

asset_class(eurusd, forex_major).
asset_class(gbpusd, forex_major).
asset_class(usdjpy, forex_major).
asset_class(usdchf, forex_major).
asset_class(audusd, forex_major).
asset_class(nzdusd, forex_major).
asset_class(usdcad, forex_major).

asset_class(xauusd, metals).
asset_class(xagusd, metals).

asset_class(usdzar, forex_exotic).
asset_class(usdmxn, forex_exotic).
asset_class(usdrub, forex_exotic).
asset_class(usdtry, forex_exotic).

asset_class(ndx100, indices).
asset_class(spx500, indices).
asset_class(us30, indices).

asset_class(btcusd, crypto).
asset_class(ethusd, crypto).

asset_class(tsla, equity).

max_leverage_limit(forex_major, 100).
max_leverage_limit(metals, 50).
max_leverage_limit(forex_exotic, 20).
max_leverage_limit(indices, 20).
max_leverage_limit(crypto, 10).
max_leverage_limit(equity, 20).

baseline_spread_tolerance(xauusd, 4.0).
baseline_spread_tolerance(xagusd, 4.5).
baseline_spread_tolerance(eurusd, 1.5).
baseline_spread_tolerance(gbpusd, 1.8).
baseline_spread_tolerance(usdjpy, 2.0).
baseline_spread_tolerance(usdchf, 1.6).
baseline_spread_tolerance(audusd, 1.7).
baseline_spread_tolerance(usdzar, 8.0).
baseline_spread_tolerance(usdmxn, 6.0).
baseline_spread_tolerance(ndx100, 3.0).
baseline_spread_tolerance(btcusd, 15.0).

blacklisted_symbol(xauusd).
blacklisted_symbol(xagusd).
blacklisted_symbol(tsla).

exotic_symbol(usdzar).
exotic_symbol(usdmxn).
exotic_symbol(usdrub).
exotic_symbol(usdtry).

min_balance_exotic(1000.0).

% --- Category 2: Account Tiers & Risk Limits ---

min_balance_floor(retail_standard, 100.0).
min_balance_floor(retail_pro, 250.0).
min_balance_floor(prop_funded_eval_1, 500.0).
min_balance_floor(prop_funded_eval_2, 500.0).
min_balance_floor(prop_funded_pro, 500.0).

max_open_exposure_ratio(retail_standard, 0.5).
max_open_exposure_ratio(retail_pro, 0.5).
max_open_exposure_ratio(prop_funded_eval_1, 0.6).
max_open_exposure_ratio(prop_funded_eval_2, 0.6).
max_open_exposure_ratio(prop_funded_pro, 0.5).

projected_exposure_ratio_max(retail_standard, 0.8).
projected_exposure_ratio_max(retail_pro, 0.75).
projected_exposure_ratio_max(prop_funded_eval_1, 0.7).
projected_exposure_ratio_max(prop_funded_eval_2, 0.7).
projected_exposure_ratio_max(prop_funded_pro, 0.6).

daily_drawdown_limit_pct(retail_standard, -10.0).
daily_drawdown_limit_pct(prop_funded_pro, -5.0).
max_overall_drawdown_pct(prop_funded_pro, -10.0).
max_open_exposure_usd(prop_funded_pro, 100000).

% --- Category 3: Market Microstructure & Time Regimes ---

session_status(asia, low_liquidity).
session_status(europe, high_liquidity).
session_status(us, high_liquidity).
session_status(rollover, restricted).

restricted_session(rollover).

restricted_macro_event(nfp, 1330).
restricted_macro_event(fomc, 1400).
restricted_macro_event(ecb, 1245).
restricted_macro_event(boe, 1200).
restricted_macro_event(cpi, 1330).

volatility_regime(vix_normal, normal).
volatility_regime(vix_elevated, high).
volatility_regime(vix_above_30, extreme).

high_leverage_volatility_cap(30.0).
spread_wide_leverage_cap(30.0).

% --- Category 4: Global System Thresholds ---

system_min_ticket_size_lots(0.01).
system_max_ticket_size_lots(50.0).
system_max_leverage(50.0).
lots_balance_ratio_max(0.02).
notional_balance_ratio_max(30.0).
exposure_ratio_threshold(0.5).
projected_exposure_ratio_max_default(0.8).
volatility_extreme_threshold(80.0).
limit_price_deviation_pct_max(0.01).
minimum_margin_requirement_usd(100.0).

% =============================================================================
% HELPERS (use facts, no hardcoded numbers)
% =============================================================================

ticket_notional(Notional) :-
    ticket(_, _, _, Lots, _),
    price_value(Price),
    Notional is Lots * Price * 100000.0.

market_mid(Mid) :-
    bid_value(Bid),
    ask_value(Ask),
    Mid is (Bid + Ask) / 2.0.

abs_val(X, Abs) :- (X < 0 -> Abs is -X ; Abs is X).

% Effective max leverage: min of system cap and asset-class limit (when defined)
effective_max_leverage(Symbol, Effective) :-
    system_max_leverage(SysMax),
    (   asset_class(Symbol, Class),
        max_leverage_limit(Class, ClassMax)
    ->  (ClassMax < SysMax -> Effective = ClassMax ; Effective = SysMax)
    ;   Effective = SysMax
    ).

% Effective min balance: tier-specific or system default
effective_min_balance(Min) :-
    (   account_tier(Tier),
        min_balance_floor(Tier, Min)
    ->  true
    ;   minimum_margin_requirement_usd(Min)
    ).

% Effective exposure ratio threshold: tier-specific or system default
effective_exposure_ratio_threshold(T) :-
    (   account_tier(Tier),
        max_open_exposure_ratio(Tier, T)
    ->  true
    ;   exposure_ratio_threshold(T)
    ).

% Effective projected exposure max: tier-specific or system default
effective_projected_exposure_max(M) :-
    (   account_tier(Tier),
        projected_exposure_ratio_max(Tier, M)
    ->  true
    ;   projected_exposure_ratio_max_default(M)
    ).

% =============================================================================
% CORE EVALUATION (fail-safe cut)
% =============================================================================

evaluate_trade(reject, Reason) :-
    reject_trade(Reason),
    !.
evaluate_trade(approve, 'All checks passed').

% =============================================================================
% REJECT RULES (25 distinct clauses) - all query facts, no hardcoded numbers
% =============================================================================

% 1) Symbol blacklist
reject_trade('Instrument is blacklisted') :-
    ticket(_, Symbol, _, _, _),
    blacklisted_symbol(Symbol).

% 2) Restricted session / rollover
reject_trade('Trading is blocked during restricted session') :-
    session(S),
    restricted_session(S).

% 3) Minimum lot size
reject_trade('Order size below minimum lot threshold') :-
    ticket(_, _, _, Lots, _),
    system_min_ticket_size_lots(Min),
    Lots < Min.

% 4) Maximum lot size
reject_trade('Order size exceeds maximum lot threshold') :-
    ticket(_, _, _, Lots, _),
    system_max_ticket_size_lots(Max),
    Lots > Max.

% 5) Hard leverage cap
reject_trade('Leverage exceeds hard limit') :-
    ticket(_, Symbol, _, _, Leverage),
    effective_max_leverage(Symbol, Max),
    Leverage > Max.

% 6) Low balance hard floor
reject_trade('Insufficient account balance') :-
    market(_, Balance, _, _),
    effective_min_balance(Min),
    Balance < Min.

% 7) Lots vs balance (simple sizing sanity check)
reject_trade('Over-leveraged position size vs balance') :-
    ticket(_, _, _, Lots, _),
    market(_, Balance, _, _),
    lots_balance_ratio_max(R),
    Lots > (Balance * R).

% 8) Notional too large vs balance
reject_trade('Notional size too large vs balance') :-
    ticket_notional(Notional),
    market(_, Balance, _, _),
    notional_balance_ratio_max(R),
    Notional > (Balance * R).

% 9) Critical existing exposure
reject_trade('Existing exposure is critical') :-
    exposure_level(critical).

% 10) Exposure ratio too high (numeric)
reject_trade('Open exposure exceeds risk threshold') :-
    open_exposure_value(OpenExp),
    market(_, Balance, _, _),
    Balance > 0.0,
    effective_exposure_ratio_threshold(T),
    (OpenExp / Balance) > T.

% 11) New + existing exposure too high
reject_trade('Projected exposure exceeds threshold') :-
    open_exposure_value(OpenExp),
    ticket_notional(Notional),
    market(_, Balance, _, _),
    Balance > 0.0,
    effective_projected_exposure_max(M),
    ((OpenExp + Notional) / Balance) > M.

% 12) Extreme volatility (fuzzy)
reject_trade('Market volatility is extreme') :-
    market(_, _, extreme, _).

% 13) Volatility extreme (numeric)
reject_trade('Volatility metric exceeds extreme threshold') :-
    volatility_value(V),
    volatility_extreme_threshold(T),
    V > T.

% 14) Wide spread (fuzzy)
reject_trade('Spread is too wide') :-
    market(_, _, _, wide).

% 15) Market order with wide spread
reject_trade('Market order blocked due to wide spread') :-
    order_type(market),
    market(_, _, _, wide).

% 16) High leverage in high volatility regime
reject_trade('High leverage not allowed in high volatility regime') :-
    ticket(_, _, _, _, Leverage),
    high_leverage_volatility_cap(Cap),
    Leverage > Cap,
    market(_, _, high, _).

% 17) High leverage in wide spread regime
reject_trade('High leverage not allowed with wide spreads') :-
    ticket(_, _, _, _, Leverage),
    spread_wide_leverage_cap(Cap),
    Leverage > Cap,
    market(_, _, _, wide).

% 18) Exotic symbol with small balance
reject_trade('Exotic instrument blocked for small accounts') :-
    ticket(_, Symbol, _, _, _),
    exotic_symbol(Symbol),
    market(_, Balance, _, _),
    min_balance_exotic(Min),
    Balance < Min.

% 19) IOC with limit (simplified policy constraint)
reject_trade('IOC not allowed for limit orders') :-
    order_type(limit),
    time_in_force(ioc).

% 20) FOK only permitted for limit orders (simplified)
reject_trade('FOK not allowed for market orders') :-
    order_type(market),
    time_in_force(fok).

% 21) Limit price too far from mid (stale/errant pricing)
reject_trade('Limit price too far from current market mid') :-
    order_type(limit),
    price_value(Price),
    market_mid(Mid),
    Mid > 0.0,
    Diff is (Price - Mid) / Mid,
    abs_val(Diff, AbsDiff),
    limit_price_deviation_pct_max(Max),
    AbsDiff > Max.

% 22) Buy limit above ask
reject_trade('Buy limit price crosses the ask') :-
    ticket(_, _, buy, _, _),
    order_type(limit),
    price_value(Price),
    ask_value(Ask),
    Price >= Ask.

% 23) Sell limit below bid
reject_trade('Sell limit price crosses the bid') :-
    ticket(_, _, sell, _, _),
    order_type(limit),
    price_value(Price),
    bid_value(Bid),
    Price =< Bid.

% 24) Very negative sentiment blocks buys
reject_trade('Negative sentiment blocks buy-side trading') :-
    ticket(_, _, buy, _, _),
    sentiment_level(negative).

% 25) Very positive sentiment blocks sells (simple contrarian risk policy)
reject_trade('Positive sentiment blocks sell-side trading') :-
    ticket(_, _, sell, _, _),
    sentiment_level(positive).
