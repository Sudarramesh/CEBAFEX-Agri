# CEBAFEX business workflow acceptance

This document covers the original uploaded planning workspace. For the Complete edition operational ledger, historical forecasting and outcome evaluation, see [COMPLETE_ACCEPTANCE.md](COMPLETE_ACCEPTANCE.md) and the current [README](../README.md).

1. Open a new session; no stock or buyer opportunities are invented. The company logo, correct company text and eight navigation destinations are visible in English. Tamil uses a Tamil brand wordmark and Tamil-only application text.
2. Home → Manage records opens Workspace. Add a crop with finite non-negative quantities, demand, price and harvest age. Add a second crop. Duplicate crop names ignoring case/whitespace must be rejected.
3. Add buyer opportunities. Select an active crop, enter required quantity, offer price and per-trip transport quote. Duplicate buyer/crop identities must be rejected. Buyer ordering remains stable during edits.
4. Edit a crop quantity and open Dashboard. Totals, surplus/shortages, risk, matching, financials and assistant answers recalculate from the same active data.
5. In Version history, save a named version. Change a quantity, then restore that version after checking the replacement confirmation. Both datasets and the applied planning policy must return to the saved state.
6. Open another session, restore the latest saved workspace, and save a new version there. The older session must receive a conflict message if it tries to save with an outdated base revision.
7. Delete a selected record only after explicit confirmation. Deleting the final record clears that dataset; saving an empty workspace must preserve that cleared state. Older saved versions remain recoverable.
8. Download an original-data backup. The ZIP must contain workspace.json and the available canonical CSVs. Use manage.py to import it into a separate database; restored datasets must match exactly.
9. Repeat forms, records, history and reports in Tamil. Change language after selecting a crop: selection identities and calculations remain stable. Typed input and original source/backup files preserve their original identities.
10. Repeat at desktop, phone and tablet/landscape widths. Check visible keyboard focus, native input labels, no horizontal page overflow, chart/table readability and reduced-motion behavior.

The original numeric judging contract remains in JUDGING_DEMO.md and the Pytest suite. These operational checks add business management behavior; they do not turn opportunity previews into confirmed orders or estimates into actual profit.
