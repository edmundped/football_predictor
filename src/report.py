"""
Light sports-site HTML report.
Bankroll dashboard, Kelly staking, result-logging UI.
"""

from __future__ import annotations

import html
import json
import math
from datetime import datetime

import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
  --bg:        #090c12;
  --bg2:       #0f1420;
  --card:      #131926;
  --card2:     #1a2135;
  --border:    #1e293b;
  --border2:   #253047;
  --text:      #e2e8f0;
  --muted:     #64748b;
  --muted2:    #8898aa;
  --green:     #10b981;
  --green-dim: #064e3b;
  --red:       #ef4444;
  --red-dim:   #450a0a;
  --gold:      #f59e0b;
  --gold-dim:  #451a03;
  --blue:      #3b82f6;
  --blue-dim:  #1e3a5f;
  --purple:    #a855f7;
  --purple-dim:#3b0764;
  --accent:    #10b981;
  --glow:      0 0 20px rgba(16,185,129,0.15);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
  line-height: 1.5;
  min-height: 100vh;
}

/* ── HEADER ── */
.header {
  background: linear-gradient(135deg, #0a0f1a 0%, #0d1525 40%, #0a1628 100%);
  border-bottom: 1px solid var(--border2);
  position: relative;
  overflow: hidden;
}
.header::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 20% 50%, rgba(16,185,129,0.08) 0%, transparent 60%),
              radial-gradient(ellipse at 80% 20%, rgba(59,130,246,0.06) 0%, transparent 50%);
  pointer-events: none;
}
.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 22px 24px 20px;
  position: relative;
}
.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--green), #059669);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  box-shadow: 0 0 16px rgba(16,185,129,0.4);
}
.brand-name {
  font-size: 1.2rem;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: #fff;
}
.brand-sub {
  font-size: 0.7rem;
  color: var(--muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.live-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: rgba(239,68,68,0.15);
  border: 1px solid rgba(239,68,68,0.3);
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--red);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.live-dot {
  width: 6px;
  height: 6px;
  background: var(--red);
  border-radius: 50%;
  animation: pulse 1.4s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.header-title { font-size: clamp(2rem, 4vw, 3rem); font-weight: 900; letter-spacing: -0.03em; line-height: 1; color: #fff; }
.header-sub { color: var(--muted2); font-size: 0.9rem; margin-top: 6px; }

.pills-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.pill {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 11px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border2);
  border-radius: 999px;
  font-size: 0.78rem;
  color: var(--muted2);
  white-space: nowrap;
}
.pill strong { color: var(--text); font-weight: 700; }
.pill.green { background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3); color: var(--green); }

/* ── TICKER STRIP ── */
.ticker-strip {
  background: rgba(0,0,0,0.3);
  border-top: 1px solid var(--border);
  padding: 0 24px;
  overflow: hidden;
  white-space: nowrap;
}
.ticker-inner {
  display: inline-flex;
  gap: 0;
  animation: scroll-left 40s linear infinite;
}
.ticker-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  border-right: 1px solid var(--border);
  font-size: 0.78rem;
}
.ticker-item .teams { font-weight: 700; color: var(--text); }
.ticker-item .odds { color: var(--green); font-weight: 800; font-variant-numeric: tabular-nums; }
.ticker-item .league { color: var(--muted); font-size: 0.7rem; text-transform: uppercase; }
@keyframes scroll-left {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

/* ── SHELL ── */
.shell {
  max-width: 1280px;
  margin: 0 auto;
  padding: 20px 24px 48px;
}

/* ── NAV TABS ── */
.nav-tabs {
  display: flex;
  gap: 4px;
  padding: 14px 0 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
  overflow-x: auto;
}
.nav-tab {
  appearance: none;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  padding: 10px 16px 12px;
  color: var(--muted);
  font: inherit;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: color .15s, border-color .15s;
}
.nav-tab:hover { color: var(--text); }
.nav-tab[aria-selected="true"] {
  color: var(--green);
  border-bottom-color: var(--green);
}
.tab-icon { margin-right: 5px; }

.panel { display: none; }
.panel.active { display: block; }

/* ── SECTION HEADING ── */
.section-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.section-head h2 { font-size: 1.05rem; font-weight: 800; letter-spacing: -0.01em; }
.section-head .hint { color: var(--muted); font-size: 0.82rem; }

/* ── STAT GRID ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}
.stat-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  position: relative;
  overflow: hidden;
}
.stat-card::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: var(--accent-bar, var(--border));
}
.stat-card.green-accent::after { background: var(--green); }
.stat-card.gold-accent::after  { background: var(--gold); }
.stat-card.red-accent::after   { background: var(--red); }
.stat-card.blue-accent::after  { background: var(--blue); }
.stat-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
  margin-bottom: 8px;
}
.stat-value {
  font-size: 1.7rem;
  font-weight: 900;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}
.stat-sub { color: var(--muted2); font-size: 0.78rem; margin-top: 5px; }
.text-green { color: var(--green); }
.text-red   { color: var(--red); }
.text-gold  { color: var(--gold); }
.text-blue  { color: var(--blue); }
.text-muted { color: var(--muted); }

/* ── BANKROLL PROGRESS ── */
.bankroll-hero {
  background: linear-gradient(135deg, var(--card) 0%, #0d1b2a 100%);
  border: 1px solid var(--border2);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}
.bankroll-hero::before {
  content: '';
  position: absolute;
  top: -40px; right: -40px;
  width: 180px; height: 180px;
  background: radial-gradient(circle, rgba(16,185,129,0.12), transparent 70%);
  pointer-events: none;
}
.bankroll-numbers { display: flex; align-items: flex-end; gap: 24px; flex-wrap: wrap; margin-bottom: 18px; }
.bankroll-main { }
.bankroll-main .label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin-bottom: 4px; }
.bankroll-main .amount { font-size: 2.8rem; font-weight: 900; color: var(--green); letter-spacing: -0.03em; line-height: 1; font-variant-numeric: tabular-nums; }
.bankroll-secondary { display: flex; gap: 24px; flex-wrap: wrap; }
.bk-stat .label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin-bottom: 2px; }
.bk-stat .val { font-size: 1rem; font-weight: 800; font-variant-numeric: tabular-nums; }

.progress-section { }
.progress-labels { display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--muted); margin-bottom: 6px; }
.progress-labels strong { color: var(--text); font-weight: 700; }
.progress-track {
  background: var(--border);
  border-radius: 999px;
  height: 10px;
  overflow: hidden;
  margin-bottom: 6px;
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #059669, #10b981, #34d399);
  box-shadow: 0 0 10px rgba(16,185,129,0.5);
  transition: width 0.6s ease;
}
.progress-pct { font-size: 0.72rem; color: var(--muted); }
.progress-pct strong { color: var(--green); }

/* ── FIXTURE TICKER (cards) ── */
.fixture-ticker {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(220px, 240px);
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 24px;
  scrollbar-width: thin;
  scrollbar-color: var(--border2) transparent;
}
.match-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
}
.match-card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.league-tag {
  font-size: 0.68rem; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--muted); background: var(--bg2);
  padding: 2px 7px; border-radius: 4px;
}
.match-time { font-size: 0.72rem; color: var(--muted2); font-variant-numeric: tabular-nums; }
.match-teams { margin-bottom: 10px; }
.match-teams .team { font-weight: 700; font-size: 0.9rem; padding: 1px 0; }
.match-teams .vs { font-size: 0.7rem; color: var(--muted); padding: 2px 0; }
.match-lean { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border); padding-top: 8px; }
.lean-pick { font-size: 0.78rem; color: var(--muted2); }
.lean-prob { font-size: 0.85rem; font-weight: 800; color: var(--green); font-variant-numeric: tabular-nums; }

/* ── SLIP GRID ── */
.slip-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.slip-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.slip-card.value-card { border-color: rgba(168,85,247,0.4); box-shadow: 0 0 20px rgba(168,85,247,0.08); }
.slip-card.safe-card  { border-color: rgba(16,185,129,0.3); }
.slip-card.dream-card {
  grid-column: 1 / -1;
  border-color: rgba(245,158,11,0.45);
  box-shadow: 0 0 24px rgba(245,158,11,0.08);
}
.slip-card.dream-card .table-wrap { max-height: 440px; }
.slip-card.dream-card .slip-name { white-space: normal; line-height: 1.15; }

.slip-header {
  padding: 14px 16px;
  background: var(--card2);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
}
.slip-title-row { display: flex; align-items: center; gap: 8px; }
.slip-name { font-size: 1rem; font-weight: 900; text-transform: uppercase; letter-spacing: 0.04em; }

.badge {
  display: inline-flex; align-items: center;
  padding: 2px 9px; border-radius: 999px;
  font-size: 0.66rem; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.08em;
}
.badge-safe     { background: var(--green-dim); color: var(--green); border: 1px solid rgba(16,185,129,0.3); }
.badge-balanced { background: var(--blue-dim);  color: var(--blue);  border: 1px solid rgba(59,130,246,0.3); }
.badge-aggressive { background: var(--red-dim); color: var(--red);   border: 1px solid rgba(239,68,68,0.3); }
.badge-value    { background: var(--purple-dim); color: var(--purple); border: 1px solid rgba(168,85,247,0.3); }
.badge-dream    { background: rgba(245,158,11,0.1); color: var(--gold); border: 1px solid rgba(245,158,11,0.3); }
.badge-win      { background: var(--green-dim); color: var(--green); border: 1px solid rgba(16,185,129,0.3); }
.badge-loss     { background: var(--red-dim);   color: var(--red);   border: 1px solid rgba(239,68,68,0.3); }
.badge-pending  { background: rgba(245,158,11,0.1); color: var(--gold); border: 1px solid rgba(245,158,11,0.3); }
.badge-void     { background: rgba(100,116,139,0.15); color: var(--muted); border: 1px solid var(--border2); }

.slip-stats-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 1px;
  background: var(--border);
}
.slip-stat-cell {
  background: var(--card);
  padding: 10px 12px;
}
.slip-stat-cell .lbl { font-size: 0.64rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 3px; }
.slip-stat-cell .val { font-size: 0.95rem; font-weight: 900; font-variant-numeric: tabular-nums; }

/* Kelly stake highlight */
.kelly-banner {
  margin: 12px 16px;
  background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(16,185,129,0.03));
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.kelly-left .kl { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 2px; }
.kelly-left .ks { font-size: 1.3rem; font-weight: 900; color: var(--green); font-variant-numeric: tabular-nums; }
.kelly-right { text-align: right; }
.kelly-right .kl { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 2px; }
.kelly-right .ks { font-size: 1rem; font-weight: 800; color: var(--gold); font-variant-numeric: tabular-nums; }

.copy-cmd {
  margin: 0 16px 12px;
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 6px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.copy-cmd code { font-size: 0.75rem; color: var(--muted2); font-family: 'Courier New', monospace; word-break: break-all; }
.copy-btn {
  appearance: none;
  background: var(--border2);
  border: 1px solid var(--border2);
  border-radius: 4px;
  color: var(--muted2);
  cursor: pointer;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 4px 10px;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background .15s, color .15s;
}
.copy-btn:hover { background: var(--green); color: #fff; border-color: var(--green); }

/* ── TABLE ── */
.table-wrap {
  overflow: auto;
  border-radius: 0 0 12px 12px;
  max-height: 280px;
  flex: 1;
}
.full-table .table-wrap { max-height: 64vh; border-radius: 10px; }
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.83rem;
}
th {
  position: sticky; top: 0; z-index: 2;
  background: #0e1520;
  border-bottom: 1px solid var(--border2);
  color: var(--muted);
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 9px 12px;
  white-space: nowrap;
  text-align: left;
}
td {
  padding: 9px 12px;
  border-bottom: 1px solid rgba(30,41,59,0.5);
  vertical-align: middle;
}
tbody tr:hover td { background: rgba(255,255,255,0.02); }
tbody tr:last-child td { border-bottom: none; }
td.match-col { min-width: 180px; font-weight: 700; }
.row-sub { display: block; margin-top: 2px; color: var(--muted); font-size: 0.75rem; font-weight: 400; }
.num { font-variant-numeric: tabular-nums; }
.sport-pill {
  display: inline-block;
  padding: 1px 7px;
  background: rgba(59,130,246,0.12);
  border: 1px solid rgba(59,130,246,0.2);
  border-radius: 4px;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--blue);
  white-space: nowrap;
}
.market-pill {
  display: inline-block;
  padding: 1px 7px;
  background: rgba(245,158,11,0.1);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--gold);
  white-space: nowrap;
}
.edge-pos { color: var(--green); font-weight: 700; }
.edge-neg { color: var(--muted); }
.result-ok { color: var(--green); font-weight: 800; }
.result-bad { color: var(--red); font-weight: 800; }
.result-na { color: var(--muted); font-weight: 700; }

/* ── COMMUNITY CODES ── */
.code-form {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}
.code-form-grid {
  display: grid;
  grid-template-columns: minmax(180px, 1.2fr) minmax(120px, .6fr) minmax(160px, 1fr) auto;
  gap: 10px;
  align-items: end;
}
.field label {
  display: block;
  font-size: 0.68rem;
  font-weight: 800;
  color: var(--muted);
  letter-spacing: 0.08em;
  margin-bottom: 5px;
  text-transform: uppercase;
}
.field input {
  width: 100%;
  background: var(--bg2);
  border: 1px solid var(--border2);
  border-radius: 6px;
  color: var(--text);
  font: inherit;
  min-height: 38px;
  padding: 8px 10px;
}
.field input:focus { outline: 1px solid rgba(16,185,129,0.5); border-color: rgba(16,185,129,0.45); }
.submit-btn {
  appearance: none;
  background: var(--green);
  border: 1px solid var(--green);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 800;
  min-height: 38px;
  padding: 8px 14px;
  white-space: nowrap;
}
.status-line { color: var(--muted); font-size: 0.78rem; margin-top: 10px; }

/* ── BET LOG TABLE ── */
.bet-log-table th { background: #0c1118; }
.bet-outcome-row td { }

/* ── PENDING BETS ── */
.pending-card {
  background: var(--card);
  border: 1px solid rgba(245,158,11,0.25);
  border-radius: 10px;
  margin-bottom: 10px;
  overflow: hidden;
}
.pending-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(245,158,11,0.05);
  border-bottom: 1px solid rgba(245,158,11,0.15);
}
.pending-id { font-family: monospace; font-size: 0.82rem; font-weight: 700; color: var(--gold); }
.pending-body { padding: 12px 16px; }
.pending-legs { margin-bottom: 10px; }
.pending-leg { font-size: 0.82rem; color: var(--muted2); padding: 2px 0; }
.pending-leg strong { color: var(--text); }
.log-commands { display: flex; gap: 8px; flex-wrap: wrap; }
.log-cmd-btn {
  appearance: none;
  border: 1px solid var(--border2);
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  padding: 6px 14px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  transition: all .15s;
}
.log-cmd-btn.win  { background: var(--green-dim); color: var(--green); border-color: rgba(16,185,129,0.3); }
.log-cmd-btn.loss { background: var(--red-dim);   color: var(--red);   border-color: rgba(239,68,68,0.3); }
.log-cmd-btn.void { background: rgba(100,116,139,0.1); color: var(--muted2); }
.log-cmd-btn:hover.win  { background: var(--green); color: #fff; }
.log-cmd-btn:hover.loss { background: var(--red);   color: #fff; }

/* ── EMPTY STATE ── */
.empty {
  background: var(--card);
  border: 1px dashed var(--border2);
  border-radius: 10px;
  color: var(--muted);
  font-size: 0.88rem;
  padding: 24px;
  text-align: center;
}

/* ── FOOTER ── */
footer {
  text-align: center;
  color: var(--muted);
  font-size: 0.74rem;
  margin-top: 40px;
  padding-bottom: 24px;
}

/* ── TOAST ── */
.toast {
  position: fixed;
  bottom: 24px; right: 24px;
  background: var(--green);
  color: #fff;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  opacity: 0;
  transform: translateY(8px);
  transition: opacity .2s, transform .2s;
  pointer-events: none;
  z-index: 99;
}
.toast.show { opacity: 1; transform: translateY(0); }

/* ── LIGHT SPORTS DESK THEME ── */
:root {
  --bg:        #ffffff;
  --bg2:       #f3f5f7;
  --card:      #ffffff;
  --card2:     #f8fafc;
  --border:    #e5e7eb;
  --border2:   #d1d5db;
  --text:      #111827;
  --muted:     #6b7280;
  --muted2:    #4b5563;
  --green:     #007a3d;
  --green-dim: #e7f6ee;
  --red:       #c1121f;
  --red-dim:   #fde8ea;
  --gold:      #b7791f;
  --gold-dim:  #fff5dc;
  --blue:      #1d4ed8;
  --blue-dim:  #e8f0ff;
  --purple:    #6d28d9;
  --purple-dim:#f0e9ff;
  --accent:    #007a3d;
  --glow:      none;
}

body {
  background: #ffffff;
  color: var(--text);
}

.header {
  background: #ffffff;
  border-bottom: 1px solid var(--border);
  overflow: visible;
}
.header::before,
.bankroll-hero::before {
  display: none;
}
.header-inner {
  padding: 18px 24px 16px;
}
.header-top {
  margin-bottom: 14px;
}
.brand-icon {
  background: #111827;
  border-radius: 4px;
  box-shadow: none;
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.04em;
}
.brand-name {
  color: var(--text);
}
.brand-sub {
  color: var(--muted2);
}
.live-badge {
  background: #fff5f5;
  border-color: #fecaca;
  border-radius: 4px;
  color: #b91c1c;
}
.header-title {
  color: var(--text);
  font-size: clamp(1.8rem, 3vw, 2.6rem);
  letter-spacing: -0.02em;
}
.header-sub {
  color: var(--muted2);
}
.pill {
  background: #f8fafc;
  border-color: var(--border);
  color: var(--muted2);
}
.pill strong {
  color: var(--text);
}
.pill.green {
  background: var(--green-dim);
  border-color: #b7e1c7;
  color: var(--green);
}

.ticker-strip {
  background: #111827;
  border-top: 1px solid #111827;
}
.ticker-item {
  border-right: 1px solid rgba(255,255,255,0.14);
  color: #e5e7eb;
}
.ticker-item .teams {
  color: #ffffff;
}
.ticker-item .league {
  color: #9ca3af;
}
.ticker-item .odds {
  color: #34d399;
}

.nav-tabs {
  background: #ffffff;
  border-bottom-color: var(--border);
  padding-top: 4px;
}
.nav-tab {
  border-bottom-width: 3px;
  color: var(--muted2);
  font-weight: 800;
  padding: 11px 15px 13px;
}
.nav-tab[aria-selected="true"] {
  color: var(--green);
}
.tab-icon {
  display: none;
}

.section-head h2 {
  color: var(--text);
}

.stat-card,
.match-card,
.slip-card,
.code-form,
.pending-card,
.empty {
  background: #ffffff;
  border-color: var(--border);
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}
.stat-card::after {
  height: 3px;
}
.bankroll-hero {
  background: #f8fafc;
  border-color: var(--border);
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}
.bankroll-main .amount {
  color: var(--green);
}
.progress-track {
  background: #e5e7eb;
}
.progress-fill {
  background: #007a3d;
  box-shadow: none;
}

.league-tag {
  background: #f3f4f6;
  color: #374151;
}
.match-lean {
  border-top-color: var(--border);
}
.lean-prob {
  color: var(--green);
}

.slip-card.value-card,
.slip-card.safe-card,
.slip-card.dream-card {
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}
.slip-card.safe-card {
  border-left: 4px solid var(--green);
}
.slip-card.value-card {
  border-left: 4px solid var(--purple);
}
.slip-card.dream-card {
  background: #fffbeb;
  border-color: #f3d27a;
  border-left: 4px solid var(--gold);
}
.slip-header {
  background: var(--card2);
  border-bottom-color: var(--border);
}
.slip-card.dream-card .slip-header,
.slip-card.dream-card .slip-stat-cell {
  background: #fff8d7;
}
.slip-stats-row {
  background: var(--border);
}
.slip-stat-cell {
  background: #ffffff;
}
.badge {
  border-radius: 4px;
}

.kelly-banner {
  background: #ecfdf5;
  border-color: #b7e1c7;
}
.copy-cmd {
  background: #f9fafb;
  border-color: var(--border);
}
.copy-btn {
  background: #ffffff;
  border-color: var(--border2);
  color: #374151;
}
.copy-btn:hover {
  background: var(--green);
  border-color: var(--green);
  color: #ffffff;
}

th,
.bet-log-table th {
  background: #f3f4f6;
  border-bottom-color: var(--border2);
  color: #374151;
}
td {
  border-bottom-color: #edf0f3;
}
tbody tr:hover td {
  background: #f9fafb;
}
.sport-pill {
  background: var(--blue-dim);
  border-color: #c7d7fe;
}
.market-pill {
  background: var(--gold-dim);
  border-color: #f5d78f;
}

.field input {
  background: #ffffff;
}
.pending-head {
  background: #fffbeb;
}
.log-cmd-btn.win,
.log-cmd-btn.loss,
.log-cmd-btn.void {
  background: #ffffff;
}
footer {
  border-top: 1px solid var(--border);
  padding-top: 20px;
}

/* ── RESPONSIVE ── */
@media (max-width: 960px) {
  .stat-grid { grid-template-columns: 1fr 1fr; }
  .slip-grid  { grid-template-columns: 1fr; }
  .slip-stats-row { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 600px) {
  .header-inner, .shell { padding-left: 14px; padding-right: 14px; }
  .stat-grid { grid-template-columns: 1fr 1fr; }
  .bankroll-numbers { gap: 14px; }
  .bankroll-main .amount { font-size: 2rem; }
}
@media (max-width: 760px) {
  .code-form-grid { grid-template-columns: 1fr; }
}

/* ── SPORTSBOOK COMMAND CENTER SKIN ── */
:root {
  --bg:        #07120f;
  --bg2:       #0c1b16;
  --card:      #0f211a;
  --card2:     #142b22;
  --border:    #1f3a30;
  --border2:   #2d5546;
  --text:      #f4fbf7;
  --muted:     #8aa399;
  --muted2:    #b8c9c1;
  --green:     #18d26e;
  --green-dim: rgba(24,210,110,0.13);
  --red:       #ff4b5f;
  --red-dim:   rgba(255,75,95,0.13);
  --gold:      #ffbf45;
  --gold-dim:  rgba(255,191,69,0.14);
  --blue:      #45a6ff;
  --blue-dim:  rgba(69,166,255,0.14);
  --purple:    #b47cff;
  --purple-dim:rgba(180,124,255,0.14);
  --accent:    #18d26e;
}

body {
  background:
    linear-gradient(180deg, rgba(7,18,15,0.86), #07120f 260px),
    url("https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=1800&q=78") center top / cover fixed;
}

.header {
  background: linear-gradient(120deg, rgba(5,16,13,.96), rgba(8,37,27,.92));
  border-bottom: 1px solid rgba(255,255,255,.08);
}
.header::before {
  display: block;
  background:
    linear-gradient(90deg, rgba(24,210,110,.12) 1px, transparent 1px),
    linear-gradient(0deg, rgba(255,255,255,.06) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(90deg, transparent, #000 16%, #000 84%, transparent);
}
.header-inner { max-width: 1440px; padding: 26px 28px 22px; }
.brand-icon {
  background: var(--green);
  color: #062014;
  border-radius: 6px;
  box-shadow: 0 12px 28px rgba(24,210,110,.24);
}
.brand-name, .header-title { color: #fff; }
.header-title {
  max-width: 760px;
  font-size: clamp(2.2rem, 5vw, 4.7rem);
  letter-spacing: -.045em;
}
.header-sub {
  max-width: 760px;
  color: #d6e7df;
  font-size: 1rem;
}
.live-badge {
  background: rgba(24,210,110,.12);
  border-color: rgba(24,210,110,.38);
  color: var(--green);
}
.live-dot { background: var(--green); }
.pill {
  min-height: 34px;
  border-radius: 6px;
  background: rgba(255,255,255,.07);
  border-color: rgba(255,255,255,.12);
  color: #dbe9e3;
}
.pill.green {
  background: rgba(24,210,110,.16);
  border-color: rgba(24,210,110,.36);
}
.ticker-strip {
  background: #07120f;
  border-top: 1px solid rgba(255,255,255,.08);
}
.ticker-item {
  min-height: 40px;
  border-right-color: rgba(255,255,255,.08);
}
.ticker-item .league {
  background: rgba(255,255,255,.08);
  border-radius: 4px;
  color: #d7e6df;
  padding: 2px 6px;
}
.shell { max-width: 1440px; padding: 0 28px 56px; }
.nav-tabs {
  position: sticky;
  top: 0;
  z-index: 20;
  margin: 0 -28px 24px;
  padding: 0 28px;
  background: rgba(7,18,15,.92);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255,255,255,.08);
}
.nav-tab {
  min-height: 54px;
  border-bottom-width: 3px;
  color: #aec5bb;
  font-weight: 800;
}
.nav-tab[aria-selected="true"] {
  color: #fff;
  border-bottom-color: var(--green);
}
.tab-icon { display: none; }

.bet-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, .85fr);
  gap: 16px;
  margin-bottom: 18px;
}
.bet-hero-main,
.bet-hero-side,
.market-board {
  border: 1px solid rgba(255,255,255,.1);
  background: linear-gradient(145deg, rgba(15,33,26,.96), rgba(8,22,17,.96));
  box-shadow: 0 18px 55px rgba(0,0,0,.28);
}
.bet-hero-main {
  min-height: 310px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  padding: 28px;
}
.bet-hero-main::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(120deg, rgba(24,210,110,.18), transparent 42%),
    radial-gradient(circle at 82% 22%, rgba(255,191,69,.18), transparent 28%),
    url("https://images.unsplash.com/photo-1522778119026-d647f0596c20?auto=format&fit=crop&w=1200&q=70") center / cover;
  opacity: .28;
}
.bet-hero-main > * { position: relative; }
.hero-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 6px 10px;
  border-radius: 6px;
  background: rgba(24,210,110,.15);
  border: 1px solid rgba(24,210,110,.28);
  color: var(--green);
  font-size: .72rem;
  font-weight: 900;
  letter-spacing: .12em;
  text-transform: uppercase;
}
.hero-title {
  max-width: 740px;
  color: #fff;
  font-size: clamp(2rem, 4vw, 4.1rem);
  font-weight: 950;
  letter-spacing: -.045em;
  line-height: .96;
}
.hero-copy {
  max-width: 700px;
  margin-top: 12px;
  color: #cfe2d9;
  font-size: 1rem;
}
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}
.hero-btn {
  appearance: none;
  min-height: 42px;
  border: 1px solid rgba(255,255,255,.14);
  border-radius: 6px;
  background: rgba(255,255,255,.08);
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-weight: 900;
  padding: 10px 14px;
}
.hero-btn.primary {
  background: var(--green);
  border-color: var(--green);
  color: #052015;
}
.bet-hero-side {
  border-radius: 8px;
  padding: 18px;
}
.bet-hero-side h3,
.market-board h3 {
  font-size: .78rem;
  color: var(--muted2);
  letter-spacing: .12em;
  text-transform: uppercase;
  margin-bottom: 12px;
}
.ticket-stack {
  display: grid;
  gap: 10px;
}
.ticket-mini {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  padding: 12px;
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 6px;
  background: rgba(255,255,255,.045);
}
.ticket-mini strong {
  color: #fff;
  font-size: .92rem;
}
.ticket-mini .ticket-meta {
  color: var(--muted);
  font-size: .76rem;
  margin-top: 2px;
}
.ticket-mini .ticket-odds {
  align-self: center;
  color: var(--gold);
  font-size: 1.05rem;
  font-weight: 950;
  font-variant-numeric: tabular-nums;
}
.market-board {
  border-radius: 8px;
  padding: 18px;
  margin-bottom: 22px;
}
.market-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.market-tile {
  min-height: 112px;
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 6px;
  background: rgba(255,255,255,.045);
  padding: 12px;
}
.market-tile .market-name {
  color: var(--muted);
  font-size: .68rem;
  font-weight: 900;
  letter-spacing: .1em;
  text-transform: uppercase;
}
.market-tile .market-pick {
  margin-top: 8px;
  color: #fff;
  font-weight: 900;
  line-height: 1.25;
}
.market-tile .market-match {
  color: var(--muted2);
  font-size: .75rem;
  margin-top: 4px;
}
.market-tile .market-prob {
  color: var(--green);
  font-size: 1.22rem;
  font-weight: 950;
  margin-top: 8px;
}

.stat-grid { gap: 12px; }
.stat-card,
.match-card,
.slip-card,
.code-form,
.pending-card,
.empty,
.bankroll-hero {
  border-radius: 8px;
  background: rgba(15,33,26,.96);
  border-color: rgba(255,255,255,.1);
  box-shadow: 0 12px 35px rgba(0,0,0,.18);
}
.stat-card::after { height: 4px; }
.stat-label, th { color: #9fb8ad; }
.stat-value { color: #fff; }
.fixture-ticker {
  grid-auto-columns: minmax(250px, 280px);
}
.match-card {
  min-height: 170px;
  display: flex;
  flex-direction: column;
}
.match-teams { flex: 1; }
.match-teams .team { color: #fff; font-size: .98rem; }
.match-lean {
  margin-top: 10px;
  padding-top: 10px;
  border-top-color: rgba(255,255,255,.1);
}
.slip-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.slip-card {
  border-radius: 8px;
  background: rgba(15,33,26,.98);
}
.slip-card.dream-card {
  background: linear-gradient(145deg, rgba(48,34,12,.98), rgba(16,28,20,.98));
  border-color: rgba(255,191,69,.34);
}
.slip-header,
.slip-card.dream-card .slip-header,
.slip-card.dream-card .slip-stat-cell {
  background: rgba(255,255,255,.045);
}
.slip-stats-row { background: rgba(255,255,255,.1); }
.slip-stat-cell { background: rgba(8,22,17,.72); }
.badge, .league-tag, .sport-pill, .market-pill { border-radius: 4px; }
.table-wrap { max-height: 420px; }
th {
  background: #0a1712;
  color: #b4c9bf;
}
td { border-bottom-color: rgba(255,255,255,.07); }
tbody tr:hover td { background: rgba(255,255,255,.04); }
.copy-cmd,
.field input {
  background: rgba(255,255,255,.045);
  border-color: rgba(255,255,255,.12);
}
.copy-btn,
.submit-btn {
  border-radius: 5px;
}

@media (max-width: 1100px) {
  .bet-hero { grid-template-columns: 1fr; }
  .market-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .shell { padding-left: 14px; padding-right: 14px; }
  .nav-tabs { margin-left: -14px; margin-right: -14px; padding-left: 14px; padding-right: 14px; }
  .bet-hero-main { padding: 20px; min-height: 280px; }
  .hero-title { font-size: 2.25rem; }
  .market-grid { grid-template-columns: 1fr; }
  .slip-grid { grid-template-columns: 1fr; }
}
</style>
"""


JS = r"""
<script>
function showTab(id) {
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === id));
  document.querySelectorAll('.nav-tab').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === id ? 'true' : 'false'));
}

function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    btn.style.background = 'var(--green)';
    btn.style.color = '#fff';
    showToast('Command copied to clipboard');
    setTimeout(() => { btn.textContent = orig; btn.style.background=''; btn.style.color=''; }, 2000);
  }).catch(() => {
    btn.textContent = 'Error';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
  });
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2400);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  }[ch]));
}

function logResult(betId, outcome) {
  const cmd = `python log_result.py --id ${betId} --outcome ${outcome}`;
  navigator.clipboard.writeText(cmd).then(() => {
    showToast(`Command copied — paste in your terminal (${outcome})`);
  });
}

function communitySettings() {
  return window.PREDICTOR_COMMUNITY || { endpoint: '', ttl_hours: 24 };
}

function communityTtlMs() {
  const cfg = communitySettings();
  const hours = Number(cfg.ttl_hours || 24);
  return Math.max(1, hours) * 60 * 60 * 1000;
}

function freshCodes(codes) {
  const cutoff = Date.now() - communityTtlMs();
  return (codes || []).filter(c => {
    const t = new Date(c.created_at || 0).getTime();
    return Number.isFinite(t) && t >= cutoff;
  }).sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
}

function localCodes() {
  try {
    return freshCodes(JSON.parse(localStorage.getItem('predictorpro.community.codes') || '[]'));
  } catch (_) {
    return [];
  }
}

function saveLocalCodes(codes) {
  localStorage.setItem('predictorpro.community.codes', JSON.stringify(freshCodes(codes)));
}

function renderCommunityRows(codes) {
  const tbody = document.getElementById('community-code-rows');
  const empty = document.getElementById('community-empty');
  if (!tbody || !empty) return;
  const rows = freshCodes(codes);
  empty.style.display = rows.length ? 'none' : 'block';
  tbody.innerHTML = rows.map(c => {
    const when = new Date(c.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    return `<tr>
      <td class="num">${escapeHtml(when)}</td>
      <td style="font-weight:800">${escapeHtml(c.code)}</td>
      <td class="num">${escapeHtml(c.odds || '')}</td>
      <td>${escapeHtml(c.note || '')}</td>
    </tr>`;
  }).join('');
}

async function loadCommunityCodes() {
  const cfg = communitySettings();
  const status = document.getElementById('community-status');
  if (!document.getElementById('community-code-rows')) return;
  if (!cfg.endpoint) {
    const codes = localCodes();
    renderCommunityRows(codes);
    if (status) status.textContent = 'Browser-local board · expires after 24 hours';
    return;
  }
  try {
    const res = await fetch(cfg.endpoint, { headers: { 'Accept': 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const payload = await res.json();
    renderCommunityRows(payload.codes || payload || []);
    if (status) status.textContent = 'Community board · expires after 24 hours';
  } catch (_) {
    renderCommunityRows(localCodes());
    if (status) status.textContent = 'Community endpoint unavailable · showing browser-local codes';
  }
}

async function submitCommunityCode(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const code = form.elements.code.value.trim();
  if (!code) return;
  const item = {
    code,
    odds: form.elements.odds.value.trim(),
    note: form.elements.note.value.trim(),
    created_at: new Date().toISOString()
  };
  const cfg = communitySettings();
  if (cfg.endpoint) {
    try {
      const res = await fetch(cfg.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(item)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      showToast('Code submitted');
      form.reset();
      loadCommunityCodes();
      return;
    } catch (_) {
      showToast('Endpoint unavailable; saved locally');
    }
  } else {
    showToast('Code saved locally');
  }
  const codes = [item, ...localCodes()];
  saveLocalCodes(codes);
  renderCommunityRows(codes);
  form.reset();
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('community-form');
  if (form) form.addEventListener('submit', submitCommunityCode);
  loadCommunityCodes();
});
</script>
"""


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _esc(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return html.escape(str(v))

def _pct(x, dash="—") -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return dash
    pct = float(x) * 100
    if 0 < pct < 0.1:
        return f"{pct:.3f}%"
    return f"{pct:.1f}%"

def _odds(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{float(x):.2f}"

def _money(x) -> str:
    if x is None:
        return "—"
    value = float(x)
    sign = "-" if value < 0 else ""
    return f"{sign}GHS {abs(value):,.2f}"

def _num(x, d=1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{float(x):.{d}f}"

def _sign(x) -> str:
    if x is None:
        return "—"
    v = float(x)
    s = f"{v:+.2f}"
    return s

def _date_label(v) -> str:
    if v is None:
        return "—"
    try:
        return pd.to_datetime(v).strftime("%a %d %b")
    except Exception:
        return str(v)

def _time_label(v) -> str:
    if v is None:
        return ""
    try:
        dt = pd.to_datetime(v)
        if dt.hour == 0 and dt.minute == 0:
            return ""
        return dt.strftime("%H:%M")
    except Exception:
        return ""

def _date_range(*frames) -> str:
    dates = []
    for df in frames:
        if df is not None and not df.empty and "date" in df.columns:
            dates.extend(pd.to_datetime(df["date"], errors="coerce").dropna().tolist())
    if not dates:
        return "no fixtures"
    d0 = min(dates).strftime("%a %d %b")
    d1 = max(dates).strftime("%a %d %b")
    return d0 if d0 == d1 else f"{d0} – {d1}"

def _football_lean(row) -> tuple:
    opts = [
        (str(row.get("home", "Home")), row.get("p_home")),
        ("Draw",                        row.get("p_draw")),
        (str(row.get("away", "Away")),  row.get("p_away")),
    ]
    label, prob = max(opts, key=lambda x: float(x[1]) if x[1] is not None and not (isinstance(x[1], float) and math.isnan(x[1])) else -1)
    return label, prob

def _basketball_lean(row) -> tuple:
    opts = [
        (str(row.get("home", "Home")), row.get("p_home")),
        (str(row.get("away", "Away")), row.get("p_away")),
    ]
    label, prob = max(opts, key=lambda x: float(x[1]) if x[1] is not None and not (isinstance(x[1], float) and math.isnan(x[1])) else -1)
    return label, prob

def _slip_badge(variant: str) -> str:
    if variant.startswith("HUNDRED_K"):
        return '<span class="badge badge-dream">100K</span>'
    css = {
        "SAFE": "badge-safe",
        "BALANCED": "badge-balanced",
        "AGGRESSIVE": "badge-aggressive",
        "ONE_CEDI_DREAM": "badge-dream",
        "VALUE": "badge-value",
    }.get(variant, "badge-balanced")
    label = {
        "ONE_CEDI_DREAM": "1 CEDI",
    }.get(variant, variant)
    return f'<span class="badge {css}">{html.escape(label)}</span>'

def _slip_title(variant: str) -> str:
    if variant.startswith("HUNDRED_K"):
        suffix = variant.rsplit("_", 1)[-1]
        return f"100K Safest Route {suffix}"
    return {
        "ONE_CEDI_DREAM": "1 Cedi and a Small Dream",
    }.get(variant, f"{variant} slip")

def _outcome_badge(outcome) -> str:
    if outcome == "WIN":
        return '<span class="badge badge-win">WIN</span>'
    if outcome == "LOSS":
        return '<span class="badge badge-loss">LOSS</span>'
    if outcome == "VOID":
        return '<span class="badge badge-void">VOID</span>'
    return '<span class="badge badge-pending">Pending</span>'


# ──────────────────────────────────────────────────────────────────────────────
# Header ticker items
# ──────────────────────────────────────────────────────────────────────────────

def _ticker_html(football: pd.DataFrame, basketball: pd.DataFrame) -> str:
    items = []
    for _, r in football.head(6).iterrows():
        lean, prob = _football_lean(r)
        p_str = _pct(prob, "")
        odds_h = r.get("odds_home")
        odds_str = f"{float(odds_h):.2f}" if odds_h and not (isinstance(odds_h, float) and math.isnan(odds_h)) else ""
        items.append(
            f'<span class="ticker-item">'
            f'<span class="league">{_esc(r.get("league"))}</span>'
            f'<span class="teams">{_esc(r.get("home"))} v {_esc(r.get("away"))}</span>'
            + (f'<span class="odds">{odds_str}</span>' if odds_str else '')
            + f'<span class="text-muted">{html.escape(lean)} {p_str}</span>'
            f'</span>'
        )
    for _, r in basketball.head(4).iterrows():
        lean, prob = _basketball_lean(r)
        p_str = _pct(prob, "")
        items.append(
            f'<span class="ticker-item">'
            f'<span class="league">{_esc(r.get("league"))}</span>'
            f'<span class="teams">{_esc(r.get("home"))} v {_esc(r.get("away"))}</span>'
            f'<span class="text-muted">{html.escape(lean)} {p_str}</span>'
            f'</span>'
        )
    if not items:
        return ""
    doubled = "".join(items * 2)  # duplicate for seamless loop
    return f'<div class="ticker-strip"><div class="ticker-inner">{doubled}</div></div>'


def _render_featured_tickets(slips: dict) -> str:
    if not slips:
        return "<div class='empty'>No active slips.</div>"

    preferred = [
        name for name in slips
        if name.startswith("HUNDRED_K")
    ][:3]
    for name in ("VALUE", "SAFE", "ONE_CEDI_DREAM"):
        if name in slips and name not in preferred:
            preferred.append(name)
    preferred = preferred[:4]

    rows = []
    for name in preferred:
        stats = slips[name]["stats"]
        ev = stats.get("expected_value_per_unit")
        ev_text = f"{ev:+.3f}" if ev is not None and not (isinstance(ev, float) and math.isnan(ev)) else "—"
        rows.append(f"""
        <div class="ticket-mini">
          <div>
            <strong>{html.escape(_slip_title(name))}</strong>
            <div class="ticket-meta">{stats.get('legs', 0)} legs · P {_pct(stats.get('combined_prob'))} · EV {ev_text}</div>
          </div>
          <div class="ticket-odds">{_odds(stats.get('combined_market_odds') or stats.get('combined_fair_odds'))}</div>
        </div>""")
    return "".join(rows)


def _render_market_board(football: pd.DataFrame, basketball: pd.DataFrame) -> str:
    try:
        from . import slip_builder
    except Exception:  # noqa: BLE001
        return ""

    frames = [
        df.dropna(axis=1, how="all")
        for df in (football, basketball)
        if df is not None and not df.empty
    ]
    if not frames:
        return ""

    pool = slip_builder.build_candidate_pool(pd.concat(frames, ignore_index=True, sort=False))
    if pool.empty:
        return ""

    tiles = []
    top = pool.sort_values(["prob", "fair_odds"], ascending=[False, True]).head(8)
    for _, r in top.iterrows():
        tiles.append(f"""
        <article class="market-tile">
          <div class="market-name">{_esc(r.get('market'))}</div>
          <div class="market-pick">{_esc(r.get('pick'))}</div>
          <div class="market-match">{_esc(r.get('match'))}</div>
          <div class="market-prob">{_pct(r.get('prob'))}</div>
        </article>""")

    return f"""
    <section class="market-board">
      <h3>Market Radar</h3>
      <div class="market-grid">{"".join(tiles)}</div>
    </section>"""


# ──────────────────────────────────────────────────────────────────────────────
# Overview tab
# ──────────────────────────────────────────────────────────────────────────────

def _render_overview(football: pd.DataFrame, basketball: pd.DataFrame, slips: dict, bankroll: dict, kelly: dict) -> str:
    n_slips  = len(slips)
    total_fx = len(football) + len(basketball)

    # best value EV
    best_ev = None
    for sd in slips.values():
        ev = sd["stats"].get("expected_value_per_unit")
        if ev is not None and not (isinstance(ev, float) and math.isnan(ev)):
            if best_ev is None or ev > best_ev:
                best_ev = ev
    ev_str   = f"{best_ev:+.3f}" if best_ev is not None else "—"
    ev_cls   = "text-green" if (best_ev or 0) > 0 else "text-red"
    bal      = bankroll.get("current_balance", 100.0)
    start    = bankroll.get("starting_capital", 100.0)
    pnl      = bal - start
    pnl_pct  = (pnl / start * 100)
    pnl_cls  = "text-green" if pnl >= 0 else "text-red"

    # headline stats
    stats_html = f"""
    <div class="stat-grid">
      <div class="stat-card green-accent">
        <div class="stat-label">Balance</div>
        <div class="stat-value {pnl_cls}">{_money(bal)}</div>
        <div class="stat-sub">started at {_money(start)}</div>
      </div>
      <div class="stat-card gold-accent">
        <div class="stat-label">Net P&L</div>
        <div class="stat-value {pnl_cls}">{'+' if pnl >= 0 else ''}{_money(pnl)}</div>
        <div class="stat-sub">{'+' if pnl_pct >= 0 else ''}{pnl_pct:.1f}% return</div>
      </div>
      <div class="stat-card blue-accent">
        <div class="stat-label">Fixtures</div>
        <div class="stat-value">{total_fx}</div>
        <div class="stat-sub">{len(football)} football · {len(basketball)} basketball</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Best EV</div>
        <div class="stat-value {ev_cls}">{ev_str}</div>
        <div class="stat-sub">{n_slips} slip variant{'s' if n_slips != 1 else ''}</div>
      </div>
    </div>
    """

    # fixture ticker cards
    all_rows = []
    for _, r in football.head(8).iterrows():
        lean, prob = _football_lean(r)
        all_rows.append({"date": r.get("date"), "league": r.get("league"),
                         "sport": "Football", "home": r.get("home"), "away": r.get("away"),
                         "lean": lean, "prob": prob})
    for _, r in basketball.head(8).iterrows():
        lean, prob = _basketball_lean(r)
        all_rows.append({"date": r.get("date"), "league": r.get("league"),
                         "sport": "Basketball", "home": r.get("home"), "away": r.get("away"),
                         "lean": lean, "prob": prob})
    all_rows.sort(key=lambda x: pd.to_datetime(x["date"], errors="coerce") if x["date"] else pd.Timestamp.max)

    cards = []
    for item in all_rows[:14]:
        time_str = _time_label(item["date"])
        when     = _date_label(item["date"]) + (f" {time_str}" if time_str else "")
        cards.append(f"""
        <article class="match-card">
          <div class="match-card-top">
            <span class="league-tag">{_esc(item['league'])}</span>
            <span class="match-time">{html.escape(when)}</span>
          </div>
          <div class="match-teams">
            <div class="team">{_esc(item['home'])}</div>
            <div class="vs">vs</div>
            <div class="team">{_esc(item['away'])}</div>
          </div>
          <div class="match-lean">
            <span class="lean-pick">{_esc(item['lean'])}</span>
            <span class="lean-prob">{_pct(item['prob'])}</span>
          </div>
        </article>""")
    ticker = f'<div class="fixture-ticker">{"".join(cards)}</div>' if cards else '<div class="empty">No fixtures in window.</div>'
    market_board = _render_market_board(football, basketball)
    featured = _render_featured_tickets(slips)

    return f"""
    <section class="bet-hero">
      <div class="bet-hero-main">
        <div class="hero-kicker">Model board · {_date_range(football, basketball)}</div>
        <div class="hero-title">Find the best route through today’s slate.</div>
        <div class="hero-copy">Prioritized slips, high-confidence markets, live fixture windows, and bankroll context are grouped into one betting desk.</div>
        <div class="hero-actions">
          <button class="hero-btn primary" onclick="showTab('tab-slips')" type="button">View Slips</button>
          <button class="hero-btn" onclick="showTab('tab-football')" type="button">Football Board</button>
          <button class="hero-btn" onclick="showTab('tab-bankroll')" type="button">Bankroll</button>
        </div>
      </div>
      <aside class="bet-hero-side">
        <h3>Featured Tickets</h3>
        <div class="ticket-stack">{featured}</div>
      </aside>
    </section>
    {market_board}
    <div class="section-head"><div><h2>Desk Snapshot</h2><div class="hint">{_date_range(football, basketball)}</div></div></div>
    {stats_html}
    <div class="section-head"><div><h2>Upcoming fixtures</h2></div></div>
    {ticker}
    """


# ──────────────────────────────────────────────────────────────────────────────
# Slips tab
# ──────────────────────────────────────────────────────────────────────────────

def _render_slip_card(variant: str, slip: dict, kelly_info: dict) -> str:
    legs: pd.DataFrame = slip["legs"]
    stats = slip["stats"]
    ev    = stats.get("expected_value_per_unit")
    ev_str = f"{ev:+.3f}" if ev is not None and not (isinstance(ev, float) and math.isnan(ev)) else "—"
    ev_cls = "text-green" if (ev or 0) > 0 else "text-red"
    mk_odds = stats.get("combined_market_odds")
    target_payout = stats.get("target_payout")

    stake   = kelly_info.get("recommended_stake", 0)
    payout  = kelly_info.get("potential_payout", 0)
    edge    = kelly_info.get("edge", 0)
    capped  = kelly_info.get("capped", False)
    stake_label = kelly_info.get("stake_label", "Kelly Stake")

    stake_str  = _money(stake) if stake > 0 else "—"
    payout_str = _money(payout) if payout > 0 else "—"
    edge_pct   = f"{edge*100:+.1f}%" if edge else "—"
    target_hint = ""
    if target_payout and mk_odds:
        target_hint = f" · target {_money(target_payout)}"

    # build log_bet command stub
    leg_picks = "|".join(
        f"{r.get('match','?')}:{r.get('pick','?')}"
        for _, r in legs.iterrows()
    )
    log_cmd = (
        f"python log_result.py --log --slip {variant} "
        f"--stake {stake:.2f} --odds {stats.get('combined_market_odds') or stats.get('combined_fair_odds'):.2f}"
        if stake > 0 else ""
    )

    # kelly banner
    kelly_html = ""
    if stake > 0:
        capped_note = " <span style='font-size:.7rem;color:var(--muted)'>(capped)</span>" if capped else ""
        kelly_html = f"""
        <div class="kelly-banner">
          <div class="kelly-left">
            <div class="kl">{html.escape(stake_label)}{capped_note}</div>
            <div class="ks">{stake_str}</div>
          </div>
          <div class="kelly-right">
            <div class="kl">Potential Payout</div>
            <div class="ks">{payout_str}</div>
          </div>
        </div>"""

    # copy command
    cmd_html = ""
    if log_cmd:
        cmd_html = f"""
        <div class="copy-cmd">
          <code>{html.escape(log_cmd)}</code>
          <button class="copy-btn" onclick="copyText('{html.escape(log_cmd)}', this)">Copy</button>
        </div>"""

    # table rows
    rows_html = []
    for _, r in legs.iterrows():
        edge_v = r.get("edge")
        e_str  = f"{float(edge_v)*100:+.1f}%" if pd.notna(edge_v) else "—"
        e_cls  = "edge-pos" if pd.notna(edge_v) and float(edge_v) > 0 else "edge-neg"
        sport  = str(r.get("sport", "")).title()
        rows_html.append(
            f"<tr>"
            f"<td><span class='sport-pill'>{html.escape(sport)}</span></td>"
            f"<td class='match-col'>{_esc(r.get('match'))}<span class='row-sub'>{_esc(r.get('league'))}</span></td>"
            f"<td><span class='market-pill'>{_esc(r.get('market'))}</span></td>"
            f"<td style='font-weight:700'>{_esc(r.get('pick'))}</td>"
            f"<td class='num text-green'>{_pct(r.get('prob'))}</td>"
            f"<td class='num'>{_odds(r.get('fair_odds'))}</td>"
            f"<td class='num'>{_odds(r.get('market_odds'))}</td>"
            f"<td class='num {e_cls}'>{e_str}</td>"
            f"</tr>"
        )

    card_extra = ""
    if variant == "VALUE":
        card_extra = " value-card"
    elif variant == "SAFE":
        card_extra = " safe-card"
    elif variant == "ONE_CEDI_DREAM" or variant.startswith("HUNDRED_K"):
        card_extra = " dream-card"

    return f"""
    <article class="slip-card{card_extra}">
      <div class="slip-header">
        <div class="slip-title-row">
          {_slip_badge(variant)}
          <span class="slip-name">{html.escape(_slip_title(variant))}</span>
        </div>
        <span style="color:var(--muted);font-size:.82rem">{stats['legs']} legs{target_hint}</span>
      </div>
      <div class="slip-stats-row">
        <div class="slip-stat-cell"><div class="lbl">Comb. Prob</div><div class="val text-green">{_pct(stats['combined_prob'])}</div></div>
        <div class="slip-stat-cell"><div class="lbl">Fair Odds</div><div class="val">{_odds(stats['combined_fair_odds'])}</div></div>
        <div class="slip-stat-cell"><div class="lbl">Market Odds</div><div class="val">{_odds(mk_odds)}</div></div>
        <div class="slip-stat-cell"><div class="lbl">EV / unit</div><div class="val {ev_cls}">{ev_str}</div></div>
      </div>
      {kelly_html}
      {cmd_html}
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Sport</th><th>Match</th><th>Market</th><th>Pick</th>
            <th>Prob</th><th>Fair</th><th>Odds</th><th>Edge</th>
          </tr></thead>
          <tbody>{"".join(rows_html)}</tbody>
        </table>
      </div>
    </article>"""


def _render_slips(slips: dict, kelly: dict) -> str:
    if not slips:
        return "<div class='empty'>No slip variants available. Widen lookahead_days or check data freshness.</div>"
    cards = [_render_slip_card(name, slip, kelly.get(name, {})) for name, slip in slips.items()]
    return f'<div class="slip-grid">{"".join(cards)}</div>'


# ──────────────────────────────────────────────────────────────────────────────
# Bankroll tab
# ──────────────────────────────────────────────────────────────────────────────

def _render_bankroll(bk: dict) -> str:
    start   = bk.get("starting_capital", 100.0)
    balance = bk.get("current_balance", 100.0)
    goal    = 1_000_000.0

    # log-scale progress
    try:
        pct = math.log(max(balance, start) / start) / math.log(goal / start) * 100
        pct = max(0.0, min(100.0, pct))
    except Exception:
        pct = 0.0

    pnl     = balance - start
    pnl_cls = "text-green" if pnl >= 0 else "text-red"
    roi     = bk.get("roi_pct", 0.0)
    hit     = bk.get("hit_rate_pct", 0.0)

    hero = f"""
    <div class="bankroll-hero">
      <div class="bankroll-numbers">
        <div class="bankroll-main">
          <div class="label">Current Balance</div>
          <div class="amount">{_money(balance)}</div>
        </div>
        <div class="bankroll-secondary">
          <div class="bk-stat">
            <div class="label">Net Profit</div>
            <div class="val {pnl_cls}">{'+' if pnl >= 0 else ''}{_money(pnl)}</div>
          </div>
          <div class="bk-stat">
            <div class="label">ROI</div>
            <div class="val {pnl_cls}">{'+' if roi >= 0 else ''}{roi:.2f}%</div>
          </div>
          <div class="bk-stat">
            <div class="label">Hit Rate</div>
            <div class="val">{hit:.1f}%</div>
          </div>
          <div class="bk-stat">
            <div class="label">Bets (W/L)</div>
            <div class="val">{bk.get('resolved_bets', 0)} ({bk.get('wins', 0)}/{bk.get('losses', 0)})</div>
          </div>
          <div class="bk-stat">
            <div class="label">Pending</div>
            <div class="val text-gold">{bk.get('pending_bets', 0)}</div>
          </div>
        </div>
      </div>
      <div class="progress-section">
        <div class="progress-labels">
          <span><strong>{_money(start)}</strong> start</span>
          <span>Goal: <strong>{_money(goal)}</strong></span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width:{pct:.3f}%"></div>
        </div>
        <div class="progress-pct">Journey progress (log scale): <strong>{pct:.3f}%</strong></div>
      </div>
    </div>"""

    # stats grid
    stats_html = f"""
    <div class="stat-grid">
      <div class="stat-card green-accent">
        <div class="stat-label">Total Staked</div>
        <div class="stat-value">{_money(bk.get('total_staked', 0))}</div>
        <div class="stat-sub">across resolved bets</div>
      </div>
      <div class="stat-card gold-accent">
        <div class="stat-label">Total Returned</div>
        <div class="stat-value">{_money(bk.get('total_returned', 0))}</div>
        <div class="stat-sub">winnings before stake</div>
      </div>
      <div class="stat-card blue-accent">
        <div class="stat-label">Total Bets</div>
        <div class="stat-value">{bk.get('total_bets', 0)}</div>
        <div class="stat-sub">{bk.get('pending_bets', 0)} pending</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Balance Δ</div>
        <div class="stat-value {pnl_cls}">{'+' if (bk.get('balance_change_pct',0) >= 0) else ''}{bk.get('balance_change_pct', 0):.2f}%</div>
        <div class="stat-sub">vs starting capital</div>
      </div>
    </div>"""

    # pending bets — actionable section
    pending = bk.get("pending", [])
    pending_html = ""
    if pending:
        cards = []
        for b in pending:
            legs = b.get("legs") or []
            legs_html = "".join(
                f'<div class="pending-leg"><strong>{html.escape(str(lg.get("pick","?")))}</strong> — {html.escape(str(lg.get("match","?")))}'
                f' <span style="color:var(--muted)">({html.escape(str(lg.get("market","?")))})</span></div>'
                for lg in legs
            ) or '<div class="pending-leg text-muted">Manually logged bet</div>'

            win_cmd  = f"python log_result.py --id {b['id']} --outcome WIN"
            loss_cmd = f"python log_result.py --id {b['id']} --outcome LOSS"
            void_cmd = f"python log_result.py --id {b['id']} --outcome VOID"

            cards.append(f"""
            <div class="pending-card">
              <div class="pending-head">
                <div style="display:flex;align-items:center;gap:10px">
                  <span class="pending-id">{b['id']}</span>
                  {_slip_badge(b.get('slip_type','?'))}
                  <span class="badge badge-pending">Pending</span>
                </div>
                <div style="font-size:.8rem;color:var(--muted)">{b.get('date','')} · stake {_money(b.get('stake'))} · odds {_odds(b.get('combined_odds'))}</div>
              </div>
              <div class="pending-body">
                <div class="pending-legs">{legs_html}</div>
                <div class="log-commands">
                  <button class="log-cmd-btn win"  onclick="logResult('{b['id']}','WIN')">✓ Win</button>
                  <button class="log-cmd-btn loss" onclick="logResult('{b['id']}','LOSS')">✗ Loss</button>
                  <button class="log-cmd-btn void" onclick="logResult('{b['id']}','VOID')">↩ Void</button>
                  <button class="copy-btn" onclick="copyText('{html.escape(win_cmd)}', this)" style="margin-left:auto">Copy WIN cmd</button>
                </div>
              </div>
            </div>""")
        pending_html = f"""
        <div class="section-head"><div><h2>Pending bets</h2><div class="hint">Click a button to copy the log command — paste it in your terminal</div></div></div>
        {"".join(cards)}"""
    else:
        pending_html = ""

    # bet history table
    recent = bk.get("recent_bets", [])
    if recent:
        rows = []
        for b in recent:
            outcome    = b.get("outcome")
            payout     = b.get("payout")
            pnl_b      = (payout or 0) - b.get("stake", 0) if outcome in ("WIN","LOSS") else None
            pnl_str    = (f"{'+' if (pnl_b or 0) >= 0 else ''}{_money(pnl_b)}"
                          if pnl_b is not None else "—")
            pnl_c      = "text-green" if (pnl_b or 0) > 0 else ("text-red" if (pnl_b or 0) < 0 else "")
            rows.append(
                f"<tr>"
                f"<td class='num text-muted'>{html.escape(str(b.get('date','?')))}</td>"
                f"<td><code style='font-size:.78rem;color:var(--muted2)'>{b['id']}</code></td>"
                f"<td>{_slip_badge(b.get('slip_type','?'))}</td>"
                f"<td class='num'>{_money(b.get('stake'))}</td>"
                f"<td class='num'>{_odds(b.get('combined_odds'))}</td>"
                f"<td class='num'>{_money(payout) if payout is not None else '—'}</td>"
                f"<td class='num {pnl_c}'>{pnl_str}</td>"
                f"<td>{_outcome_badge(outcome)}</td>"
                f"</tr>"
            )
        history_html = f"""
        <div class="section-head"><div><h2>Bet history</h2><div class="hint">Most recent 20 bets</div></div></div>
        <div class="full-table">
          <div class="table-wrap">
            <table class="bet-log-table">
              <thead><tr>
                <th>Date</th><th>ID</th><th>Slip</th><th>Stake</th>
                <th>Odds</th><th>Payout</th><th>P&amp;L</th><th>Result</th>
              </tr></thead>
              <tbody>{"".join(rows)}</tbody>
            </table>
          </div>
        </div>"""
    else:
        history_html = """
        <div class="section-head"><div><h2>Bet history</h2></div></div>
        <div class="empty">No bets logged yet. Run <code>python log_result.py --log --slip VALUE --stake 5 --odds 3.20</code> to log your first bet.</div>"""

    return f"""
    <div class="section-head"><div><h2>Bankroll tracker</h2><div class="hint">GHS 100 -> GHS 1,000,000 goal</div></div></div>
    {hero}
    {stats_html}
    {pending_html}
    {history_html}"""


# ──────────────────────────────────────────────────────────────────────────────
# Football / Basketball prediction tables
# ──────────────────────────────────────────────────────────────────────────────

def _render_football(df: pd.DataFrame) -> str:
    if df.empty:
        return "<div class='empty'>No football fixtures in the current window.</div>"
    rows = []
    for _, r in df.iterrows():
        lean, lp = _football_lean(r)
        time_s   = _time_label(r.get("date"))
        date_s   = _date_label(r.get("date")) + (f" {time_s}" if time_s else "")
        total_pack = (
            f"O1.5 {_pct(r.get('p_over15'))}"
            f"<span class='row-sub'>O2.5 {_pct(r.get('p_over25'))} · U3.5 {_pct(r.get('p_under35'))}</span>"
        )
        double_chance = max(
            [
                ("1X", r.get("p_home_or_draw")),
                ("X2", r.get("p_away_or_draw")),
                ("12", r.get("p_home_or_away")),
            ],
            key=lambda item: float(item[1]) if item[1] is not None and not (isinstance(item[1], float) and math.isnan(item[1])) else -1,
        )
        team_goal = max(
            [
                (f"{r.get('home')} 0.5+", r.get("p_home_over05")),
                (f"{r.get('away')} 0.5+", r.get("p_away_over05")),
                (f"{r.get('home')} 1.5+", r.get("p_home_over15")),
                (f"{r.get('away')} 1.5+", r.get("p_away_over15")),
            ],
            key=lambda item: float(item[1]) if item[1] is not None and not (isinstance(item[1], float) and math.isnan(item[1])) else -1,
        )
        rows.append(
            "<tr>"
            f"<td class='num'>{html.escape(date_s)}</td>"
            f"<td><span class='sport-pill'>{_esc(r.get('league'))}</span></td>"
            f"<td class='match-col'>{_esc(r.get('home'))}<span class='row-sub'>vs {_esc(r.get('away'))}</span></td>"
            f"<td class='num'>{_num(r.get('lambda_home'),2)} – {_num(r.get('lambda_away'),2)}</td>"
            f"<td><strong>{html.escape(lean)}</strong><span class='row-sub'>{_pct(lp)}</span></td>"
            f"<td class='num'>{_pct(r.get('p_home'))} / {_pct(r.get('p_draw'))} / {_pct(r.get('p_away'))}</td>"
            f"<td class='num text-green'><strong>{html.escape(double_chance[0])}</strong><span class='row-sub'>{_pct(double_chance[1])}</span></td>"
            f"<td class='num'>{total_pack}</td>"
            f"<td class='num'>{_pct(r.get('p_btts'))}</td>"
            f"<td class='num'><strong>{_esc(team_goal[0])}</strong><span class='row-sub'>{_pct(team_goal[1])}</span></td>"
            f"<td class='num'>{_esc(r.get('top1_score'))}<span class='row-sub'>{_pct(r.get('top1_prob'))}</span></td>"
            f"<td class='num'>{_pct(r.get('confidence_gap'))}</td>"
            f"<td class='num'>{_odds(r.get('odds_home'))} / {_odds(r.get('odds_draw'))} / {_odds(r.get('odds_away'))}</td>"
            "</tr>"
        )
    return f"""
    <div class="full-table">
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Date</th><th>League</th><th>Match</th><th>xG</th><th>Lean</th>
            <th>1X2</th><th>Double</th><th>Totals</th><th>BTTS</th><th>Team Goal</th>
            <th>Top Score</th><th>Gap</th><th>Odds H/D/A</th>
          </tr></thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </div>"""


def _render_basketball(df: pd.DataFrame) -> str:
    if df.empty:
        return "<div class='empty'>No NBA or EuroLeague fixtures in the current window.</div>"
    rows = []
    for _, r in df.iterrows():
        lean, lp = _basketball_lean(r)
        time_s   = _time_label(r.get("date"))
        date_s   = _date_label(r.get("date")) + (f" {time_s}" if time_s else "")
        spread   = "—"
        if pd.notna(r.get("spread_home")):
            sign = "+" if float(r["spread_home"]) > 0 else ""
            spread = f"{sign}{float(r['spread_home']):.1f} ({_pct(r.get('p_home_cover'))})"
        total = "—"
        if pd.notna(r.get("total_line")):
            total = f"{_num(r.get('total_line'),1)} · over {_pct(r.get('p_over_total'))}"
        rows.append(
            "<tr>"
            f"<td class='num'>{html.escape(date_s)}</td>"
            f"<td><span class='sport-pill'>{_esc(r.get('league'))}</span></td>"
            f"<td class='match-col'>{_esc(r.get('home'))}<span class='row-sub'>vs {_esc(r.get('away'))}</span></td>"
            f"<td class='num'>{_num(r.get('pred_home_score'),1)} – {_num(r.get('pred_away_score'),1)}</td>"
            f"<td><strong>{html.escape(lean)}</strong><span class='row-sub'>{_pct(lp)}</span></td>"
            f"<td class='num'>{_pct(r.get('p_home'))} / {_pct(r.get('p_away'))}</td>"
            f"<td class='num'>{html.escape(spread)}</td>"
            f"<td class='num'>{html.escape(total)}</td>"
            "</tr>"
        )
    return f"""
    <div class="full-table">
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Date</th><th>League</th><th>Match</th><th>Projection</th>
            <th>Lean</th><th>H / A</th><th>Spread</th><th>Total</th>
          </tr></thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </div>"""


# ──────────────────────────────────────────────────────────────────────────────
# Accuracy / community tabs
# ──────────────────────────────────────────────────────────────────────────────

def _metric_text(metric: dict) -> tuple[str, str]:
    total = int(metric.get("total") or 0)
    correct = int(metric.get("correct") or 0)
    accuracy = metric.get("accuracy")
    if not total or accuracy is None:
        return "—", "0 tracked"
    return f"{accuracy:.1f}%", f"{correct}/{total} correct"

def _result_cell(value) -> str:
    if value is None or (not isinstance(value, bool) and pd.isna(value)):
        return '<span class="result-na">—</span>'
    if bool(value):
        return '<span class="result-ok">Correct</span>'
    return '<span class="result-bad">Miss</span>'

def _render_accuracy(accuracy: dict | None) -> str:
    if not accuracy:
        return "<div class='empty'>No accuracy data yet. Run the predictor after tracked fixtures have final scores.</div>"
    summary = accuracy.get("summary", {})
    rows = accuracy.get("rows", [])

    main_v, main_sub = _metric_text(summary.get("main", {}))
    football_v, football_sub = _metric_text(summary.get("football_main", {}))
    basketball_v, basketball_sub = _metric_text(summary.get("basketball_main", {}))
    totals_v, totals_sub = _metric_text(summary.get("football_totals", {}))

    stats = f"""
    <div class="stat-grid">
      <div class="stat-card green-accent">
        <div class="stat-label">Main Lean</div>
        <div class="stat-value text-green">{main_v}</div>
        <div class="stat-sub">{main_sub}</div>
      </div>
      <div class="stat-card blue-accent">
        <div class="stat-label">Football 1X2</div>
        <div class="stat-value">{football_v}</div>
        <div class="stat-sub">{football_sub}</div>
      </div>
      <div class="stat-card gold-accent">
        <div class="stat-label">Basketball ML</div>
        <div class="stat-value">{basketball_v}</div>
        <div class="stat-sub">{basketball_sub}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Football Totals</div>
        <div class="stat-value">{totals_v}</div>
        <div class="stat-sub">{totals_sub}</div>
      </div>
    </div>
    """

    if not rows:
        return stats + "<div class='empty'>No completed tracked fixtures yet.</div>"

    html_rows = []
    for r in rows:
        date_s = _date_label(r.get("date"))
        total_result = r.get("total_correct")
        side_prob = r.get("main_prob")
        side_prob_s = _pct(side_prob) if side_prob is not None else "—"
        extras = []
        if r.get("total_pick"):
            extras.append(f"{_esc(r.get('total_pick'))} {_result_cell(total_result)}")
        if r.get("btts_pick"):
            extras.append(f"{_esc(r.get('btts_pick'))} {_result_cell(r.get('btts_correct'))}")
        if r.get("spread_pick"):
            extras.append(f"{_esc(r.get('spread_pick'))} {_result_cell(r.get('spread_correct'))}")
        if r.get("scoreline_pick"):
            extras.append(f"Score {_esc(r.get('scoreline_pick'))} {_result_cell(r.get('scoreline_correct'))}")
        extra_html = "<br>".join(extras) if extras else "—"
        html_rows.append(
            "<tr>"
            f"<td class='num'>{html.escape(date_s)}</td>"
            f"<td><span class='sport-pill'>{_esc(r.get('sport'))}</span><span class='row-sub'>{_esc(r.get('league'))}</span></td>"
            f"<td class='match-col'>{_esc(r.get('home'))}<span class='row-sub'>vs {_esc(r.get('away'))}</span></td>"
            f"<td class='num'>{_esc(r.get('score'))}</td>"
            f"<td><strong>{_esc(r.get('main_pick'))}</strong><span class='row-sub'>{side_prob_s}</span></td>"
            f"<td>{_esc(r.get('main_result'))}</td>"
            f"<td>{_result_cell(r.get('main_correct'))}</td>"
            f"<td>{extra_html}</td>"
            "</tr>"
        )

    return stats + f"""
    <div class="full-table">
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Date</th><th>Sport</th><th>Match</th><th>Score</th>
            <th>Main Pick</th><th>Result</th><th>Main</th><th>Other Markets</th>
          </tr></thead>
          <tbody>{"".join(html_rows)}</tbody>
        </table>
      </div>
    </div>"""


def _render_community(community: dict | None) -> str:
    ttl = int((community or {}).get("ttl_hours") or 24)
    scope = "Community board" if (community or {}).get("endpoint") else "Browser-local board"
    return f"""
    <div class="section-head">
      <div><h2>Community codes</h2><div class="hint">{html.escape(scope)} · {ttl}h TTL</div></div>
    </div>
    <form class="code-form" id="community-form">
      <div class="code-form-grid">
        <div class="field">
          <label for="community-code">Code</label>
          <input id="community-code" name="code" autocomplete="off" maxlength="80" required>
        </div>
        <div class="field">
          <label for="community-odds">Odds</label>
          <input id="community-odds" name="odds" autocomplete="off" maxlength="20">
        </div>
        <div class="field">
          <label for="community-note">Note</label>
          <input id="community-note" name="note" autocomplete="off" maxlength="120">
        </div>
        <button class="submit-btn" type="submit">Add Code</button>
      </div>
      <div class="status-line" id="community-status"></div>
    </form>
    <div class="full-table">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Added</th><th>Code</th><th>Odds</th><th>Note</th></tr></thead>
          <tbody id="community-code-rows"></tbody>
        </table>
      </div>
    </div>
    <div class="empty" id="community-empty">No active codes yet.</div>
    """


# ──────────────────────────────────────────────────────────────────────────────
# Main render
# ──────────────────────────────────────────────────────────────────────────────

def render(
    football: pd.DataFrame,
    basketball: pd.DataFrame,
    slips: dict,
    run_ts: datetime,
    bankroll: dict | None = None,
    kelly: dict | None = None,
    accuracy: dict | None = None,
    community: dict | None = None,
) -> str:
    if bankroll is None:
        bankroll = {"starting_capital": 100.0, "current_balance": 100.0, "bets": [],
                    "pending": [], "recent_bets": [], "total_bets": 0, "resolved_bets": 0,
                    "pending_bets": 0, "wins": 0, "losses": 0, "total_staked": 0,
                    "total_returned": 0, "net_profit": 0, "roi_pct": 0, "hit_rate_pct": 0,
                    "balance_change_pct": 0}
    if kelly is None:
        kelly = {}
    if community is None:
        community = {}

    date_range  = _date_range(football, basketball)
    total_fx    = len(football) + len(basketball)
    balance     = bankroll.get("current_balance", 100.0)
    pending_n   = bankroll.get("pending_bets", 0)
    community_enabled = bool(community.get("enabled", True))
    community_cfg = {
        "endpoint": community.get("endpoint") or "",
        "ttl_hours": int(community.get("ttl_hours") or 24),
    }
    community_tab_button = ""
    community_panel = ""
    if community_enabled:
        community_tab_button = (
            '<button class="nav-tab" data-tab="tab-community" aria-selected="false" '
            'onclick="showTab(\'tab-community\')" type="button">'
            '<span class="tab-icon">🧾</span>Community Codes</button>'
        )
        community_panel = f'<div id="tab-community" class="panel">{_render_community(community)}</div>'

    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PredictorPro — {date_range}</title>
{CSS}
<script>window.PREDICTOR_COMMUNITY = {json.dumps(community_cfg)};</script>
{JS}
</head>
<body>

<header class="header">
  <div class="header-inner">
    <div class="header-top">
      <div class="brand">
        <div class="brand-icon">PP</div>
        <div>
          <div class="brand-name">PredictorPro</div>
          <div class="brand-sub">Sports predictions desk</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <div class="live-badge"><div class="live-dot"></div>Live</div>
      </div>
    </div>
    <div class="header-title">Betting Command Center</div>
    <div class="header-sub">Slip strategy, market radar, odds checks, bankroll, and fixture intelligence</div>
    <div class="pills-row">
      <span class="pill">Run <strong>{run_ts.strftime('%d %b %Y %H:%M')}</strong></span>
      <span class="pill">Window <strong>{html.escape(date_range)}</strong></span>
      <span class="pill"><strong>{total_fx}</strong> fixtures</span>
      <span class="pill"><strong>{len(slips)}</strong> slips</span>
      <span class="pill green">Balance <strong>{_money(balance)}</strong></span>
      {f'<span class="pill" style="background:rgba(245,158,11,.1);border-color:rgba(245,158,11,.3);color:var(--gold)"><strong>{pending_n}</strong> pending bet{"s" if pending_n != 1 else ""}</span>' if pending_n else ''}
    </div>
  </div>
  {_ticker_html(football, basketball)}
</header>

<main class="shell">
  <nav class="nav-tabs" aria-label="Sections">
    <button class="nav-tab" data-tab="tab-overview"   aria-selected="true"  onclick="showTab('tab-overview')"   type="button"><span class="tab-icon">📊</span>Overview</button>
    <button class="nav-tab" data-tab="tab-slips"      aria-selected="false" onclick="showTab('tab-slips')"      type="button"><span class="tab-icon">🎯</span>Slips &amp; Stakes</button>
    <button class="nav-tab" data-tab="tab-bankroll"   aria-selected="false" onclick="showTab('tab-bankroll')"   type="button"><span class="tab-icon">💰</span>Bankroll{f' <span class="badge badge-pending" style="margin-left:4px">{pending_n}</span>' if pending_n else ''}</button>
    <button class="nav-tab" data-tab="tab-accuracy"   aria-selected="false" onclick="showTab('tab-accuracy')"   type="button"><span class="tab-icon">✅</span>Accuracy</button>
    <button class="nav-tab" data-tab="tab-football"   aria-selected="false" onclick="showTab('tab-football')"   type="button"><span class="tab-icon">⚽</span>Football</button>
    <button class="nav-tab" data-tab="tab-basketball" aria-selected="false" onclick="showTab('tab-basketball')" type="button"><span class="tab-icon">🏀</span>Basketball</button>
    {community_tab_button}
  </nav>

  <div id="tab-overview"   class="panel active">{_render_overview(football, basketball, slips, bankroll, kelly)}</div>
  <div id="tab-slips"      class="panel">{_render_slips(slips, kelly)}</div>
  <div id="tab-bankroll"   class="panel">{_render_bankroll(bankroll)}</div>
  <div id="tab-accuracy"   class="panel">
    <div class="section-head"><div><h2>Prediction accuracy</h2><div class="hint">Completed tracked fixtures · scores joined from source data</div></div></div>
    {_render_accuracy(accuracy)}
  </div>
  <div id="tab-football"   class="panel">
    <div class="section-head"><div><h2>Football predictions</h2><div class="hint">1X2 · double chance · totals ladder · BTTS · team goals · top scoreline</div></div></div>
    {_render_football(football)}
  </div>
  <div id="tab-basketball" class="panel">
    <div class="section-head"><div><h2>NBA &amp; EuroLeague</h2><div class="hint">Moneyline · projected score · spread · total</div></div></div>
    {_render_basketball(basketball)}
  </div>
  {community_panel}

  <footer>
    PredictorPro — football Elo + Dixon-Coles Poisson · basketball Elo + normal model
    · data: football-data.co.uk, ESPN, EuroLeague API · fractional Kelly staking ·
    <strong>For analysis only — not betting advice.</strong>
  </footer>
</main>

<div class="toast" id="toast"></div>
</body></html>"""
    return "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
