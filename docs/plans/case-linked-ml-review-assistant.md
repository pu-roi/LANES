# Case-linked ML review assistant

> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Started:** October 08, 2026, 9:44 AM (Asia/Manila)

## Complete prediction-locality and input-source continuation

[Current evaluation](../evaluations/pasig-location-feature-models-20261008/README.md) completes automatic prediction location across all 30 source polygons. Separate OSM/NOAH operational geometry is unchanged. Existing calculation details lazily inspect source-labelled current terrain/rainfall context; new report/create/edit audits freeze available features and null clocks without manual inputs or historical backfill. Feature candidates are evaluated but not active because their held-group results are worse/unidentifiable. This does not complete independent street-specific accuracy or forecast-to-Unconfirmed/public retention.

## October 8 model/simulation continuation

The developer authorizes pooled Pasig experimental transfer with explicit training-cohort versus prediction-scope metadata, a separate source-derived light-vehicle-passability fit, and automatic registration-based simulation for unchanged official zones lacking an observed clock. Subsidence remains the main Overview output. Registration is a simulation proxy, not physical observation; no observed label or zone expiry is backfilled. Forecast issuance is anchored to recorded evidence/registration and stays fixed across refresh until evidence changes. The separate passability API retains explicit nonpassability assumptions; passability does not imply exact depth or dry roads. [Current acceptance](../evaluations/case-linked-ml-review-assistant-20261008.md#october-8-pooled-research-transfer-transport-target-and-automatic-registration-simulation). Future operational behavior should become Unconfirmed with retained public updates, never confirmed Cleared from a forecast alone; this read-only delivery does not implement that state transition.

The older geometry/evidence section below records the initial adapter checkpoint; its four-barangay abstention is superseded by explicit pooled transfer, and #17 now has a labeled registration simulation while its actual observation clock remains unknown.

## Initial automatic zone prediction — October 8 correction (historical checkpoint)

The developer rejected the hypothetical test fields and acknowledgment checkbox. Active Zone Info → Overview now calls authenticated, no-store `GET /api/v1/admin/zones/{zone_id}/subsidence-prediction` on entry and every minute. There is no manual input, save step, separate ML page/tab, or Moderation Center section. The frontend renders the backend median/interval, recorded clocks and compact states; calculation details remain read-only.

The service resolves the entire saved zone polygon against the reviewed barangay catalog, returning canonical location, a point inside the zone and boundary revision. It reuses Needs Review's 500 m discovery radius and spatial locality normalization. Nearby pending reports remain candidates: proximity alone cannot establish a shared incident. Calculation uses approved citizen reports already linked to the same zone/event and contained by its footprint, or current resolved linked news with matched immutable footprint/incident history and explicit observed/available clocks. Accepted subsidence, pending/later condition evidence, closed incidents, changed geometry, missing/old clocks and unsupported locations stop calculation. Zone creation, submission, approval and expiry are never substituted for observation time.

Geometry resolution is broader than model qualification. The bundled boundary catalog covers 20 Pasig barangays; the current model's research cohort is only Maybunga, Dela Paz, Santolan and Sta. Lucia. Canonical Santa Lucia maps to the artifact's Sta. Lucia identity without adding model coverage. The artifact remains pooled/intercept-only, with no learned depth/rainfall/locality effects. Server-selected experimental continuity is disclosed as an unverified assumption; there is no automatic operational expiry, Cleared decision, persistence or training admission.

Read-only shared-database inspection resolves Zone #17's polygon to Ugong, Pasig. It still has no linked report/news or qualified observation clock, and Ugong is outside the research cohort. The new adapter therefore gives specific reasons without asking for hypothetical inputs or inventing a forecast.

The dataset does contain reported subsidence bounds: Dela Paz August 18 says before 2:00 PM, Maybunga August 11 is bounded by the 9:50 AM summary, and August 30 by the 11:00 AM summary. The 37 conditional rows reuse these three summaries; they are not 37 independent clearance observations. Many other wet observations lack matched same-episode outcomes. The 726-row annual DRRMO CSV lacks timed duration endpoints. Full boundary geometry coverage, verified episode/outcome correspondence, independent evaluation, prospective accuracy and operational expiry remain open; all 30 identities already have some historical evidence and explicitly experimental pooled transfer.

## Retained backend case contracts

Earlier case-suggestion APIs remain available for authenticated staff: Reports view/full GET `/admin/reports/{report_id}/review-suggestion`, full-only POST with immutable UUID retries, and bounded `/admin/flood-review-suggestions`. Existing private audit JSONB is reused. Their save controls and queues are not mounted in the accepted Overview/Moderation UI. Owner timed follow-ups and independent staff review/export retain their separate contracts; staff follow-up review placement before release remains open.

No SQLAlchemy models, migrations, packages, public bubble content beyond its accepted status badge, or routing policy changes. Validate native PostGIS evidence/permissions/read-only behavior, actual model outputs, responsive states and real authenticated live-zone abstention separately. Fixtures establish presentation; they do not establish prospective accuracy.
