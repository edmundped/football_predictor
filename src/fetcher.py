"""
Data fetcher for football-data.co.uk.

Why this source:
- No API key, no auth, no rate limits (just polite HTTP).
- CSVs include results, upcoming fixtures, and historical bookmaker odds.
- Covers every major European league going back 10+ seasons.

URL shape:
  https://www.football-data.co.uk/mmz4281/{season}/{league}.csv
    e.g. mmz4281/2526/E0.csv    Premier League 2025-26 completed matches
  https://www.football-data.co.uk/fixtures.csv
    All upcoming fixtures across supported leagues with opening odds.
"""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path

import pandas as pd
import requests

BASE = "https://www.football-data.co.uk"
RESULTS_URL = BASE + "/mmz4281/{season}/{league}.csv"
FIXTURES_URL = BASE + "/fixtures.csv"

log = logging.getLogger(__name__)


def _prior_seasons(current: str, n: int) -> list[str]:
    """Given current season code like '2526', return N prior codes: ['2425', '2324', ...]."""
    start = int(current[:2])
    end = int(current[2:])
    out = []
    for i in range(1, n + 1):
        s = (start - i) % 100
        e = (end - i) % 100
        out.append(f"{s:02d}{e:02d}")
    return out


def _cache_path(data_dir: Path, name: str) -> Path:
    return data_dir / name


def _is_fresh(path: Path, cache_hours: float) -> bool:
    if not path.exists():
        return False
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < cache_hours


def _download(url: str, timeout: int) -> bytes | None:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "football-predictor/1.0"})
        if r.status_code == 200 and len(r.content) > 100:
            return r.content
        log.warning("Non-200 or empty for %s (status=%s, bytes=%d)", url, r.status_code, len(r.content))
    except requests.RequestException as e:
        log.warning("Request failed %s: %s", url, e)
    return None


def _read_csv_bytes(raw: bytes) -> pd.DataFrame:
    # football-data.co.uk sometimes ships latin-1; try utf-8 first.
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc, on_bad_lines="skip")
        except UnicodeDecodeError:
            continue
    # last resort
    return pd.read_csv(io.BytesIO(raw), encoding="latin-1", on_bad_lines="skip", engine="python")


def fetch_league_results(
    league: str,
    season: str,
    data_dir: Path,
    cache_hours: float,
    timeout: int,
) -> pd.DataFrame | None:
    """Fetch one league+season completed results CSV. Returns None if unavailable."""
    name = f"{league}_{season}.csv"
    path = _cache_path(data_dir, name)

    if _is_fresh(path, cache_hours):
        log.info("cache hit %s", name)
    else:
        url = RESULTS_URL.format(season=season, league=league)
        log.info("download %s", url)
        raw = _download(url, timeout)
        if raw is None:
            if path.exists():
                log.info("using stale cache for %s", name)
            else:
                return None
        else:
            path.write_bytes(raw)

    try:
        df = _read_csv_bytes(path.read_bytes())
    except Exception as e:  # noqa: BLE001
        log.warning("failed to parse %s: %s", name, e)
        return None

    return _normalize_results(df, league, season)


def fetch_upcoming_fixtures(
    data_dir: Path,
    cache_hours: float,
    timeout: int,
) -> pd.DataFrame | None:
    """Fetch the combined upcoming-fixtures CSV. Returns None if unavailable."""
    name = "fixtures.csv"
    path = _cache_path(data_dir, name)

    if _is_fresh(path, cache_hours):
        log.info("cache hit %s", name)
    else:
        log.info("download %s", FIXTURES_URL)
        raw = _download(FIXTURES_URL, timeout)
        if raw is None:
            if path.exists():
                log.info("using stale cache for %s", name)
            else:
                return None
        else:
            path.write_bytes(raw)

    try:
        df = _read_csv_bytes(path.read_bytes())
    except Exception as e:  # noqa: BLE001
        log.warning("failed to parse fixtures.csv: %s", e)
        return None

    return _normalize_fixtures(df)


def _parse_date(series: pd.Series) -> pd.Series:
    # football-data.co.uk uses DD/MM/YY or DD/MM/YYYY
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def _normalize_results(df: pd.DataFrame, league: str, season: str) -> pd.DataFrame:
    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
    missing = required - set(df.columns)
    if missing:
        log.warning("%s %s missing columns: %s", league, season, missing)
        return pd.DataFrame()

    df = df.copy()
    df["Date"] = _parse_date(df["Date"])
    df = df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    df["FTHG"] = pd.to_numeric(df["FTHG"], errors="coerce")
    df["FTAG"] = pd.to_numeric(df["FTAG"], errors="coerce")
    df = df.dropna(subset=["FTHG", "FTAG"])
    df["FTHG"] = df["FTHG"].astype(int)
    df["FTAG"] = df["FTAG"].astype(int)

    df["league"] = league
    df["season"] = season
    keep = ["Date", "league", "season", "HomeTeam", "AwayTeam", "FTHG", "FTAG"]
    # keep a few odds columns if present, for post-hoc calibration
    for col in ("B365H", "B365D", "B365A", "PSH", "PSD", "PSA", "B365>2.5", "B365<2.5"):
        if col in df.columns:
            keep.append(col)
    return df[keep].rename(columns={
        "Date": "date", "HomeTeam": "home", "AwayTeam": "away",
        "FTHG": "home_goals", "FTAG": "away_goals",
    })


def _normalize_fixtures(df: pd.DataFrame) -> pd.DataFrame:
    required = {"Div", "Date", "HomeTeam", "AwayTeam"}
    missing = required - set(df.columns)
    if missing:
        log.warning("fixtures.csv missing columns: %s", missing)
        return pd.DataFrame()

    df = df.copy()
    df["date"] = _parse_date(df["Date"])
    df = df.dropna(subset=["date", "HomeTeam", "AwayTeam"])

    out = pd.DataFrame({
        "date": df["date"],
        "league": df["Div"],
        "home": df["HomeTeam"],
        "away": df["AwayTeam"],
    })

    # Carry opening odds if available
    for src, dst in [
        ("B365H", "odds_home"), ("B365D", "odds_draw"), ("B365A", "odds_away"),
        ("PSH", "ps_home"), ("PSD", "ps_draw"), ("PSA", "ps_away"),
        ("B365>2.5", "odds_over25"), ("B365<2.5", "odds_under25"),
    ]:
        if src in df.columns:
            out[dst] = pd.to_numeric(df[src], errors="coerce")

    return out


def fetch_all(cfg: dict, data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch history for training and upcoming fixtures for prediction.
    Returns (history_df, upcoming_df).
    """
    seasons = [cfg["current_season"]] + _prior_seasons(cfg["current_season"], cfg["history_seasons"])
    leagues = cfg["leagues"]
    cache_hours = float(cfg["http"]["cache_hours"])
    timeout = int(cfg["http"]["timeout_seconds"])

    frames = []
    for league in leagues:
        for season in seasons:
            df = fetch_league_results(league, season, data_dir, cache_hours, timeout)
            if df is not None and not df.empty:
                frames.append(df)

    history = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not history.empty:
        history = history.sort_values("date").reset_index(drop=True)

    upcoming = fetch_upcoming_fixtures(data_dir, cache_hours, timeout)
    if upcoming is not None and not upcoming.empty:
        upcoming = upcoming[upcoming["league"].isin(leagues)].reset_index(drop=True)
    else:
        upcoming = pd.DataFrame()

    return history, upcoming
