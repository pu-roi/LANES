# News Intelligence field verification badges

> **Last Updated:** October 25, 2026, 12:46 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: implemented and verified locally. All six new/existing desktop/mobile cases pass. Not pushed or deployed.**

## Behavior and scope

Flooded Areas cards and their Flood Details dialog now display an amber **Needs Verification** badge with separate field chips for location, street/road, water level/depth, flood time, flood condition and source evidence, when the saved evidence requires them. Water level and flood depth share one field to avoid duplicate warnings. Each chip identifies missing, uncertain or conflicting information; an accessible native disclosure explains the reasons without a hover-only interaction.

Decisions are computed in the FastAPI presentation service from existing saved claims, uncertainty, source-audit evidence and capture comparison. React only presents backend-supplied issues. Known source measurements stay visible and are not marked missing solely because their road is unresolved. Qualitative-only measurements are preserved without inventing numerical depth. Missing observation time does not inherit publication time. Changed captures, ambiguous locations and source-depth discrepancies remain distinct reasons.

An existing polygon does not establish a field-verified flooded extent. The seven saved Philstar corrections retain a location-verification issue describing the plotted estimate. Their summaries now say that an estimated zone is plotted instead of repeating stale ambiguous-candidate wording. Original extraction, source text, processing results and old correction evidence remain unchanged. Legacy responses without the new metadata display verification status as unavailable, never an invented Verified badge.

The API change is additive presentation metadata in `NewsFloodSummary`: `verification_status`, `verification_issues` and `placement_is_estimate`. No route, authentication rule, SQLAlchemy model or database schema changed. No new dependencies, migration, provider request, automation change, polygon correction, database write, deployment or Git publication is part of this work.

## Developer location hints and skipped observation

The developer supplied latitude/longitude hints **14.643080, 121.011474** for West Riverside Interior/Damayan and **14.645922, 121.013534** for West Riverside/Pat Senador. They remain developer-supplied hints, not publisher evidence or automatic placement authorization.

Read-only comparison with the checked OSM/community-boundary catalog finds:

- The first point is about **1.5 m** from West Riverside Drive (11435673), but falls in the saved **Del Monte** boundary rather than Damayan.
- The second is about **4.0 m** from Attorney Pat Senador Sr. Avenue (11436044), in the saved **San Antonio** boundary, and about **134.3 m** from the checked Riverside/Pat Senador shared node 101867477.

These are findings from the saved catalog, not cadastral determinations. The differences require review against the source and current map evidence before moving any zone. Neither hint was inserted into a claim or flood record. **Talipapa Alley is explicitly skipped for plotting**, remains unplotted, and may still appear as an observation requiring manual location/street checking. Nothing was deleted or suppressed from News Intelligence.

## Implementation and validation

- Backend: `news_verification_presentation.py` provides pure field review decisions and full-claim recovery for lightweight native details. Existing presentation/list/source-detail readers attach the result without editing inference code or stored evidence. The reviewed-corner reader supplies saved-estimate context.
- Frontend: `NewsVerificationNotice.tsx` is reused by cards and the existing details dialog. Wrapping chips, visible text, 44-pixel disclosure targets and existing grid/modal layouts support mobile and desktop. Card roles/names support assistive technology.
- **47 scoped backend tests pass** for field semantics and result/native routes, including normalized-only depth needing a source-wording check. **43 additional reader/browsing/correction tests pass**: **90 passing backend checks total**. Three existing geometry/PostGIS tests skip because a disposable PostGIS connection was not configured for that run. Geometry construction did not change.
- TypeScript and scoped ESLint pass. All **62 normalizer-bound files** match the previously pinned correction context; inference identity is unchanged.
- **Six Playwright cases pass**: two new desktop/mobile badge cases plus four existing dialog/source cases. Coverage includes known versus missing depth, missing road, estimated placement, older-response fallback, disclosure explanations, source evidence, processing-history navigation, current versus immutable article captures, no horizontal overflow at 320 pixels and landscape, and GET-only interaction. Actual desktop/mobile card and mobile dialog screenshots were inspected: badges wrap, source values remain visible and reasons do not require hover. Final artifacts are retained in ignored `data/news-verification-badges-20261025/final-ui/`.
- Initial browser attempts used the incorrect development startup (encrypted environment was not loaded); the normal project startup fixes that harness configuration. A subsequent fixture lacked the required result `scope` and correctly triggered the application's existing visible error; the fixture was corrected without changing application error handling. The mobile tests explicitly use Chromium, matching existing test files rather than the device preset's default WebKit browser. Existing dialog assertions also referred to an obsolete inner-panel scroll container and capture label; they now check the map action's actual viewport reachability and the existing extraction-input label. Shared dialog layouts were not changed. These setup/test failures are recorded rather than described as passing attempts.

Application tests use isolated fixtures; there is no production-write path in the new presentation service. Existing unrelated News Automation edits and all pre-existing work remain intact. [Earlier location investigation](philstar-location-accuracy-investigation-20261025.md).
