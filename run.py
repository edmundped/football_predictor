"""
Football predictor — single entry point.

Usage:
    python run.py
    python run.py --lookahead 5
    python run.py --offline          # use cached CSVs only
    python run.py --config config.yaml

Outputs, overwritten on every run:
    outputs/output.html
    outputs/predictions.csv
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src import (  # noqa: E402
    basketball_fetcher,
    basketball_model,
    fetcher,
    model,
    ratings as rating_mod,
    report,
    slip_builder,
)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        datefmt="%H:%M:%S",
    )


def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def filter_upcoming(
    upcoming: pd.DataFrame,
    lookahead_days: int,
    now: datetime | None = None,
) -> pd.DataFrame:
    if upcoming.empty:
        return upcoming
    now = now or datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=lookahead_days + 1)
    mask = (upcoming["date"] >= start) & (upcoming["date"] < end)
    return upcoming[mask].sort_values(["date", "league", "home"]).reset_index(drop=True)


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config.yaml"))
    parser.add_argument("--lookahead", type=int, default=None,
                        help="override lookahead_days from config")
    parser.add_argument("--offline", action="store_true",
                        help="never hit the network; rely on cached CSVs")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    if args.lookahead is not None:
        cfg["lookahead_days"] = args.lookahead
    if args.offline:
        cfg["http"]["cache_hours"] = 10 ** 9  # effectively infinite
        if "basketball" in cfg:
            cfg["basketball"]["cache_hours"] = 10 ** 9

    data_dir = ROOT / cfg["paths"]["data_dir"]
    out_dir = ROOT / cfg["paths"]["output_dir"]
    data_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    log = logging.getLogger("run")
    run_ts = datetime.now()

    log.info("fetching data (leagues=%s, history_seasons=%d)",
             cfg["leagues"], cfg["history_seasons"])
    history, upcoming = fetcher.fetch_all(cfg, data_dir)

    if history.empty:
        log.error("No historical data available. Check connectivity or cache.")
        return 1

    log.info("history rows=%d, upcoming rows=%d", len(history), len(upcoming))

    log.info("fitting Elo ratings on %d matches", len(history))
    state = rating_mod.fit(history, cfg["elo"])
    window = filter_upcoming(upcoming, cfg["lookahead_days"])
    if window.empty:
        log.warning("No fixtures in the next %d days.", cfg["lookahead_days"])
    else:
        log.info("predicting %d fixtures in next %d days", len(window), cfg["lookahead_days"])

    predictions = model.predict_fixtures(window, state, cfg["goals"])

    basketball_predictions = pd.DataFrame()
    if cfg.get("basketball", {}).get("enabled", False):
        log.info("fetching basketball data (leagues=%s)", cfg["basketball"].get("leagues", []))
        basketball_history, basketball_upcoming = basketball_fetcher.fetch_all(cfg, data_dir, now=run_ts)
        log.info(
            "basketball history rows=%d, upcoming rows=%d",
            len(basketball_history),
            len(basketball_upcoming),
        )
        if basketball_history.empty:
            log.warning("No basketball historical data available. Basketball tab will be empty.")
        else:
            log.info("fitting basketball ratings on %d games", len(basketball_history))
            basketball_state = basketball_model.fit(basketball_history, cfg["basketball"]["elo"])
            basketball_window = filter_upcoming(basketball_upcoming, cfg["lookahead_days"], now=run_ts)
            if basketball_window.empty:
                log.warning("No basketball fixtures in the next %d days.", cfg["lookahead_days"])
            else:
                log.info(
                    "predicting %d basketball fixtures in next %d days",
                    len(basketball_window),
                    cfg["lookahead_days"],
                )
            basketball_predictions = basketball_model.predict_fixtures(
                basketball_window,
                basketball_state,
                cfg["basketball"]["model"],
            )

    prediction_frames = [
        df.dropna(axis=1, how="all")
        for df in [predictions, basketball_predictions]
        if not df.empty
    ]
    all_predictions = pd.concat(
        prediction_frames,
        ignore_index=True,
        sort=False,
    ) if prediction_frames else pd.DataFrame()

    log.info("building consolidated slip variants")
    slips = slip_builder.build_slips(all_predictions, cfg["slip"])

    # write stable artifacts, overwriting the prior run
    html_path = out_dir / "output.html"
    html_path.write_text(report.render(predictions, basketball_predictions, slips, run_ts), encoding="utf-8")

    predictions_path = out_dir / "predictions.csv"
    all_predictions.to_csv(predictions_path, index=False)

    log.info("done. report: %s", html_path)
    # sanity print to stdout
    print(f"\nReport:      {html_path}")
    print(f"Predictions: {predictions_path}")
    if slips:
        print("\nConsolidated slip summary:")
        for name, slip in slips.items():
            s = slip["stats"]
            ev = f"  EV={s['expected_value_per_unit']:+.3f}" if s["expected_value_per_unit"] is not None else ""
            print(f"  {name:11s} legs={s['legs']}  P={s['combined_prob']*100:5.2f}%  "
                  f"fair_odds={s['combined_fair_odds']:6.2f}{ev}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
