"""
Goal-weighted Elo ratings.

Each team has a single rating. Home advantage is added to the home team's
rating at match time (not baked into rating). After each match we update based
on expected vs actual outcome, scaled by margin of victory (goal-weighted).

Separately we estimate per-league attack/defense adjustments so that Elo gaps
map to sensible expected goals for a given league's average goals per game.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


DEFAULT_RATING = 1500.0


@dataclass
class RatingState:
    ratings: dict[str, float] = field(default_factory=dict)
    league_home_goals: dict[str, float] = field(default_factory=dict)
    league_away_goals: dict[str, float] = field(default_factory=dict)
    league_home_adv_goals: dict[str, float] = field(default_factory=dict)
    team_attack: dict[str, float] = field(default_factory=dict)
    team_defense: dict[str, float] = field(default_factory=dict)
    k: float = 20.0
    home_adv: float = 65.0
    goal_diff_weight: float = 1.0

    def key(self, league: str, team: str) -> str:
        return f"{league}::{team}"

    def get(self, team: str) -> float:
        return self.ratings.get(team, DEFAULT_RATING)

    def set(self, team: str, rating: float) -> None:
        self.ratings[team] = rating

    def attack(self, league: str, team: str) -> float:
        return self.team_attack.get(self.key(league, team), 0.0)

    def defense(self, league: str, team: str) -> float:
        return self.team_defense.get(self.key(league, team), 0.0)


def _expected_score(rating_home: float, rating_away: float, home_adv: float) -> float:
    diff = (rating_home + home_adv) - rating_away
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


def _match_score(home_goals: int, away_goals: int) -> float:
    if home_goals > away_goals:
        return 1.0
    if home_goals < away_goals:
        return 0.0
    return 0.5


def _goal_diff_multiplier(home_goals: int, away_goals: int, weight: float) -> float:
    # classic FIFA-style margin weighting, scaled by `weight`
    margin = abs(home_goals - away_goals)
    if margin <= 1:
        return 1.0 * weight + (1 - weight)
    if margin == 2:
        return 1.5 * weight + (1 - weight)
    return ((11 + margin) / 8.0) * weight + (1 - weight)


def fit(history: pd.DataFrame, elo_cfg: dict) -> RatingState:
    """
    Walk forward through history chronologically, updating team ratings.
    Also compute per-league average goals (home/away) for scaling later.
    """
    state = RatingState(
        k=float(elo_cfg["k_factor"]),
        home_adv=float(elo_cfg["home_advantage"]),
        goal_diff_weight=float(elo_cfg["goal_diff_weight"]),
    )

    if history.empty:
        return state

    # per-league goal averages
    lg = history.groupby("league").agg(
        home_goals=("home_goals", "mean"),
        away_goals=("away_goals", "mean"),
    )
    for league, row in lg.iterrows():
        state.league_home_goals[league] = float(row["home_goals"])
        state.league_away_goals[league] = float(row["away_goals"])
        state.league_home_adv_goals[league] = float(row["home_goals"] - row["away_goals"])

    team_rows = []
    for row in history.itertuples(index=False):
        team_rows.append({
            "league": row.league,
            "team": row.home,
            "scored": float(row.home_goals),
            "allowed": float(row.away_goals),
        })
        team_rows.append({
            "league": row.league,
            "team": row.away,
            "scored": float(row.away_goals),
            "allowed": float(row.home_goals),
        })

    team_df = pd.DataFrame(team_rows)
    if not team_df.empty:
        for (league, team), row in team_df.groupby(["league", "team"]).mean(numeric_only=True).iterrows():
            league_avg_team = (
                state.league_home_goals.get(league, 1.50)
                + state.league_away_goals.get(league, 1.15)
            ) / 2.0
            key = state.key(league, team)
            state.team_attack[key] = float(row["scored"] - league_avg_team)
            # Positive defense means this team suppresses opponent scoring.
            state.team_defense[key] = float(league_avg_team - row["allowed"])

    # walk through matches in order
    for row in history.itertuples(index=False):
        rh = state.get(row.home)
        ra = state.get(row.away)
        expected_h = _expected_score(rh, ra, state.home_adv)
        actual_h = _match_score(row.home_goals, row.away_goals)
        mult = _goal_diff_multiplier(row.home_goals, row.away_goals, state.goal_diff_weight)
        delta = state.k * mult * (actual_h - expected_h)
        state.set(row.home, rh + delta)
        state.set(row.away, ra - delta)

    return state


def win_prob_1x2_elo(
    state: RatingState,
    home: str,
    away: str,
    draw_factor: float = 0.25,
) -> tuple[float, float, float]:
    """
    Elo-only 1X2 approximation. Used as a sanity check next to the goal model.
    draw_factor shifts mass from the favored side toward draw based on gap tightness.
    """
    rh = state.get(home)
    ra = state.get(away)
    p_home_vs_away = _expected_score(rh, ra, state.home_adv)
    # gap-based draw probability: larger gap -> smaller draw prob
    gap = abs((rh + state.home_adv) - ra)
    draw = max(0.05, draw_factor * math.exp(-gap / 400.0))
    # split home/away proportional to elo expectation, scaled by (1 - draw)
    home_p = p_home_vs_away * (1 - draw)
    away_p = (1 - p_home_vs_away) * (1 - draw)
    return home_p, draw, away_p


def expected_goals_for_match(
    state: RatingState,
    league: str,
    home: str,
    away: str,
    fallback_home: float,
    fallback_away: float,
) -> tuple[float, float]:
    """
    Translate Elo difference into expected goals (lambda_home, lambda_away).

    Approach: start from the league's average home/away goals, then nudge both
    teams' lambdas based on their rating gap relative to the league.
    """
    lg_home = state.league_home_goals.get(league, fallback_home)
    lg_away = state.league_away_goals.get(league, fallback_away)

    rh = state.get(home)
    ra = state.get(away)
    # gap in 100s of Elo points; each 100 ~= 0.18 goals shift (empirical, rough)
    gap = ((rh + state.home_adv) - ra) / 100.0
    shift = 0.18 * gap

    attack_home = state.attack(league, home)
    attack_away = state.attack(league, away)
    defense_home = state.defense(league, home)
    defense_away = state.defense(league, away)

    # Blend market-agnostic strength (Elo) with observed scoring profile.
    # Defense is signed so stronger defense lowers the opponent's lambda.
    lambda_home = lg_home + shift + 0.28 * attack_home - 0.22 * defense_away
    lambda_away = lg_away - shift + 0.28 * attack_away - 0.22 * defense_home
    lambda_home = min(4.5, max(0.15, lambda_home))
    lambda_away = min(4.5, max(0.15, lambda_away))
    return lambda_home, lambda_away


def ratings_table(state: RatingState) -> pd.DataFrame:
    return (
        pd.DataFrame(
            [{"team": t, "rating": r} for t, r in state.ratings.items()]
        )
        .sort_values("rating", ascending=False)
        .reset_index(drop=True)
    )
