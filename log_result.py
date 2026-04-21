#!/usr/bin/env python3
"""
Result logger — mark today's bets WIN / LOSS / VOID and update the bankroll.

Usage examples
--------------
# Interactive mode — lists pending bets and prompts for each:
    python log_result.py

# Direct mode — resolve a specific bet by ID:
    python log_result.py --id a1b2c3d4 --outcome WIN
    python log_result.py --id a1b2c3d4 --outcome LOSS
    python log_result.py --id a1b2c3d4 --outcome VOID

# Log a new bet manually (if you placed one outside run.py):
    python log_result.py --log --slip VALUE --stake 4.50 --odds 3.20

# Print bankroll summary:
    python log_result.py --summary
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.tracker import get_bankroll, log_bet, resolve_bet, summary


# ── ANSI colours (degrade gracefully on Windows) ─────────────────────────────
try:
    import os
    _colour = os.name != "nt" or "WT_SESSION" in os.environ
except Exception:
    _colour = False

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _colour else text

GREEN  = lambda t: _c("32;1", t)
RED    = lambda t: _c("31;1", t)
YELLOW = lambda t: _c("33;1", t)
CYAN   = lambda t: _c("36;1", t)
BOLD   = lambda t: _c("1", t)
DIM    = lambda t: _c("2", t)


# ── Helpers ───────────────────────────────────────────────────────────────────

CURRENCY = "GHS"

def _money(amount: float) -> str:
    value = float(amount)
    sign = "-" if value < 0 else ""
    return f"{sign}{CURRENCY} {abs(value):,.2f}"

def _print_summary() -> None:
    s = summary()
    balance_colour = GREEN if s["net_profit"] >= 0 else RED
    balance_text = _money(s["current_balance"])
    profit_prefix = "+" if s["net_profit"] >= 0 else ""
    profit_text = f"{profit_prefix}{_money(s['net_profit'])}"
    roi_text = f"{s['roi_pct']:+.2f}%"
    print()
    print(BOLD("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"))
    print(BOLD("  BANKROLL SUMMARY"))
    print(BOLD("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"))
    print(f"  Starting capital : {_money(s['starting_capital'])}")
    print(f"  Current balance  : {balance_colour(balance_text)}")
    print(f"  Net profit       : {balance_colour(profit_text)}")
    print(f"  ROI              : {balance_colour(roi_text)}")
    print(f"  Hit rate         : {s['hit_rate_pct']:.1f}%")
    print(f"  Bets resolved    : {s['resolved_bets']}  (W:{s['wins']} L:{s['losses']})")
    print(f"  Bets pending     : {YELLOW(str(s['pending_bets']))}")
    print(BOLD("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"))
    print()

    goal = 1_000_000.0
    start = s["starting_capital"]
    current = s["current_balance"]
    import math
    try:
        pct = math.log(current / start) / math.log(goal / start) * 100
        pct = max(0.0, min(100.0, pct))
    except Exception:
        pct = 0.0
    bar_len = 40
    filled  = int(bar_len * pct / 100)
    bar     = "█" * filled + "░" * (bar_len - filled)
    print(f"  Goal  {_money(start)} -> {_money(goal)}")
    print(f"  [{GREEN(bar)}] {pct:.2f}%")
    print()


def _print_pending() -> list[dict]:
    s = summary()
    pending = s["pending"]
    if not pending:
        print(DIM("  No pending bets."))
    else:
        print(f"\n  {BOLD('PENDING BETS')}\n")
        for b in pending:
            legs_str = ", ".join(
                f"{lg.get('pick')} ({lg.get('match')})"
                for lg in (b.get("legs") or [])
            )
            print(f"  {CYAN(b['id'])}  {b['date']}  {BOLD(b['slip_type'])}  "
                  f"stake={_money(b['stake'])}  odds={b['combined_odds']:.2f}")
            if legs_str:
                print(f"           {DIM(legs_str)}")
    return pending


def _interactive() -> None:
    _print_summary()
    pending = _print_pending()
    if not pending:
        return

    print()
    for bet in pending:
        print(f"  Resolve {CYAN(bet['id'])} — {bet['slip_type']} ({bet['date']})?")
        choice = input("    [W]in / [L]oss / [V]oid / [S]kip  > ").strip().lower()
        if choice.startswith("w"):
            resolved = resolve_bet(bet["id"], "WIN")
            payout   = resolved["payout"]
            bal      = get_bankroll()["current_balance"]
            print(GREEN(f"    ✓ WIN  — payout {_money(payout)}  |  balance now {_money(bal)}"))
        elif choice.startswith("l"):
            resolve_bet(bet["id"], "LOSS")
            bal = get_bankroll()["current_balance"]
            print(RED(f"    ✗ LOSS — balance now {_money(bal)}"))
        elif choice.startswith("v"):
            resolve_bet(bet["id"], "VOID")
            bal = get_bankroll()["current_balance"]
            print(YELLOW(f"    ↩ VOID — stake refunded  |  balance now {_money(bal)}"))
        else:
            print(DIM("    Skipped."))
        print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Log results and track bankroll for football_predictor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--id",      help="Bet ID to resolve (8 chars)")
    parser.add_argument("--outcome", choices=["WIN","LOSS","VOID"],
                        help="Result of the bet")
    parser.add_argument("--payout",  type=float, default=None,
                        help="Actual payout if different from stake × odds")
    parser.add_argument("--log",     action="store_true",
                        help="Log a new bet manually")
    parser.add_argument("--slip",    default="MANUAL",
                        help="Slip type for --log (default MANUAL)")
    parser.add_argument("--stake",   type=float,
                        help="Stake amount for --log")
    parser.add_argument("--odds",    type=float,
                        help="Combined decimal odds for --log")
    parser.add_argument("--summary", action="store_true",
                        help="Print bankroll summary and exit")
    args = parser.parse_args()

    if args.summary:
        _print_summary()
        return 0

    if args.log:
        if args.stake is None or args.odds is None:
            print(RED("Error: --log requires --stake and --odds"))
            return 1
        bet_id = log_bet(
            slip_type    = args.slip,
            stake        = args.stake,
            combined_odds= args.odds,
            legs         = [],
        )
        print(GREEN(f"Bet logged. ID: {bet_id}"))
        _print_summary()
        return 0

    if args.id and args.outcome:
        resolved = resolve_bet(args.id, args.outcome, args.payout)
        bal      = get_bankroll()["current_balance"]
        outcome_colour = GREEN if args.outcome == "WIN" else (RED if args.outcome == "LOSS" else YELLOW)
        print(outcome_colour(f"  {args.outcome}  — bet {args.id}"))
        if resolved.get("payout"):
            print(f"  Payout: {_money(resolved['payout'])}")
        print(f"  Balance now: {_money(bal)}")
        return 0

    # default: interactive mode
    _interactive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
