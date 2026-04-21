"""
Basketball data fetchers.

NBA comes from ESPN's public scoreboard JSON. EuroLeague comes from the
EuroLeague live API XML endpoints. Both are cached under data/ so --offline
can still render from the most recent successful run.
"""

from __future__ import annotations

import json
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import requests


log = logging.getLogger(__name__)

ESPN_NBA_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
)
EUROLEAGUE_RESULTS = "https://api-live.euroleague.net/v1/results/"
EUROLEAGUE_SCHEDULE = "https://api-live.euroleague.net/v1/schedules"


def _is_fresh(path: Path, cache_hours: float) -> bool:
    if not path.exists():
        return False
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < cache_hours


def _download_json(url: str, params: dict[str, Any], timeout: int) -> dict | None:
    try:
        r = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={"User-Agent": "football-predictor/1.0"},
        )
        if r.status_code == 200:
            return r.json()
        log.warning("Non-200 for %s (status=%s)", r.url, r.status_code)
    except requests.RequestException as e:
        log.warning("Request failed %s: %s", url, e)
    except ValueError as e:
        log.warning("JSON parse failed %s: %s", url, e)
    return None


def _download_text(url: str, params: dict[str, Any], timeout: int) -> str | None:
    try:
        r = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={"User-Agent": "football-predictor/1.0"},
        )
        if r.status_code == 200 and r.text:
            return r.text
        log.warning("Non-200 or empty for %s (status=%s)", r.url, r.status_code)
    except requests.RequestException as e:
        log.warning("Request failed %s: %s", url, e)
    return None


def _cached_json(
    data_dir: Path,
    name: str,
    url: str,
    params: dict[str, Any],
    cache_hours: float,
    timeout: int,
) -> dict | None:
    path = data_dir / name
    if _is_fresh(path, cache_hours):
        log.info("cache hit %s", name)
    else:
        log.info("download %s", url)
        data = _download_json(url, params, timeout)
        if data is None:
            if path.exists():
                log.info("using stale cache for %s", name)
            else:
                return None
        else:
            path.write_text(json.dumps(data), encoding="utf-8")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        log.warning("failed to read %s: %s", name, e)
        return None


def _cached_text(
    data_dir: Path,
    name: str,
    url: str,
    params: dict[str, Any],
    cache_hours: float,
    timeout: int,
) -> str | None:
    path = data_dir / name
    if _is_fresh(path, cache_hours):
        log.info("cache hit %s", name)
    else:
        log.info("download %s", url)
        text = _download_text(url, params, timeout)
        if text is None:
            if path.exists():
                log.info("using stale cache for %s", name)
            else:
                return None
        else:
            path.write_text(text, encoding="utf-8")

    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log.warning("failed to read %s: %s", name, e)
        return None


def _parse_dt(value: str | None) -> pd.Timestamp | pd.NaT:
    if not value:
        return pd.NaT
    return pd.to_datetime(value, utc=True, errors="coerce").tz_convert(None)


def _parse_euro_date(date_value: str | None, time_value: str | None = None) -> pd.Timestamp | pd.NaT:
    if not date_value:
        return pd.NaT
    joined = f"{date_value} {time_value or '00:00'}"
    return pd.to_datetime(joined, errors="coerce")


def _float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace("+", "").replace("o", "").replace("u", ""))
    except ValueError:
        return None


def _american_to_decimal(value) -> float | None:
    if value is None:
        return None
    raw = str(value).strip().replace("−", "-")
    if not raw:
        return None
    try:
        odds = float(raw.replace("+", ""))
    except ValueError:
        return None
    if odds >= 100:
        return 1.0 + odds / 100.0
    if odds <= -100:
        return 1.0 + 100.0 / abs(odds)
    if odds > 1:
        return odds
    return None


def _nested(dct: dict, *keys: str):
    cur = dct
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _odds_from_competition(comp: dict) -> dict:
    odds_rows = comp.get("odds") or []
    if not odds_rows:
        return {}

    odds = odds_rows[0]
    moneyline = odds.get("moneyline") or {}
    spread = odds.get("pointSpread") or {}
    total = odds.get("total") or {}

    total_line = _float(odds.get("overUnder"))
    total_over_line = _float(_nested(total, "over", "close", "line"))
    total_under_line = _float(_nested(total, "under", "close", "line"))
    if total_line is None:
        total_line = total_over_line or total_under_line

    return {
        "odds_home": _american_to_decimal(_nested(moneyline, "home", "close", "odds")),
        "odds_away": _american_to_decimal(_nested(moneyline, "away", "close", "odds")),
        "spread_home": _float(_nested(spread, "home", "close", "line")),
        "spread_away": _float(_nested(spread, "away", "close", "line")),
        "odds_spread_home": _american_to_decimal(_nested(spread, "home", "close", "odds")),
        "odds_spread_away": _american_to_decimal(_nested(spread, "away", "close", "odds")),
        "total_line": total_line,
        "odds_over": _american_to_decimal(_nested(total, "over", "close", "odds")),
        "odds_under": _american_to_decimal(_nested(total, "under", "close", "odds")),
    }


def _parse_nba_scoreboard(data: dict) -> pd.DataFrame:
    rows = []
    for event in data.get("events", []):
        competitions = event.get("competitions") or []
        if not competitions:
            continue
        comp = competitions[0]
        competitors = comp.get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue

        status = comp.get("status") or event.get("status") or {}
        status_type = status.get("type") or {}
        completed = bool(status_type.get("completed"))

        home_team = home.get("team") or {}
        away_team = away.get("team") or {}
        row = {
            "event_id": event.get("id"),
            "date": _parse_dt(comp.get("date") or event.get("date")),
            "sport": "basketball",
            "league": "NBA",
            "home": home_team.get("displayName") or home_team.get("name"),
            "away": away_team.get("displayName") or away_team.get("name"),
            "home_score": pd.to_numeric(home.get("score"), errors="coerce") if completed else pd.NA,
            "away_score": pd.to_numeric(away.get("score"), errors="coerce") if completed else pd.NA,
            "completed": completed,
            "neutral_site": bool(comp.get("neutralSite")),
        }
        row.update(_odds_from_competition(comp))
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.dropna(subset=["date", "home", "away"])
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
    return df.drop_duplicates(subset=["event_id"]).sort_values("date").reset_index(drop=True)


def _fetch_nba_chunk(
    data_dir: Path,
    start: datetime,
    end: datetime,
    cache_hours: float,
    timeout: int,
    limit: int,
) -> pd.DataFrame:
    dates = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
    name = f"nba_scoreboard_{dates}_limit{limit}.json"
    data = _cached_json(
        data_dir,
        name,
        ESPN_NBA_SCOREBOARD,
        {"dates": dates, "limit": limit},
        cache_hours,
        timeout,
    )
    if data is None:
        return pd.DataFrame()
    return _parse_nba_scoreboard(data)


def fetch_nba(
    data_dir: Path,
    start: datetime,
    end: datetime,
    cache_hours: float,
    timeout: int,
    limit: int = 500,
    chunk_days: int = 35,
) -> pd.DataFrame:
    frames = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
        chunk = _fetch_nba_chunk(data_dir, cursor, chunk_end, cache_hours, timeout, limit)
        if not chunk.empty:
            frames.append(chunk)
        cursor = chunk_end + timedelta(days=1)

    if not frames:
        return pd.DataFrame()
    return (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset=["event_id"])
        .sort_values("date")
        .reset_index(drop=True)
    )


def _xml_items(text: str, parent: str, child: str) -> list[dict[str, str]]:
    root = ET.fromstring(text)
    if root.tag != parent:
        return []
    rows = []
    for elem in root.findall(child):
        rows.append({item.tag: item.text for item in elem})
    return rows


def _normalize_euro_results(text: str) -> pd.DataFrame:
    rows = []
    for item in _xml_items(text, "results", "game"):
        if str(item.get("played")).lower() != "true":
            continue
        rows.append({
            "event_id": item.get("gamecode") or item.get("gamenumber"),
            "date": _parse_euro_date(item.get("date"), item.get("time")),
            "sport": "basketball",
            "league": "EuroLeague",
            "home": item.get("hometeam"),
            "away": item.get("awayteam"),
            "home_score": pd.to_numeric(item.get("homescore"), errors="coerce"),
            "away_score": pd.to_numeric(item.get("awayscore"), errors="coerce"),
            "completed": True,
            "neutral_site": False,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.dropna(subset=["date", "home", "away", "home_score", "away_score"]).sort_values("date").reset_index(drop=True)


def _normalize_euro_schedule(text: str) -> pd.DataFrame:
    rows = []
    for item in _xml_items(text, "schedule", "item"):
        played = str(item.get("played")).lower() == "true"
        rows.append({
            "event_id": item.get("gamecode") or item.get("game"),
            "date": _parse_euro_date(item.get("date"), item.get("startime")),
            "sport": "basketball",
            "league": "EuroLeague",
            "home": item.get("hometeam"),
            "away": item.get("awayteam"),
            "home_score": pd.NA,
            "away_score": pd.NA,
            "completed": played,
            "neutral_site": False,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.dropna(subset=["date", "home", "away"]).sort_values("date").reset_index(drop=True)


def fetch_euroleague(
    data_dir: Path,
    season_start_year: int,
    cache_hours: float,
    timeout: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    season_code = f"E{season_start_year}"
    results_text = _cached_text(
        data_dir,
        f"euroleague_results_{season_code}.xml",
        EUROLEAGUE_RESULTS,
        {"seasonCode": season_code},
        cache_hours,
        timeout,
    )
    schedule_text = _cached_text(
        data_dir,
        f"euroleague_schedule_{season_code}.xml",
        EUROLEAGUE_SCHEDULE,
        {"seasonCode": season_code},
        cache_hours,
        timeout,
    )

    history = _normalize_euro_results(results_text) if results_text else pd.DataFrame()
    schedule = _normalize_euro_schedule(schedule_text) if schedule_text else pd.DataFrame()
    return history, schedule


def _default_euro_season_start(now: datetime) -> int:
    return now.year if now.month >= 7 else now.year - 1


def fetch_all(cfg: dict, data_dir: Path, now: datetime | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    bcfg = cfg.get("basketball", {})
    if not bcfg.get("enabled", False):
        return pd.DataFrame(), pd.DataFrame()

    now = now or datetime.now()
    lookahead_days = int(cfg.get("lookahead_days", 3))
    history_days = int(bcfg.get("history_days", 180))
    nba_limit = int(bcfg.get("nba_limit", 500))
    nba_chunk_days = int(bcfg.get("nba_chunk_days", 35))
    cache_hours = float(bcfg.get("cache_hours", cfg["http"]["cache_hours"]))
    timeout = int(cfg["http"]["timeout_seconds"])

    start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=history_days)
    end = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=lookahead_days + 1)

    history_frames = []
    upcoming_frames = []

    leagues = {str(l).upper() for l in bcfg.get("leagues", [])}
    if "NBA" in leagues:
        nba = fetch_nba(
            data_dir,
            start,
            end,
            cache_hours,
            timeout,
            limit=nba_limit,
            chunk_days=nba_chunk_days,
        )
        if not nba.empty:
            history_frames.append(nba[nba["completed"]].copy())
            upcoming_frames.append(nba[~nba["completed"]].copy())

    if "EUROLEAGUE" in leagues:
        season_start = int(bcfg.get("euroleague_season_start_year") or _default_euro_season_start(now))
        euro_history, euro_schedule = fetch_euroleague(data_dir, season_start, cache_hours, timeout)
        if not euro_history.empty:
            euro_history = euro_history[euro_history["date"] >= start].copy()
            history_frames.append(euro_history)
        if not euro_schedule.empty:
            euro_upcoming = euro_schedule[
                (~euro_schedule["completed"])
                & (euro_schedule["date"] >= now.replace(hour=0, minute=0, second=0, microsecond=0))
                & (euro_schedule["date"] < end)
            ].copy()
            upcoming_frames.append(euro_upcoming)

    history = pd.concat(history_frames, ignore_index=True) if history_frames else pd.DataFrame()
    upcoming = pd.concat(upcoming_frames, ignore_index=True) if upcoming_frames else pd.DataFrame()

    if not history.empty:
        history = history.sort_values("date").reset_index(drop=True)
    if not upcoming.empty:
        upcoming = upcoming.sort_values(["date", "league", "home"]).reset_index(drop=True)

    return history, upcoming
