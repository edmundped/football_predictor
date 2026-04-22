"""
Prediction history and post-match accuracy scoring.

The public report is regenerated on each run, so we keep a small private CSV in
data/ that remembers the latest prediction made for each fixture. Later runs
join that history to completed scores from the normal football/basketball
fetchers and publish only the aggregate accuracy summary.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:  # noqa: BLE001 - corrupt local cache should not kill report generation
        return pd.DataFrame()


def _fixture_date(value) -> str:
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return ""
    return str(dt.date())


def _football_fixture_id(row) -> str:
    return f"football_{row['league']}_{row['home']}_{row['away']}_{_fixture_date(row['date'])}"


def _basketball_fixture_id(row) -> str:
    existing = row.get("event_id")
    if existing is not None and pd.notna(existing):
        return str(existing)
    return f"basketball_{row['league']}_{row['home']}_{row['away']}_{_fixture_date(row['date'])}"


def _with_prediction_run(df: pd.DataFrame, run_ts: datetime) -> pd.DataFrame:
    out = df.copy()
    out["prediction_run_ts"] = run_ts.isoformat(timespec="seconds")
    return out


def seed_from_previous_predictions(store_path: Path, previous_predictions_path: Path) -> None:
    """
    Bootstrap the private history from the currently published predictions file
    once. This lets a newly added accuracy tracker score the last generated
    slate without requiring a second day of data first.
    """
    if store_path.exists() or not previous_predictions_path.exists():
        return
    previous = _read_csv(previous_predictions_path)
    if previous.empty or "fixture_id" not in previous.columns:
        return
    mtime = datetime.fromtimestamp(previous_predictions_path.stat().st_mtime)
    previous = _with_prediction_run(previous, mtime)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    previous.to_csv(store_path, index=False)


def update_prediction_history(store_path: Path, predictions: pd.DataFrame, run_ts: datetime) -> pd.DataFrame:
    existing = _read_csv(store_path)
    current = _with_prediction_run(predictions, run_ts) if not predictions.empty else pd.DataFrame()

    frames = [df for df in (existing, current) if not df.empty]
    if not frames:
        return pd.DataFrame()

    history = pd.concat(frames, ignore_index=True, sort=False)
    if "fixture_id" not in history.columns:
        return pd.DataFrame()

    history = history.dropna(subset=["fixture_id"]).copy()
    history["fixture_id"] = history["fixture_id"].astype(str)
    history["_run_sort"] = pd.to_datetime(history["prediction_run_ts"], errors="coerce")
    history = (
        history.sort_values(["fixture_id", "_run_sort"])
        .drop_duplicates(subset=["fixture_id"], keep="last")
        .drop(columns=["_run_sort"])
        .reset_index(drop=True)
    )

    store_path.parent.mkdir(parents=True, exist_ok=True)
    history.to_csv(store_path, index=False)
    return history


def actual_results(football_history: pd.DataFrame, basketball_history: pd.DataFrame) -> pd.DataFrame:
    frames = []

    if not football_history.empty:
        required = ["date", "league", "home", "away", "home_goals", "away_goals"]
        if all(col in football_history.columns for col in required):
            football = football_history.dropna(subset=required).copy()
            football["fixture_id"] = football.apply(_football_fixture_id, axis=1)
            football["sport"] = "football"
            football["actual_home_score"] = pd.to_numeric(football["home_goals"], errors="coerce")
            football["actual_away_score"] = pd.to_numeric(football["away_goals"], errors="coerce")
            frames.append(football[[
                "fixture_id", "date", "sport", "league", "home", "away",
                "actual_home_score", "actual_away_score",
            ]])

    if not basketball_history.empty:
        required = ["date", "league", "home", "away", "home_score", "away_score"]
        if all(col in basketball_history.columns for col in required):
            basketball = basketball_history.dropna(subset=required).copy()
            basketball["fixture_id"] = basketball.apply(_basketball_fixture_id, axis=1)
            basketball["sport"] = "basketball"
            basketball["actual_home_score"] = pd.to_numeric(basketball["home_score"], errors="coerce")
            basketball["actual_away_score"] = pd.to_numeric(basketball["away_score"], errors="coerce")
            frames.append(basketball[[
                "fixture_id", "date", "sport", "league", "home", "away",
                "actual_home_score", "actual_away_score",
            ]])

    if not frames:
        return pd.DataFrame()
    return (
        pd.concat(frames, ignore_index=True)
        .dropna(subset=["fixture_id", "actual_home_score", "actual_away_score"])
        .drop_duplicates(subset=["fixture_id"], keep="last")
        .reset_index(drop=True)
    )


def _num(value):
    value = pd.to_numeric(value, errors="coerce")
    if pd.isna(value):
        return None
    return float(value)


def _best(candidates: list[tuple[str, str, float | None]]) -> tuple[str | None, str | None, float | None]:
    clean = [(code, label, prob) for code, label, prob in candidates if prob is not None]
    if not clean:
        return None, None, None
    return max(clean, key=lambda item: item[2])


def _score_row(row) -> dict:
    sport = str(row.get("sport", "")).lower()
    home = str(row.get("home", "Home"))
    away = str(row.get("away", "Away"))
    home_score = int(row["actual_home_score"])
    away_score = int(row["actual_away_score"])
    total_score = home_score + away_score

    item = {
        "date": row.get("date_actual") if pd.notna(row.get("date_actual")) else row.get("date"),
        "sport": sport,
        "league": row.get("league_actual") if pd.notna(row.get("league_actual")) else row.get("league"),
        "home": home,
        "away": away,
        "score": f"{home_score}-{away_score}",
        "prediction_run_ts": row.get("prediction_run_ts"),
    }

    if sport == "football":
        pred_code, pred_label, pred_prob = _best([
            ("H", f"{home} win", _num(row.get("p_home"))),
            ("D", "Draw", _num(row.get("p_draw"))),
            ("A", f"{away} win", _num(row.get("p_away"))),
        ])
        actual_code = "H" if home_score > away_score else ("A" if away_score > home_score else "D")
        actual_label = f"{home} win" if actual_code == "H" else (f"{away} win" if actual_code == "A" else "Draw")
        item.update({
            "main_pick": pred_label,
            "main_prob": pred_prob,
            "main_result": actual_label,
            "main_correct": pred_code == actual_code if pred_code else None,
        })

        over_prob = _num(row.get("p_over25"))
        under_prob = _num(row.get("p_under25"))
        if over_prob is not None and under_prob is not None:
            pred_over = over_prob >= under_prob
            actual_over = total_score > 2.5
            item["total_pick"] = "Over 2.5" if pred_over else "Under 2.5"
            item["total_correct"] = pred_over == actual_over

        btts_prob = _num(row.get("p_btts"))
        btts_no_prob = _num(row.get("p_btts_no"))
        if btts_prob is not None and btts_no_prob is not None:
            pred_btts = btts_prob >= btts_no_prob
            actual_btts = home_score > 0 and away_score > 0
            item["btts_pick"] = "BTTS Yes" if pred_btts else "BTTS No"
            item["btts_correct"] = pred_btts == actual_btts

        top_score = row.get("top1_score")
        if top_score is not None and pd.notna(top_score):
            item["scoreline_pick"] = str(top_score)
            item["scoreline_correct"] = str(top_score) == item["score"]

    elif sport == "basketball":
        pred_code, pred_label, pred_prob = _best([
            ("H", f"{home} ML", _num(row.get("p_home"))),
            ("A", f"{away} ML", _num(row.get("p_away"))),
        ])
        actual_code = "H" if home_score > away_score else "A"
        actual_label = f"{home} ML" if actual_code == "H" else f"{away} ML"
        item.update({
            "main_pick": pred_label,
            "main_prob": pred_prob,
            "main_result": actual_label,
            "main_correct": pred_code == actual_code if pred_code else None,
        })

        total_line = _num(row.get("total_line"))
        over_prob = _num(row.get("p_over_total"))
        under_prob = _num(row.get("p_under_total"))
        if total_line is not None and over_prob is not None and under_prob is not None:
            pred_over = over_prob >= under_prob
            if total_score != total_line:
                actual_over = total_score > total_line
                item["total_pick"] = f"{'Over' if pred_over else 'Under'} {total_line:g}"
                item["total_correct"] = pred_over == actual_over

        home_line = _num(row.get("spread_home"))
        away_line = _num(row.get("spread_away"))
        if home_line is None and away_line is not None:
            home_line = -away_line
        home_cover_prob = _num(row.get("p_home_cover"))
        away_cover_prob = _num(row.get("p_away_cover"))
        if home_line is not None and home_cover_prob is not None and away_cover_prob is not None:
            pred_home_cover = home_cover_prob >= away_cover_prob
            margin_with_line = home_score + home_line - away_score
            if margin_with_line != 0:
                actual_home_cover = margin_with_line > 0
                item["spread_pick"] = f"{home if pred_home_cover else away} spread"
                item["spread_correct"] = pred_home_cover == actual_home_cover

    return item


def scored_predictions(prediction_history: pd.DataFrame, actuals: pd.DataFrame) -> pd.DataFrame:
    if prediction_history.empty or actuals.empty or "fixture_id" not in prediction_history.columns:
        return pd.DataFrame()

    preds = prediction_history.copy()
    preds["fixture_id"] = preds["fixture_id"].astype(str)
    actuals = actuals.copy()
    actuals["fixture_id"] = actuals["fixture_id"].astype(str)
    merged = preds.merge(actuals, on="fixture_id", how="inner", suffixes=("", "_actual"))
    if merged.empty:
        return pd.DataFrame()

    rows = [_score_row(row) for _, row in merged.iterrows()]
    scored = pd.DataFrame(rows)
    if scored.empty:
        return scored
    scored["date"] = pd.to_datetime(scored["date"], errors="coerce")
    return scored.sort_values("date", ascending=False).reset_index(drop=True)


def _metric(series: pd.Series) -> dict:
    clean = series.dropna()
    total = int(len(clean))
    correct = int(clean.astype(bool).sum()) if total else 0
    accuracy = (correct / total * 100.0) if total else None
    return {"correct": correct, "total": total, "accuracy": accuracy}


def summarize(scored: pd.DataFrame) -> dict:
    if scored.empty:
        return {
            "completed_predictions": 0,
            "main": _metric(pd.Series(dtype=object)),
            "football_main": _metric(pd.Series(dtype=object)),
            "basketball_main": _metric(pd.Series(dtype=object)),
            "football_totals": _metric(pd.Series(dtype=object)),
            "football_btts": _metric(pd.Series(dtype=object)),
            "basketball_spread": _metric(pd.Series(dtype=object)),
            "basketball_totals": _metric(pd.Series(dtype=object)),
            "scorelines": _metric(pd.Series(dtype=object)),
        }

    football = scored[scored["sport"] == "football"]
    basketball = scored[scored["sport"] == "basketball"]
    return {
        "completed_predictions": int(len(scored)),
        "main": _metric(scored["main_correct"]),
        "football_main": _metric(football["main_correct"] if "main_correct" in football else pd.Series(dtype=object)),
        "basketball_main": _metric(basketball["main_correct"] if "main_correct" in basketball else pd.Series(dtype=object)),
        "football_totals": _metric(football["total_correct"] if "total_correct" in football else pd.Series(dtype=object)),
        "football_btts": _metric(football["btts_correct"] if "btts_correct" in football else pd.Series(dtype=object)),
        "basketball_spread": _metric(basketball["spread_correct"] if "spread_correct" in basketball else pd.Series(dtype=object)),
        "basketball_totals": _metric(basketball["total_correct"] if "total_correct" in basketball else pd.Series(dtype=object)),
        "scorelines": _metric(football["scoreline_correct"] if "scoreline_correct" in football else pd.Series(dtype=object)),
    }


def update(
    *,
    store_path: Path,
    previous_predictions_path: Path,
    current_predictions: pd.DataFrame,
    run_ts: datetime,
    football_history: pd.DataFrame,
    basketball_history: pd.DataFrame,
) -> dict:
    seed_from_previous_predictions(store_path, previous_predictions_path)
    prediction_history = update_prediction_history(store_path, current_predictions, run_ts)
    actuals = actual_results(football_history, basketball_history)
    scored = scored_predictions(prediction_history, actuals)
    return {
        "summary": summarize(scored),
        "rows": scored.head(120).to_dict("records") if not scored.empty else [],
        "store_path": str(store_path),
    }
