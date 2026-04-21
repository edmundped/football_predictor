"""
Daily slip (accumulator) variant generator.

Given a per-fixture prediction table, build four slip variants:

  1. SAFE         — fewer legs, each with very high probability.
  2. BALANCED     — middle risk.
  3. AGGRESSIVE   — longer accumulator, more picks, lower combined prob but higher payout.
  4. VALUE        — picks where model probability most exceeds market implied probability.
                    Requires bookmaker odds to be present in the fixtures CSV.

Rules:
  - At most one leg per fixture. Two picks from the same match are correlated
    (e.g. "home win" and "over 2.5") and break the independence assumption
    used to compute combined probability.
  - Each candidate pick is scored by prob (safe/balanced/aggressive) or by
    edge = model_prob / market_implied - 1 (value).
  - Combined probability = product of leg probabilities.
  - Combined fair odds = product of 1/leg_prob.
  - If market odds are attached to a leg, also compute combined market payout
    and slip EV = combined_prob * combined_payout - 1.
"""

from __future__ import annotations

import pandas as pd


# ---------- candidate pool ----------

def _base_fixture_id(row: pd.Series, sport: str) -> str:
    existing = row.get("fixture_id")
    if existing is not None and pd.notna(existing):
        return str(existing)
    date_part = row["date"].date() if pd.notna(row.get("date")) else ""
    return f"{sport}_{row['league']}_{row['home']}_vs_{row['away']}_{date_part}"


def _football_market_candidates(row: pd.Series) -> list[dict]:
    """
    For one fixture, emit one candidate per supported market, using the pick
    with the highest probability within that market.
    """
    fid = _base_fixture_id(row, "football")
    match_label = f"{row['home']} v {row['away']}"

    cands = []

    # 1X2: pick the side with highest prob
    prices_1x2 = [
        ("Home win", row["p_home"], row.get("odds_home")),
        ("Draw", row["p_draw"], row.get("odds_draw")),
        ("Away win", row["p_away"], row.get("odds_away")),
    ]
    label, prob, odds = max(prices_1x2, key=lambda x: x[1])
    cands.append({
        "fixture_id": fid, "sport": "football", "match": match_label, "league": row["league"],
        "market": "1X2", "pick": label, "prob": float(prob),
        "market_odds": float(odds) if pd.notna(odds) else None,
    })

    # Over / Under 2.5
    if row["p_over25"] >= row["p_under25"]:
        ou_label, ou_prob, ou_odds = "Over 2.5", row["p_over25"], row.get("odds_over25")
    else:
        ou_label, ou_prob, ou_odds = "Under 2.5", row["p_under25"], row.get("odds_under25")
    cands.append({
        "fixture_id": fid, "sport": "football", "match": match_label, "league": row["league"],
        "market": "Totals", "pick": ou_label, "prob": float(ou_prob),
        "market_odds": float(ou_odds) if pd.notna(ou_odds) else None,
    })

    # BTTS — no market odds in the free CSV feed, but still useful
    if row["p_btts"] >= row["p_btts_no"]:
        btts_label, btts_prob = "BTTS: Yes", row["p_btts"]
    else:
        btts_label, btts_prob = "BTTS: No", row["p_btts_no"]
    cands.append({
        "fixture_id": fid, "sport": "football", "match": match_label, "league": row["league"],
        "market": "BTTS", "pick": btts_label, "prob": float(btts_prob),
        "market_odds": None,
    })

    return cands


def _basketball_market_candidates(row: pd.Series) -> list[dict]:
    fid = _base_fixture_id(row, "basketball")
    match_label = f"{row['home']} v {row['away']}"
    cands = []

    prices_ml = [
        (f"{row['home']} ML", row["p_home"], row.get("odds_home")),
        (f"{row['away']} ML", row["p_away"], row.get("odds_away")),
    ]
    label, prob, odds = max(prices_ml, key=lambda x: x[1])
    cands.append({
        "fixture_id": fid, "sport": "basketball", "match": match_label, "league": row["league"],
        "market": "Moneyline", "pick": label, "prob": float(prob),
        "market_odds": float(odds) if pd.notna(odds) else None,
    })

    if pd.notna(row.get("p_home_cover")) and pd.notna(row.get("p_away_cover")):
        spread_home = row.get("spread_home")
        spread_away = row.get("spread_away")
        home_line = f"{float(spread_home):+g}" if pd.notna(spread_home) else ""
        away_line = f"{float(spread_away):+g}" if pd.notna(spread_away) else ""
        prices_spread = [
            (f"{row['home']} {home_line}".strip(), row["p_home_cover"], row.get("odds_spread_home")),
            (f"{row['away']} {away_line}".strip(), row["p_away_cover"], row.get("odds_spread_away")),
        ]
        label, prob, odds = max(prices_spread, key=lambda x: x[1])
        cands.append({
            "fixture_id": fid, "sport": "basketball", "match": match_label, "league": row["league"],
            "market": "Spread", "pick": label, "prob": float(prob),
            "market_odds": float(odds) if pd.notna(odds) else None,
        })

    if pd.notna(row.get("total_line")) and pd.notna(row.get("p_over_total")) and pd.notna(row.get("p_under_total")):
        line = f"{float(row['total_line']):g}"
        prices_total = [
            (f"Over {line}", row["p_over_total"], row.get("odds_over")),
            (f"Under {line}", row["p_under_total"], row.get("odds_under")),
        ]
        label, prob, odds = max(prices_total, key=lambda x: x[1])
        cands.append({
            "fixture_id": fid, "sport": "basketball", "match": match_label, "league": row["league"],
            "market": "Totals", "pick": label, "prob": float(prob),
            "market_odds": float(odds) if pd.notna(odds) else None,
        })

    return cands


def _market_candidates(row: pd.Series) -> list[dict]:
    sport = str(row.get("sport", "football")).lower()
    if sport == "basketball":
        return _basketball_market_candidates(row)
    return _football_market_candidates(row)


def build_candidate_pool(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in predictions.iterrows():
        rows.extend(_market_candidates(row))
    pool = pd.DataFrame(rows)
    if pool.empty:
        return pd.DataFrame(columns=[
            "fixture_id", "sport", "match", "league", "market", "pick", "prob",
            "market_odds", "fair_odds", "market_implied", "edge",
        ])
    pool["prob"] = pd.to_numeric(pool["prob"], errors="coerce")
    pool["market_odds"] = pd.to_numeric(pool["market_odds"], errors="coerce")
    pool = pool.dropna(subset=["prob"])
    pool["fair_odds"] = 1.0 / pool["prob"]
    # edge is only meaningful when market odds exist
    pool["market_implied"] = 1.0 / pool["market_odds"]
    pool["edge"] = pool["prob"] / pool["market_implied"] - 1.0
    return pool


# ---------- slip assembly ----------

def _assemble(
    pool: pd.DataFrame,
    *,
    min_prob: float,
    target_legs: int,
    max_legs: int,
    sort_key: str,
    ascending: bool = False,
) -> pd.DataFrame:
    """
    Greedy: take the top picks by sort_key that clear min_prob, one per fixture,
    up to target_legs (or max_legs if fewer eligible).
    """
    eligible = pool[pool["prob"] >= min_prob].sort_values(sort_key, ascending=ascending)
    picked = []
    used_fixtures: set[str] = set()
    for _, row in eligible.iterrows():
        if row["fixture_id"] in used_fixtures:
            continue
        picked.append(row)
        used_fixtures.add(row["fixture_id"])
        if len(picked) >= target_legs:
            break
    if len(picked) < 2:
        # no slip if we can't even get a double
        return pd.DataFrame()
    # don't exceed max_legs
    picked = picked[:max_legs]
    return pd.DataFrame(picked).reset_index(drop=True)


def _slip_stats(legs: pd.DataFrame) -> dict:
    combined_prob = float(legs["prob"].prod())
    combined_fair_odds = float(legs["fair_odds"].prod())

    # combined market payout only if ALL legs have market odds
    if legs["market_odds"].notna().all():
        combined_market = float(legs["market_odds"].prod())
        ev = combined_prob * combined_market - 1.0
    else:
        combined_market = None
        ev = None

    return {
        "legs": len(legs),
        "combined_prob": combined_prob,
        "combined_fair_odds": combined_fair_odds,
        "combined_market_odds": combined_market,
        "expected_value_per_unit": ev,
    }


def build_slips(predictions: pd.DataFrame, slip_cfg: dict) -> dict:
    """
    Return a dict of variant -> {legs: DataFrame, stats: dict}.
    Missing variants are omitted (e.g. value slip omitted if no market odds).
    """
    if predictions.empty:
        return {}

    pool = build_candidate_pool(predictions)
    out: dict[str, dict] = {}

    for name, kwargs in {
        "SAFE": dict(
            min_prob=float(slip_cfg["safe_min_leg_prob"]),
            target_legs=int(slip_cfg["safe_legs"]),
            max_legs=int(slip_cfg["max_per_slip"]),
            sort_key="prob",
        ),
        "BALANCED": dict(
            min_prob=float(slip_cfg["balanced_min_leg_prob"]),
            target_legs=int(slip_cfg["balanced_legs"]),
            max_legs=int(slip_cfg["max_per_slip"]),
            sort_key="prob",
        ),
        "AGGRESSIVE": dict(
            min_prob=float(slip_cfg["aggressive_min_leg_prob"]),
            target_legs=int(slip_cfg["aggressive_legs"]),
            max_legs=int(slip_cfg["max_per_slip"]),
            sort_key="prob",
        ),
    }.items():
        legs = _assemble(pool, **kwargs)
        if not legs.empty:
            out[name] = {"legs": legs, "stats": _slip_stats(legs)}

    # VALUE slip — needs market odds
    if pool["market_odds"].notna().any():
        edge_pool = pool[pool["market_odds"].notna()].copy()
        edge_pool = edge_pool[edge_pool["edge"] >= float(slip_cfg["value_min_edge"])]
        edge_pool = edge_pool[edge_pool["prob"] >= float(slip_cfg["min_market_prob"])]
        if not edge_pool.empty:
            legs = _assemble(
                edge_pool,
                min_prob=float(slip_cfg["min_market_prob"]),
                target_legs=int(slip_cfg["balanced_legs"]),
                max_legs=int(slip_cfg["max_per_slip"]),
                sort_key="edge",
            )
            if not legs.empty:
                out["VALUE"] = {"legs": legs, "stats": _slip_stats(legs)}

    return out
