# GMA three-location News Intelligence completion

> **Last Updated:** October 23, 2026, 7:07 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Completed correction 388 is serving three accurate GMA observations on navlanes.live and localhost.** API/manual-worker v26 is deployed; the frontend is unchanged. This completes GMA News Intelligence extraction and reader verification only. No GMA historical event, polygon or active instance was created. Tribune 25, Philstar 274 and spatial qualification remain pending review.

## Accepted source and observations

Article **47**, original source **140/native 569**, retains the complete 1,297-character publisher capture, SHA-256 `f5ff7d13e255ed82ab9c024bcd1aae02fee4ce5806c4a7411bc818e2f58ed763`. Immutable **NER 382** was reused without inference. The three accepted projected targets are n6, n8 and n10.

| Reported location | City / supported locality | Source facts |
|---|---|---|
| Rizal Ave Extn | San Agustin, City of Malabon | Gutter deep; September 9, 2026, 2:47 PM Asia/Manila; passable to all vehicle types |
| Tañong F. Sevilla Blvd. (Bayan) | City of Malabon; Tañong retained verbatim in the reported section | Same reported depth, time and passability |
| Marcos Highway Underloop | City of Marikina | Same reported depth, time and passability |

Individual measured inches/meters remain **null**. Marcos Highway keeps its original **LANDMARK** label; no retagging or geometry substitution occurred. F. Sevilla's canonical barangay remains **unknown** because this source names Tañong in the road section without explicitly assigning an administrative role. The exact Tañong wording and Malabon city evidence are preserved and displayed; no missing field was fabricated.

## Repairs, retained failures and finalization

The opt-in `scoped-quote-options-v4` contract preserves the v3 city-heading repair and adds exact inline-locality ownership. Brgy San Agustin is context for the independently accepted Rizal Avenue observation only when their source entry, city, clock, condition, depth scope and access agree. Its original provider row remains unchanged. The derived context-only record retains owner n6, passage 9 and exact locality offsets. Independent locality-only reports, ambiguous ownership, wider-area statements and unsupported/conflicting owning roads are not silently suppressed. V2/v3 behavior remains reproducible.

Two existing paid v3 responses were authenticated and adopted by immutable bundle hashes. Their original prompts, article text, quote ordering, targets, native proposals, model and generation settings are retained. Only the reviewed instructions/layout contract differs in the new projection; adoption does not claim those responses were generated with v4 and does not settle their spending again.

One new full-article n8–n10 request ran in `lanes-news-verified-vntf5`. Its references and source-fact checks passed and supplied all three projected observations, but the final manual gate unnecessarily required F. Sevilla's `barangay` field to equal Tañong. Gemini had returned the correct verbatim section and city, with `barangay: null`; failed correction **387** is preserved.

The v4 final gate was corrected to require the exact supported **Tañong F. Sevilla Blvd. (Bayan)** section and Malabon city, rejecting a conflicting barangay while allowing an unknown role. The ordinary reference, date, location, depth and passability validators were not relaxed. The older v3 gate remains unchanged. A regression verifies this source distinction.

A separately frozen **zero-provider finalization authority** then adopted all three retained responses and saved completed correction **388** in `lanes-news-verified-pqcq6`. Its budget object rejects every provider reservation, its resolver receives a network-forbidden client, and it verifies the stopped ledger's content and generation before and after. No new generation or token-count call was possible in this operation. Repetition `lanes-news-verified-rgt5p` reused 388 with **zero provider requests and zero additional extraction rows**. Failed runs 386/387 remain immutable.

## Releases and spending

| Item | Verified identity / result |
|---|---|
| Serving API | `lanes-api-gma-inline-finalize-20261023-v26` |
| Manual-worker image | `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-news-verified@sha256:b51d1185d2320800a7ba9a4a38336470f8c7e636b26f71d44d9c9e18cd7055a3` |
| Release hash | `ca6befd3719e1882a37d9183bb933848e8545faa6a65da05f7956613221a961b` |
| Corrected pipeline | `ner-v1:abb4e0674b807a124328dbabc65cd71f2df9c4f8362a4280a197a1b9672482f6` |
| Original parent proof | NER 382 authenticated against original frozen v23 release; model/runtime/spatial identities unchanged |
| Runtime | Linux amd64, 1 CPU, 3 GiB, 600 seconds, zero automatic retries; supervised shutdown |
| Credentials / defaults | LANES secret version 2; general processing disabled; default read-only preflight; personal key unused |

The baseline **41 attempts / US$0.748841 effective commitment** was preserved through an immutable one-request accounting transition. The sole new request counted 5,934 input tokens and reserved a full maximum **US$0.0238403**, yielding a reviewed maximum cumulative commitment of **US$0.7726813** under the unchanged US$1 cap.

Actual retained usage was **5,934 prompt + 749 candidate tokens**, zero thinking tokens: **US$0.0036527** estimated usage. The ledger remains **stopped at 42 attempts / US$0.7524937 effective commitment**. Finalization and repeat did not change its content or storage generation. These estimates and conservative commitments are not verified invoice charges. All earlier attempts, reservations, settlements and failure receipts remain retained; no retry, model fallback, cap increase or spending reset occurred. Cloud hosting and ordinary weather costs remain outside the news allowance.

## Verification and preservation

- **234 regression tests passed**, including source-context ownership, independent locality reports, unknown administrative role, invalid citations, cached-adoption tampering, interrupted/resend rejection, concurrency/storage failures and accounting limits.
- **29 PostGIS tests** and fresh/repeated upgrades through existing head `f1a9c7e2b604` passed. No models, migrations, dependencies or public API shapes changed.
- **Seven frozen Linux contracts** passed. Actual saved parent/model/runtime/spatial bindings and canonical UTF-8 request hashes agree across Windows and Linux.
- Frozen-image disposable verification adopted **all three actual responses**, saved exactly three observations and reused them with zero provider calls/new rows. An outbound tripwire would reject any provider dispatch.
- All three provider bundles replayed twice with networking disabled. The complete accepted saved result and source bindings independently recomputed twice, including context-only ownership and original raw labels.
- Protected API canary passed three cards/details, source hashes, counts, filters, pagination, authentication and unchanged history/analytics/export/active readers before API promotion. Local reader selection was re-pinned to the same pipeline while retaining its TCP database identity and local signing key; the task-equivalent backend was restarted.
- Actual **hosted/local desktop and mobile** checks passed all three summaries, source articles, time/depth/passability, modal scrolling and no raw-NER duplication in Flood Details. A screenshot of the hosted F. Sevilla summary was visually inspected. Existing UI and frontend artifact were unchanged.

The overall continuation added failed extraction **387** and completed extraction **388** only; finalization added just 388 relative to its own baseline. No article/version, claim case/source/evaluation, citizen report/moderation, event/zone/location/timeline or account/community record was modified by this task. Earlier runs, source bodies and five supersession markers remain exact. Repeated execution added no extraction rows; ordinary serial allocation was not reset.

During implementation, independent authenticated admin actions created, edited and deactivated **event/zone 76**, evidenced by `CREATE_OFFICIAL_ZONE`, `UPDATE_ZONE` and `DEACTIVATE_ZONE` audit records. Its latest baseline was captured separately and preserved. Consequently, existing Flood History contains that **one manual ended event**, rather than being empty; it was not produced by GMA. The five superseded news archives remain retained/excluded, and public active zones remain empty. Normal routing and existing event lifecycles are unchanged.

News collection/processing/publication stays paused, both expiry switches OFF, and the old seed job remains disabled. No scheduled RSS behavior, source facts, original training/model assets, UI or schema changed.

## Evidence, review stop and recovery

Ignored private evidence is retained under `data/gma-inline-20261023/` and `data/gma-inline-finalize-20261023/`: original-parent proofs, immutable cached bundles/pins, count/reservation/settlement receipts, both release manifests, stopped ledger snapshots, failed 387/completed 388, canary and serving identities, before/after fingerprints, independent admin-activity evidence, offline replay, repeat receipts and hosted/local desktop/mobile screenshots. Earlier `data/gma-heading-repair-20261023/` evidence remains unchanged.

**Stop for GMA review.** This completes three-location News Intelligence, not all three articles or automatic plotting. OSM/NOAH qualification, genuine Flood History outputs, Tribune, Philstar and active presentation instances require their separate continuation scope. Do not resume the stopped ledger or consumed authorities automatically.

Recovery retains database/evidence and stops execution. Previous serving v23 and worker specifications are preserved privately; reverting readers must retain supersession support. No reset, destructive cleanup, reseeding, commit or push was performed.
