# Harvest Intelligence AI project requirements

## User language requirement — applies to Phase 6, Phase 7 and later edits

When English is selected, application-owned visible text must be English only. When Tamil is selected, application-owned visible text must be Tamil only. Never append the other language in brackets, captions, headings, widget options, explanations or assistant messages.

Use `Translator`, the strict catalog and the `locale_ui` rendering boundary. Do not import Streamlit directly in screen modules or render backend English reasons directly. Data calculations and storage retain canonical values; display/report localization must not mutate active datasets. Unknown foreign-script identifiers use stable numbered labels instead of invented translations. Known demo crop and buyer identities have explicit translations. Tamil uploads use the bundled local component, not an English default upload prompt.

Assistant responses must call the existing calculation functions, be rendered from structured facts, and be recalculated against active inputs. No live prices, weather, confirmed orders, model forecasts or actual profit may be invented.

Before delivering Phase 7, rerun all regression and language tests. Preserve the 143 Phase 6 checks and add final workflow checks. Real browser desktop/phone checks are recorded in docs/VERIFICATION.md; rerun relevant checks after UI changes and do not claim checks that were not performed.

All seven phases are delivered. Preserve the final workflow, strict language policy and existing numerical assertions in future edits.


## CEBAFEX Business Edition

Preserve the supplied original logo, CEBAFEX company spelling specified by the user, and the strict selected-language contract. English mode displays the supplied logo; Tamil mode uses the localized brand wordmark because the image embeds Latin text. User source files and lossless backup archives retain canonical identities and schemas.

Business records must pass the shared validators before activation. Buyer edits must preserve source order. Save both datasets and planning rules atomically; compare revision numbers to reject stale-session saves. Version history is immutable. Clearing a dataset must not resurrect an older legacy snapshot. Saving is explicit and the UI must expose unsaved changes.

The app is a local single-company business workspace. Do not describe it as a public multi-tenant platform or claim authentication, payments, real-time feeds or confirmed sales that are not implemented. Keep tests isolated from actual business storage.

## Complete operational edition

Planning snapshots and operational records are intentionally separate. Never infer actual sales or supplier identities from uploaded aggregate planning rows. Preserve physical-stock ledger semantics, immutable saved model payloads, transactional capacity checks and idempotency tokens. Recorded buyer acceptance is an operator entry, not an externally verified order. Forecasts require dated history, chronological validation and later-observation evaluation; never substitute forecast output for entered estimated demand. Full backups must include operations and forecasts, not only planning snapshots. Sum positive per-lot surplus and shortages separately across suppliers/markets.
