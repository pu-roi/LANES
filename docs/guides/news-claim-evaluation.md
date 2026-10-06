# Independent news claim evaluation

> **Last Updated:** October 05, 2026, 7:02 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Source-alert continuation:** standalone seed/evaluate commands below still create no public decisions. The separate explicit saved-article pipeline now connects them to atomic source-alert publication/refresh/clearance/expiry; see [publication lifecycle guide](news-publication-lifecycle.md). Operational zones and deployment remain gated. [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Local evaluation worker implemented. No automatic publication, zone creation, expiry worker or deployed evaluator is delivered here.

## Configuration and storage

Apply approved migration `d7e4b9a21c60` before using the evaluator against the intended database. The implementation checks were confined to fresh disposable local PostGIS; the normal application and cloud databases were not migrated by this task. The evaluator uses the existing configured `SessionLocal`. Check the target environment before running either command; these are write commands, not previews.

Configure `LANES_NEWS_AUDITOR_PROVIDER` as `openrouter` or `gemini`, and `LANES_NEWS_AUDITOR_MODEL` as an explicitly verified model for that provider. OpenRouter uses only `OPENROUTER_API_KEY`; Gemini uses only `GEMINI_API_KEY`. No configured provider/model means no external confirmation. Model availability has not been checked through live requests in this implementation.

The auditor and legacy hybrid wrapper read the backend `.env` using the existing settings convention. Exported process variables override that file, including explicit blank values; loading configuration does not mutate `os.environ`. The [example](../../backend/.env.example) leaves provider/model/keys blank. Do not run paid evaluation merely to check configuration.

`LANES_NEWS_AUDITOR_CONFIG_REVISION` defaults to `1`. Use a new safe revision token after repairing credentials, provider access or equivalent configuration without changing the model. Terminal evaluations are immutable: the new policy creates another evaluation against the same source binding and retains the failed result. Credentials and credential hashes never enter policy identity or output.

## Explicit extraction-to-evaluation handoff

Run from `backend/`, using the configured Python environment:

```powershell
python -m scripts.evaluate_news_claims --seed --after-run-id 0 --limit 50
python -m scripts.evaluate_news_claims --evaluate --limit 50
```

`--seed` reads at most the specified number of completed extraction runs, validates their immutable article/result and evidence offsets, and checks current extraction/asset identity, reviewed publisher and twelve-hour publication admission. It creates unpublished cases, immutable run/ordinal/hash source bindings and one evaluation per source/policy. No provider request occurs. Reuse the output `next_after_run_id` as the next seed cursor. `--run-id` selects one run instead; it cannot be combined with a nonzero cursor.

`--evaluate` handles at most the specified number of due evaluations. Limits must be 1–200. It commits a UUID lease before any provider request, then completes only if that lease is still owned and unexpired. PostgreSQL `SKIP LOCKED` supports concurrent workers. Five attempts, bounded exponential retry delays and crash recovery prevent unbounded retries. A lost lease is reported and is not immediately reclaimed by the same batch. Storage failures propagate; the command never reports a successful save after a failed completion transaction.

The commands return safe identifiers, counts and reason codes. Skipped seeds and failed/retry/lost work return nonzero status with their reasons in JSON. Neither command changes completed extraction, article moderation, decisions, reports, events, zones, public visibility or routing. They are not currently scheduled or appended to the deployed collector.

## Evidence and evaluation meaning

The auditor receives the full frozen article body and structured textual candidate facts. Saved claim identity includes its complete normalized extraction, including placement evidence; geometry, prior audit/actions and ranking scores are excluded from the prompt because they do not independently establish reported flooding. Exact body quotes/offsets support parent locality, status, observation time, reported depth/qualifiers and road access. Publisher instructions remain untrusted text.

Requests have a twenty-second total deadline and bounded input/output sizes. Invalid JSON, unsupported evidence, missing credentials, timeouts, provider errors and disagreement cannot create independent confirmation. Current source/observation/policy checks are separate from audit confirmation. Unknown depth stays unknown. A confirmed clearance claim remains evidence for a future matched-target clearance transaction; it does not clear any existing zone here.

The twelve-hour admission limit does not extend observation freshness. The accepted two-hour observation-based fallback prevents an already expired wet claim from receiving fresh active eligibility. Completion records both publication and observation freshness. These checks prepare evidence; **runtime Active → Unconfirmed and matched Cleared transitions are still pending**.

Completed evaluation records explicitly carry `publication_permitted=false` and `may_affect_routing=false`. A `verified` audit is not an operational footprint or permission to publish. Automatic decisions, supported polygon provenance, shared-source support, expiry/correction and safe public readers are the next backend slice under the [readiness contract](../plans/news-publication-readiness-plan.md).

## Spatial assets

Audit installed placement coverage without network or database writes:

```powershell
python -m scripts.audit_news_spatial_assets --city Pasig --road C5
python -m scripts.audit_news_spatial_assets --city Pasig --road C5 --barangay Ugong
```

Both commands now find source-backed candidates. The second narrows them within installed Ugong OSM community boundary relation `108731`. Twenty of Pasig's thirty barangays have reviewed community polygons; missing or excluded localities still return explicit coverage reasons. The API retains source classification, relation ID and source URL. Use the [boundary asset contract](news-barangay-boundary-assets.md) for coverage, exclusions and provisioning. Automated identity/topology review is distinct from official legal or field verification. Catalog validation and modeled NOAH fragments do not establish observed flood width or permit routing.

[Implementation evidence](../evaluations/phase-36-independent-evaluation-and-spatial-coverage.md).
