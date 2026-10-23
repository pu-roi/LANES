# Manually verify saved NER output with Gemini

> **Last Updated:** October 22, 2026, 10:50 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current execution stop:** GMA raw run 375 is completed; derived run 376 failed `native_resolution_evidence_invalid` after 13 successful requests. The same ledger is stopped with 17 attempts/US$0.6481486 conservative reservations. Do not rerun correction or advance to Tribune/Philstar: first retain private provider batches and precise evidence diagnostics, then inspect/qualify the cause-specific repair. No events/zones were created. [Actual execution and limits](../evaluations/three-article-cloud-pilot-20261022/pilot-execution.md). Earlier successful fictional-provider acceptance below remains valid but does not supersede this real-article gate.

Current LANES version-2 credential passes actual cloud provider/backend acceptance. Personal version 3 remains stored and unused. The HTTP 400 was isolated by schema-only comparison; the accepted release uses compact schema with exact batch IDs/count and strict local evidence validation. [Repair, release, spending and recovery](../evaluations/three-article-cloud-pilot-20261022/provider-repair.md). Earlier HTTP 402/personal-key attempts remain historical evidence, not current provider blockers.

The real smoke test passed quoted-time/source validation and saved-result recomputation using fictional evidence. It does not establish real-article NER or spatial accuracy. The subsequent GMA attempt is recorded above; no flood outputs were seeded. Do not paste keys into commands or committed files, automatically repeat provider checks, or reset the stopped cumulative US$1 ledger.

## Cloud operating state

API revision `lanes-api-gemini-fix-20261022-v5` serves navlanes.live with the matching derived/raw reader context. Separate manual job `lanes-news-verified` has one CPU/3 GiB, 600 seconds, zero automatic retries and no scheduler. Resolver profile is explicitly `compact`, config revision `native-gemini-compact-cloud-v2`, model `gemini-3.5-flash-lite`. Its default `preflight` verifies frozen application/model/reference hashes, exact Cloud SQL target/schema, saved readers, configured secret binding and paused news settings without provider requests or database writes. `contract-check` adds fixed fictional software checks with outbound sockets denied after preflight.

General provider execution remains disabled. `resolve` additionally requires explicit `LANES_NEWS_GEMINI_EXECUTION_ENABLED=1`, at most two raw run IDs and the exact hash-pinned resolve authority; none are supplied by default. `provider-check --allow-one-provider-request` is a distinct, explicitly authorized fictional one-request smoke test; never use it as an automatic readiness probe. The accepted October 22 request does not process saved articles or save fictional data. The spending ledger is stopped pending explicit review of the next article stage.

News collection/processing/publication and the news scheduler remain paused. The historical seed job retains its disabled no-op command. Existing scheduled RSS method/resources and zone-expiry scheduling are unchanged; both expiry flags stay OFF. No UI artifact was deployed. Future selected articles require newly frozen input/application authorities; old manifests cannot authorize this release. Restore retained API revision `lanes-api-gemini-20261022-v4` and the prior manual-job specification to roll back serving code, keeping data and receipts intact.

## Restricted three-article pilot

The supervised manual worker now also exposes `pilot-ner`, `pilot-resolve`, `pilot-preview` and `pilot-apply`. Each requires an exact SHA-pinned authority object under the private approved storage prefix. These commands accept one article/run per invocation, bind exactly three original/native source captures and keep all ordinary news flags paused and both expiry switches OFF. Do not reuse the ordinary resolve authority or an archive-only authority for pilot activation.

The funded `provider-check` additionally requires `LANES_NEWS_PILOT_BUDGET_OBJECT` and `LANES_NEWS_PILOT_BUDGET_IDENTITY`, pointing to an existing private create-only ledger in `lanes-storage`. Runtime access is conditional on the exact ledger object; authorities have a separate read-only prefix. No missing, stopped, in-flight, conflicting or exhausted ledger is reset automatically. Retain failed/unknown dispatches and investigate before explicit resumption. Price reservations include full request framing, maximum output and thinking tokens. Provider diagnostics retain bounded redacted messages, allowlisted reasons/field violations and status; never credentials, unrestricted metadata, headers or raw error bodies. Target mismatch diagnostics retain counts, not generated facts.

Read [the current pilot checkpoint](../evaluations/three-article-cloud-pilot-20261022/README.md) before running any mode. Local tests/image construction do not establish successful Gemini acceptance or authorize skipping cloud acceptance gates.

## Post-reset prerequisite

The separately authorized October 22 cloud reset removed every extraction run and flood output while preserving 174 articles/224 source versions. The pilot has since registered Philstar and completed GMA parent NER run 375 on native version 574; derived run 376 failed. Current counts are 175 articles/226 versions/two runs/zero flood outputs. Preserve these stages and inspect the failure before any new correction dispatch. Do not reuse deleted pre-reset IDs, obsolete authorities or historical batch receipts as current execution approval. The model and earlier private evidence remain intact; news automation stays paused. [Reset acceptance](../evaluations/flood-data-reset-20261022/README.md) · [Current pilot](../evaluations/three-article-cloud-pilot-20261022/pilot-execution.md).

## Read-only preparation

Run from `backend/` with the normal decrypted backend environment and virtual environment. Keep `LANES_NEWS_AUDITOR_BATCH_SIZE` at 4 or 8, `LANES_NEWS_AUDITOR_CONFIG_REVISION` valid and `LANES_NEWS_GEMINI_SCHEMA_PROFILE` explicitly configured. `--model` selects the Gemini model independently of the legacy source-rule model setting. No SDK/dependency installation is needed.

Choose at most two completed original native run IDs. Supply the authenticated unchanged NER bundle and worker-code hashes. The bundle is verified without loading/inferencing the model. Write receipts under this repository's ignored `data/` directory.

```powershell
.\venv\Scripts\python.exe -m scripts.resolve_news_native preflight `
  --run-id <original-native-run-id> --model <qualified-gemini-model> `
  --bundle <authenticated-bundle-folder> --bundle-sha256 <bundle-hash> `
  --worker-code-sha256 <worker-code-hash> `
  --confirm-database <exact-database-name> `
  --receipt-directory <absolute-repository-data-subfolder>
```

This makes no Gemini request or database write. Review the generated authority and its printed hash. It binds exact database identity, selected inputs/parent result hashes, current application assets, model/prompt/config identity and `resolve` only. Retain it privately. Do not reuse an old application's asset pin or overwrite original Part 2A evidence.

## Explicit processing

Use the same arguments and selected run order, change `preflight` to `resolve`, and add:

```powershell
  --authority <generated-authority-file> --authority-sha256 <printed-authority-hash>
```

This can incur Gemini charges. Shared targets require the exact authority; default authority-free operation accepts only explicitly named disposable `lanes_p3_verify_*` databases. The existing approved Alembic head and PostGIS are checked. Each article commits its own owned result; the command creates no citizen reports, live decisions, flood events or zones. A failed second article cannot erase a completed first article.

Retain receipts before resuming. A completed repeat reuses the same derived run with zero API calls. Retryable transport/429/5xx failures wait under existing run backoff/attempt limits; nonretryable failed runs require investigation, not automatic reset. Cancellation remains cancellation after saving its bounded retry state. Selected-source suppression is checked again after the request, before saving corrections.

## Existing interface and downstream use

Preflight writes a hash-pinned `saved-native-read-context-v2` descriptor and prints its path/hash plus the derived pipeline version. Configure the matching backend release with `LANES_NEWS_NATIVE_READ_CONTEXT` and `LANES_NEWS_NATIVE_READ_CONTEXT_SHA256` pointing to this exact descriptor. Its explicit raw pipeline fallback versions keep other retained native articles visible during rollout; for each article the latest selected native attempt wins, including failed/pending verification. A failed verification never silently reverts to an earlier raw or legacy result. Preserve all previously approved raw versions when preparing a release-wide context; a two-article preflight names only its selected parents. This exposes corrected scalar facts through the existing cards, source detail and filters without new UI labels/components. Original source versions and NER runs stay in article history; the native evidence panel retains original model evidence.

The local Linux native pipeline also accepts `--verify-with-gemini --gemini-model <model>` with its existing bundle/hash flags. It resolves raw output before existing evaluation/publication gates. Its disposable-target guard remains intact. The matching manual resolution worker is now deployed, but the scheduled cloud RSS worker and disabled Part 2A seed job are unchanged; purchasing credits alone does not enable article processing.

Historical source dates remain historical. Spatial/NOAH qualification, incident matching, routing eligibility and lifecycle checks still decide downstream effects. Administrative publication-time starting-time proxies are internally marked and do not become measured-duration statistics.

See [implementation and release boundaries](../plans/ner-gemini-verification.md). Google documents the [structured-output API](https://ai.google.dev/gemini-api/docs/structured-output).
