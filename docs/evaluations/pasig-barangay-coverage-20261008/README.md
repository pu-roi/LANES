# Pasig barangay data coverage audit

> **Last Updated:** October 08, 2026, 12:24 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Coverage/normalization audit completed; no source rewrite, training admission, model change, UI change or database write.

The collection is **not limited to four barangays**. The annual DRRMO export has 726 records across 29 barangays. The main wet-observation register has 819 records across 20 canonical barangays, plus 14 rows without a resolved barangay and four without an observation clock. Combining annual and main wet coverage accounts for **all 30 Pasig barangays**: Bagong Katipunan is absent from the annual table but has one retained wet observation. Coverage means a retained record exists, not adequate duration labels, accurate prediction or equal sampling.

The October 7 overlay adds 30 wet claims across eight named barangays and two unresolved wet rows. Main plus overlay wet coverage reaches 21 named barangays. It also contains one subsidence endpoint without a preceding wet clock and nine passability projections; these different record types must not be concatenated or counted as additional independent subsidence durations.

The current conditional model used only 37 projections across **Dela Paz, Maybunga, Santolan and Santa Lucia**, sharing three subsidence summary groups. That subset is distinct from overall collection coverage. It has no learned barangay/depth/rainfall effects. All counts below are records, not independent events; sum of per-barangay summary counts can double-count the same shared summary.

## Complete prediction-location continuation

The separate [COD prediction locality catalog](../evaluations/pasig-location-feature-models-20261008/README.md) now has all 30 canonical barangays and the source-consistent city boundary. The coverage CSV adds prediction_location_catalog_present alongside the unchanged 20-record OSM news boundary presence. These are different purpose/source catalogs; no news activation gate is weakened. Feature capture/evaluation is implemented, while useful street-specific model effects remain unqualified.

## Subsequent model/simulation continuation

The later [passability experiment](../pasig-passability-model-20261008/README.md) fits seven of these barangays, including Ugong, on nine conditional transport projections/two summaries. The coverage CSV now separates the four-location subsidence cohort from the seven-location passability cohort and marks all 30 canonical identities as available for explicitly pooled experimental transfer. Source labels remain unchanged; no additional observed dry outcomes are manufactured. [Current automatic Overview simulations](../case-linked-ml-review-assistant-20261008.md#october-8-pooled-research-transfer-transport-target-and-automatic-registration-simulation) use a separately labeled official registration proxy when actual observation is unknown; this does not establish prospective accuracy or automatically apply Unconfirmed/public retention.

## Reviewable outputs

- [barangay_coverage.csv](barangay_coverage.csv): one canonical PSGC row per barangay, retaining observed spelling variants and separating annual/wet/duration/passability/boundary/model coverage.
- [ugong_evidence.csv](ugong_evidence.csv): 19 indexed Ugong entries with dataset, ID, clock, source/capture/line and separate passability outcome provenance.
- [coverage_audit.json](coverage_audit.json): input/output/builder SHA-256, scope counts, missing boundary identities and explicit unchanged-model/admission status.

Existing cleaner normalization handles whitespace, case and Sta./Sto. aliases; source labels and immutable earlier exports are untouched. Dela Paz's 60 plus one `dela Paz` row become one 61-row coverage identity. `Sta. Lucia` and `Santa Lucia` are one barangay. Unresolved C5 sections remain unresolved; the audit does not infer barangays from road text.

## Ugong findings

**Ugong data exists:** eight annual location/depth rows (2021, 2022, 2024 and 2025); seven explicitly located wet observations in the main register; three in the October 7 overlay; and one conditional light-vehicle-passability projection. The 19-entry index contains different evidence types, not 19 independent floods.

Annual streets include F. Legaspi Street, C5/Canley, C5/Eagle Street, C. Santos, C5/Hypermarket and Meralco Avenue/The Alexandra. They supply no dated observation/subsidence endpoints. Four main-register wet snapshots concern Eagle Street/C5 on July 24, 2024 at 2:00, 3:00, 5:00 and 6:00 PM PHT; three concern C. Santos 1-4 on July 21, 2025 at 7:00, 10:00 and 11:45 PM PHT. Two additional C5 contextual rows mention Ugong in other fields but retain unresolved section/barangay; they are excluded from explicit-Ugong counts.

The October 24-25, 2024 overlay places **Eagles Street corner E. Rodriguez Avenue, Ugong** in wet/nonpassable lists at 9:15 PM, 11:30 PM and 1:00 AM. At 2:30 AM the source says all areas are passable to light vehicles. Its conditional passability bracket is `(0,90]` minutes after the 1:00 AM reference; that is not an exact flood duration or confirmation that water subsided. See [captured source](../pasig-clearance-followup-20261007/official/sources/PASIG-20241025-0230.cfcb88b46186.txt) and the preserved [overlay evaluation](../pasig-clearance-followup-20261007/README.md).

The retained Ugong exports have **zero matched subsidence-duration rows**. This finding is limited to the inspected captures/exports, not a claim that no Ugong subsidence report exists elsewhere. The October 10, 2025 C5 Ortigas southbound subsidence endpoint has an unresolved barangay and missing preceding wet clock; it cannot be assigned to Ugong or paired with a different-year C5 report from road-name similarity.

Historical Ugong data also does not establish Zone #17's October 7, 2026 wet clock. Zone #17's live linked evidence and model-cohort limits remain separate from historical geographic coverage.

## Barangay counts

| Barangay | Annual rows | Main wet rows | Overlay wet rows | Conditional duration rows | Separate passability rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bagong Ilog | 42 | 9 | 0 | 0 | 0 |
| Bagong Katipunan | 0 | 1 | 0 | 0 | 0 |
| Bambang | 10 | 1 | 0 | 0 | 0 |
| Buting | 3 | 0 | 0 | 0 | 0 |
| Caniogan | 10 | 1 | 0 | 0 | 0 |
| Dela Paz | 29 | 61 | 4 | 6 | 1 |
| Kalawaan | 16 | 0 | 0 | 0 | 0 |
| Kapasigan | 4 | 0 | 0 | 0 | 0 |
| Kapitolyo | 10 | 0 | 0 | 0 | 0 |
| Malinao | 19 | 1 | 0 | 0 | 0 |
| Manggahan | 120 | 201 | 4 | 0 | 1 |
| Maybunga | 23 | 63 | 1 | 8 | 0 |
| Oranbo | 5 | 2 | 0 | 0 | 0 |
| Palatiw | 30 | 3 | 0 | 0 | 0 |
| Pinagbuhatan | 78 | 13 | 8 | 0 | 3 |
| Pineda | 8 | 0 | 0 | 0 | 0 |
| Rosario | 40 | 19 | 2 | 0 | 1 |
| Sagad | 6 | 6 | 0 | 0 | 0 |
| San Antonio | 2 | 0 | 0 | 0 | 0 |
| San Joaquin | 23 | 3 | 0 | 0 | 0 |
| San Jose | 2 | 0 | 0 | 0 | 0 |
| San Miguel | 64 | 42 | 3 | 0 | 1 |
| San Nicolas | 32 | 0 | 3 | 0 | 1 |
| Santa Cruz | 5 | 1 | 0 | 0 | 0 |
| Santa Lucia | 77 | 224 | 0 | 12 | 0 |
| Santa Rosa | 1 | 0 | 0 | 0 | 0 |
| Santo Tomas | 7 | 0 | 0 | 0 | 0 |
| Santolan | 33 | 124 | 0 | 11 | 0 |
| Sumilang | 19 | 23 | 0 | 0 | 0 |
| Ugong | 8 | 7 | 3 | 0 | 1 |


## Remaining fixes in order

1. Use the canonical coverage view when reporting coverage: 30 barangays with some retained historical evidence, 21 with named wet claims across the registers, four in the existing conditional-duration cohort. Keep unresolved location/clock rows visible.
2. Recover/qualify wet-to-subsidence correspondence beyond the four-barangay cohort. Preserve explicit before/by time bounds; require matching section, date/episode, evidence scope and availability/version. Additional wet-only records and transport recovery cannot supply missing physical subsidence labels.
3. Evaluate a pooled Pasig duration baseline across represented independent episodes, including location-transfer checks and properly qualified censoring. A citywide pooled model does not require 30 separate models. Broader experimental transfer must be explicitly evaluated; adding names to the current supported list does not validate coverage.
4. Prediction locality is now complete through the distinct COD catalog. Expansion of the existing news-placement catalog remains separate for its previously missing identities: Bambang, Kalawaan, Malinao, Palatiw, Pinagbuhatan, San Joaquin, San Miguel, San Nicolas, Santa Cruz, Santo Tomas. The existing catalog has 20 polygons; geographic data rows do not provide administrative geometry.
5. Qualify prospective accuracy and adaptive evidence-expiry policy before operational use. Observed Cleared remains separate from a forecast deadline.

Canonical coverage views and explicitly pooled research transfer are implemented. A separate passability model now uses the transport outcomes; dry-outcome recovery, independent evaluation, boundary completion and operational expiry remain open in the task plan.

## Reproduce and verification

From the repository root:

```powershell
python backend/scripts/audit_pasig_barangay_coverage.py
```

The standard-library builder reuses the existing annual-cleaner PSGC normalization. It verifies existing manifest-bound exports, 80 ancestor/overlay captures, retained experiment input hashes and unchanged runtime model identity, then rechecks inputs after writing analysis views. A repeated build is byte-identical. Direct checks reconcile 30 unique PSGC rows, annual/main/overlay totals, alias identities, Ugong 8/7/3/0/1 counts and target/provenance separation. No automated test suite or frontend/API/database operation is needed for this read-only data audit. Packages, SQL models, migrations and runtime training inputs remain unchanged.
