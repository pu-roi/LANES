# Preserve source coordinates during modeled line reconstruction

> **Last Updated:** October 13, 2026, 12:25 AM
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Implemented/verified locally; source-line round trip is resolved. Target polygon/audit acceptance remains open in the [follow-up plan](news-audit-and-corridor-followup.md).

The ordered real replay verified Santo Domingo's 19-inch and 10-inch claims but created no zones. Both exact original 70.692-metre centerlines pass parent containment. `source_aligned_line_union` converts that source to metres, reconstructs supported intervals, then inversely scales coordinates. The resulting endpoint differs by approximately 1.6e-15 degrees and fails strict parent containment. The predicate evidence is retained separately from the original replay; do not misread the 19-metre boundary-parallel difference as a 19-metre displacement.

Reconstruct interval endpoints against the original WGS84 source segments using distances along the metric source. Preserve original vertices exactly, including whole-source overlaps. Keep the existing ten-micrometre interval union precision, original bends, disconnected dry gaps and source ownership. Do not buffer the parent, round the source asset, clip/repair imported polygons, relax containment or bypass any audit/access/grade/NOAH gate. Genuine source-outside-parent lines must still fail.

Add regressions for source-border equality, partial intervals retaining original end vertices, bent segments and genuine dry gaps. Run existing geometry/estimated-road/publication tests. Version the preview asset policy and extraction identity; preserve previous terminal records. Repeat September 24 first and September 9 afterward on fresh guarded databases, with real quota preflight and bounded provider dispatch. Inspect initial zone eligibility, later-event decisions, public APIs and protected History. A later report remains a separate event when original evidence already expired.

Other real model evidence/schema disagreements remain terminal rejections. This repair does not reclassify them, synthesize approvals or introduce a provider fallback. If subsequent provider failures prevent positive acceptance, retain that blocker and prepare a separate provider-reliability plan.
