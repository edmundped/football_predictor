"""
Fractional Kelly criterion staking.

For a single bet or accumulator:
    edge        = prob * decimal_odds - 1
    kelly_f     = edge / (decimal_odds - 1)
    stake       = kelly_fraction * kelly_f * bankroll

Fractional Kelly (default 0.25) dramatically reduces variance while
preserving most of the long-run growth rate. Stake is also capped at
max_bet_pct of bankroll so no single slip can blow up the roll.
"""

from __future__ import annotations

DEFAULT_KELLY_FRACTION = 0.25   # quarter-Kelly
DEFAULT_MAX_BET_PCT    = 0.05   # never risk > 5 % of bankroll per slip
DEFAULT_MIN_STAKE      = 0.50   # ignore bets smaller than 50 cents


def kelly_stake(
    prob: float,
    decimal_odds: float,
    bankroll: float,
    kelly_fraction: float = DEFAULT_KELLY_FRACTION,
    max_bet_pct: float    = DEFAULT_MAX_BET_PCT,
    min_stake: float      = DEFAULT_MIN_STAKE,
) -> dict:
    """
    Compute the recommended stake for a single bet or an accumulator treated as
    a single outcome (combined prob / combined odds).

    Returns
    -------
    dict with keys:
        edge                -- model edge (prob * odds - 1)
        kelly_f             -- full-Kelly fraction
        recommended_stake   -- what to actually bet (GHS)
        capped              -- True if max_bet_pct limit was binding
        expected_profit     -- stake * edge
        potential_payout    -- stake * decimal_odds
    """
    if decimal_odds <= 1.0 or not (0 < prob < 1) or bankroll <= 0:
        return _zero(bankroll)

    edge = prob * decimal_odds - 1.0
    if edge <= 0:
        return {
            "edge": round(edge, 4),
            "kelly_f": 0.0,
            "recommended_stake": 0.0,
            "capped": False,
            "expected_profit": 0.0,
            "potential_payout": 0.0,
        }

    kelly_f  = edge / (decimal_odds - 1.0)
    raw      = kelly_fraction * kelly_f * bankroll
    max_     = max_bet_pct * bankroll
    capped   = raw > max_
    stake    = round(min(raw, max_), 2)

    if stake < min_stake:
        stake = 0.0

    return {
        "edge":              round(edge,   4),
        "kelly_f":           round(kelly_f, 4),
        "recommended_stake": stake,
        "capped":            capped,
        "expected_profit":   round(stake * edge, 2),
        "potential_payout":  round(stake * decimal_odds, 2),
    }


def slip_kelly(
    combined_prob: float,
    combined_market_odds: float | None,
    combined_fair_odds: float,
    bankroll: float,
    kelly_fraction: float = DEFAULT_KELLY_FRACTION,
    max_bet_pct: float    = DEFAULT_MAX_BET_PCT,
) -> dict:
    """
    Kelly stake for an accumulator.
    Uses market odds when available; falls back to fair odds (edge will be 0).
    """
    odds = combined_market_odds if (combined_market_odds is not None) else combined_fair_odds
    return kelly_stake(combined_prob, odds, bankroll, kelly_fraction, max_bet_pct)


def _zero(bankroll: float) -> dict:
    return {
        "edge": 0.0,
        "kelly_f": 0.0,
        "recommended_stake": 0.0,
        "capped": False,
        "expected_profit": 0.0,
        "potential_payout": 0.0,
    }
