# Pasig flood-duration pilot: first public-report collection

> **Last Updated:** October 04, 2026, 9:37 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Eighteen source captures and candidate registers delivered. No training-admitted dataset, fitted model, observed exact duration or application lifecycle change.

**Expanded current snapshot:** see the [Pasig/NCR register](../metro-manila-flood-duration-20261004/README.md) for acquired 2021/2022 evidence, separate historical incident rows, and regional coverage summaries. This original pilot remains a reproducible historical batch; its missing-year statements describe that batch.

## Result

| Measure | Result |
| --- | --- |
| Selected official Pasig reports captured | 18; no retrieval failures in this batch |
| Extracted observations | 398: 395 positive flood observations and 3 clearance summaries |
| Observation years | 2024: 77; 2025: 129; 2026: 192 |
| Canonical barangays represented | 14 |
| Candidate continuity groups | 6; these are not established independent storm identities |
| Candidate location/clearance-bound records | 37, sharing only **3 clearance episodes** |
| Same-location/time depth conflict | 2 rows for one conflict, retained and listed in exceptions |
| Extraction exceptions | 32: 16 alternate-unit checks, 14 unsupported bullets, 2 depth-conflict rows |
| Rows lacking a supported observation clock | 0 in this selected batch |
| Training-admitted incidents / trained models | 0 / 0 |

The pilot establishes a usable collection route without waiting for an external request. It does not establish sufficient independent outcomes to train and credibly evaluate a generalizable Pasig/NCR duration model. Multiple streets and repeated snapshots from one storm are correlated; a random row split would exaggerate accuracy. Archive years 2021–2023 have not been collected, and later storms/geographies are not yet reserved as independent evaluation data.

The revised collection target is **2021–2026**, with 2026 marked partial through the recorded cutoff (currently October 4, 2026, Asia/Manila). Existing captures are a selected pilot within that window, not complete coverage.

## Files

- [Source citations and capture versions](sources.md): each source's original title, URL, displayed publication date, fetched time, hashes and observation IDs. The [main research source register](../../research/flood-duration-data-sources.md) remains the documentation entry point.
- [Source manifest](source_manifest.json) and immutable HTML/text files under `sources/`.
- [Observation register](observations.csv) and [JSON equivalent](observations.json): original place/depth/passability text, supported clocks, normalized units, source/version and evidence line.
- [Candidate interval register](candidate_incidents.csv) and [JSON equivalent](candidate_incidents.json): last wet observation, reported clearance bound, shared episode identity and interpretation limitations. These records are not training-admitted.
- [Exceptions](exceptions.csv): conflicting same-clock depths, alternate-unit disagreement and unsupported bullet lists. Qualitative or unreported depth stays nonnumeric in the observation register; no body-level wording is assigned a centimeter value.
- [Coverage report](coverage.json) and candidate registers retain the numeric summaries. Generated coverage and clearance-bound graph exports were removed to keep this evidence bundle focused; `backend/scripts/plot_flood_duration_pilot.py` can regenerate them from the saved registers when needed. The figures describe data coverage, not model results.
- [Seeds](seeds.json) and [reviewed interpretation rules](review_rules.json): reproducible bounded source selection and explicit agent-reviewed summary-link assumptions. Developer acceptance remains pending.
- [Access-policy capture](access_policy.json): public robots rules retrieved for this run. Reuse terms remain unverified; robots access is not a reuse license.
- [UrbanFlood24 metadata](urbanflood24_metadata.json): saved public Figshare metadata, **not the simulation archive**. SHA-256 `02b7719a309ae399e4681f0fc756f6b3a25583d95eea8910a8f57650237658ff`.

## Second collection batch

Four additional official pages add 122 observations: September 2, 2024 (31), July 23, 2025, 09:00 (14), July 25, 2025, 23:30 (20), and August 29, 2026, 20:30 (57). All four originals/captures are listed in [sources.md](sources.md). This adds one candidate episode group but no explicit matched clearance episode; candidate bounds remain 37 across three shared episodes. The generated coverage graph was removed during cleanup and can be regenerated from the saved coverage data.

## Interpreting the recovered bounds

| Candidate episode | Last wet observation used | Reported clearance bound | Remaining-time interval after that wet observation | Locations sharing it |
| --- | --- | --- | --- | --- |
| Maybunga, August 10–11, 2026 | August 11, 05:30 | Reported subsided by the 09:50 update | **(0, 4 h 20 min]** | 8 listed blocks |
| Dela Paz, August 17–18, 2026 | August 18, 12:00 | Reported subsided **before 14:00** | **(0, 2 h)** | 1 noon-listed place |
| Listed barangays, August 29–30, 2026 | August 30, 05:00 | Summary says recorded flooding subsided by the 11:00 update | **(0, 6 h]** | 28 listed places |

All times are Asia/Manila. The late-evening August 18 response page reports an earlier clearance bound; **23:00 is not the clearance time**. Parentheses indicate a strict endpoint. These intervals are conditional on matching each summary to the preceding listed flooding; they are not individually measured street times.

Flood onset is unknown. Earlier positive observations provide an observed wet span, not total duration. The candidate register leaves total duration empty. Gaps between positive observations may conceal clearance/re-flooding, so continuity remains an assumption. A place disappearing from a subsequent report is never converted to clearance.

## Extraction and data-quality notes

The collector preserves original HTML bytes and their SHA-256. It extracts only the Pasig article's main column, excluding navigation and related-news text. Unicode normalization is applied to the separately hashed text view, making stylized headings readable. Evidence line numbers refer to that normalized text capture, not HTML lines.

The page's displayed date is recorded as publication-date text, with no invented publication clock. Full dated observation headings override the title clock. For pages with an explicit observation time only in the title, that title remains the clock evidence. Twelve noon is resolved explicitly as 12:00; historical repeated headings may belong to earlier days than the page date.

Numbered location/depth lists and explicitly flood-attributed closure lists are supported. Numeric cm/inches/feet and ranges are converted, preserving the original measurement. Knee/gutter/above-head descriptions remain qualitative. `Sta Lucia`, `Sta.Lucia` and `Sta. Lucia` normalize to the same barangay, while the raw qualifier remains available. A trailing parenthetical landmark is removed only from the barangay key. The collector does not geocode roads or prove affected geometry.

The July 21, 2025 19:00 report repeats Karangalan Phase 2 A with **Knee Level** and **1 FT**. Both claims are retained and flagged. Neither is selected as the true measurement. The July 2024 F. Manalo Bridge closure refers to a collision/unspecified continued closure and is excluded from flood observations. Reported vehicle passability stays separate from flooding and clearance.

Parser revision `pasig-duration-pilot-v2` accepts numbering such as `5 . Caliwag St.`. It compares alternate metric/imperial values in parentheses with a conservative 0.25 cm tolerance; 16 rows are flagged, including possible rounding differences, and retain raw evidence with blank canonical depths. Fourteen later September 2 bullet claims lack repeated explicit flood attribution and remain review exceptions; they are not interpreted as dry or silently assigned earlier status.

This is a narrow pilot parser, not a validated general news extractor. Image-only facts, prose outside its explicit patterns, unknown aliases and new publisher layouts require further review. Selected source text and representative positive/clearance/conflict records were inspected during construction; comprehensive extraction accuracy has not been measured. No automated test suite was added or run for this new script.

## Reproduction

From the repository root, use the backend Python environment with dependencies from `backend/requirements.txt`. Collection and extraction use the standard library; figure export uses Matplotlib 3.10.7. ContourPy 1.3.2 keeps plotting compatible with the existing NumPy 1.x NLP environment. No application configuration, authentication or database connection is required.

```powershell
& backend/venv/Scripts/python.exe backend/scripts/collect_flood_duration_pilot.py --seeds docs/evaluations/flood-duration-pilot-20261004/seeds.json --output docs/evaluations/flood-duration-pilot-20261004 --review-rules docs/evaluations/flood-duration-pilot-20261004/review_rules.json
```

To change or regenerate only the figures without touching observations, citations or collection timestamps:

```powershell
& backend/venv/Scripts/python.exe backend/scripts/plot_flood_duration_pilot.py --bundle docs/evaluations/flood-duration-pilot-20261004
```

The collector also calls this plotting helper when rebuilding derived files. This rebuilds derived files offline from saved captures. Add `--collect` to fetch approved seed URLs; valid cached captures are reused. `--refresh` requests fresh captures while preserving old hash-named source files. Retrieval is bounded to two attempts, a 25-second timeout and a 3 MB HTML response; public robots rules must be readable and allow each source. Failures are saved and surfaced, never interpreted as dry observations. There is no archive-pagination crawler yet.

## Role of recent related research

The [2026 Balanga study](https://doi.org/10.3389/frwa.2026.1775842) helps justify investigating rainfall sequencing/antecedent wetness. It does not supply Pasig clearance labels. The [UrbanFlood24 release](https://figshare.com/articles/dataset/28082549) exposes simulated depth sequences and geographic inputs associated with the 2025 U-RNN study. Its verified ZIP is approximately 19.6 GB; it has not been downloaded. A simulation-only method-development experiment could be explored using a bounded subset, with simulated outcomes labelled and no claim of validated NCR transfer.

## Next data and model decision

1. Expand public-report collection to more independent storms with explicit matched outcomes. Resolve flagged ambiguity; never generate missing durations from published averages.
2. Join compatible rainfall/hydrologic features with supported time/location and as-of availability. No matched rainfall export exists in this bundle yet.
3. Examine downloadable supplements for usable time-series labels and manageable subsets. Keep simulations, recalled ranges and measured outcomes distinguishable.
4. Count independent outcomes and reserve storm/time/geography holdouts before fitting. If support permits, compare an interval-aware statistical baseline and supported nonlinear model; otherwise report the measured data gap and a separately labelled experimental method.
5. Keep model-result figures and calibration/error evaluation mandatory when a model is trained. No accuracy percentage is available from this pilot.

The original adaptive-estimation goal remains active. The accepted two-hour Unconfirmed fallback is retained where validated adaptive support is absent. None of the recovered intervals is adopted as a production timer or observed-clearance rule.
