# Flood Zone community updates — revised interface discussion

> **Last Updated:** October 08, 2026, 02:42 AM
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Revised workflow implemented and verified locally. No schema change or deployment. [Acceptance and release limits](../evaluations/flood-zone-community-updates-20261008.md). Original interface discussion below is retained as design rationale.

## October 8 follow-up: reuse the Report Flood panel

**Implemented locally:** The separate public `ZoneUpdatePanel` is removed. `GlobalMap` renders one `FloodReportPanel`; `MapContext` carries selected-zone/condition and independent update-road anchors. Update mode renders `ZoneUpdateForm` inside that panel. Both modes share `FloodReportFields` depth, survey launcher/fields, description/media and `useFloodMedia` attachment lifecycle. Ordinary unfinished road reports, batch drafts, text and files remain intact when switching modes.

**Guest state:** Both modes render the original shared `FloodReportLoginGate` and header controls. Zone context and the New report header action appear only after authentication. The login redirect retains selected zone/condition. Responsive parity tests compare markup and dimensions.

**Return action:** The existing panel header shows New report only during signed-in update mode. It opens the shared discard confirmation; Keep editing retains the current update, while Discard removes its local fields/files and restores the original unfinished report. The action is disabled during submission. The old body return button is removed, and the header remains readable at 320px.

**Final interface contract:** Keep the Report Flood title, orange styling, desktop collapse and mobile sheet. Existing zone context is populated, and road-zone start/end coordinates are loaded from saved source geometry through authenticated `GET /zones/{id}/update-context`. Area zones without a stored road centreline ask the witness to select a road; multiple sections are disclosed instead of asserting whole-zone coverage. The same LocationInputGroup supports search, typed coordinates, map picking, current location and direction swapping. The existing both-directions checkbox and backend road-preview service remain. Step one shows location, condition and the existing eight depth buttons. Step two has the existing Take Survey button/separate survey view, large Add photos or videos area, one Open camera control, description and Back/Submit actions. There are no observation-time, observed-spot/direction or depth-unsure controls. No-floodwater hides wet depth. New-report fields remain unchanged apart from the previously requested removal of observation time and extraction into shared controls.

**Data boundaries:** A submitted zone update contains road endpoints/labels, direction, condition/depth, survey, description and optional media. The server rebuilds its proposed road extent with the existing carriageway service and records geometry/status/message in audit JSON. An absent observation time remains null; submission time is separately recorded and never presented as a field observation. Geometry proposals do not edit official zones or routing. Staff sees the proposed start/end and verification context under Active Zones, then uses existing Edit/Deactivate and explicit review. Report creation still uses `/reports`; zone updates use `/zones/{id}/updates`. No model, migration or package change.

**Draft/presentation verification:** Verify preserved original description/files/endpoints when returning from update mode; private endpoint separation; shared survey/camera/attachments; editable endpoint/extent submission; desktop/mobile map picking and upload retries. Native storage/API checks and responsive browser checks are recorded in the [acceptance contract](../evaluations/flood-zone-community-updates-20261008.md). The shared location dropdown now follows input bounds during mobile keyboard/sheet movement, opens within the viewport and sits above sheets.

**Removed-field provenance:** Commit `f04108c` (October 7, 2026, 9:40 PM Manila time) added the unwanted new-report observation-time field for citizen automatic approval. Its UI/state/draft submission path was removed, including old queued timestamps. The existing backend automatic-approval policy still requires explicit observation time, so ordinary reports without it remain for staff review. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Earlier implemented direction (historical rationale; superseded by the contract above)


Revisit the withdrawn Flood Zone update proposal without restoring its rejected interface. Community observations about an existing Active Flood Zone belong exclusively in `/admin/map` → **Active Zones**, not Flood Report Moderation. Preserve the current zone cards and operational editor.

The developer selected **No floodwater** as the second quick action and **optional media for every condition**, with an evidence prompt when reporting no visible floodwater. **Still flooded**, **No floodwater**, and **Update** open the same contextual form. Quick actions preselect a condition; they do not submit votes or alter the official map immediately. The withdrawn interface was absent before this revised implementation.

## Existing implementation and reusable pieces

| Workflow | Fields and behavior | Reuse for zone observations |
| --- | --- | --- |
| Public `FloodReportPanel` | Road start/end, validated road preview, optional opposite carriageway; eight depth choices; required description and vehicle/hazard survey; multiple photos/videos; drafts and queued reports. New-report observation-time field removed in the October 8 follow-up. | Public panel shell, field presentation, draft preservation, attachment preview/removal and visible upload errors. Replace road drawing with the selected zone and an observed-part field. |
| Admin Create / Edit | Both use `OfficialZoneDrawer` and `ZoneDataEditorForm`; road or drawn geometry, canonical depth/severity, vehicle/hazard overrides, direction and operational description; multiple media; edit also displays existing evidence | Shared depth vocabulary and survey controls. Keep official geometry, direction overrides, buffer settings and administrative notes under staff control. |
| Admin Merge | Candidates → Compare → Edit zone → Confirm; compares depth, severity, passability and coverage; reuses `ZoneDataEditorForm`; requires vehicles and operational description when editing final conditions | Current-versus-submitted comparison and evidence inspection. A zone observation does not need a full merge wizard. |
| Active Zones | Flat `FloodRecordSummary` entries, shared `SpatialPanelButton`, selection, contributor inspection, View on map, Edit and Deactivate | Add Info and a compact observation indicator through existing summary slots; preserve layout and current actions. |
| Existing zone details | `FloodZoneDetailsModal` is an archived-zone view with an Archived badge, required primary report ID, evidence and restore/delete actions | Adapt the view model for active status, actual source and nullable report association. Use accessible `RecordDetailsDialog` behavior and existing `MediaViewer`. |

Public depth choices are duplicated locally, while admin forms import `FLOOD_DEPTH_OPTIONS` from `frontend/src/lib/floodDepth.ts`. All eight choices are wet conditions: gutter / half-knee (Low), half-tire / knee (Medium), tires / waist / chest (High), neck and above (Extreme). **No floodwater** must be an independent condition, and **Depth unsure** must not become a guessed Low depth.

Public survey vehicles currently use display labels; admin forms use `walk`, `bicycle`, `motorcycle`, `light`, `suv`, `heavy`. Reuse common field components and normalize these contracts on the backend; do not import the entire administrative editor into the public form. Preserve unknown answers separately from an explicit observation of no passable vehicles.

## Proposed public interaction

1. Keep desktop hover and mobile tap zone information. Make the popup stable while moving toward its actions, with keyboard/touch access. Use two compact outlined quick actions and a quieter Update action instead of three competing primary buttons.
2. Open one zone-update form with the chosen condition selected. Require sign-in, preserving the selected zone and condition if authentication interrupts the flow.
3. Show the zone name/road and current official condition as read-only context. Official depth is not a default witness answer. Users do not redraw the official area.
4. Ask for the observed condition, observation time, observed part/direction and brief description. Offer an explicit Now choice. For Still flooded, reuse the eight depths plus Depth unsure. Update also supports hazards, lower depth, passability and other changes without requiring a clearance claim.
5. Offer optional observed coordinates through a map point or device location. Device location must be confirmed as the observed spot; it does not prove coverage of the whole zone. Store the observed point separately from official geometry.
6. Place optional vehicle/hazard survey fields in an Additional details section, with Unsure available. Avoid requiring a witness to assert vehicle safety to report dry water conditions.
7. Offer **Take photo**, **Record video**, and **Choose files**, followed by previews, filenames, removal and agreed limits. Media remains optional; the dry-condition prompt explains that evidence helps staff verify the observed location.
8. Submit once for staff review. Show a clear received confirmation; preserve text and files on failure and support retry without duplicate observations. Submissions are private staff evidence in the first version.

Desktop uses the existing public `Panel` styling and anchored form behavior. Mobile uses its bottom-sheet treatment, scrollable fields and reachable submission controls. Keep the selected zone context visible, use touch targets of at least 44px, and calculate navigation/safe-area clearance from the shared CSS variables. Do not stack bordered cards inside the panel.

Separate image/video file controls can request the environment-facing device camera using HTML media capture; the browser controls the capture experience and fallback. Keep Choose files available and verify on physical Android/iOS devices and the future wrapper. [W3C HTML Media Capture](https://www.w3.org/TR/html-media-capture/).

## Proposed Active Zones administration

- Add **Info** beside the zone heading, matching Needs Review. Add a small `MessageSquare` icon and text such as **3 new updates** below the heading when unreviewed observations exist. A message icon describes submitted observations directly. Clicking the indicator opens Community updates; Info opens Overview. Neither action selects the zone or flies the map accidentally.
- The count represents **unreviewed** submissions. Reading details does not clear it. Use an explicit staff decision to mark an observation reviewed; duplicate or unusable evidence gets a reason.
- Flood Zone Details has **Overview** and **Community updates** tabs. Overview preserves current official attributes and evidence. Community updates lists condition/depth, observed time, submitted time, observed location/direction, description, survey, author, attachments and review outcome. Keep witness attachments distinct from official zone evidence.
- Desktop uses a wider existing details shell; mobile uses a single scrollable view with the same tabs. Reuse shared tabs/buttons/media viewer, accessible focus management, loading placeholders, empty copy and error/retry feedback. Retain View map/Return to workspace conventions where map inspection is needed.
- Staff selects relevant evidence, then uses existing **Edit** to change operational attributes or existing **Deactivate** to clear the verified covered area. Link reviewed observation IDs to the resulting audit entry. Opening Edit does not count as a successful decision, and a failed save must not resolve observations.
- Staff can record an observation as reviewed while retaining the official zone. Show conflicting and stale observations during review; order freshness by observation time, not just submission time. A single dry point cannot clear several roads or both carriageways.
- Submission and actionable indicators apply only to active zones in Active Zones. A concurrent deactivation must be surfaced before submission or a staff decision. Retain historical evidence without introducing a second review location in Moderation Center.

## Data flow and validation considerations

The conceptual observation includes zone ID/version, authenticated author, condition, observed timestamp, optional point, observed-part/direction context, optional canonical depth and survey, description and media references. The backend owns active-zone eligibility, depth/severity consistency, timestamp and location validation, duplicate protection, permissions and review transitions. Dry/unknown observations have no inferred official severity. Public submissions do not refresh zone expiry, change routing or enter new-report approval automatically.

Use server-returned summary counts in the existing zone list and load private observations on demand. Evaluate the existing SSE invalidation pattern with authenticated staff delivery; avoid private observation bodies on public map events. The existing owner-only Pasig citizen follow-up endpoint has a different purpose and should not be repurposed for arbitrary zone witnesses. Its append-only review/idempotency patterns may be reused after permission/privacy assessment.

Choose persistence after reviewing existing event/audit storage. Any necessary model or Alembic modification needs the developer's explicit schema approval before implementation. No new package or schema requirement is assumed by this interface plan.

## Known reuse gaps

- The admin picker advertises 10MB, but the inspected picker/upload paths do not enforce that application limit. Define consistent file-count/type/size limits on the server and reflect them in all reused attachment controls.
- Admin Create skips failed uploads; Edit saves zone fields before a separate media request, whose endpoint can skip partially failed uploads. Public reports reject a failed evidence upload explicitly. The new observation flow must not silently claim all selected evidence was submitted.
- Create's description is visually required but can become undefined; Merge checks trimmed operational descriptions. Choose and enforce the new observation's brief-description requirement consistently.
- Create/merge schemas check depth/severity consistency; the zone update schema does not provide the same combined check. Reuse canonical backend depth policy rather than trusting submitted severity.
- The inspected `GET /admin/zones/{zone_id}` referenced undefined `body.is_active`. Implementation relocates that mutation guard into PUT; the existing-zone HTTP reader now passes native acceptance (BUG-121).

## Review evidence and next gates

Source review covers Public Flood Report, shared official Create/Edit, Merge, Active Zones, details shells and upload handlers. The existing Playwright scenario `active zones share report styling and keep zone-specific actions and contributor focus` passes in **desktop-chromium and mobile-chromium: 2 checks**, using controlled fixtures and asserting no API writes. Desktop, mobile and 320px screenshots were visually inspected. These checks establish the existing layout only, not acceptance of the proposed feature or live backend behavior.

Implementation uses existing append-only audit JSONB with zones capabilities; no model/migration approval or new package is needed. Public depth/survey vocabulary and the panel/media/details shells are reused. Drafts survive submission failures in the mounted form; durable reload recovery is not added. Operational Edit/Deactivate and explicit observation review remain separate staff actions, rather than automatically marking evidence applied merely because the editor was opened. Ten native checks and eight desktop/mobile browser checks pass; [release and remaining legacy gaps](../evaluations/flood-zone-community-updates-20261008.md#release-limits) remain explicit.
