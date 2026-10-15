# Final acceptance matrix

This document covers the original uploaded planning workspace. For the Complete edition operational ledger, historical forecasting and outcome evaluation, see [COMPLETE_ACCEPTANCE.md](COMPLETE_ACCEPTANCE.md) and the current [README](../README.md).

| Requirement | Implementation / verification |
|---|---|
| 3 records; 1,050 available; 850 demand; 250 positive surplus; 50 shortage | analytics.calculate_kpis; original numeric tests and test_phase7 full workflow |
| Tomatoes 200 surplus, 180 matched, 20 unmatched | analytics.crop_balances + matching.matching_preview; capped matching tests and browser workflow |
| Green Leaf ₹2,600; City Hostel ₹1,830; combined ₹4,430 | money decimal rounding + financials.analyse_financials; original financial assertions, Phase 7 workflow |
| Suggestions, editable mapping, quality summaries | ingestion + upload_view; aliases, ambiguous mappings, duplicate/invalid rows, missing-price rejection tests |
| Shared active validated data | Session State activation, invalid replacement prevention, SQLite save/restore tests |
| Separate estimates / forecasts | Uploaded estimated-demand fields only; no model-generated forecast in this version |
| Transparent surplus and risk | Pure risk module with displayed adjustable rules, ranking and evidence; boundary tests |
| No duplicate/over-allocation | Stateless source-order capped matching, original dataset identities, repeated-run tests |
| Sample opportunities | Explicit sample/unconfirmed labels in matching, financials and assistant |
| Return versus profit | Charged transport, partial/zero matches, negative returns and half-up rounding tested; unknown production costs disclosed |
| Assistant grounded in current calculations | Pure assistant routing, active evidence, changed-data and language rerender tests |
| English-only / Tamil-only | Strict catalog, canonical-to-display boundary, local upload/chrome components, fonts; AppTest and real browser text/selection checks |
| Accessibility / responsiveness | Localized skip link, focus, headings, local fonts, reduced motion, table paging, phone-width browser checks; see VERIFICATION.md for scan scope |
| Local project / run instructions | Complete modules, samples, requirements, Windows Command Prompt and PowerShell commands in README |

The complete original Pytest assertions remain in the suite. Native-widget locators were adapted to locale-specific display keys; numerical acceptance values were not relaxed. `scripts/browser_acceptance.py` supplies repeatable real-browser coverage beyond Streamlit AppTest.

## Business edition additions

| Requirement | Implementation / verification |
|---|---|
| CEBAFEX professional UI and supplied logo | brand.py, static/brand/business.css, original PNG; desktop/phone browser inspection |
| Add/edit/remove and search crop/buyer records | business.change_record + business_view; immutable-input, duplicate and UI tests |
| Durable named versions and optimistic conflict check | business.save_version atomic transaction; stale revision tests |
| Recover historical and empty workspaces | load_version, confirmation UI and legacy snapshot synchronization; recovery tests |
| Portable backup and validated CLI recovery | workspace_backup + manage.py; lossless and invalid archive tests |
| Strict business English/Tamil interface | business_labels + existing translation boundary; both-language forms and browser checks |

Business workflow steps are in BUSINESS_WORKFLOW.md. Actual verification scope and limits are in VERIFICATION.md.
