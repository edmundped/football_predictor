"""
Daily slip (accumulator) variant generator.

Given a per-fixture prediction table, build slip variants:

  1. SAFE         — fewer legs, each with very high probability.
  2. BALANCED     — middle risk.
  3. AGGRESSIVE   — longer accumulator, more picks, lower combined prob but higher payout.
  4. ONE_CEDI_DREAM — priced picks from the consolidated pool targeting 100+ market odds.
  5. HUNDRED_K_*  — diversified priced accumulators targeting a 100,000 GHS payout.
  6. VALUE        — picks where model probability most exceeds market implied probability.
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

    def add(market: str, pick: str, prob, odds=None) -> None:
        if pd.isna(prob):
            return
        cands.append({
            "fixture_id": fid, "sport": "football", "match": match_label, "league": row["league"],
            "market": market, "pick": pick, "prob": float(prob),
            "market_odds": float(odds) if pd.notna(odds) else None,
        })

    # 1X2: pick the side with highest prob
    prices_1x2 = [
        ("Home win", row["p_home"], row.get("odds_home")),
        ("Draw", row["p_draw"], row.get("odds_draw")),
        ("Away win", row["p_away"], row.get("odds_away")),
    ]
    label, prob, odds = max(prices_1x2, key=lambda x: x[1])
    add("1X2", label, prob, odds)

    double_chance = [
        ("Home or Draw", row.get("p_home_or_draw")),
        ("Away or Draw", row.get("p_away_or_draw")),
        ("Home or Away", row.get("p_home_or_away")),
    ]
    label, prob = max(double_chance, key=lambda x: x[1] if pd.notna(x[1]) else -1)
    add("Double Chance", label, prob)

    for line in ("05", "15", "25", "35"):
        over = row.get(f"p_over{line}")
        under = row.get(f"p_under{line}")
        display = f"{int(line[0])}.{line[1]}"
        over_odds = row.get("odds_over25") if line == "25" else None
        under_odds = row.get("odds_under25") if line == "25" else None
        if pd.notna(over) and pd.notna(under):
            if over >= under:
                add("Totals", f"Over {display}", over, over_odds)
            else:
                add("Totals", f"Under {display}", under, under_odds)

    # BTTS — no market odds in the free CSV feed, but still useful
    if row["p_btts"] >= row["p_btts_no"]:
        btts_label, btts_prob = "BTTS: Yes", row["p_btts"]
    else:
        btts_label, btts_prob = "BTTS: No", row["p_btts_no"]
    add("BTTS", btts_label, btts_prob)

    for market, pick, prob in [
        ("Team Goals", f"{row['home']} over 0.5", row.get("p_home_over05")),
        ("Team Goals", f"{row['away']} over 0.5", row.get("p_away_over05")),
        ("Team Goals", f"{row['home']} over 1.5", row.get("p_home_over15")),
        ("Team Goals", f"{row['away']} over 1.5", row.get("p_away_over15")),
        ("Clean Sheet", f"{row['home']} clean sheet", row.get("p_home_clean_sheet")),
        ("Clean Sheet", f"{row['away']} clean sheet", row.get("p_away_clean_sheet")),
    ]:
        add(market, pick, prob)

    return cands


def _basketball_market_candidates(row: pd.Series) -> list[dict]:
    fid = _base_fixture_id(row, "basketball")
    match_label = f"{row['home']} v {row['away']}"
    cands = []

    def add(market: str, pick: str, prob, odds=None) -> None:
        if pd.isna(prob):
            return
        cands.append({
            "fixture_id": fid, "sport": "basketball", "match": match_label, "league": row["league"],
            "market": market, "pick": pick, "prob": float(prob),
            "market_odds": float(odds) if pd.notna(odds) else None,
        })

    prices_ml = [
        (f"{row['home']} ML", row["p_home"], row.get("odds_home")),
        (f"{row['away']} ML", row["p_away"], row.get("odds_away")),
    ]
    label, prob, odds = max(prices_ml, key=lambda x: x[1])
    add("Moneyline", label, prob, odds)

    alt_spreads = [
        (f"{row['home']} +5.5", row.get("p_home_plus55")),
        (f"{row['away']} +5.5", row.get("p_away_plus55")),
        (f"{row['home']} +9.5", row.get("p_home_plus95")),
        (f"{row['away']} +9.5", row.get("p_away_plus95")),
    ]
    label, prob = max(alt_spreads, key=lambda x: x[1] if pd.notna(x[1]) else -1)
    add("Alt Spread", label, prob)

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
        add("Spread", label, prob, odds)

    if pd.notna(row.get("total_line")) and pd.notna(row.get("p_over_total")) and pd.notna(row.get("p_under_total")):
        line = f"{float(row['total_line']):g}"
        prices_total = [
            (f"Over {line}", row["p_over_total"], row.get("odds_over")),
            (f"Under {line}", row["p_under_total"], row.get("odds_under")),
        ]
        label, prob, odds = max(prices_total, key=lambda x: x[1])
        add("Totals", label, prob, odds)

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


def _assemble_target_market_odds(
    pool: pd.DataFrame,
    *,
    min_prob: float,
    target_odds: float,
    max_legs: int,
    used_counts: dict[str, int] | None = None,
) -> pd.DataFrame:
    """
    Build a priced accumulator from the best available consolidated picks.
    The first pass keeps the configured minimum probability; later passes
    relax it slightly so the report still offers the strongest available
    100-odds attempt on short fixture slates.
    """
    priced = pool[
        pool["market_odds"].notna()
        & pool["prob"].notna()
        & (pool["market_odds"] > 1.0)
    ].copy()
    if priced.empty:
        return pd.DataFrame()

    if used_counts:
        priced["_usage"] = priced["fixture_id"].astype(str).map(used_counts).fillna(0).astype(int)
    else:
        priced["_usage"] = 0

    floors = [min_prob, 0.50, 0.45, 0.40, 0.35, 0.30]
    thresholds = []
    for floor in floors:
        floor = min(float(floor), float(min_prob))
        if floor not in thresholds:
            thresholds.append(floor)

    best_picked: list[pd.Series] = []
    best_odds = 0.0
    for threshold in thresholds:
        eligible = priced[priced["prob"] >= threshold].sort_values(
            ["_usage", "prob", "edge", "market_odds"],
            ascending=[True, False, False, False],
        )
        picked = []
        used_fixtures: set[str] = set()
        combined_market = 1.0
        for _, row in eligible.iterrows():
            if row["fixture_id"] in used_fixtures:
                continue
            picked.append(row)
            used_fixtures.add(row["fixture_id"])
            combined_market *= float(row["market_odds"])
            if combined_market >= target_odds or len(picked) >= max_legs:
                break

        if len(picked) >= 2 and combined_market > best_odds:
            best_picked = picked
            best_odds = combined_market
        if len(picked) >= 2 and combined_market >= target_odds:
            return pd.DataFrame(picked).reset_index(drop=True)

    if len(best_picked) < 2:
        return pd.DataFrame()
    return pd.DataFrame(best_picked).reset_index(drop=True)


def _assemble_target_payout_ladder(
    pool: pd.DataFrame,
    *,
    count: int,
    stake: float,
    target_payout: float,
    min_prob: float,
    max_legs: int,
) -> dict[str, pd.DataFrame]:
    """
    Build multiple diversified attempts at a target payout.

    This is still an accumulator long-shot, so "safe" means the least unsafe
    construction available from priced legs: high model probability first,
    one pick per fixture, and later slips prefer unused fixtures before reusing
    anything from earlier slips.
    """
    if stake <= 0 or target_payout <= stake or count <= 0:
        return {}

    target_odds = target_payout / stake
    out: dict[str, pd.DataFrame] = {}
    used_counts: dict[str, int] = {}
    floors = [min_prob, max(0.55, min_prob - 0.05), 0.50, 0.45, 0.40, 0.35]

    for idx in range(1, count + 1):
        floor = floors[min(idx - 1, len(floors) - 1)]
        legs = _assemble_target_market_odds(
            pool,
            min_prob=floor,
            target_odds=target_odds,
            max_legs=max_legs,
            used_counts=used_counts,
        )
        if legs.empty:
            continue

        out[f"HUNDRED_K_SAFE_{idx}"] = legs
        for fixture_id in legs["fixture_id"].astype(str):
            used_counts[fixture_id] = used_counts.get(fixture_id, 0) + 1

    return out


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

    if slip_cfg.get("banker_100_enabled", True):
        legs = _assemble_target_market_odds(
            pool,
            min_prob=float(slip_cfg.get("banker_100_min_leg_prob", 0.50)),
            target_odds=float(slip_cfg.get("banker_100_target_odds", 100.0)),
            max_legs=int(slip_cfg.get("banker_100_max_legs", 20)),
        )
        if not legs.empty:
            out["ONE_CEDI_DREAM"] = {"legs": legs, "stats": _slip_stats(legs)}

    if slip_cfg.get("hundred_k_enabled", True):
        stake = float(slip_cfg.get("hundred_k_stake", 1.0))
        target_payout = float(slip_cfg.get("hundred_k_target_payout", 100000.0))
        ladder = _assemble_target_payout_ladder(
            pool,
            count=int(slip_cfg.get("hundred_k_slip_count", 5)),
            stake=stake,
            target_payout=target_payout,
            min_prob=float(slip_cfg.get("hundred_k_min_leg_prob", 0.55)),
            max_legs=int(slip_cfg.get("hundred_k_max_legs", 40)),
        )
        for name, legs in ladder.items():
            stats = _slip_stats(legs)
            stats["target_stake"] = stake
            stats["target_payout"] = target_payout
            stats["target_odds"] = target_payout / stake if stake > 0 else None
            out[name] = {"legs": legs, "stats": stats}

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
