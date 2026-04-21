"""
Bankroll tracker — reads/writes bankroll.json at the project root.

Schema
------
{
  "starting_capital": 100.0,
  "current_balance":  100.0,
  "bets": [
    {
      "id":             "a1b2c3d4",
      "date":           "2026-04-21",
      "slip_type":      "VALUE",
      "stake":          5.23,
      "combined_odds":  3.45,
      "outcome":        null,          // null | "WIN" | "LOSS" | "VOID"
      "payout":         null,
      "legs":           [...],
      "logged_at":      "2026-04-21T10:30:00"
    }
  ]
}
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from pathlib import Path

BANKROLL_FILE    = Path(__file__).resolve().parent.parent / "bankroll.json"
STARTING_CAPITAL = 100.0


# ── I/O helpers ──────────────────────────────────────────────────────────────

def _load() -> dict:
    if BANKROLL_FILE.exists():
        with open(BANKROLL_FILE) as f:
            return json.load(f)
    return {
        "starting_capital": STARTING_CAPITAL,
        "current_balance":  STARTING_CAPITAL,
        "bets": [],
    }


def _save(data: dict) -> None:
    with open(BANKROLL_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ── Public API ────────────────────────────────────────────────────────────────

def get_bankroll() -> dict:
    """Return the full bankroll JSON."""
    return _load()


def get_balance() -> float:
    return _load()["current_balance"]


def log_bet(
    slip_type: str,
    stake: float,
    combined_odds: float,
    legs: list[dict],
    bet_date: str | None = None,
) -> str:
    """
    Record a new pending bet. Returns the short bet ID (8 chars).
    Stake is deducted from balance immediately (funds are committed).
    """
    data    = _load()
    bet_id  = str(uuid.uuid4())[:8]
    bet_date = bet_date or date.today().isoformat()

    if data["current_balance"] < stake:
        raise ValueError(
            f"Insufficient balance: £{data['current_balance']:.2f} < stake £{stake:.2f}"
        )

    data["current_balance"] = round(data["current_balance"] - stake, 2)
    data["bets"].append({
        "id":           bet_id,
        "date":         bet_date,
        "slip_type":    slip_type,
        "stake":        round(stake, 2),
        "combined_odds": round(combined_odds, 3),
        "outcome":      None,
        "payout":       None,
        "legs":         legs,
        "logged_at":    datetime.now().isoformat(),
    })
    _save(data)
    return bet_id


def resolve_bet(
    bet_id: str,
    outcome: str,
    actual_payout: float | None = None,
) -> dict:
    """
    Mark a bet WIN / LOSS / VOID and adjust the balance accordingly.

    WIN  — adds payout to balance (stake was already deducted at log_bet time)
    LOSS — no further change (stake already gone)
    VOID — refunds the stake
    """
    outcome = outcome.strip().upper()
    if outcome not in ("WIN", "LOSS", "VOID"):
        raise ValueError("outcome must be WIN, LOSS, or VOID")

    data = _load()
    for bet in data["bets"]:
        if bet["id"] != bet_id:
            continue
        if bet["outcome"] is not None:
            raise ValueError(f"Bet {bet_id!r} already resolved as {bet['outcome']}")

        bet["outcome"] = outcome

        if outcome == "WIN":
            payout = (
                actual_payout
                if actual_payout is not None
                else round(bet["stake"] * bet["combined_odds"], 2)
            )
            bet["payout"] = round(payout, 2)
            data["current_balance"] = round(data["current_balance"] + payout, 2)

        elif outcome == "LOSS":
            bet["payout"] = 0.0
            # balance already reduced at placement; nothing more to do

        elif outcome == "VOID":
            bet["payout"] = bet["stake"]
            data["current_balance"] = round(data["current_balance"] + bet["stake"], 2)

        _save(data)
        return bet

    raise ValueError(f"Bet ID {bet_id!r} not found")


def summary() -> dict:
    """Compute headline P&L stats from the bet log."""
    data     = _load()
    bets     = data["bets"]
    resolved = [b for b in bets if b["outcome"] is not None]
    pending  = [b for b in bets if b["outcome"] is None]
    wins     = [b for b in resolved if b["outcome"] == "WIN"]
    losses   = [b for b in resolved if b["outcome"] == "LOSS"]

    total_staked   = sum(b["stake"] for b in resolved)
    total_returned = sum(b.get("payout") or 0.0 for b in resolved)
    net_profit     = total_returned - total_staked
    roi            = (net_profit / total_staked * 100) if total_staked > 0 else 0.0
    hit_rate       = (len(wins) / len(resolved) * 100) if resolved else 0.0
    balance_pct    = (data["current_balance"] / data["starting_capital"] - 1) * 100

    return {
        "starting_capital": data["starting_capital"],
        "current_balance":  data["current_balance"],
        "total_bets":       len(bets),
        "resolved_bets":    len(resolved),
        "pending_bets":     len(pending),
        "pending":          pending,
        "wins":             len(wins),
        "losses":           len(losses),
        "total_staked":     round(total_staked,   2),
        "total_returned":   round(total_returned, 2),
        "net_profit":       round(net_profit,      2),
        "roi_pct":          round(roi,             2),
        "hit_rate_pct":     round(hit_rate,        1),
        "balance_change_pct": round(balance_pct,  2),
        "recent_bets":      list(reversed(bets))[:20],
    }
