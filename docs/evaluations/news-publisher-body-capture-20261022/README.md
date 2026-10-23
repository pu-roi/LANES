# Automatic publisher-body capture and September 9 correction

> **Last Updated:** October 22, 2026, 3:45 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Automatic GMA capture is fixed and verified locally. After reviewing the original publisher replacement, the user explicitly approved **“Apply this one-article correction”** as a narrow exception to the earlier shared-write restriction. Article **47** now selects new immutable version **140** and completed rules-only run **140**. Original version 137/runs 137 and 139 and ended history remain intact. Phase 2 seeding, native inference and active-zone execution remain open.

## Defect and fix

The manually imported September 9 article 47/version 137 came from a 9:55 AM search-index snapshot, wrapped in reconstructed HTML. That imported text is distinct from the retained original publisher HTML updated at 3:09 PM. Separately, normal automatic retrieval read GMA's outer article/main wrapper, allowing the repeated headline, Google promotion and caption into the saved body.

`backend/app/services/news_discovery_service.py` now selects GMA's standard `story_main` or AMP `article-text` reporting container. It keeps source byline/publication/update evidence needed by the existing temporal checks, preserves paragraph/list boundaries and the final reporting paragraph, and excludes page chrome, captions, related/dynamically loaded articles and scripts. Missing/short reporting bodies produce a retrieval error rather than an outer-page or JSON/index fallback. Existing size, redirect/domain and continuation checks remain. Other publishers retain their current parser; the September 24 Tribune body remains exactly 1,136 characters with SHA-256 `dc4773d602277a22fb0660705e21eb45f64125f4bd8167cd55ad21ec3350bc0f`.

Existing reconstructed GMA replay wrappers now declare the body container. Their original indexed source bytes remain unchanged; this compatibility adjustment does not make the old index capture original publisher HTML. The old September 9 local replay adapter also forwards the current `local_update_only` argument. SQLite source-health fixtures include the current settings/checkpoint tables, and the replay fixture derives its historical publisher label from the current registry so the immutable-version assertions still test identical inputs.

## Verification

- Capture/discovery/replay and network-boundary batch: **225 passed, 13 subtests passed**, with 20 PostGIS cases initially skipped.
- Those native cases were then run with owned disposable PostGIS: **22 passed, no skips**. Across the two batches, **245 distinct test functions/parameter cases pass**. Three owned databases were removed; no case databases remain.
- New capture checks cover standard/AMP pages, whitespace-preserving native capture, exact source update anchors, full lists and final paragraphs, related/second-story suppression, absent/short bodies, ordinary RSS discovery, append-only source versions, repeats and failed-refresh evidence retention. Existing protected reads, blocked-source, continuation, size and other-publisher regressions pass.
- Retained standard/AMP publisher captures produce complete reporting bodies without the Google promotion; both retain the September 9 3:09 PM update anchor. Fresh live retrieval through the normal bounded fetcher also succeeded.
- All seven changed Python files parse; no dependency, schema, UI or scheduled-RSS configuration changes were introduced.

A broader September 9 extraction check has **36 passes and two existing failures**. Replacing the collector in memory with its original Git HEAD implementation reproduces both: one assertion expects an older uncertainty-reason name, and one independent-road sentence incorrectly inherits another road's clock. They remain unresolved and are not counted as successful article-capture acceptance. Real source/temporal qualification must address these separately before claiming the broader extraction suite is green.

Private receipts and logs: `data/news-gma-body-fix-20261022/` (`capture-regressions.xml`, `checks.xml`, `baseline-extraction.xml`, `captures.json`, `cleanup.json`). No credentials are included in this public report or its [structured summary](summary.json).

## Applied September 9 replacement

A fresh approved-publisher fetch supplies a **1,297-character** reporting capture updated September 9 at **3:09 PM PHT**, retaining original publication **9:19:06 AM PHT**. Its body SHA-256 is `f5ff7d13e255ed82ab9c024bcd1aae02fee4ce5806c4a7411bc818e2f58ed763`; proposed immutable input fingerprint is `3305b740213c71681f13fdb53f4ed1a3141f4b8e4d00a6294e5d22afa06af7fa`.

The separate rules-only preview finds the later report's three listed road observations at **2:47 PM**: Rizal Avenue Extension and F. Sevilla Boulevard in Malabon, and Marcos Highway Underloop in Marikina. Pump-deployment references to E. Rodriguez/Araneta remain context with unknown observation facts; they are not invented flood-zone decisions. No native NER inference, publication, geometry acceptance or activation was performed.

The approved correction targets article **47**, appended immutable version **140** and completed rules-only run **140**, and selects that completed run for the newer article results. It preserves morning version **137**, completed runs **137/139**, and ended/inactive event/zone pairs **61–63**. These morning events must not inherit the later report's locations. The September 24 record and the frozen E0 package are untouched; using the newer GMA input in Part 2B needs a separately reconciled input/match selection rather than editing that package in place.

Reviewable private artifacts: `replacement-article-47.txt`, `replacement-snapshot-47.json`, `replacement-rules-preview-47.json`, `replacement-review-47.json`; final verification is in `applied-article-47.json`. The apply computes the actual existing rules/placement-preview result before locking, pins the exact target/current source, then atomically saves article text, immutable input, normal owned queue completion and actual administrative timestamps. The target still has the legacy unique constraint at migration `d7e4b9a21c60`; a normal bounded INSERT respects that deployed key without applying a native-mode migration. No event/publication service was called.

Apply-side retained-row hash checks passed before/after commit. Final verification ran in a new database-enforced read-only transaction: the article reader and all three result readers return the new input; old version 137's fingerprint remains exact; old runs remain completed; event/zone fields, locations and timeline counts match the earlier inspection. Global events/zones remain **56/56**, and source/case/evaluation/decision/zone-link counts remain **53/53/75/87/6**. Article 47 has two versions and three completed runs. An operator verification initially accessed a typed DTO as a dictionary after commit; this verification-only error was corrected and completed read-only, without repeating the shared write.

Reload News Intelligence and reopen the newer September 9 result to see the corrected source. Opening an older processing-history record intentionally continues showing its original morning evidence. Original source: [GMA September 9 flood alert](https://www.gmanetwork.com/news/topstories/metro/1001693/list-flooded-roads-in-metro-manila-wednesday-sept-9-2026/story/).
