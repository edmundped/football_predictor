# football_predictor

Run-and-use daily football and basketball predictor. No API keys, no accounts. Football scrapes free CSVs from [football-data.co.uk](https://www.football-data.co.uk/). Basketball uses ESPN's public NBA scoreboard and the EuroLeague live API. The report builds per-sport predictions plus consolidated daily slip (accumulator) variants.

## Quick start

```bash
pip install -r requirements.txt
python run.py
```

Outputs land in `docs/`:
- `index.html` — opens in any browser and is ready for GitHub Pages. Full report: consolidated slip variants plus football and basketball prediction tabs.
- `predictions.csv` — consolidated football + basketball prediction export. This is overwritten on every run.

Accuracy history is kept privately in `data/prediction_history.csv`; only the summary is rendered to the public report.

## What the tool does

1. Downloads historical match CSVs + current-season fixtures for the leagues in `config.yaml`. First run can take about a minute with the expanded league list; afterwards it's cached for 6 hours.
2. Walks every match in history to build goal-weighted Elo ratings per team.
3. For each upcoming fixture in the next `lookahead_days` days: converts Elo gap + league baseline into expected goals, then runs a Dixon-Coles Poisson model to get probabilities for home/draw/away, over/under 2.5, BTTS, and top scorelines.
4. Downloads basketball results/fixtures for NBA and EuroLeague, fits a recent-results basketball Elo, then predicts moneyline plus spread/total probabilities where market lines are available.
5. Builds five consolidated slip variants from the predictions:
   - **SAFE** — short accumulator, each leg > 72% probability.
   - **BALANCED** — mid-length, each leg > 60%.
   - **AGGRESSIVE** — longer accumulator, each leg > 50%, higher payout.
   - **ONE_CEDI_DREAM** — priced accumulator from the consolidated pool, aiming for combined market odds of 100+.
   - **VALUE** — only when market odds are present in the source data: picks where model probability exceeds market implied probability by at least 5%. Sorted by edge, not raw probability.
6. Stores a private prediction history and joins later scores back to prior predictions for the Accuracy tab.
7. Renders a self-contained HTML report.

One-pick-per-fixture is enforced across all slips so the independence assumption behind combined probability is at least defensible.

## Configuration

Edit `config.yaml`:

- `leagues` — league codes from football-data.co.uk. Defaults now include the big five, English Championship/League One/League Two, major second divisions, Eredivisie, Primeira Liga, Jupiler League, Super Lig, Greek Super League, and Scottish Premiership.
- `current_season` — e.g. `"2526"` for 2025-26.
- `history_seasons` — how many past seasons to fit Elo on (3 is plenty).
- `lookahead_days` — how far ahead to predict (default 3).
- `slip.*` — leg count targets, minimum leg probabilities, and the 100-odds banker target settings.
- `basketball.enabled` — turn NBA/EuroLeague predictions on or off.
- `basketball.leagues` — currently supports `NBA` and `EuroLeague`.
- `basketball.history_days` — how many recent basketball days to train on.
- `community.endpoint` — optional write/read API for community codes. Without an endpoint, the Community Codes tab is browser-local only.

## Command-line flags

```bash
python run.py --lookahead 7        # wider window
python run.py --offline            # only use cached CSVs, no network
python run.py --config other.yaml
```

## GitHub Pages

The generated site is written to `docs/index.html`. In GitHub, enable Pages from:

```text
Settings -> Pages -> Deploy from a branch -> main -> /docs
```

After each run, commit and push the refreshed `docs/index.html` and `docs/predictions.csv` to update the public page.

## Data source and freshness

- Historical results: `football-data.co.uk/mmz4281/{season}/{league}.csv`
- Upcoming fixtures: `football-data.co.uk/fixtures.csv`
- NBA results/fixtures/odds: ESPN public scoreboard JSON.
- EuroLeague results/fixtures: EuroLeague live API XML.

The football upcoming fixtures file typically contains games for the next week or so, with opening bookmaker odds (Bet365, Pinnacle). ESPN usually carries NBA moneyline, spread, and total lines. When market odds are present, the VALUE slip becomes available and per-slip EV is computed.

## Model notes and limits

- Football Elo k-factor, home-advantage, and goal-diff weighting are tunable in `config.yaml`.
- Football expected goals are derived from Elo gap + league average goals per game. This is simple but surprisingly robust for a v1.
- Dixon-Coles `rho = -0.10` corrects the well-known Poisson under-estimate of low-score cells (0-0, 1-0, 0-1, 1-1).
- Basketball expected scores are derived from recent team scoring/allowing rates plus Elo-adjusted margin; spread and total probabilities use normal distributions.
- No injury or lineup data — accepted tradeoff for the "no API" constraint.
- Combined slip probability assumes independence. Real events are slightly correlated, so combined probability is a mild overestimate. One pick per fixture mitigates the worst of it.
- **Not betting advice.** This is a model output, not a tip service.

## Project layout

```
football_predictor/
├── run.py                # single entry point
├── config.yaml           # knobs
├── requirements.txt
├── src/
│   ├── fetcher.py        # scrapes football-data.co.uk CSVs
│   ├── basketball_fetcher.py
│   ├── ratings.py        # goal-weighted Elo
│   ├── basketball_model.py
│   ├── model.py          # Dixon-Coles Poisson scoreline matrix
│   ├── slip_builder.py   # consolidated SAFE / BALANCED / AGGRESSIVE / ONE_CEDI_DREAM / VALUE variants
│   ├── accuracy.py       # prediction history and score checking
│   └── report.py         # standalone HTML report
├── data/                 # cached CSVs (auto-populated)
└── docs/                 # GitHub Pages output
```

## Extending it

- **More leagues**: add or remove football-data.co.uk codes in `leagues:`. The default set is broad, so trim it if you want faster runs or a tighter model scope.
- **Better injuries**: the honest path is a manual CSV with team rating overrides (`team,rating_delta`) read at predict time. Easy add.
- **Backtesting**: walk-forward split on `history`, predict, compute Brier/log-loss. Skeleton for this is a straightforward extension of `model.predict_fixtures`.
- **LLM narration** (optional): once you trust the math, a deterministic templated report works; an LLM narration layer can be bolted on later and should never generate numbers.
