# Credit-free news processing for the October 19 defense

> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Local end-to-end acceptance and focused production backend release completed October 13. Git integration and frontend diagnostics publication remain separate.

The developer selected local NLP and deterministic source checks instead of mandatory external LLM validation. The defense is Monday, October 19, 2026. Keep the existing collectors, immutable article/extraction history, evaluation leases, publication, geometry and expiry services. Preserve LLM/MCP experiments as optional future work without consuming their credits.

## Delivered path

October 13 follow-up applies the developer's explicit measurement-first rule and restores longer saved evidence without decorative play markers or composed ellipses. The real scheduled-worker replay produces 27 alerts and seven zones, including the 19-inch Santo Domingo target. Production v2 and its worker are verified; [measured evidence](../evaluations/news-source-validation-20261013/README.md#measurement-precedence-and-scheduled-worker-follow-up). Earlier six-zone counts below are the initial acceptance run.

- [x] Explicit `source_rules` / `source-rules-v1` validator needs no API key and makes no inference or quota requests.
- [x] Match exact source occurrences and source-derived place, time, status, depth, access and segment facts. Reject altered, conflicting, ambiguous, forecast, negated and historical evidence.
- [x] Keep trusted publisher, admission, expiry, duplicate, override, asset, locality and bounded-geometry checks in their existing backend stages.
- [x] Distinguish text alerts, estimated road zones and field-verified footprints. Source consistency is not independent AI validation or field verification.
- [x] Prove collector → extraction → source validation → publication → real OSM/NOAH zone creation, repeat safety and expiry on local PostGIS in the existing LANES container.
- [x] Verify actual persisted map/source details and the new diagnostics at desktop/mobile widths.
- [x] Ship only tested runtime changes on the existing production image; exclude unfinished MCP and shared framework upgrades.
- [x] Require a private production JWT key, restrict automatic admin bootstrap to development and retire exposed legacy API tags.
- [x] Enable the mode in the encrypted local configuration and existing API/news/expiry cloud resources; preserve provider credentials and all historical records.
- [ ] Integrate the focused source changes into Git main through a reviewed feature-branch PR before another main-triggered release. Do not merge the whole unqualified MCP/dependency experiment simply to obtain this feature.
- [ ] Publish the optional frontend diagnostics explanation when its matching Git rollout is ready; existing production map/source interfaces already consume the backend geometry.
- [ ] Rehearse the preserved historical dataset and inspect representative later live collection cycles before the defense.

## Acceptance and limits

Captured September 9 news gives 31 evaluations, 26 source alerts and six estimated road zones with zero model requests. Repeat execution creates no duplicate zones; expiry ends active geometry without claiming that floodwater physically cleared. The local replay explicitly uses a historical clock and reconstructed publisher HTTP; historical RSS membership is not claimed.

Live production is enabled and its first source-mode cycle reads 135 feed entries, finds zero new eligible flood reports and makes zero inference requests. It does not establish a newly plotted current flood. Use the captured replay to demonstrate a positive event when weather/news availability is outside the developer's control.

Rule consistency cannot detect every reporting or extraction mistake. Approved-source reporting is evidence, not ground truth. Ambiguous geometry, unknown depth/access and unsupported timing stay review/text-only; a susceptibility layer or policy margin does not measure live water extent. [Acceptance](../evaluations/news-source-validation-20261013/README.md), [defense guide](../guides/news-source-validation-defense.md).
