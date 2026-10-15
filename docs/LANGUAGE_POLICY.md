# Mandatory language policy

User requirement: selecting English must produce English-only application text; selecting Tamil must produce Tamil-only application text. This applies to Phase 6, Phase 7 and later changes.

Use strict translation keys and structured numeric evidence. Never concatenate English and Tamil. Never render backend English reason strings directly in Tamil mode. Never silently fall back to English. Keep canonical source data immutable, and localize only presentation/report copies. Unknown foreign-script identifiers use stable numbered display labels rather than invented translations.

Every screen, chart label, table cell, validation message, assistant reply and user-facing report must be checked. Keep the local Tamil upload asset with the project. User input, original source files and host browser/OS controls are external to the generated application text.

Assistant history stores question contexts, not stale rendered answers. Switching language must render every current answer in the selected language, using current calculations. Changing active data or planning rules must recompute answers.

Phase 7 must retain all existing tests and add final workflow verification. Browser-level visual checks are distinct from AppTest/text audits and must be reported accurately.
