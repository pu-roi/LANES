# V46 qualified location repairs connected to the backend preview

> **Last Updated:** October 20, 2026, 12:58 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Backend-preview integration is complete and verified.** The selected combined location repairs now run between v40 proposals and unchanged v42 grouping. The trained v19 model is unchanged. The preview remains disabled by default; the admin-panel interface is the next task.

[Verification](verification.json) · [Metrics](metrics.json) · [Approved plan](../../plans/ner-backend-location-repairs-v46.md) · [Backend guide](../../guides/ner-backend-preview.md).

## Resulting behavior

The pipeline is **v19 neural locations → v40 proposals → v44 combined repairs → v42 context grouping**. A shared pure adapter serves the isolated worker and host validator. V44 is a verbatim authenticated runtime copy; application code imports no research workers, fixtures or scorers.

Original neural mentions remain separate from effective mentions. Ordered proposals preserve both stages' hashes and implementation identities; abstentions identify their implementation stage. Boundary replacements retain original mention IDs, exact source spans and evidence and are explicitly rule proposals. The host recomputes both the complete proposal chain and graph, rejecting altered proposals, stale provenance and structurally valid but mismatched facts/targets without fallback.

The endpoint and `lanes-ner-preview-v1` fields remain unchanged, including article URL, grouped fields and unassigned facts. Provenance now reports `location_rules: lanes-location-repair-v40+v44`, `location_method: combined` and unchanged v42 context identity. The response includes the type-family and rule-versus-neural limitations.

## Verification

**1,281 software checks pass**, covering the adapter and preserved context/proposal behavior, authorization, disabled-feature/errors, source/Unicode handling, temporal roles/qualifiers/subsided evidence, concurrency, isolation and cleanup. Tampering checks reject proposal actions/hashes/origins, abstention stages, effective labels, old/mismatched location provenance, changed measurements, partial target groups and invented onset roles. The only existing test-fixture change supplies the intentional new pipeline/provenance; semantic expectations remain intact.

Before wiring, cached parity matches all **788 inputs**, all **407 saved context graphs**, **418 applicable fixtures** and **three repaired-view expectations**. Original-control expectations remain preserved through the authenticated v45 evidence. No neural inference occurs during these cached checks.

One real isolated-worker API request then succeeds using the existing saved article snapshot and fake read-only article storage. It preserves **all 53 original neural mentions** and exactly matches the saved combined effective mentions, proposals, abstentions, graph and groups. The article retains eight corrected location occurrences and 40 restored facts across eight measured rows. **Eleven rows remain unresolved**. All 34 affected target occurrences, 19 affected rows and 93 affected facts reconcile, with 53 affected facts still unassigned; the eight previously complete article rows remain retained. No depth is invented for the unmeasured junction.

Actual container inspection confirms the pinned qualified Linux image, two CPUs, 4 GiB RAM/swap, no network, read-only root/code/assets, dropped capabilities, no-new-privileges, 128 PIDs and bounded temporary storage. Completion inspection confirms a successful stopped worker; owned-container removal, empty matching-container query and cleared lease verify cleanup. No inference retry occurs. Independent verification repeats cached parity and validates source/model/code bindings, response shape/link, proposal provenance, isolation and cleanup without another neural inference.

## Preservation and limits

Twenty predecessor application/test files were snapshotted before edits. Five existing files change intentionally: the worker, host service, projection limitations, active promotion manifest and shared test-runner fixture. Four predecessor promotion hashes are reconciled against authenticated snapshots; the historical promotion receipts themselves remain unchanged. All frozen v40/v42/v44/v45 code and evidence remain intact.

All 208 protected evidence hashes and 55 frozen v41 files match. Historical metadata matches 1,538 entries, with the earlier declared config change separately accounted; all 82 excluded metadata entries match (sets overlap). Validation/holdout contents were not opened. Environment-file metadata, requirements/package manifests and normal processing remain unchanged. The private bundle and original model/resource manifests are authenticated without training or asset changes.

The real API check uses no database connection or writes. No article fetch, frontend, normal news-processing activation, history storage, geography/plotting, routing, upload, commit or push occurs. The default feature flag remains false; verification enables it only in scoped process configuration and restores it afterward.

The combined view is qualified within the exposed development workload. The type family still lacks a standalone real correction, and existing strict recognition errors, 11 unresolved article rows, three reference holds, the non-flood access omission, unfinished learned DEPTH/TIME recognition and unmeasured real pure-Tagalog performance remain. This integration check is not an independent accuracy measurement.

Observation/report/publication clocks never establish onset automatically. Subsided status/time remain extraction evidence. The requested future database-history-without-current-plotting behavior remains subsequent work.

## Next task

Plan the admin-panel interface for this existing backend preview: article link, extracted location/depth/time/status/access, labeled rule changes and unresolved information. No further backend research gate is added by this result; ordinary interface/API verification still belongs to that task.
