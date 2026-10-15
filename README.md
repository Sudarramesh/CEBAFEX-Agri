# CEBAFEX Agri — Complete Local Edition

A local agricultural business web app with the supplied CEBAFEX branding, English-only or Tamil-only application text, validated planning imports, durable stock and purchase records, explained buyer matching, historical forecasting and outcome evaluation. No API key is needed.

## Windows: run in VS Code

1. Install Python 3.12 (3.11 also works), with **Add Python to PATH** selected.
2. Extract `CEBAFEX_Agri_Complete.zip` to `C:\CEBAFEX`. Open the extracted `CEBAFEX_Agri_Complete` folder in VS Code.
3. Select **Terminal → New Terminal → Command Prompt** and run:

```bat
cd /d C:\CEBAFEX\CEBAFEX_Agri_Complete
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Open http://localhost:8501. Stop with Ctrl+C. In VS Code, select `.venv\Scripts\python.exe` using **Python: Select Interpreter**. If Python 3.11 is installed instead, use `py -3.11` for the environment command.

PowerShell can run without activation:

```powershell
Set-Location C:\CEBAFEX\CEBAFEX_Agri_Complete
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Alternatively double-click `start_windows.bat`. It creates an environment and installs missing dependencies. `run_tests_windows.bat` runs Pytest. Installation needs internet; the installed app, logo and bundled Tamil fonts work locally. No Node.js, database server, cloud subscription or AI key is required. Exact checked dependency versions are in `requirements-tested.txt`.

## What changed

| Capability | Working implementation |
|---|---|
| Actual outcomes | Proposed, accepted, declined and cancelled purchases; partial/full sales; redistribution and discarded quantities; actual dates, prices, transport and other costs |
| Separate identities | Markets/locations with optional coordinates; farmers, vendors, cooperatives and distributors; separate buyer records; stock lots linked to suppliers and requests linked to buyers |
| Better matching | Crop, minimum grade, reported freshness, delivery dates, optional distance limit and inspection requirement; explained score and rejection reasons; globally capped previews |
| Historical forecasts | Reviewed daily history imports by market/crop; trained Ridge regression compared with a seasonal baseline; saved model versions and later-observation error |
| Outcome evaluation | Estimated versus actual returns on the same sold quantity; proposal-to-sale conversion; physical, reserved, sold, redistributed and discarded stock; all recorded outcome costs |
| Broader imports | CSV and multi-sheet XLSX, reviewed heuristic aliases, manual mappings, bounds and validation; formulas require export as values |

## Eleven screens

Home, Upload Data, Dashboard, Surplus and Risk, Buyer Matching, Profit Analysis, AI Assistant and Workspace remain available. **Supply Network**, **History and Forecasts** and **Outcome Evaluation** add business operations. The supplied logo remains unchanged in English; Tamil uses a Tamil wordmark because the PNG contains Latin lettering.

## Two explicit data sources

Select **Planning source** in the sidebar:

- **Uploaded workspace** uses the validated crop/buyer datasets shared by the original screens. Uploads and edits are session changes until you explicitly save a workspace version. Planning versions preserve both datasets, rules and provenance atomically, with stale-save conflict checks. Buyer previews remain sample/uploaded opportunities, never confirmed orders.
- **Operational ledger** uses durable stock lots, recorded movements and accepted reservations. Each successful ledger form saves immediately to SQLite. All operational dashboard, risk, matching, financial and assistant views recalculate from that ledger. Changing source preserves the uploaded workspace. Restoring an old planning version cannot restore stock already sold in the operational ledger.

An uploaded aggregate crop sheet does not automatically create real supplier identities or actual sales. Enter the associated identities and lots through Supply Network. This avoids inventing provenance or counting the same inventory twice.

## First operational workflow

1. Select **Operational ledger → Supply Network → Markets**. Add a market and location. Coordinates are optional; both latitude and longitude are needed when used.
2. In **Participants**, add suppliers/farmers and buyers, each linked to a market. These are distinct stored identities.
3. In **Stock lots**, enter supplier, crop, grade, received quantity, entered local demand, market reference price, harvest date, ready date, reported freshness and storage notes. Lot review can update entered demand, price, freshness and notes; actual received quantity is not silently overwritten.
4. In **Buyer requests**, enter crop, minimum grade, required quantity, quoted price and transport, deadline, optional straight-line distance limit and inspection requirement. Close a request when it should no longer receive new allocations.
5. Open **Buyer Matching**. Review suitability reasons and quantities, then create a proposal. A proposal does not reserve stock.
6. In **Supply Network → Orders and outcomes**, record the buyer response. Acceptance reserves the outstanding quantity after transactional capacity checks. Decline leaves stock unchanged; cancellation releases unsold reservations. The app records the operator's report; it does not contact or authenticate the buyer.
7. Record actual sales against accepted orders. Enter the actual quantity, date, price and actual trip costs. Partial sales are supported. Record redistribution or discard separately against unreserved physical stock. Every actual movement reduces physical stock once; retries with the same transaction token are idempotent.
8. Open **Outcome Evaluation**. Review stock balances, conversion and returns. Download a complete SQLite backup from **Supply Network → Ledger backup**.

Physical stock = received − actual sales − redistribution − discard. Reserved stock = outstanding accepted quantities. Free stock = physical − reserved. Allocatable surplus = max(free − entered local demand, 0), calculated per lot and summed positively. Shortages are also summed per lot; a surplus at one supplier does not silently cancel a shortage elsewhere. Local demand is a planning estimate, not automatically fulfilled by an external buyer sale; review it when business circumstances change.

Stock movements are append-only through the UI. There is no implemented sales-return/reversal journal; verify records before saving and preserve backups. Identity records are additive in this release. Corrections to demand/price/freshness and request closure have explicit controls.

## Matching and risk rules

A pair must have the same crop identity (case/whitespace normalized), an adequate grade (A > B > C), compatible dates, suitable reported freshness and sufficient free surplus/request remainder. A distance-constrained request needs known coordinates within its limit. Inspection-required requests need reported Acceptable freshness. Unsuitable stock is rejected.

Score = grade fit up to 30 + reported freshness up to 20 + straight-line distance up to 20 + quantity coverage up to 30. Equal grade: 30; better grade: 25. Acceptable freshness: 20; unassessed: 10; needs inspection: 0. Distance: max(0, 20 − km/10), unknown: 0. Coverage: 30 × min(free surplus / request remainder, 1). Ties use estimated return, then lot/request IDs. This is an explained planning rule, not a trained purchase probability. Preview allocation caps quantities across all pairs; actual acceptance rechecks balances in a SQLite write transaction, including concurrent sessions.

Distance is geographic straight-line distance, not a road route, travel time or delivery guarantee. Grades, locations and freshness are user-reported; no image-based spoilage detection is claimed. Operational risk reviews prioritize inspection concerns, then surplus quantity and age. Adjustable surplus-share and harvest-age flags are planning assumptions, not crop shelf-life predictions. Operational ages advance from recorded harvest dates; uploaded snapshot ages remain as entered.

## Historical training and honest evaluation

Create a market, then open **History and Forecasts**. Upload CSV/XLSX and review date, crop, quantity and optional stockout mappings. Declare whether the target is **Observed demand** or a **Sales proxy**. Sales do not measure unmet demand; stockout sales are censored. The model refuses mixed targets and stockout-marked sales training.

Each market/crop needs at least **56 consecutive daily records**. Missing dates are not filled. Import history in chronological daily units, with no future actual observations. Duplicate crop/date rows and conflicting existing values are rejected unless explicit corrections are selected. An import validates before the transaction commits.

The model uses lag 1, lag 7, seven-day mean, weekday and annual cycles. Earlier dates train a standardized Ridge model. The latest at least 14 targets compare rolling one-day-ahead MAE with a previous-week seasonal baseline. The lower-error method is selected, then final Ridge weights are fitted on available data. This method-selection validation is **not an independent final test** and does not establish general business accuracy. More history and seasonal coverage are advisable before relying on forecasts.

Forecasts are recursive for 1–30 days **after the last observed date**, which may be in the past. They do not overwrite entered demand estimates. Each run saves cutoff, features, coefficients, history digest, validation predictions, sources and forecast rows as JSON/SQLite, without pickle. Later actual observations for matching dates and target basis produce a separate MAE; no actuals means no reported actual error. Stockout sales are excluded from later sales-proxy scoring. Historical corrections affect current later-observation evaluation, while saved original model/validation payloads remain unchanged; retrain after correcting training history.

`data/history_synthetic.csv` is explicitly synthetic demonstration data. Its apparent accuracy is not evidence of real performance. The three-row agriculture demo is suitable for calculation testing and **cannot train a time-series model**.

## Financial and outcome definitions

Estimated return after transport = allocated quantity × quoted price − full quoted trip cost for a positive allocation. Repeated partial actual sales use their actual recorded trip costs. For estimated-versus-actual comparisons only, the original quoted transport is allocated in proportion to sold quantity. Full-order estimates are displayed separately from actual sold quantities.

All-outcome totals include sales, redistribution and discard transport/other costs. After recorded costs is not true profit unless every relevant cost, including production, labour, packaging, storage, taxes and overheads, has been captured. Money uses decimal half-up paise rounding and sums rounded lines. There are no payment collections or accounting integrations.

Conversion = proposals with any recorded sale / all recorded proposals, including declined/cancelled proposals. Zero proposals gives an unavailable result. Physical remaining stock is measured from the recorded ledger; the app does not claim that redistribution or a sale proves causal waste avoided.

The rule-based assistant uses active calculation functions. Planning mode supports typed English/Tamil questions; operational mode offers grounded topics for stock priority, suitability, actual outcomes and saved forecast evidence. It does not invent live prices, weather, routes, orders or financial results.

## Backups and upgrading safely

Default database: `data/cebafex.sqlite3`. Set `HARVEST_DB_PATH` for another local writable path. No business database is included in the ZIP. SQLite is built into Python.

Keep your previous project unchanged. Close the old app, back up its database, then copy its `data/cebafex.sqlite3` into this new folder's `data` directory **only if the new destination does not already contain business records**. Older Harvest editions may use `harvest.sqlite3`; copy that under the new filename. Start this complete app and restore the saved planning workspace explicitly. New operations tables are additive. Do not mix individual old/new Python files.

Create a complete, consistent database backup while the app is running using the ledger download or:

```bat
python manage.py backup-all cebafex-complete-backup.sqlite3
```

The command refuses to overwrite an existing file. A complete backup includes planning versions, identities, stock, orders, movements, history and models. To recover a complete database, close all app instances, preserve the current database as another backup, and copy the chosen `.sqlite3` backup to `data\cebafex.sqlite3`. For custom storage use:

```bat
python manage.py --database D:\CEBAFEX\cebafex.sqlite3 backup-all cebafex-complete-backup.sqlite3
```

Legacy planning-only ZIP backups remain supported:

```bat
python manage.py backup planning-backup.zip
python manage.py restore planning-backup.zip --replace-current
```

Those ZIPs cover saved **planning datasets/rules only**; they are not operational ledger backups. Restore imports a new planning version, which must then be selected in the app.

## Original judging acceptance values

| Check | Calculated demo result |
|---|---:|
| Records | 3 |
| Available / entered demand | 1,050 / 850 kg |
| Positive surplus / shortage | 250 / 50 kg |
| Tomato surplus / potentially matched / unmatched | 200 / 180 / 20 kg |
| Green Leaf / City Hostel after transport | ₹2,600 / ₹1,830 |
| Combined tomato buyer return | ₹4,430 |

The original CSVs and judging workflow remain in `data/` and `docs/JUDGING_DEMO.md`. Results are calculated, not hardcoded KPIs.

## Tools and modules

Python provides validation and calculations. Streamlit provides forms, session state and navigation without a separate frontend build. Pandas handles tabular records; Plotly supplies interactive charts. SQLite provides local transactional persistence. Openpyxl reads XLSX. Scikit-learn supplies Ridge regression; a seasonal baseline remains eligible if it validates better. Pytest covers calculations, transactions, validation, languages and UI flows. Playwright and axe are optional development checks, not runtime dependencies.

`harvest/operations.py` contains ledger, matching and outcome logic; `operations_view.py` renders operational screens. `forecasting.py` contains temporal training/evaluation; `forecast_view.py` renders it. `tabular.py` handles XLSX and heuristic mapping. Existing calculation, ingestion, business version, strict localization and branded UI modules are retained. `app.py` only coordinates source selection and routing. See `docs/COMPLETE_ACCEPTANCE.md` and `docs/VERIFICATION.md` for evidence and limits.

Optional browser checks:

```bat
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
python scripts/browser_acceptance.py --report planning-browser-report.json
python scripts/operational_acceptance.py --port 8511 --report operational-browser-report.json
```

Supply `--axe-script path\to\axe.min.js` for accessibility scans, and optionally `--artifacts local-qa` for local screenshots. Tests create isolated databases. Browser binaries/screenshots are not bundled. Windows commands are provided; execution on actual Windows is not claimed.

This is a local, single-company app bound to `127.0.0.1`, not a publicly deployed multi-tenant service. It has no authentication, buyer messaging, payments or external live feeds. Validation can flag invalid/inconsistent input; it cannot independently prove that plausible entered data is true. Protect the machine and database as business records. The supplied PNG and bundled Noto Tamil fonts retain their respective notices in `THIRD_PARTY_NOTICES.md`.
