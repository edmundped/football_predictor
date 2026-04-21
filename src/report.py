"""
Self-contained HTML report. No external CSS/JS; opens anywhere.
"""

from __future__ import annotations

import html
from datetime import datetime

import pandas as pd


CSS = """
<style>
  :root {
    --ink: #17202a;
    --muted: #667085;
    --line: #d9dee7;
    --panel: #ffffff;
    --page: #f2f5f8;
    --header: #111827;
    --header-soft: #1f2937;
    --accent: #d71920;
    --blue: #0057b8;
    --green: #16803c;
    --gold: #b86e00;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--page);
    color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  }

  .masthead {
    background: linear-gradient(135deg, var(--header) 0%, #202733 55%, #3c1115 100%);
    color: #fff;
    border-bottom: 4px solid var(--accent);
  }
  .masthead-inner {
    max-width: 1240px;
    margin: 0 auto;
    padding: 20px 22px 18px;
  }
  .league-strip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 18px;
    color: #cfd6e2;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .league-strip strong {
    color: #fff;
    letter-spacing: 0.1em;
  }
  h1 {
    margin: 0;
    font-size: clamp(2rem, 4vw, 3.5rem);
    line-height: 0.95;
    letter-spacing: 0;
  }
  .dek {
    margin: 10px 0 0;
    max-width: 860px;
    color: #dce3ee;
    font-size: 1rem;
  }
  .run-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 18px;
  }
  .pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-height: 30px;
    padding: 5px 10px;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    color: #eef2f7;
    font-size: 0.84rem;
    white-space: nowrap;
  }

  .shell {
    max-width: 1240px;
    margin: 0 auto;
    padding: 18px 22px 34px;
  }

  .main-tabs {
    position: sticky;
    top: 0;
    z-index: 5;
    display: flex;
    gap: 8px;
    padding: 10px 0;
    margin-bottom: 12px;
    background: rgba(242,245,248,0.95);
    backdrop-filter: blur(8px);
    overflow-x: auto;
  }
  .main-tab {
    appearance: none;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: #fff;
    color: var(--ink);
    cursor: pointer;
    font: inherit;
    font-size: 0.9rem;
    font-weight: 700;
    padding: 9px 14px;
    white-space: nowrap;
  }
  .main-tab[aria-selected="true"] {
    background: var(--header);
    border-color: var(--header);
    color: #fff;
  }
  .main-panel { display: none; }
  .main-panel.active { display: block; }

  .section-head {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 14px;
    margin: 16px 0 12px;
  }
  h2 {
    margin: 0;
    font-size: 1.2rem;
    letter-spacing: 0;
  }
  .muted { color: var(--muted); font-size: 0.9rem; }
  .fineprint { color: var(--muted); font-size: 0.82rem; margin-top: 18px; }

  .metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin: 16px 0 18px;
  }
  .metric {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 13px 14px;
    min-width: 0;
  }
  .metric .label {
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .metric .value {
    margin-top: 6px;
    font-size: 1.45rem;
    font-weight: 850;
    font-variant-numeric: tabular-nums;
  }
  .metric .sub {
    margin-top: 3px;
    color: var(--muted);
    font-size: 0.82rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .ticker {
    display: grid;
    grid-auto-flow: column;
    grid-auto-columns: minmax(236px, 1fr);
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 6px;
  }
  .match-tile {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    min-height: 118px;
    padding: 12px;
  }
  .tile-top {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    color: var(--muted);
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .teams {
    margin-top: 10px;
    display: grid;
    gap: 5px;
    font-weight: 800;
  }
  .lean {
    margin-top: 10px;
    display: flex;
    justify-content: space-between;
    gap: 8px;
    border-top: 1px solid var(--line);
    padding-top: 8px;
    color: var(--muted);
    font-size: 0.84rem;
  }
  .lean strong { color: var(--ink); }

  .slip-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }
  .slip-card {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
  }
  .slip-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 13px 14px;
    background: #f8fafc;
    border-bottom: 1px solid var(--line);
  }
  .slip-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 900;
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }
  .tag {
    display: inline-flex;
    align-items: center;
    min-height: 22px;
    padding: 2px 8px;
    border-radius: 999px;
    color: #fff;
    font-size: 0.72rem;
    font-weight: 900;
  }
  .tag-safe { background: var(--green); }
  .tag-balanced { background: var(--blue); }
  .tag-aggressive { background: var(--accent); }
  .tag-value { background: #7a3db8; }
  .slip-stats {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1px;
    background: var(--line);
  }
  .slip-stat {
    background: #fff;
    padding: 10px 12px;
  }
  .slip-stat .label {
    color: var(--muted);
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
  }
  .slip-stat .value {
    margin-top: 3px;
    font-weight: 900;
    font-variant-numeric: tabular-nums;
  }
  .pos { color: var(--green); }
  .neg { color: var(--accent); }

  .table-frame {
    overflow: auto;
    max-height: 62vh;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
  }
  .slip-card .table-frame {
    max-height: 260px;
    border: 0;
    border-radius: 0;
  }
  table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.88rem;
  }
  th {
    position: sticky;
    top: 0;
    z-index: 1;
    background: #f8fafc;
    border-bottom: 1px solid var(--line);
    color: #465161;
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  th, td {
    padding: 9px 10px;
    text-align: left;
    border-bottom: 1px solid #eef1f5;
    vertical-align: middle;
  }
  tbody tr:hover { background: #fafcff; }
  td.match-cell { min-width: 230px; font-weight: 800; }
  .subline {
    display: block;
    margin-top: 2px;
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 500;
  }
  .pct, .num { font-variant-numeric: tabular-nums; white-space: nowrap; }
  .sport-badge {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 2px 7px;
    background: #edf2f7;
    color: #344054;
    font-size: 0.72rem;
    font-weight: 850;
    text-transform: uppercase;
  }
  .market-badge {
    display: inline-flex;
    border-radius: 999px;
    padding: 2px 7px;
    background: #fff1d6;
    color: #6f4300;
    font-size: 0.74rem;
    font-weight: 850;
    white-space: nowrap;
  }
  .empty {
    background: var(--panel);
    border: 1px dashed var(--line);
    border-radius: 8px;
    color: var(--muted);
    padding: 18px;
  }
  footer {
    margin: 28px 0 0;
    color: var(--muted);
    font-size: 0.78rem;
    text-align: center;
  }

  @media (max-width: 920px) {
    .metric-grid, .slip-grid { grid-template-columns: 1fr 1fr; }
    .slip-stats { grid-template-columns: 1fr 1fr; }
  }
  @media (max-width: 620px) {
    .masthead-inner, .shell { padding-left: 14px; padding-right: 14px; }
    .league-strip, .section-head { align-items: flex-start; flex-direction: column; }
    .metric-grid, .slip-grid { grid-template-columns: 1fr; }
    .table-frame { max-height: 68vh; }
  }
</style>
"""


JS = """
<script>
  function showTab(id) {
    for (const panel of document.querySelectorAll('.main-panel')) {
      panel.classList.toggle('active', panel.id === id);
    }
    for (const button of document.querySelectorAll('.main-tab')) {
      button.setAttribute('aria-selected', button.dataset.target === id ? 'true' : 'false');
    }
  }
</script>
"""


def _pct(x) -> str:
    if x is None or pd.isna(x):
        return "-"
    return f"{x * 100:.1f}%"


def _odds(x) -> str:
    if x is None or pd.isna(x):
        return "-"
    return f"{x:.2f}"


def _num(x, digits: int = 1) -> str:
    if x is None or pd.isna(x):
        return "-"
    return f"{float(x):.{digits}f}"


def _line(x) -> str:
    if x is None or pd.isna(x):
        return "-"
    return f"{float(x):+g}"


def _esc(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    return html.escape(str(value))


def _date_range(*frames: pd.DataFrame) -> str:
    dates = []
    for df in frames:
        if df is not None and not df.empty and "date" in df:
            dates.extend(pd.to_datetime(df["date"], errors="coerce").dropna().tolist())
    if not dates:
        return "no fixtures in window"
    d0 = min(dates).strftime("%a %d %b")
    d1 = max(dates).strftime("%a %d %b")
    return d0 if d0 == d1 else f"{d0} - {d1}"


def _date_label(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    return pd.to_datetime(value).strftime("%a %d %b")


def _time_label(value) -> str:
    if value is None or pd.isna(value):
        return ""
    dt = pd.to_datetime(value)
    if dt.hour == 0 and dt.minute == 0:
        return ""
    return dt.strftime("%H:%M")


def _tag(variant: str) -> str:
    css = {
        "SAFE": "tag-safe",
        "BALANCED": "tag-balanced",
        "AGGRESSIVE": "tag-aggressive",
        "VALUE": "tag-value",
    }.get(variant, "tag-balanced")
    return f'<span class="tag {css}">{html.escape(variant)}</span>'


def _football_lean(row: pd.Series) -> tuple[str, float | None]:
    choices = [
        (str(row.get("home", "Home")), row.get("p_home")),
        ("Draw", row.get("p_draw")),
        (str(row.get("away", "Away")), row.get("p_away")),
    ]
    label, prob = max(choices, key=lambda item: -1.0 if pd.isna(item[1]) else float(item[1]))
    return label, None if pd.isna(prob) else float(prob)


def _basketball_lean(row: pd.Series) -> tuple[str, float | None]:
    choices = [
        (str(row.get("home", "Home")), row.get("p_home")),
        (str(row.get("away", "Away")), row.get("p_away")),
    ]
    label, prob = max(choices, key=lambda item: -1.0 if pd.isna(item[1]) else float(item[1]))
    return label, None if pd.isna(prob) else float(prob)


def _top_edge(slips: dict) -> tuple[str, float | None]:
    best_label = "-"
    best_edge = None
    for slip in slips.values():
        legs = slip.get("legs")
        if legs is None or legs.empty or "edge" not in legs:
            continue
        for _, leg in legs.iterrows():
            edge = leg.get("edge")
            if pd.isna(edge):
                continue
            if best_edge is None or float(edge) > best_edge:
                best_edge = float(edge)
                best_label = f"{leg.get('pick')} - {leg.get('match')}"
    return best_label, best_edge


def _best_value_stat(slips: dict) -> str:
    value_slip = slips.get("VALUE")
    if not value_slip:
        return "-"
    ev = value_slip["stats"].get("expected_value_per_unit")
    return f"{ev:+.3f}" if ev is not None and pd.notna(ev) else "-"


def _render_metrics(
    football_predictions: pd.DataFrame,
    basketball_predictions: pd.DataFrame,
    slips: dict,
) -> str:
    best_label, best_edge = _top_edge(slips)
    return f"""
      <div class="metric-grid">
        <div class="metric">
          <div class="label">Football board</div>
          <div class="value">{len(football_predictions)}</div>
          <div class="sub">fixtures in window</div>
        </div>
        <div class="metric">
          <div class="label">Basketball board</div>
          <div class="value">{len(basketball_predictions)}</div>
          <div class="sub">NBA and EuroLeague</div>
        </div>
        <div class="metric">
          <div class="label">Slip variants</div>
          <div class="value">{len(slips)}</div>
          <div class="sub">consolidated cards</div>
        </div>
        <div class="metric">
          <div class="label">Best value EV</div>
          <div class="value">{html.escape(_best_value_stat(slips))}</div>
          <div class="sub" title="{html.escape(best_label)}">{_pct(best_edge) if best_edge is not None else '-' } edge</div>
        </div>
      </div>
    """


def _render_ticker(football_predictions: pd.DataFrame, basketball_predictions: pd.DataFrame) -> str:
    rows = []
    for _, row in football_predictions.head(8).iterrows():
        lean, prob = _football_lean(row)
        rows.append({
            "date": row.get("date"),
            "league": row.get("league"),
            "sport": "Football",
            "home": row.get("home"),
            "away": row.get("away"),
            "lean": lean,
            "prob": prob,
        })
    for _, row in basketball_predictions.head(8).iterrows():
        lean, prob = _basketball_lean(row)
        rows.append({
            "date": row.get("date"),
            "league": row.get("league"),
            "sport": "Basketball",
            "home": row.get("home"),
            "away": row.get("away"),
            "lean": lean,
            "prob": prob,
        })
    rows.sort(key=lambda item: pd.to_datetime(item["date"], errors="coerce"))
    if not rows:
        return '<div class="empty">No fixtures in the selected window.</div>'

    tiles = []
    for item in rows[:12]:
        time = _time_label(item["date"])
        when = _date_label(item["date"]) + (f" {time}" if time else "")
        tiles.append(f"""
          <article class="match-tile">
            <div class="tile-top">
              <span>{_esc(item['sport'])}</span>
              <span>{_esc(item['league'])}</span>
            </div>
            <div class="teams">
              <span>{_esc(item['away'])}</span>
              <span>{_esc(item['home'])}</span>
            </div>
            <div class="lean">
              <span>{html.escape(when)}</span>
              <strong>{_esc(item['lean'])} {_pct(item['prob'])}</strong>
            </div>
          </article>
        """)
    return f'<div class="ticker">{"".join(tiles)}</div>'


def _render_slip(variant: str, slip: dict) -> str:
    legs: pd.DataFrame = slip["legs"]
    stats = slip["stats"]

    rows = []
    for _, r in legs.iterrows():
        edge = r.get("edge")
        edge_str = f"{edge * 100:+.1f}%" if pd.notna(edge) else "-"
        sport = str(r.get("sport", "")).title() if pd.notna(r.get("sport", "")) else "-"
        rows.append(
            f"<tr><td><span class='sport-badge'>{html.escape(sport)}</span></td>"
            f"<td class='match-cell'>{_esc(r['match'])}<span class='subline'>{_esc(r['league'])}</span></td>"
            f"<td><span class='market-badge'>{_esc(r['market'])}</span></td>"
            f"<td>{_esc(r['pick'])}</td>"
            f"<td class='pct'>{_pct(r['prob'])}</td>"
            f"<td>{_odds(r['fair_odds'])}</td>"
            f"<td>{_odds(r.get('market_odds'))}</td>"
            f"<td class='pct'>{edge_str}</td></tr>"
        )

    ev = stats["expected_value_per_unit"]
    ev_cls = "pos" if ev is not None and ev > 0 else "neg"
    ev_value = f"{ev:+.3f}" if ev is not None else "-"
    market_value = (
        f"{stats['combined_market_odds']:.2f}"
        if stats["combined_market_odds"] is not None
        else "-"
    )

    return f"""
      <article class="slip-card">
        <div class="slip-head">
          <div class="slip-title">{_tag(variant)} <span>{html.escape(variant)} slip</span></div>
          <span class="muted">{stats['legs']} legs</span>
        </div>
        <div class="slip-stats">
          <div class="slip-stat"><div class="label">Prob</div><div class="value">{_pct(stats['combined_prob'])}</div></div>
          <div class="slip-stat"><div class="label">Fair odds</div><div class="value">{stats['combined_fair_odds']:.2f}</div></div>
          <div class="slip-stat"><div class="label">Market</div><div class="value">{market_value}</div></div>
          <div class="slip-stat"><div class="label">EV/unit</div><div class="value {ev_cls}">{ev_value}</div></div>
        </div>
        <div class="table-frame">
          <table>
            <thead><tr>
              <th>Sport</th><th>Match</th><th>Market</th><th>Pick</th>
              <th>Prob</th><th>Fair</th><th>Odds</th><th>Edge</th>
            </tr></thead>
            <tbody>{"".join(rows)}</tbody>
          </table>
        </div>
      </article>
    """


def _render_slips(slips: dict) -> str:
    if not slips:
        return (
            "<div class='empty'>No consolidated slip variants could be built. "
            "Try widening lookahead_days or lowering thresholds in config.yaml.</div>"
        )
    cards = [_render_slip(name, slip) for name, slip in slips.items()]
    return f'<div class="slip-grid">{"".join(cards)}</div>'


def _render_football_predictions(predictions: pd.DataFrame) -> str:
    if predictions.empty:
        return "<div class='empty'>No football fixtures in the selected window.</div>"

    body_rows = []
    for _, r in predictions.iterrows():
        lean, lean_prob = _football_lean(r)
        time = _time_label(r.get("date"))
        date = _date_label(r.get("date")) + (f" {time}" if time else "")
        body_rows.append(
            "<tr>"
            f"<td class='num'>{html.escape(date)}</td>"
            f"<td><span class='sport-badge'>{_esc(r.get('league'))}</span></td>"
            f"<td class='match-cell'>{_esc(r.get('away'))}<span class='subline'>at {_esc(r.get('home'))}</span></td>"
            f"<td class='num'>{_num(r.get('lambda_home'), 2)} - {_num(r.get('lambda_away'), 2)}</td>"
            f"<td>{html.escape(lean)} <span class='subline'>{_pct(lean_prob)}</span></td>"
            f"<td class='pct'>{_pct(r.get('p_home'))} / {_pct(r.get('p_draw'))} / {_pct(r.get('p_away'))}</td>"
            f"<td class='pct'>{_pct(r.get('p_over25'))}</td>"
            f"<td class='pct'>{_pct(r.get('p_btts'))}</td>"
            f"<td>{_esc(r.get('top1_score'))}<span class='subline'>{_pct(r.get('top1_prob'))}</span></td>"
            "</tr>"
        )
    return f"""
      <div class="table-frame">
        <table>
          <thead><tr>
            <th>Date</th><th>Lg</th><th>Match</th><th>xG</th><th>Lean</th>
            <th>H/D/A</th><th>Over 2.5</th><th>BTTS</th><th>Top score</th>
          </tr></thead>
          <tbody>{"".join(body_rows)}</tbody>
        </table>
      </div>
    """


def _render_basketball_predictions(predictions: pd.DataFrame) -> str:
    if predictions.empty:
        return "<div class='empty'>No NBA or EuroLeague fixtures in the selected window.</div>"

    body_rows = []
    for _, r in predictions.iterrows():
        lean, lean_prob = _basketball_lean(r)
        time = _time_label(r.get("date"))
        date = _date_label(r.get("date")) + (f" {time}" if time else "")
        spread = "-"
        if pd.notna(r.get("spread_home")):
            spread = f"{_line(r.get('spread_home'))} home - {_pct(r.get('p_home_cover'))}"
        total = "-"
        if pd.notna(r.get("total_line")):
            total = f"{_num(r.get('total_line'), 1)} - over {_pct(r.get('p_over_total'))}"
        body_rows.append(
            "<tr>"
            f"<td class='num'>{html.escape(date)}</td>"
            f"<td><span class='sport-badge'>{_esc(r.get('league'))}</span></td>"
            f"<td class='match-cell'>{_esc(r.get('away'))}<span class='subline'>at {_esc(r.get('home'))}</span></td>"
            f"<td class='num'>{_num(r.get('pred_home_score'), 1)} - {_num(r.get('pred_away_score'), 1)}</td>"
            f"<td>{html.escape(lean)} <span class='subline'>{_pct(lean_prob)}</span></td>"
            f"<td class='pct'>{_pct(r.get('p_home'))} / {_pct(r.get('p_away'))}</td>"
            f"<td class='num'>{html.escape(spread)}</td>"
            f"<td class='num'>{html.escape(total)}</td>"
            "</tr>"
        )
    return f"""
      <div class="table-frame">
        <table>
          <thead><tr>
            <th>Date</th><th>Lg</th><th>Match</th><th>Projection</th>
            <th>Lean</th><th>H/A</th><th>Spread</th><th>Total</th>
          </tr></thead>
          <tbody>{"".join(body_rows)}</tbody>
        </table>
      </div>
    """


def render(
    football_predictions: pd.DataFrame,
    basketball_predictions: pd.DataFrame,
    slips: dict,
    run_ts: datetime,
) -> str:
    date_range = _date_range(football_predictions, basketball_predictions)
    total_fixtures = len(football_predictions) + len(basketball_predictions)

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Sports predictor - {date_range}</title>
{CSS}
{JS}
</head><body>
<header class="masthead">
  <div class="masthead-inner">
    <div class="league-strip">
      <strong>Sports Predictor</strong>
      <span>Football | NBA | EuroLeague</span>
    </div>
    <h1>Daily betting board</h1>
    <p class="dek">Model probabilities, projected scores, and consolidated slips in a compact game-day layout.</p>
    <div class="run-meta">
      <span class="pill">Run {run_ts.strftime('%Y-%m-%d %H:%M')}</span>
      <span class="pill">Window {html.escape(date_range)}</span>
      <span class="pill">{total_fixtures} fixtures</span>
      <span class="pill">{len(slips)} slip variants</span>
    </div>
  </div>
</header>

<main class="shell">
  <nav class="main-tabs" aria-label="Report sections">
    <button class="main-tab" data-target="overview-panel" aria-selected="true" onclick="showTab('overview-panel')" type="button">Overview</button>
    <button class="main-tab" data-target="slips-panel" aria-selected="false" onclick="showTab('slips-panel')" type="button">Slips</button>
    <button class="main-tab" data-target="football-panel" aria-selected="false" onclick="showTab('football-panel')" type="button">Football</button>
    <button class="main-tab" data-target="basketball-panel" aria-selected="false" onclick="showTab('basketball-panel')" type="button">NBA &amp; Euro basketball</button>
  </nav>

  <section id="overview-panel" class="main-panel active">
    <div class="section-head">
      <div>
        <h2>Board snapshot</h2>
        <div class="muted">Quick read before opening the detailed tabs.</div>
      </div>
    </div>
    {_render_metrics(football_predictions, basketball_predictions, slips)}
    <div class="section-head">
      <div>
        <h2>Upcoming fixtures</h2>
        <div class="muted">Sorted by kickoff or tipoff time.</div>
      </div>
    </div>
    {_render_ticker(football_predictions, basketball_predictions)}
  </section>

  <section id="slips-panel" class="main-panel">
    <div class="section-head">
      <div>
        <h2>Consolidated slips</h2>
        <div class="muted">One pick per fixture. Fair odds = 1 / prob. Edge = model prob / market implied - 1.</div>
      </div>
    </div>
    {_render_slips(slips)}
  </section>

  <section id="football-panel" class="main-panel">
    <div class="section-head">
      <div>
        <h2>Football predictions</h2>
        <div class="muted">1X2, totals, BTTS, and top scoreline projections.</div>
      </div>
    </div>
    {_render_football_predictions(football_predictions)}
  </section>

  <section id="basketball-panel" class="main-panel">
    <div class="section-head">
      <div>
        <h2>NBA and Euro basketball</h2>
        <div class="muted">Moneyline, projected score, spread, and total board where lines are available.</div>
      </div>
    </div>
    {_render_basketball_predictions(basketball_predictions)}
  </section>

  <footer>
    Models: football Elo + Dixon-Coles Poisson; basketball Elo + normal margin/total model.
    Data: football-data.co.uk, ESPN public scoreboard, EuroLeague live API.
    For analysis only - not betting advice.
  </footer>
</main>
</body></html>
"""
