# Plot the two developer-reviewed Philstar coordinates

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). October 25, 2026, Asia/Manila.

The developer explicitly requests plotting West Riverside Interior at **14.643080, 121.011474** and W Riverside/Attorney Pat Senador at **14.645922, 121.013534**. Talipapa Alley remains skipped. This replaces the previous investigation-only instruction for these two entries; it does not revive the cancelled whole-street expansion or authorize reprocessing the seventeen omitted list entries.

## Source and interpretation

- Bind article 274/version 573/result 401, groups resolved-n22 and resolved-n31, unchanged source/body/result hashes and saved source verification. Zero new NER/Gemini requests.
- Treat each pin as a developer-reviewed estimate, not publisher coordinates or independent field confirmation. Preserve original source barangays (Damayan/Del Monte), depth/access (19 inches/light-vehicle closure; 8 inches/caution) and September 9, 4:30 PM Philippine-time observation.
- Retain checked mapped barangays (Del Monte/San Antonio) separately, with explicit mismatch evidence. The second pin is on Attorney Pat Senador, about 134 metres from the mapped Riverside junction; do not present it as a newly proved exact article junction.

## Geometry, storage and delivery

- Select the two checked OSM ways by authenticated catalog/name/ground-level geometry and the reviewed coordinates. Require Quezon City context and no more than 15 metres of road snapping. Follow at most 25 metres each direction on the containing block, stopping at another mapped named-road intersection/end.
- Intersect with exact NOAH 5-/25-/100-year classes, preserve supported core gaps, and construct full rounded staff-road buffers in EPSG:32651 without cropping their outer edges. Susceptibility does not override source depth/access or prove flooded length.
- Take a fresh full backup and baseline row fingerprints. Preview and apply both outputs atomically with source/application/assets/coordinates/buffer/baseline/complete-preview binding and concurrency locks. Preserve all existing rows; append source-bound events/zones/metadata/receipts only.
- Reuse must not duplicate or reactivate manually deactivated zones. Keep historical presentation exclusion from routing/real-event statistics and final-deactivation-to-unified-history behavior.
- Publish the checked backend reader/placement support before shared apply. Existing News Intelligence and active/public maps read saved geometry; original extraction remains immutable. Git publication/main integration and frontend deployment are outside this task.

## Checks

- Run scoped and required PostGIS tests, then restored-data preview, rollback, concurrency/reuse, source projection, map handoff, deactivation/history and no-reactivation rehearsal.
- Confirm all pre-existing records survive, no retention-eligible records would be purged by deployment, ledger unchanged, automation paused and expiry disabled.
- Compare cloud preview with the restored preview, apply once and verify zero-write reuse. Check protected staff/public reads and actual desktop/mobile selected/public geometry and colors.
- Record actual results and limitations in the evaluation, task/progress and bug records. No schema/dependency changes.
