# News Intelligence tabs — local acceptance

October 11, 2026 (Asia/Manila). Author: [@roicambe](https://github.com/roicambe) (Roi Cambe).

The design scan covered Moderation Center, Data Management, Dashboard, System Settings, AdminLayout and shared Tabs/Card/Button/Skeleton. The implementation reuses underline tabs and flat admin cards, preserving responsive spacing and safe-area padding.

Overview shows worker status, next collection, latest cycle, automatic interval, publishers, pipeline switches, recent results and provider freshness/health. Weather details and run diagnostics start collapsed; overdue, retrieval, controller-stale and dispatch failures remain visible. Flooded Areas contains existing search/filter/cards and Info/source/processing history. Both panels remain mounted to preserve state and cycle-completion invalidation; results fetch on demand. Global drawers and navigation remain accessible from either tab.

Tab/panel relationships, selected state, roving focus and arrow/Home/End navigation use opt-in shared Tabs semantics. Other consumers keep their current button behavior.

## Verification

Final local acceptance completed October 11, 2026, 11:59 PM PHT:

- `npx tsc --noEmit` and scoped ESLint for the three changed components and three news test suites pass.
- `npx playwright test news-automation.spec.ts news-intelligence.spec.ts news-articles.spec.ts --workers=1`: **37 passed, 3 intentional skips**, no failures (7.3 minutes). Two skips require an optional private captured-article fixture; the third is a mobile-only navigation check on desktop.
- Both tabs, lazy results, preserved search, arrow/Home/End navigation, collapsed diagnostic details, loading/paused/empty/error/retry states and GET-only refresh pass. Polling updates stages and refreshes cards on completed cycles while Overview is hidden.
- Existing collection/source/telemetry drawers, article input provenance, processing history, focus restoration and staff guards pass. Overflow checks cover 320/390-pixel mobile and 1440/1920-pixel desktop widths, with mobile landscape coverage in the existing navigation suite.
- Desktop/mobile screenshots of both tabs were visually inspected and retained below. These are viewport captures; the existing admin content area scrolls independently.
- The exploratory run exposed old single-page navigation/selector assumptions, transient page-load timeouts and the browser-engine mismatch recorded as BUG-148. The corrected final run passes without retries. A separate development-console probe confirms tab rendering without the React key warning after placing keys before spread props.

Fixtures are synthetic and use intercepted API responses on the local frontend. They verify presentation and interaction, not live weather, cloud scheduling, publication accuracy or production release. No backend, package, database model or migration changed. The existing scheduling rollout remains separate.

## Documentation audit

Task plan, progress, screen documentation, scheduling plan and master index are synchronized. BUG-148 records the corrected mobile test-browser selection. The existing feature reference stays accurate. This presentation change requires no architecture decision, tech-stack or database-design edit.

## Screenshots

- [Desktop Overview](overview-desktop.png)
- [Desktop Flooded Areas](flooded-areas-desktop.png)
- [Mobile Overview](overview-mobile.png)
- [Mobile Flooded Areas](flooded-areas-mobile.png)
