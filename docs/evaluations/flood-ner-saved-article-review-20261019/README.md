# Saved database article extraction review and source link

> **Last Updated:** October 19, 2026, 11:03 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The backend response now includes `source.canonical_url`, copied from the same saved input snapshot already used for the request hash. The source link remains attached to the exact body being extracted. No frontend, schema migration, collection or plotting change was made. All **379 preview tests pass**, including response URL assertions.

## Actual database check

One saved flood-list article was read through the real endpoint using a read-only PostgreSQL transaction and the real isolated model worker. Administrator authentication was overridden only inside the test app; existing authorization behavior is covered separately by the API suite. The request returned 200 with the correct saved URL and body hash. The transaction was rolled back. The application feature flag was enabled only in the check process and remains off in ordinary local configuration.

The response contains 53 original/effective location mentions, 31 groups, 59 facts and 13 unassigned facts. Review accounts for all 59 facts and all 26 measured source rows. All 52 extracted depth substrings and their source offsets match the stored text. **Source-exact recognition does not establish correct location association.** This single-article diagnostic is not a new accuracy measurement or an independent benchmark.

## Findings — extraction is not fully correct

- **Equivalent depths split across a junction:** numeric and verbal descriptions in one measured row can be attached to different road mentions instead of retaining the named junction as the joint target. Nineteen junction rows do not retain complete collective scope; some also have missing/incomplete mentions. Preserve the distinction between matching errors and absent neural targets.
- **Missed list clock:** a dotted clock without its final period is not recognized. The inherited clock pattern accepts the fully dotted form or the undotted form. Report/list timing must remain separate from onset; a future repair must establish its grammatical role and list scope rather than using publication time.
- **Incomplete or missing locations:** several street/address rows lose their specific target, retain an incomplete road name, or attach to a broader locality. Eight depth facts remain unassigned across four measured rows. Other specificity errors are resolved to incomplete targets and therefore are not included in that unassigned count.
- **Dateline treated as observed city flooding:** the opening city dateline receives status/date even though the sentence describes the metropolitan region. A dateline must not establish a separate city-level flood observation.
- **List access context:** heading-level vehicle restrictions are not carried through to the source rows; the caution modifier is not preserved in the extracted access value. Do not treat this as correct per-location access extraction.
- **Appropriate abstentions remain:** the vague subsided-area statement retains its status without inventing named affected places. A forecast duration and rainfall-warning time remain unassigned rather than becoming flood onset. These are distinct from the demonstrated misses.

The ordered target/value matching branch explains the split-depth behavior when two depth descriptions and two targets occur together; conjunction handling mistakes the equivalent descriptions for separate measurements. Recognition boundaries and heading/clock handling are separate causes. No model, extraction rule, reference or historical result was changed during this review.

## Evidence and next task

Private input, code freeze, read-only database receipts, full API response, source slices, 26 row dispositions and 59 fact dispositions are retained under `backend/training/flood_ner/artifacts/ner-preview-source-link-20261019-v2`. Four pre-change application/test files were copied with their original v1 hashes before the additive URL change; earlier adapter receipts remain historical. The publisher page was not fetched: this review compares extraction against the exact stored article body.

The backend connection and source-link checks pass. Full-article extraction readiness remains open. The next proposed work is a separately scoped repair of equivalent-depth/junction matching, list clocks/header scope, dateline exclusion and recognition-dependent omissions, with constructed regressions and the frozen v41 controls retained. This review does not implement those repairs or authorize frontend/plotting changes. [Operator guide](../../guides/ner-backend-preview.md) · [Aggregate receipt](verification.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)
