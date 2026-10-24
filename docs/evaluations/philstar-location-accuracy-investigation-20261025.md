# Philstar location accuracy: read-only investigation

> **Last Updated:** October 25, 2026, 12:05 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: investigation complete; corrections are not implemented or applied.** The developer cancelled the proposed street expansion and requested location investigation before further system changes. No application edits, deployment, database writes, NER execution or Gemini request occurred during that cancelled expansion or this investigation. Its three temporary local extent-analysis files were removed. All pre-existing implementation and unrelated local edits remain intact. Existing saved corner geometries were not expanded or reverted.

## Live News Intelligence and polygon inventory

Protected GETs return 16 total observations, including ten from Philstar article 274/version 573/result 401. Seven accepted Philstar observations have active, source-linked polygons: 83 (Banawe/Amoranto), 84 (Don Jose/Scout Alcaraz), 85 (G. Araneta/Kitanlad), 88 (Palali/Amoranto), 89 (Tabayoc/Amoranto), 90 (Don Jose/Amoranto), and 91 (Ubay/Amoranto). The total Active Zones inventory remains fifteen. A read-only Cloud SQL transaction independently confirms all seven Philstar zone/event identities and unchanged recorded depth/access values.

The other three accepted observations are:

| Claim/group | Reported location | Depth | Confirmed failing stage | Additional location evidence |
|---|---|---|---|---|
| 5 / resolved-n22 | West Riverside Interior, Damayan | 19 inches | Saved canonical road is null; placement GET returns `unresolved/no_reported_road` with zero candidates. The street phrase remains in immutable extraction evidence. | Checked OSM ways 229359793 and 1279846090 identify West Riverside Road in Damayan; 834381828 identifies a West Riverside Drive touching Damayan/Del Monte. None establishes which interior section the article means. |
| 7 / resolved-n31 | W Riverside / Atty Pat Senador, Del Monte | 8 inches | Same missing canonical-road field and placement response; the accepted primary mention is the barangay rather than the road. | OSM West Riverside Drive and Attorney Pat Senador Sr. Avenue share node 101867477 at 14.6456534, 121.0123179. The checked community boundaries place it on Del Monte/San Antonio. This is a strong candidate, not a confirmed flooded approach or extent. |
| 8 / resolved-n53 | Talipapa Alley | 8 inches | Canonical road, road section and barangay are null; same placement response. | The source list places this entry under Sto. Domingo (Matalahib), but that heading was not retained as its parent. No matching named Quezon City alley was found in the checked named-road catalog. Other Talipapa-named roads elsewhere do not identify this alley. Unnamed paths and local names need separate corroboration. |

All three placement GETs return HTTP 200 with an explicit unresolved result, rather than a provider/network failure. Their absence from the map is therefore currently caused before OSM candidate qualification. Missing candidates do not prove the streets are absent from OSM.

Some of the seven plotted News Intelligence rows still display **“Several possible map locations.”** That summary comes from older extraction placement, while saved correction handoffs and zone records have geometry. The inventory above uses actual saved source/zone relationships rather than interpreting those labels as unplotted. This is an additional presentation consistency issue, not evidence that seven polygons vanished.

## Banawe: two reports, one boundary junction

The source distinguishes Sienna's 26-inch impassable report from Sto. Domingo (Matalahib)'s 10-inch pass-with-caution report. Only the first is accepted and plotted (83). The second is saved verification target n27 with outcome `unresolved/native_resolution_barangay_unresolved`; it is absent from the accepted News Intelligence results. It is not one of the three accepted-but-unplotted observations above.

The frozen OSM catalog has a shared Banawe/Amoranto node **43080699**, longitude **121.0017254**, latitude **14.6327076**. Checked OSM community boundaries for Sienna (relation 104860) and Santo Domingo (104861) both cover that boundary node. Saint Peter also touches/overlaps the immediate junction area in the combined checked boundary registry; these are community mapping assets, not cadastral certification.

Ten-metre cardinal inspection points, used only to understand the boundary and never as flooded geometry, fall in Sienna to the north, Santo Domingo to the east, and Saint Peter to the south/west. This supports investigating separate approaches at one junction. It does **not** establish which lane, side, or road length had either reported depth. Different barangay names do not automatically mean two distant intersections, and equal coordinates do not make the reports duplicates.

The exact checked NOAH vector tiles classify the junction and the north/east inspection points as class 3 in all 5-, 25- and 100-year scenarios. The equal modeled classes cannot decide which approach had 26 versus 10 inches that day.

## Confirmed normalization and source-coverage defects

Read-only calls to the current administrative lookup reproduce:

- `Brgy. Sto. Domingo (Matalahib)` / `Sto. Domingo (Matalahib)` / `Santo Domingo (Matalahib)` return no match, while **Santo Domingo** resolves to Quezon City PSGC **1381300065**.
- `Brgy. Dona Imelda` returns no match, while **Doña Imelda** resolves to **1381300031**.
- Sienna, Damayan and Del Monte resolve normally.

The durable catalog strips a barangay prefix but otherwise uses strict name keys and limited aliases. The first failure is not proof of a missing barangay boundary. Existing boundary records already include Santo Domingo. Alias correction must remain scoped to the same city and preserve the article's original name.

Current source coverage is **27 list entries plus one separate morning-photo location**, not ten total article locations. The list has seven plotted observations, three accepted but unplotted, and seventeen entries absent from accepted results: twenty list entries lack their own polygon. Nineteen unresolved processing targets are not nineteen unique locations, because intersections can generate multiple targets and one is secondary to an accepted observation.

Among those seventeen missing entries, twelve are represented by unresolved targets with barangay-name or city-evidence linkage failures; four have no corresponding extraction target (the three numbered Kapiligan addresses and MC/Don Pepe); Santol was classified unsupported. These are extraction/verification coverage defects as well as possible later placement challenges. This investigation does not assume that all seventeen are uniquely plottable after repairing extraction.

## Possible solutions, not implemented

1. Audit one observation per source-list entry, retaining its exact city/barangay heading, intersection/address, depth, access, time and source passage. Keep warning cities and subsidence context separate. Do not deduplicate by street names alone.
2. Repair supported aliases and heading inheritance without altering original evidence. Keep city-scoped administrative identities and numbered addresses distinct.
3. For each proposed road location, verify both roads' shared OSM node, connectivity, ground-level tags and locality. For boundary junctions, review each possible approach within the reported barangay instead of assigning the entire intersection to whichever polygon contains its centre.
4. Corroborate ambiguous approaches using the original MMDA/LGU bulletin, dated photographs, landmarks or explicitly located staff evidence. Search snippets, nearest points and generic street centroids do not establish the flood location. Preserve uncertainty when evidence cannot distinguish alternatives.
5. After identifying the road/approach, compare exact NOAH vectors and preserve scenario classes and gaps. NOAH supports modeled susceptibility, not that day's measured depth, passability or affected length. A tie remains a tie.
6. Present proposed placements and unresolved reasons before applying a source-bound correction. Preserve distinct reports at the same junction and do not silently choose the larger depth or spread it down the whole street.

## Public research and limits

- [Philstar source](https://www.philstar.com/nation/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9) supplies the observation hierarchy; its separate morning caption must not be folded into the 4:30 PM list.
- [Banawe/Amoranto OSM node](https://www.openstreetmap.org/node/43080699) and [West Riverside/Pat Senador node](https://www.openstreetmap.org/node/101867477) identify the checked physical junctions. [OSM boundary documentation](https://wiki.openstreetmap.org/wiki/Metro_Manila/Boundary_Relations) describes the barangay relation hierarchy.
- [Nominatim search documentation](https://nominatim.org/release-docs/latest/api/Search/) supports structured street/city searches and bounded search areas; it also says search returns best matches rather than exhaustive object inventories. Full road connectivity should be checked in the existing extract/Overpass rather than inferred from one search result.
- [UP NOAH hazard assessment](https://noah.up.edu.ph/know-your-hazards) describes simulation/satellite/historical-based hazard levels; [NOAH Studio](https://noah.up.edu.ph/noah-studio) exposes all three return periods. These cannot resolve different actual depths at a boundary junction.
- A [Quezon City road bulletin](https://quezoncity.gov.ph/status-of-roads-in-quezon-city-0152-p-m/) contains barangay-scoped names, but its event date is July 21, 2025. A [September 9 Radyo Pilipinas report](https://radyopilipinas.ph/2026/09/09/malabon-at-qc-lgu-mahigpit-na-naka-monitor-sa-mga-binabahang-kalsada-kasunod-ng-walang-tigil-na-ulan/) cites an 8:55 AM QC bulletin. Neither was imported or used to replace Philstar's 4:30 PM observation evidence. Research results are not new database observations.

Protected live responses are retained only in ignored `data/philstar-location-audit-20261024/`. The connected search-service tool returned an error; public-source research continued with the available web tool. No application tests were rerun because application code did not change. Existing API/worker releases, saved polygons, extraction history, ledger, paused automation and disabled expiry were left untouched. No dependency, schema, architectural or UI contract changed.
