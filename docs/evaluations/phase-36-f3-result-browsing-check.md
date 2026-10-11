# Phase 36: F3 unified news reading verification

> **Last Updated:** October 03, 2026, 12:52 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer finalized one Flood Locations list using the concrete saved Philstar example and authorized implementation. Local reading steps 1–3 are implemented. Developer desktop/mobile visual acceptance remains pending. No browser was opened, browser test executed or development server started.

## Current interface and read contracts

- Main page: one Flood Locations list with specific source-reported segment/intersection headings, area, water level, flood observation time, publisher and Info. Missing depth/time remains explicit.
- Info: Flood Details shows only flood facts and evidence. Source Article uses a wide desktop dialog with article text on the left and independently scrolling processing history on the right. Mobile switches between Article and Processing history within Source Article. Flood facts and supporting sentence appear first. Source Article contains title/publisher, safe HTTPS link, original publication, initial LANES save date, captured full text and lazy collection details. Opening Source Article loads the newest twenty processing records with immutable inputs; Collection status retains lazy More details.
- Collection status: shared full-height responsive drawer. Attention is the default filter; all saved articles remain accessible. Article inspection and Back use the same drawer, preserving its filters/page and restoring focus.
- GET /api/v1/admin/news/results now uses scope latest_reported_locations. SQL selects the newest recorded run per article, then requires a completed usable result and conservative readable-claim evidence. Older completed versions cannot create main-list duplicate cards or replace a newer failed/pending attempt.
- The claim reading gate requires a usable non-sentence place, supporting sentence, affirmative condition/depth/closure evidence and no forecast/negated/historical flag. Metadata-only/error results stay in collection attention. Missing depth/time alone does not exclude a clear reported flood. This does not repair, approve or mutate extraction records.
- GET /api/v1/admin/news/collection supplies SQL-backed attention states, global counts, search/publisher/status filters and stable pagination. Cases include needs_checking, no_locations, processing_failed, retrieval_failed, missing_text, waiting, processing and ready. Counts describe articles and extracted mentions, not verified incidents.
- Historical result detail remains accessible by original run/zero-based ordinal. It uses its captured source. Result items expose saved_at (original article first_seen_at) separately from captured_at (version capture).
- Staff 401/403 checks, sanitized storage failures, explicit missing/invalid identities and bounded queries remain enforced. No models, migrations, dependencies, persisted artifacts, decisions, public alerts or routing state changed.

## Non-browser verification

- **49 focused backend tests pass:** result and article browsing, collection/newest-run screening, immutable history, source clocks, explicit unknowns, staff guards, literal searches, stable pagination, sanitized failures and no read-time SQL writes. Existing extraction/processing regressions also pass.
- Full frontend TypeScript and changed news/shared-dialog/test ESLint pass.
- UI fixtures retain foundation/navigation, filter/page/focus, missing-body, failed-processing, historical provenance, retry and optional recorded-publisher coverage. Timeline selectors, desktop pane bounds/scroll behavior and mobile Article/Processing history switching within Source Article were updated without browser execution.
- **Latest frontend-only refinement:** shared RecordDetailsPanels bounds the wide dialog; shared RecordTimeline now serves both News and Flood History. The Info reader opens full text, uses compact dates and a larger reading column; the secondary history pane keeps only status/date/counts and View details. A full-width record view uses Mentions / Article / Technical tabs with Back and focus/context restoration; its missing record/input and request failures remain explicit. TypeScript and changed-file lint pass. No backend tests or PostgreSQL checks were rerun for this layout change; the backend evidence above belongs to the preceding unified-reading implementation.
- Actual local PostgreSQL reads pass under SET TRANSACTION READ ONLY. The local database returns **28 readable extracted mentions**, one locations-available article and one waiting article. These are not verified unique sites or active zones. No INSERT/UPDATE/DELETE statements occur.
- PostgreSQL SQL/Python reading predicates agree on seven evidence cases: affirmative report, unsupported place-only mention, sentence-like place, forecast, negation, historical flag and unknown condition with reported depth.

## Real saved example

Philstar article: [LIST: Flooded Metro Manila areas on September 9](https://www.philstar.com/nation/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9).

| Field | Verified local read |
| --- | --- |
| Heading | NS Amoranto cor Don Jose St. |
| Area | Sienna, Quezon City |
| Reported water level | 37 inches / 0.94 m |
| Flood observation | September 9, 2026, 4:30 PM Philippine time |
| Article publication | September 9, 2026, 5:03 PM Philippine time |
| Initially saved in LANES | October 2, 2026, 7:57 PM Philippine time |
| Map placement | Exact map location unknown |

Article detail and result detail summaries agree for the saved ordinal. The September 9 observation is historical source evidence; the October 2 save date is not a new flood report. Current flood/zone activation is not established.

## Developer manual acceptance

1. Open /admin/news after loading the updated frontend/backend. Confirm one Flood Locations list and Collection status control, without separate Articles/Results page tabs.
2. Find the historical NS Amoranto example. Confirm the card uses the reported Don Jose intersection, Sienna/Quezon City, 37-inch depth and September 9 4:30 PM flood observation.
3. Open Info. Flood Details opens first, with source sentence and honest map uncertainty. Source Article shows the separate 5:03 PM publication and October 2 initial LANES-save time. Confirm full article text is already visible, then expand collection details.
4. Confirm Flood Details has no processing history. In Source Article on desktop, confirm the timeline stays beside article text and each pane scrolls independently. On mobile, switch between Article and Processing history within Source Article. Use View details to open a full-width record inspection. Check Mentions, Article and Technical; confirm older captured inputs/results remain distinct. Use Back and confirm reader/history scroll, selected mobile pane and record-action focus survive. Close Info using the button and Escape; main search, filters, page, scroll and opener focus should survive.
5. Open Collection status. Inspect attention/all filters and empty/error/retry states. View an article, inspect source/history, then Back to collection; filters/page/focus should survive. Confirm failed/empty/questionable articles remain inspectable without fabricated current cards.
6. Repeat desktop and mobile, including 320px width and landscape. Check text wrapping, safe areas, scrolling, touch controls, dropdowns, keyboard focus and close/Back actions.

F4a source/feed monitoring UI is implemented using existing protected reads. Developer monitoring acceptance and F4b discovery/fallback/delay telemetry remain open. Durable review/public lifecycle remains a separate backend checkpoint before F5–F7. The reading gate is conservative and does not guarantee extraction correctness.

## F4a existing source/feed read UI — October 3

The developer accepted the revised F3 design and authorized proceeding. Sources & feeds now opens a shared responsive drawer on the same page, using existing authenticated GET /sources and /feeds APIs. Publisher configuration, enabled/verification fields and saved feed check/success/error timestamps are displayed. Refresh only reads saved state. Older success and a newer recorded error remain distinct; missing dates/records are explicit. It does not establish live health, eligible article totals or verified floods.

TypeScript and changed news/API/test ESLint pass. Two additional fixture cases cover lazy feed loading, retained old-success/new-error, missing clocks, enabled/disabled configuration, GET-only refresh, safe links, error/retry/empty states, focus and narrow/landscape bounds. Browser tests were not executed; no server started and no backend/schema/dependency change. Earlier backend evidence above was not rerun for this frontend-only work.

Manual acceptance: open Sources & feeds, inspect Publishers, switch to Feed checks, compare saved check/success/error fields, refresh and close. Repeat mobile/narrow/landscape and keyboard/retry/empty states. Confirm main list filters/page remain intact. The developer's design acceptance does not replace these remaining checks. Discovery-run summaries, blocked-body/fallback history and collection-to-alert delay require additional backend reads; they remain F4b work before complete monitoring acceptance.

## October 3 delivery checkpoint

Before the requested roi-branch push, reran `test_news_browsing.py`, `test_news_results.py`, `test_news_saved_extraction.py` and `test_news_processing.py`: **49 passed**, with one existing multipart deprecation warning. The initial sandbox run could not access pytest's temporary directory; the retry with normal temporary-file access passed. Full frontend TypeScript and ESLint over news routes/features, the changed shared components, sidebar, Flood History detail and news fixtures pass with zero errors and two existing image warnings. Existing AdminLayout lint errors remain tracked in BUG-080; its only change is responsive padding. No browser tests or development servers were run. Prior PostgreSQL evidence was not rerun for this push checkpoint.

Remote roi-branch matches the local baseline. No dependency manifest, SQLAlchemy model or Alembic migration changed; the previously approved local migration application is preserved in the database plan/F2 evaluation. F3 design acceptance and F4a implementation remain separate from the pending manual checklist and F4b telemetry work.

## Earlier verification history

F3's earlier all-completed-run list passed 36 backend checks and local PostgreSQL/HTTP reads. The first clarity revision passed 41 checks and introduced shared facts, unknown clocks and condition qualifiers. Earlier browser checks belong to F1/F2 before the developer prohibited further browser verification. The old News Articles/Flood Locations page tabs and three-tab article modal are superseded by this accepted single-list design; their prior acceptance does not establish visual acceptance for the new presentation.
