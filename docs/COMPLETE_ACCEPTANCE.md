# Complete edition acceptance map

| Requested outcome | Implementation | Meaningful verification |
|---|---|---|
| Actual outcome tracking | `operations.propose/respond/movement/evaluation`; Supply Network and Outcome Evaluation | Proposals leave stock unchanged; accepted quantities reserve; partial/full sales consume once; decline/cancel behavior; bounds; concurrency; disposal/redistribution cost totals; actual UI workflow |
| Supplier and market identities | Market, supplier and buyer registry linked to lots/requests | Separate same-crop lots, market FKs, supplier source tables and localized forms |
| Better buyer matching | `suitability`, `ranked_matches`, transactional `respond` | Grade, freshness, dates, unknown/limited distance and closure rejection; pair and global quantity caps; simultaneous confirmations cannot overreserve |
| Historical forecasting | `import_history`, `train_series`, `train_and_save`, `forecast_report` | Chronological train/validation, baseline comparison, saved JSON model, later actual MAE, no-actual unavailable state, gapped/censored/mixed history rejection and explicit corrections |
| Outcome evaluation | Per-order sold-share comparison and all-event totals | Known actual return ₹4,430; additional recorded costs; physically remaining stock; true denominator conversion; unmeasured waste avoidance |
| Excel and broader mappings | `tabular` with shared ingestion validators | Multi-sheet import equals CSV calculations, malformed/formula/duplicate-header rejection, ambiguous mappings left for review, forecast columns excluded from entered-demand inference |
| Strict language | Shared Translator and rendering boundary with ops catalog | Every operational screen in both languages with saved history/model; real browser visible strings, selected values and accessible attributes |
| Preserve original demo | Existing seven-screen calculation and planning workspace | Original mandatory numbers plus original regression suite and planning browser workflow |
| Portable complete backup | SQLite online backup and `manage.py backup-all` | Restored physical stock, forecasts/history, planning versions; real browser downloaded database opened and checked |

No claim of external buyer verification, road routing, causal waste reduction, guaranteed forecasts, image-based spoilage detection, complete accounting profit or public deployment is made. These would require separate data/integrations and acceptance tests.
