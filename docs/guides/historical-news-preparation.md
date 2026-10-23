# Prepare the saved September inputs (E0)

> **Last Updated:** October 22, 2026, 3:28 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). [Verified result](../evaluations/news-historical-e0-20261021/README.md) · [E0–E6 plan](../task_plan.md#october-25-presentation--detailed-e0e6-delivery-plan).

E0 reads the existing source versions/history and writes a private, ignored local preparation package. It never collects articles, invokes the NER model, claims durable work, mutates database records or activates zones. Use the existing backend environment and configured database credentials; never paste a connection string into commands or reports.

From `backend/`, with the normal environment loaded:

```powershell
./venv/Scripts/python.exe -m scripts.prepare_news_historical_inputs `
  --confirm-database lanes `
  --output ../data/news-historical-e0-20261021/package `
  --bundle training/flood_ner/artifacts/ner-preview-bundle-20261019-v1 `
  --bundle-sha256 13137f64b216d2a9f2978f0eb3d278950754dc56731688495b8348f2ad43a8cd `
  --worker-code-sha256 fc151e22fb56ea28027117912a852b232f4320da47f312286e0213cc135a5322
```

The verified run used the repository's installed dotenvx CLI to load `backend/.env` before that Python command. Environment values are never printed by this script. The explicit database-name confirmation must match both configured and connected database. SQL begins with `SET TRANSACTION READ ONLY`, uses `REPEATABLE READ`, verifies read-only mode, applies timeouts and rolls back.

Outputs must resolve inside the repository's ignored `data/` directory. Private bodies, metadata, evidence and requests stay there. Success prints bounded hashes/counts and `prepared`; an identical repeat prints `existing_package_verified` without overwriting files. Source changes, history changes, missing records, altered assets, a partial package or changed package cause failure. Investigate the discrepancy and preserve prior evidence rather than deleting it to make a rerun pass. Unexpected failures return a bounded `preparation_failed` code without dumping a connection exception or article text; exit 130 marks interruption.

Optional `--retained-workload` and `--retained-workload-sha256` must be supplied together to authenticate a previously approved cache before exact-text comparison. They only identify possible exact input matches; they do not run or qualify predictions. Changing optional arguments changes the manifest and cannot overwrite an already frozen package.

## Completed approved shared archive execution

All 111 selected articles / 56 batches and all 56 repeats are complete; no new archive qualified. The manual worker is disabled, and its exact image/config/receipts remain retained. Re-enable only through a deliberately frozen deployment; do not remove failure evidence or reset SQL.

The user-approved Part 2A release uses the separate `scripts.cloud_news_history` controller and unscheduled `lanes-news-history-seed` job. Each dispatch binds an immutable registry image and canonical config hash; worker configuration binds the exact database, model/application/spatial hashes, selected versions and processing/output authorities. Run read-only `inspect` and `preflight` before a new frozen release. Preserve original packages and create a new freeze after code changes.

Worker modes are `register`, `process`, `preview`, `apply` and combined `batch` (process, read-only preview, atomic archive apply). Each invocation has at most two selected articles, 1 CPU, 3 GiB, 600 seconds and zero automatic retries. `register` reuses canonical articles/exact versions and preserves original bodies/review state. Shared output authority rejects active instances and live publication. Missing/ambiguous dates, unsupported geometry and uncertain incident matches remain unresolved.

Capture a protected baseline before execution. Preserve every dispatch claim, task status, raw private log page and bounded application receipt. A failed task can have committed durable processing or registration; inspect it before explicitly resuming. Never reset a claim, silently replay inference, delete evidence or use the normal release pipeline to dispatch RSS. Native result schema remains part of processing receipts; identify receipts by exact execution and stage as well as supported schema.

Rollback restores the preceding serving API revision and runs the controller's `disable` action with the same project/region/image/config/receipt arguments. `disable` verifies ownership and replaces the manual job command with `python -c "raise SystemExit(0)"`, which cannot access the database or invoke extraction. Subsequent normal seed dispatch fails the command-configuration check; re-enabling requires a deliberate fresh deployment. Retain database rows and all immutable evidence. Do not reset the database or remove imported rows. The retained pre-release revisions are API `lanes-api-build-4837919e-8495-44ab-bebc-75de3c375051` and frontend `lanes-frontend-build-2026-10-22-001`. A rollback operator can restore either exact revision using `gcloud run services update-traffic <service> --to-revisions=<revision>=100 --region=asia-east1 --project=lanes-project-508809`, then verify health/authenticated reads and call the historical controller's `disable` action. Confirm the retained metadata before acting if another normal release has since occurred. This changes serving traffic only and retains all SQL/source/output evidence.

The ordinary RSS job and resource profile remain unchanged. [Current release/receipts](../evaluations/news-history-shared-execution-20261022/README.md). The earlier disposable checkpoints below retain their original pins and limits.

## Consume the package in E1–E2

Authenticate `receipt.json` against the separately recorded manifest hash, then recompute its canonical JSON hashes (UTF-8, sorted keys, compact separators, no nonfinite values). The receipt binds inventory, manifest and both native wrapper documents; native input fingerprints bind the `input_snapshot`, not the whole wrapper or pretty-printed file bytes. Recheck source and asset/code identities before processing. Do not rewrite the frozen package to fit changed code or records.

Use `native-25.json` and `native-47.json` with their bound original IDs/text; do not recapture or normalize whitespace. The manifest's primary/backup selections reference legacy claims and are not new native group IDs. E1 must map actual supported native groups by evidence before E2 generates geometry. Quirino/Guazon is first; Gov. Pascual requires separate qualification and explicit backup selection. Reuse the manifest's stable demonstration session when implementing future persistence.

All candidates remain `not_evaluated`. Publication evidence remains unknown where original bound proof is absent. An old rules-only zone is a history reference and cannot supply a polygon in place of actual new extraction/placement. E1–E2 must preserve visible unresolved outcomes. After qualification and the later release gates, selected labeled examples belong on both active maps; archive examples reuse history. E0 itself publishes nothing.

## E1.2 — manifest-bound preflight and disposable processing

**Retained E1.2 delivery snapshot:** the pins and disposable-only limitation below describe that earlier revision. For the current E1 command, use the next section and its newly authenticated asset/policy identities.

The new `scripts.run_news_historical_processing` consumes the frozen package above. [227-check verification and limits](../evaluations/news-historical-command-e12-20261022/README.md). The command is implemented locally; historical cloud processing is still blocked. No public button or endpoint is added.

The following is the **read-only preflight form**, from `backend/` with the normal environment loaded. It has not been executed against Cloud SQL during E1.2. It reports blockers rather than applying migrations or changing settings:

```powershell
./venv/Scripts/python.exe -m scripts.run_news_historical_processing preflight `
  --manifest ../data/news-historical-e0-20261021/package/manifest.json `
  --manifest-sha256 0beb452c80dd0a805bada20dffd6c92dfdee3cd99e1951bf5eaf0862ce9f8439 `
  --confirm-database lanes `
  --bundle training/flood_ner/artifacts/ner-preview-bundle-20261019-v1 `
  --bundle-sha256 13137f64b216d2a9f2978f0eb3d278950754dc56731688495b8348f2ad43a8cd `
  --worker-code-sha256 fc151e22fb56ea28027117912a852b232f4320da47f312286e0213cc135a5322 `
  --assets-sha256 76abbcb518f0ca16cf6fbab05ba425599e4f0c31942f59d37cb213644fc9c745 `
  --receipt-directory ../data/news-historical-command-e12-20261022/operator-receipts
```

The current-assets pin records this verified application revision. Future intentional code changes require a newly authenticated execution identity and evidence; never replace the E0 package's original asset manifest. The guide's current value is not permission to accept arbitrary new assets.

`preflight` verifies the full package and connected target, reads source/schema/settings under database-enforced read-only mode and checks execution prerequisites without model startup. It returns `ready` only when no blockers remain. A configured cloud source target remains blocked for processing even if its input inspection succeeds. On Windows, Linux/Python/runtime prerequisites are expected blockers. Legacy native-mode storage or paused/unselected sources are explicit blockers too. The command never fixes them by modifying the environment, schema or settings.

`process` uses the same flags, with a separately configured **owned loopback disposable database** and its exact confirmed name. It requires environment `test`, a PostgreSQL database named `lanes_p3_verify_*` and no connection-query overrides. That disposable mirror must already contain the frozen source versions attached to the same original article IDs; the command does not create articles or silently seed a mirror. No cloud-processing example is provided because that policy is not delivered yet.

Actual processing additionally requires Linux amd64/Python 3.12/spaCy 3.7.5, the qualified one-CPU/3-GiB cgroup limits, an unused main-thread timer and the authenticated model bundle mounted at `/assets`. The inference child still performs its own mandatory isolation checks. This step's verification used fictional runtime fixtures; it did not run the real September model or establish Cloud Run readiness.

Successful processing creates/reuses native version/run evidence only. It preserves original articles/review states, legacy versions and histories. Exact run selection excludes every other queued version. Completed matching results are verified and reused without inference; failures, retry waits and foreign leases are not reset or automatically reclaimed. A pending input may run once under the existing lease/deadline rules. Any remaining incomplete input or cleanup failure makes the attempt require attention; this command is not a retry/reset tool.

Receipts must be under ignored repository `data/`, outside the sealed E0 package. Each attempt gets a new private `attempt-*.json`; a hash-named `execution-*.json` binds parent/session, current assets/code and target without replacing a previous execution identity. Results contain source/run references and hashes, not copied polygons. Output exit codes are 0 for ready/completed, 1 for blocked/failure/attention and 130 for interruption. Preserve failure receipts and investigate their bounded codes before another explicitly chosen attempt.

E1.2 makes **no event/zone/publication/history writes** and adds no predictions or zones to the hosted UI. The next E1 task qualifies the explicit cloud target policy; actual candidate/source/date/geometry qualification and both active-map displays remain later gates.


## E1 — complete controlled historical processing

**Local software gate passed; cloud release/execution has not run.** [Verification](../evaluations/news-historical-e1-20261022/README.md) · [Aggregate](../evaluations/news-historical-e1-20261022/summary.json). The command adds `--target-policy PATH` and `--target-policy-sha256 SHA256`; supply both or neither. Without them, processing remains disposable-only. Existing flags and readonly preflight remain required. The current independently authenticated assets pin is `27a379f39744ca828f82bdbfd034c596e13491326357c003a39a92b8148fe31f`; preserve the original E0 package and its manifest hash unchanged.

### Preparing the pinned origin policy for a qualified release

1. Authenticate the frozen E0 package and current trusted assets through the existing loaders. Independently confirm the configured release's database identity/name; do not substitute a target from an article or receipt.
2. Call the pure `expected_target_policy(package, trusted, engine)` helper in `app.services.news_historical_policy`. It performs no SQL, inference or writes. Save its exact JSON in the ignored private receipt area outside E0. Review the bound parent/dataset/session, two article/source-version/native fingerprints, database identity/name, assets/pipeline and application hashes. Only processing and private interpretation receipts are allowed; `publication_allowed` must be false.
3. Independently pin the canonical JSON hash using `app.services.news_ner_durable.contracts.sha(policy)`, not the raw file-byte hash. Record the policy/hash with the release artifacts. A changed application, asset, target or package requires a newly reviewed/pinned policy, never edits to E0.
4. Run the existing preflight command with the new current-assets hash and the two policy arguments. `ready` establishes the checked prerequisites only; worker isolation is still tested at runtime startup. This guide does not claim cloud preflight/migration/resource qualification has passed. An unqualified platform, schema, source setting, runtime envelope or asset mount remains a blocker.
5. Only in the later qualified E5/E6 release, invoke `process` with exactly the same confirmed target, package, assets, policy pins and private receipt directory. No scheduler or public processing control is added. The actual selected runs are rechecked against the policy inside worker transactions. Ordinary worker entrypoints remain disposable-only.

### Inspecting the outputs

Processing completion and `historical_qualification_status` are separate. Bounded counts report source-qualified/unresolved groups and preview counts. Full source evidence and previews remain private in `interpretation-<canonical-sha256>.json`; execution and unique attempt receipts are retained alongside them. Identical receipts are verified/reused without overwriting files. Completed model runs are reused without inference; failed, retry-wait and leased runs are not silently reset.

`historical-source-interpretation-v1` records run/result/input/execution/policy identities, group targets/facts, exact temporal evidence, instant/date/unknown precision, timezone/date basis, original publication limitations and selected candidate/archive disposition. Unknown publication proof is not repaired using stored normalized dates. Relative dates require original authenticated publication evidence. Native-only collective groups and unassigned facts remain visible rather than split into invented individual claims. No source closure is invented in E1.

An explicit historical preview context admits old source observations without changing the live policy or saved claims. Forecast/negation/unsupported context, future/unknown observation dates and clearance candidates remain unresolved. Existing OSM/NOAH service uncertainty and missing asset bindings remain visible; a source-qualified group is **not** an accepted polygon, active flood or publication authorization. Geometry acceptance and persistence remain E2.

Interpretation failure produces `requires_attention` and a bounded qualification error while retaining completed model evidence. Correcting that downstream problem and repeating the command must not rerun completed inference. No new zones or frontend changes should appear from E1. Do not mark the later desktop/mobile map checks passed until E2–E5 are delivered.


## Phase 1 — saved-output materialization and reading

This command consumes already completed authenticated native runs and never reruns inference. E1 processing-only authorization remains separate. The local implementation requires migration `f1a9c7e2b604`, including the explicitly approved unknown-endpoint archive exception. Shared/cloud application and real September acceptance remain Phase 2.

1. Retain the frozen E0 package, dataset `capstone-september-2026-v1` and session `ee30c69d-32cd-555f-bb90-26899cb74810`. Do not regenerate or edit the original files. Quirino/Guazon remains the primary selected demo; Gov. Pascual needs independent qualification before fallback use.
2. Load the package using `load_historical_package`, and load the release's trusted bundle using `load_trusted_assets` plus `with_placement_assets`. Re-pin current application/model/spatial assets rather than reusing a previous release's hash after code changes. Authenticate the independently chosen local target through the configured database engine.
3. Build the exact, SQL-free policy with `app.services.news_historical_outputs.expected_output_policy(package, trusted, engine)`. Save it as private JSON outside E0, review its candidate selection, dataset/session, application hashes, assets, pipeline and exact target, and pin its canonical hash using `app.services.news_ner_durable.contracts.sha`. This does not authorize E1 inference or live-news publication.
4. Run preflight with the same required inputs below. Inspect every output: extraction completion, source qualification, geometry qualification and successful saving are distinct. Unresolved groups retain reasons. Matching original history is checked without rewriting it. Ready is not proof of real candidate acceptance.

```powershell
# Use this release's already configured local environment; placeholders are required pins.
python scripts/materialize_news_historical_outputs.py preflight `
  --manifest <frozen-manifest.json> --manifest-sha256 <canonical-manifest-sha256> `
  --output-policy <reviewed-output-policy.json> --output-policy-sha256 <canonical-policy-sha256> `
  --bundle <trusted-bundle.json> --bundle-sha256 <bundle-sha256> `
  --worker-code-sha256 <worker-code-sha256> --confirm-database <owned-local-database-name> `
  --receipt-directory <ignored-repository-data-directory>
```

5. For the owned disposable target only, replace `preflight` with `apply` while retaining all pins. Archive/demo/evaluation/lineage changes commit together. Repeated and concurrent execution reuses stable outputs and never reactivates deactivated demos. Native-only groups remain inspectable without invented scalar indices. Retain unique `output-*.json` receipts; no shared output apply is qualified by Phase 1. An error after database commit but before writing the private receipt requires a pinned repeat/read to reconcile output state.
6. To read saved native output through the existing API, independently create a descriptor containing exactly `schema_version: saved-native-read-context-v1`, the authenticated `pipeline_version`, and `database_identity_sha256` from `database_identity(engine)`. Save it privately; configure `LANES_NEWS_NATIVE_READ_CONTEXT` to that file and `LANES_NEWS_NATIVE_READ_CONTEXT_SHA256` to its canonical JSON hash. This selects saved reads only. It does not enable native scheduled RSS, inference or publication. Missing configuration preserves legacy selection; malformed/tampered configuration returns a visible unavailable error.
7. Inspect News Intelligence evidence, both active maps and the unified Flood Events/Analytics history. The user removed the added Historical dataset selector; dataset/session identifiers remain internal lineage. Deactivate via the existing authenticated Spatial Operations action and confirm retained history. Per the later user correction, preserve the existing badge/modal presentation and do not render a demonstration label. Internal lineage and routing/count exclusions remain. Original archive dates/geometry/lifecycle stay unchanged. Demo activation/deactivation are administrative timestamps. Unknown source endpoints remain null; supported exact instants without sourced closure use the explicitly labeled two-hour assumption, excluded from observed-duration analytics.

The historical source adapter is now `historical-source-interpretation-v2`: a separately derived placement view preserves original neural/rule output while supplying an authenticated single-road target and bounded source-local qualifier to existing placement services. Group-local sourced clearance is retained where supported. Older E1 receipts remain historical evidence and are never rewritten to claim this newer behavior.


## Phase 2 — additional existing saved articles

The user clarified two intended outputs: selected September articles generate active flood-zone instances, and other existing saved articles are evaluated for supported Flood History observations. Existing ended September history must not be mistaken for completion of the active-zone path. Separate active instances retain links to the same source and original history; another September archive import alone is insufficient. The current E0 loader intentionally enforces exactly two bound inputs. Do not loosen that check, add unrelated input IDs to its policy or edit the sealed E0 files to process the rest.

The [Phase 2 checklist](../task_plan.md#phase-2--deploy-and-demonstrate) first inventories saved immutable article versions, compatible completed runs and existing history, then implements/qualifies separately authenticated bounded batches. Record supported observation dates, source/geometry outcomes and matching incident identities across articles; missing dates and unresolved/non-event content are explicit outcomes rather than invented Flood Events. Reuse matching history and append lineage; insert inactive archives only for genuinely missing supported observations. Preserve current operational event lifecycles and the existing unified history view. This is pending additional-batch implementation, not a claim that the present two-input command already imports the full corpus.


## Phase 2 execution order — 2A history seeding, 2B September active zones

Follow [Part 2A](../task_plan.md#part-2a--seed-flood-history-including-ner-training-articles) first. Inventory existing application sources and original articles used for NER training, reconcile source/article/incident overlap, freeze bounded archive seed batches and qualify the general seeding implementation and shared release before apply. Preserve original bodies and dates; one training passage is not one article or flood event. Training membership is internal provenance, not proof of unseen model accuracy. Retain explicit unresolved outcomes and inactive-only historical output. Validation/holdout partitions and retraining are outside this request.

Then execute [Part 2B](../task_plan.md#part-2b--september-articles-for-active-flood-zones) using the preserved September package and qualified release. Check overlap with seeded history, generate accepted geometry using actual compatible extraction, and save the selected separate active instance. Verify both maps, normal authenticated deactivation, retained history and repeat safety using the existing design. General preparation is implemented below; shared execution remains gated by storage/runtime qualification and exactly reviewed authority.

## Part 2A — General source inventory and archive preparation

Use the existing backend environment loader and invoke commands as Python modules from `backend/`. Keep bodies, selections and receipts under ignored `data/`. Training annotations and passage text never substitute for a complete article.

1. `python -m scripts.inventory_news_history_seed` accepts repeated `--provenance`/`--provenance-sha256` pairs, a pinned `--source-register`, optional repeated pinned `--captures` full-source JSONL files, `--confirm-database` and private `--output`. Input file hashes bind raw bytes. It reads the database in read-only transactions, joins only train membership, and emits inventory, selection and complete-capture documents. A corrected source capture can resolve a hash missing from an older register; dev/held-only sources are excluded.
2. `python -m scripts.register_news_history_captures` preflights `--captures`, `--captures-sha256` (canonical JSON hash of the **captures object**), `--target-sha256` and `--confirm-database`. Existing selected publishers govern admission; other publishers stay unresolved. `--apply` is restricted to owned loopback `lanes_p3_verify_*` databases with environment `test`. It performs no extraction/publication. New articles use existing `local_update` scheduled exclusion; existing article bodies/review states remain unchanged. Original date-only publication metadata is retained without inventing an hour.
3. Prepare selection JSON with `dataset_id` and explicit `version_ids`. `python -m scripts.prepare_news_historical_inputs` accepts `--selection`/`--selection-sha256` alongside its existing bundle/worker/target pins. Without selection options the frozen September preparation remains available. General packages are archive-only and support one or multiple articles within the existing 200-input worker bound. Native captures retain publication proof for exact reuse. Re-freeze after application/assets change; preserve earlier packages.
4. Run the existing historical processing **preflight**. Compatible completed native runs are reused; fresh processing requires qualified native storage and the Linux one-CPU/three-GiB runtime. Windows preflight cannot establish that qualification. The twelve-source shared preflight currently reports storage/migration and runtime/authority blockers; no shared processing ran.
5. After completed extraction, use the existing historical-output preflight and separate output policy. Archive matching requires retained evidence and supported place/time identity; cross-article reuse also requires equal qualified geometry. Ambiguous identity and geometry disagreement require review. Apply stays disposable-only until a separate shared output release is qualified and reviewed; E1 processing-only authorization does not authorize archive writes.

New archives prefer source clearance. Without clearance, supported exact observations use the labeled two-hour assumption; date-only observations use next-day 00:00 Asia/Manila (`assumed_source_day_end`) while start hour stays unknown. Assumed/admin intervals never enter observed-duration statistics. Unresolved source clearance is not replaced by an assumption. Matched archive lifecycle dates and geometry remain unchanged.

The unified history uses original news source days, separate administrative timestamps and source evidence in existing View Event details. Citizen submissions remain Reports; zero citizen reports is valid for a news event. No dataset dropdown, badge redesign or demonstration notice is added. See [verification and execution status](../evaluations/news-history-part2a-20261022/README.md).
