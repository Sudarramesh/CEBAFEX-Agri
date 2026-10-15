# Complete edition verification — 15 October 2026

## Automated checks

`python -m pytest -q`: **190 passed** on Python 3.12.14 (122.41 seconds). The exact direct dependencies are listed in `requirements-tested.txt`. The 162 prior planning/business checks remain included.

New checks cover the durable ledger and actual dates; partial/full sales; declines and cancellations; atomic stock bounds; simultaneous confirmations; retry tokens that cannot be reused with different data; grade/freshness/date/distance constraints; capped multi-supplier allocation; per-lot surplus/shortage sums; preservation of actual sales when planning versions are restored; all-event costs; full SQLite backup with saved forecasts/history; chronological training, baseline selection and later-observation MAE; insufficient, missing-date, censored or conflicting history; explicit corrections; Excel parity, sheet selection, formulas, duplicate headers, malformed XML and invalid files; reviewed mappings that do not infer forecasts as entered demand.

AppTest checks all eleven operational screens in English and Tamil, strict selected-language rendering, source switching without losing uploaded planning data, active balance refresh after reservations/sales, actual proposal/confirmation/sale forms, Excel activation in both languages, source-record creation from an empty database and invalid Tamil response dates that cannot create confirmations.

The original mandatory calculations remain: 3 records, 1,050 kg available, 850 kg entered demand, 250 kg positive surplus, 50 kg shortage; Tomatoes 200 kg potential surplus, 180 kg potential match, 20 kg unmatched; Green Leaf ₹2,600, Hostel ₹1,830 and combined tomato return ₹4,430 after quoted transport. Model tests use explicit synthetic inputs; their MAE is not business accuracy evidence.

The `manage.py backup-all` command was also exercised against a temporary database, including the refusal to overwrite an existing output file.

## Browser checks

The scripts start isolated Streamlit servers and temporary databases; test data never enters a business database. Chromium 153.0.8010.0 and a local axe-core script were used.

`scripts/browser_acceptance.py` passed the original upload workflow in both languages: invalid price rejection, corrected CSV activation, required dashboard/risk/matching/return/assistant results, direct business CRUD, saved version, downloaded planning ZIP backup and restoration. It audited eight original screens per language: **16 screen/language pairs**, plus actual phone menu navigation, keyboard skip link, local Tamil font loading and round-trip native language controls.

`scripts/operational_acceptance.py` exercises actual UI proposals, operator acceptance, stock-consuming sales, actual costs, downloaded complete database recovery, model training and saved forecasts compared with synthetic later observations. Identities, starting stock and initial historical data are seeded as test fixtures; later observations are deliberately inserted through the backend to isolate scoring from upload behavior. Real Excel upload is covered by AppTest, not claimed as a browser XLSX upload.

Both scripts audit generated visible text, selected control values and visible accessible attributes for language purity. Responsive checks cover 1,440×1,000 desktop and 375×812 phone; Dashboard and Workspace also check 768×1,024 tablet and 812×375 landscape. Screenshots of the operational English desktop and Tamil phone dashboard were inspected internally; QA images are not part of the package.

Axe checks WCAG 2 A/AA and 2.1 AA tags on desktop screens. This is automated coverage, not comprehensive WCAG certification or assistive-technology testing. Collapsed areas and every possible input are not exhaustively scanned. Language-menu automation retries account for a transient sidebar resize that can close an open menu; expected native control values are still asserted after selection.

The final operational browser run passed **22 screen/language pairs** (all eleven screens in both languages). Across both final runs, all **38 desktop screen/language audits** had zero detected axe violations, zero JavaScript page errors and zero external service requests. Both actual operational workflows and phone-menu navigation passed. Machine-readable reports are included in this directory.

## Operational limits

Windows commands and batch launchers are included, but no actual Windows execution is claimed from this Linux environment. No public hosting, authentication, multi-tenant isolation, buyer communication or payments are implemented. Acceptance is an operator-recorded response, not independent buyer verification.

Demand estimates remain separate from model forecasts. Risk is an explained planning review, not measured spoilage. Coordinates and quality are reported data. Distance is straight-line, not a road route. Returns after recorded costs are not automatically complete accounting profit. Actual quantities do not establish causal waste avoided. A syntactically valid record cannot independently be proved true by input validation.

Source identifiers and technical backup archives preserve canonical schemas. Generated reports and application-owned labels follow the selected language; user input and browser/OS file pickers remain external to that contract.
