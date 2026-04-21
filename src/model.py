"""
Dixon-Coles scoreline model.

Build a joint probability matrix over (home_goals, away_goals) for each match
using independent Poissons with lambdas from the Elo model, then apply the
Dixon-Coles low-score correction that improves 0-0 / 1-1 / 1-0 / 0-1 cells.

From the joint matrix we derive:
  - 1X2 (home/draw/away)
  - Over/Under 2.5
  - BTTS (both teams to score)
  - Top scorelines
  - Expected goals (already know the input lambdas)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import poisson

MAX_GOALS = 10  # 11x11 matrix is plenty; tails are negligible


def _dixon_coles_tau(home_goals: int, away_goals: int, lam: float, mu: float, rho: float) -> float:
    """
    DC correction factor applied to the (0,0), (0,1), (1,0), (1,1) cells only.
    Everywhere else it returns 1.0.
    """
    if home_goals == 0 and away_goals == 0:
        return 1 - lam * mu * rho
    if home_goals == 0 and away_goals == 1:
        return 1 + lam * rho
    if home_goals == 1 and away_goals == 0:
        return 1 + mu * rho
    if home_goals == 1 and away_goals == 1:
        return 1 - rho
    return 1.0


def scoreline_matrix(lam_home: float, lam_away: float, rho: float) -> np.ndarray:
    """Return P[h, a] with Dixon-Coles correction applied and renormalized."""
    h = np.arange(MAX_GOALS + 1)
    a = np.arange(MAX_GOALS + 1)
    ph = poisson.pmf(h, lam_home)
    pa = poisson.pmf(a, lam_away)
    mat = np.outer(ph, pa)

    # Apply DC correction to the four low-score cells
    for i in range(2):
        for j in range(2):
            mat[i, j] *= _dixon_coles_tau(i, j, lam_home, lam_away, rho)

    # Renormalize (DC and tail truncation both perturb the mass slightly)
    s = mat.sum()
    if s > 0:
        mat = mat / s
    return mat


def derive_markets(mat: np.ndarray) -> dict[str, float]:
    """Pull 1X2, O/U 2.5, BTTS from the scoreline matrix."""
    n = mat.shape[0]
    idx_h, idx_a = np.indices(mat.shape)

    p_home = float(mat[idx_h > idx_a].sum())
    p_draw = float(np.trace(mat))
    p_away = float(mat[idx_h < idx_a].sum())

    total_goals = idx_h + idx_a
    p_over25 = float(mat[total_goals > 2.5].sum())
    p_under25 = float(mat[total_goals < 2.5].sum())

    p_btts = float(mat[(idx_h > 0) & (idx_a > 0)].sum())
    p_btts_no = 1.0 - p_btts

    return {
        "p_home": p_home,
        "p_draw": p_draw,
        "p_away": p_away,
        "p_over25": p_over25,
        "p_under25": p_under25,
        "p_btts": p_btts,
        "p_btts_no": p_btts_no,
    }


def top_scorelines(mat: np.ndarray, n: int = 5) -> list[tuple[str, float]]:
    flat = []
    for h in range(mat.shape[0]):
        for a in range(mat.shape[1]):
            flat.append((f"{h}-{a}", float(mat[h, a])))
    flat.sort(key=lambda x: x[1], reverse=True)
    return flat[:n]


def predict_match(lam_home: float, lam_away: float, rho: float) -> dict:
    mat = scoreline_matrix(lam_home, lam_away, rho)
    markets = derive_markets(mat)
    return {
        "lambda_home": lam_home,
        "lambda_away": lam_away,
        **markets,
        "top_scores": top_scorelines(mat, n=5),
    }


def predict_fixtures(
    fixtures: pd.DataFrame,
    state,
    goals_cfg: dict,
) -> pd.DataFrame:
    """
    Run predict_match over a fixtures dataframe. Returns a dataframe with one
    row per fixture, enriched with probabilities for every market.
    """
    from .ratings import expected_goals_for_match  # local import to avoid cycle

    rho = float(goals_cfg["dixon_coles_rho"])
    fallback_h = float(goals_cfg["league_avg_home"])
    fallback_a = float(goals_cfg["league_avg_away"])

    rows = []
    for row in fixtures.itertuples(index=False):
        lam_h, lam_a = expected_goals_for_match(
            state, row.league, row.home, row.away, fallback_h, fallback_a
        )
        pred = predict_match(lam_h, lam_a, rho)
        top1, top2, top3 = (pred["top_scores"] + [("", 0.0)] * 3)[:3]
        rows.append({
            "fixture_id": f"football_{row.league}_{row.home}_{row.away}_{pd.to_datetime(row.date).date() if pd.notna(row.date) else ''}",
            "date": getattr(row, "date", None),
            "sport": "football",
            "league": row.league,
            "home": row.home,
            "away": row.away,
            "lambda_home": round(pred["lambda_home"], 3),
            "lambda_away": round(pred["lambda_away"], 3),
            "p_home": pred["p_home"],
            "p_draw": pred["p_draw"],
            "p_away": pred["p_away"],
            "p_over25": pred["p_over25"],
            "p_under25": pred["p_under25"],
            "p_btts": pred["p_btts"],
            "p_btts_no": pred["p_btts_no"],
            "top1_score": top1[0], "top1_prob": top1[1],
            "top2_score": top2[0], "top2_prob": top2[1],
            "top3_score": top3[0], "top3_prob": top3[1],
            # carry market odds through if present
            "odds_home": getattr(row, "odds_home", None),
            "odds_draw": getattr(row, "odds_draw", None),
            "odds_away": getattr(row, "odds_away", None),
            "odds_over25": getattr(row, "odds_over25", None),
            "odds_under25": getattr(row, "odds_under25", None),
        })

    return pd.DataFrame(rows)
