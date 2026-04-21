"""
Basketball prediction model.

This mirrors the football path at a simpler level: fit recent score results,
maintain Elo-style team strength, estimate expected points, then derive
moneyline, spread, and total probabilities from normal distributions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd
from scipy.stats import norm


DEFAULT_RATING = 1500.0


@dataclass
class BasketballState:
    ratings: dict[str, float] = field(default_factory=dict)
    team_offense: dict[str, float] = field(default_factory=dict)
    team_defense: dict[str, float] = field(default_factory=dict)
    league_home_points: dict[str, float] = field(default_factory=dict)
    league_away_points: dict[str, float] = field(default_factory=dict)
    league_margin_std: dict[str, float] = field(default_factory=dict)
    league_total_std: dict[str, float] = field(default_factory=dict)
    k: float = 18.0
    home_adv_elo: float = 55.0
    home_adv_points: float = 2.5
    margin_weight: float = 1.0
    rating_points_scale: float = 28.0

    def key(self, league: str, team: str) -> str:
        return f"{league}::{team}"

    def get(self, league: str, team: str) -> float:
        return self.ratings.get(self.key(league, team), DEFAULT_RATING)

    def set(self, league: str, team: str, rating: float) -> None:
        self.ratings[self.key(league, team)] = rating

    def off(self, league: str, team: str) -> float:
        return self.team_offense.get(self.key(league, team), 0.0)

    def defense(self, league: str, team: str) -> float:
        return self.team_defense.get(self.key(league, team), 0.0)


def _expected_score(rating_home: float, rating_away: float, home_adv_elo: float) -> float:
    diff = (rating_home + home_adv_elo) - rating_away
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


def _actual_score(home_score: int, away_score: int) -> float:
    return 1.0 if home_score > away_score else 0.0


def _margin_multiplier(margin: float, weight: float) -> float:
    raw = 1.0 + min(abs(margin), 35.0) / 28.0
    return raw * weight + (1.0 - weight)


def fit(history: pd.DataFrame, cfg: dict) -> BasketballState:
    state = BasketballState(
        k=float(cfg.get("k_factor", 18)),
        home_adv_elo=float(cfg.get("home_advantage_elo", 55)),
        home_adv_points=float(cfg.get("home_advantage_points", 2.5)),
        margin_weight=float(cfg.get("margin_weight", 1.0)),
        rating_points_scale=float(cfg.get("rating_points_scale", 28.0)),
    )

    if history.empty:
        return state

    hist = history.dropna(subset=["home_score", "away_score"]).copy()
    hist["home_score"] = pd.to_numeric(hist["home_score"], errors="coerce")
    hist["away_score"] = pd.to_numeric(hist["away_score"], errors="coerce")
    hist = hist.dropna(subset=["home_score", "away_score"])
    if hist.empty:
        return state

    lg = hist.groupby("league").agg(
        home_points=("home_score", "mean"),
        away_points=("away_score", "mean"),
        margin_std=("home_score", lambda s: float("nan")),
    )
    for league, row in lg.iterrows():
        league_games = hist[hist["league"] == league]
        margins = league_games["home_score"] - league_games["away_score"]
        totals = league_games["home_score"] + league_games["away_score"]
        state.league_home_points[league] = float(row["home_points"])
        state.league_away_points[league] = float(row["away_points"])
        state.league_margin_std[league] = max(8.0, float(margins.std() or 0.0))
        state.league_total_std[league] = max(10.0, float(totals.std() or 0.0))

    team_rows = []
    for r in hist.itertuples(index=False):
        team_rows.append({
            "league": r.league,
            "team": r.home,
            "scored": float(r.home_score),
            "allowed": float(r.away_score),
        })
        team_rows.append({
            "league": r.league,
            "team": r.away,
            "scored": float(r.away_score),
            "allowed": float(r.home_score),
        })

    team_df = pd.DataFrame(team_rows)
    if not team_df.empty:
        for (league, team), row in team_df.groupby(["league", "team"]).mean(numeric_only=True).iterrows():
            league_avg_team = (
                state.league_home_points.get(league, 100.0)
                + state.league_away_points.get(league, 100.0)
            ) / 2.0
            key = state.key(league, team)
            state.team_offense[key] = float(row["scored"] - league_avg_team)
            state.team_defense[key] = float(row["allowed"] - league_avg_team)

    for row in hist.sort_values("date").itertuples(index=False):
        rh = state.get(row.league, row.home)
        ra = state.get(row.league, row.away)
        expected_h = _expected_score(rh, ra, state.home_adv_elo)
        actual_h = _actual_score(int(row.home_score), int(row.away_score))
        mult = _margin_multiplier(float(row.home_score - row.away_score), state.margin_weight)
        delta = state.k * mult * (actual_h - expected_h)
        state.set(row.league, row.home, rh + delta)
        state.set(row.league, row.away, ra - delta)

    return state


def _expected_points(
    state: BasketballState,
    league: str,
    home: str,
    away: str,
    fallback_home: float,
    fallback_away: float,
) -> tuple[float, float]:
    league_home = state.league_home_points.get(league, fallback_home)
    league_away = state.league_away_points.get(league, fallback_away)

    raw_home = league_home + 0.55 * state.off(league, home) + 0.45 * state.defense(league, away)
    raw_away = league_away + 0.55 * state.off(league, away) + 0.45 * state.defense(league, home)

    rating_margin = ((state.get(league, home) - state.get(league, away)) / state.rating_points_scale) + state.home_adv_points
    raw_margin = raw_home - raw_away
    shift = (rating_margin - raw_margin) / 2.0

    return max(50.0, raw_home + shift), max(50.0, raw_away - shift)


def _fair_odds(prob: float | None) -> float | None:
    if prob is None or prob <= 0:
        return None
    return 1.0 / prob


def _prob_margin_over(threshold: float, mean_margin: float, margin_std: float) -> float:
    return float(norm.sf(threshold, loc=mean_margin, scale=margin_std))


def _prob_total_over(threshold: float, mean_total: float, total_std: float) -> float:
    return float(norm.sf(threshold, loc=mean_total, scale=total_std))


def predict_fixtures(
    fixtures: pd.DataFrame,
    state: BasketballState,
    cfg: dict,
) -> pd.DataFrame:
    if fixtures.empty:
        return pd.DataFrame()

    fallback_home = float(cfg.get("league_avg_home_points", 104.0))
    fallback_away = float(cfg.get("league_avg_away_points", 101.5))
    fallback_margin_std = float(cfg.get("margin_std", 12.0))
    fallback_total_std = float(cfg.get("total_std", 15.0))

    rows = []
    for row in fixtures.itertuples(index=False):
        pred_home, pred_away = _expected_points(
            state,
            row.league,
            row.home,
            row.away,
            fallback_home,
            fallback_away,
        )
        mean_margin = pred_home - pred_away
        mean_total = pred_home + pred_away
        margin_std = state.league_margin_std.get(row.league, fallback_margin_std)
        total_std = state.league_total_std.get(row.league, fallback_total_std)

        p_home = _prob_margin_over(0.0, mean_margin, margin_std)
        p_away = 1.0 - p_home

        spread_home = getattr(row, "spread_home", None)
        spread_away = getattr(row, "spread_away", None)
        total_line = getattr(row, "total_line", None)

        p_home_cover = None
        p_away_cover = None
        if pd.notna(spread_home):
            p_home_cover = _prob_margin_over(-float(spread_home), mean_margin, margin_std)
            p_away_cover = 1.0 - p_home_cover
        elif pd.notna(spread_away):
            p_away_cover = _prob_margin_over(float(spread_away), -mean_margin, margin_std)
            p_home_cover = 1.0 - p_away_cover

        p_over = None
        p_under = None
        if pd.notna(total_line):
            p_over = _prob_total_over(float(total_line), mean_total, total_std)
            p_under = 1.0 - p_over

        fixture_id = getattr(row, "event_id", None) or (
            f"basketball_{row.league}_{row.home}_{row.away}_{pd.to_datetime(row.date).date()}"
        )

        rows.append({
            "fixture_id": fixture_id,
            "date": getattr(row, "date", None),
            "sport": "basketball",
            "league": row.league,
            "home": row.home,
            "away": row.away,
            "pred_home_score": round(pred_home, 1),
            "pred_away_score": round(pred_away, 1),
            "pred_total": round(mean_total, 1),
            "pred_margin_home": round(mean_margin, 1),
            "p_home": p_home,
            "p_away": p_away,
            "fair_odds_home": _fair_odds(p_home),
            "fair_odds_away": _fair_odds(p_away),
            "spread_home": spread_home,
            "spread_away": spread_away,
            "p_home_cover": p_home_cover,
            "p_away_cover": p_away_cover,
            "total_line": total_line,
            "p_over_total": p_over,
            "p_under_total": p_under,
            "odds_home": getattr(row, "odds_home", None),
            "odds_away": getattr(row, "odds_away", None),
            "odds_spread_home": getattr(row, "odds_spread_home", None),
            "odds_spread_away": getattr(row, "odds_spread_away", None),
            "odds_over": getattr(row, "odds_over", None),
            "odds_under": getattr(row, "odds_under", None),
        })

    return pd.DataFrame(rows).sort_values(["date", "league", "home"]).reset_index(drop=True)


def ratings_table(state: BasketballState) -> pd.DataFrame:
    rows = []
    for key, rating in state.ratings.items():
        league, team = key.split("::", 1)
        rows.append({"league": league, "team": team, "rating": rating})
    return pd.DataFrame(rows).sort_values(["league", "rating"], ascending=[True, False]).reset_index(drop=True)
