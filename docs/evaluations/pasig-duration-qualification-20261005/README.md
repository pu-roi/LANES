# Pasig source and duration-outcome qualification

> **Last Updated:** October 05, 2026, 3:20 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Existing evidence reviewed; descriptive reported-subsidence bounds available. Physical road-section outcome labels and model training remain unadmitted.


**Latest working version:** See the [October 5 follow-up](../pasig-duration-followup-20261005/README.md) for 819 combined wet observations and purpose-specific proxy admission. This dated bundle remains preserved; its counts and original review verdicts are not overwritten.

## What this review establishes

**Byte-preserving checkout:** this qualification's manifest-bound CSV/JSON evidence and hashed builders must retain their verified bytes through Git. The pre-push audit extends `.gitattributes` rather than changing review decisions or numeric values; staged manifest hashes are checked before commit. See [BUG-102](../../others/bug-log.md#bug-102-git-newline-normalization-breaks-sha-bound-research-replay) and the [latest follow-up checkpoint](../pasig-duration-followup-20261005/README.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

The 467 wet reports are supported by their captured source text. Of these, 463 have supported reported snapshot clocks and four have date/context only. The three official clearance updates support reported subsidence summaries. These facts are useful for historical timelines and descriptive analysis even though they do not yet establish a validated road-clearance prediction dataset.

Qualification is purpose-specific. `wet_evidence_status=usable` means a source-backed wet claim, not that every location, clock or depth attribute is confirmed. Separate timing, geography and depth columns retain restrictions. Likewise, the three summaries are usable evidence of reported subsidence, while their application to 37 individual road/location outcomes remains uncertain. Missing exact timestamps do not make interval evidence invalid; scope, target meaning and evaluation independence must also be qualified.

**Collection cutoff remains October 4, 2026.** This October 5 review acquires no new sources or later observations. The 2023 Pasig direct-report gap remains. Original captures and the [October 4 working exports](../pasig-duration-cleanup-20261004/README.md) are unchanged.

## Files to use

| File | Rows | Purpose |
| --- | ---: | --- |
| [qualified_observations.csv](qualified_observations.csv) | 467 | All original wet fields plus reviewed timing, locality, depth, snapshot/timeline identifiers, reasons and source paths. Start here for reviewed observation data. |
| [candidate_timelines.csv](candidate_timelines.csv) | 221 | Candidate same-reported-place histories, linking multiple updates and conditional interval candidates. These are not 221 verified independent floods. |
| [interval_qualification.csv](interval_qualification.csv) | 37 | Original candidate intervals plus exact minute bounds, shared-summary groups and uncertain physical-section outcome verdicts. |
| [clearance_episode_review.csv](clearance_episode_review.csv) | 3 | Supported summary evidence and three conditional reported-subsidence windows; keep original scope and strict/inclusive endpoints. |
| [historical_qualification.csv](historical_qualification.csv) | 12 | NDRRMC occurrence/status rows retained as historical context, excluded from the current observation-reference duration target. |
| [review_rules.json](review_rules.json) | — | Explicit source-review decisions and candidate grouping policy used by the offline builder. |
| [qualification_manifest.json](qualification_manifest.json) | — | Counts, input/output/builder/rule hashes and checksummed source identities. |

The output has 466 candidate place/clock snapshot groups because two Karangalan Phase 2 A evidence rows describe one candidate place/time with conflicting depth claims. Both rows remain in the observation table. Ten candidate reporting groups organize chronology; neither those ten groups nor the three shared summaries are verified independent meteorological storms.

## Three reviewed clearance episodes

| Reporting episode | Last reported wet snapshot | Reported subsidence upper bound | Conditional remaining-time window | Linked locations |
| --- | --- | --- | --- | ---: |
| Maybunga, August 11, 2026 | 05:30 | By 09:50 | Greater than 0 and at most 260 minutes (4 h 20 min) | 8 |
| Dela Paz, August 18, 2026 | 12:00 | Before 14:00 | Greater than 0 and less than 120 minutes (2 h) | 1 |
| Recorded floods, August 30, 2026 | 05:00 | By 11:00 | Greater than 0 and at most 360 minutes (6 h) | 28 |

These are windows from the last wet snapshot to **reported subsidence, conditional on the summary covering the linked location**. They are not exact durations, onset-to-clearance totals, zero-water measurements, vehicle-safety labels or ready-to-use expiry timers. Preserve source clock resolution; ISO timestamps with `:00` seconds do not imply second-level measurement precision.

### Source linkage and limits

- **Maybunga:** [same captured update](../flood-duration-pilot-20261004/sources/PASIG-20260811-0950.4223ec2f856d.txt) has the 09:50 summary at lines 4–5, then its retained 05:30 wet list at line 8 and Block 1–8 entries from lines 10–31. This is source-supported collective linkage, stronger than inferring clearance from a road disappearing.
- **Dela Paz:** the [noon report](../flood-duration-pilot-20261004/sources/PASIG-20260818-1200.5f3ad14459ce.txt), lines 1–6, names Katipiran C Yap Compound. The [later response update](../flood-duration-pilot-20261004/sources/PASIG-20260818-2300.1f15b36aea0a.txt), line 7, says reported Dela Paz flooding subsided **before 02:00 PM**. Its 23:00 as-of clock is not the clearance clock.
- **August 30:** the [same captured update](../flood-duration-pilot-20261004/sources/PASIG-20260830-1100.f89215d1462c.txt), lines 4–5, says recorded flooding subsided according to barangay reports; line 8 introduces its retained 05:00 list. The 28 locations cover five Dela Paz, eleven Santolan and twelve Sta. Lucia mentions.

All 37 last-wet/support references resolve to the same original location and barangay, and their minute/hour bounds agree. Unknown continuity between earlier snapshots prevents claiming uninterrupted total flooding. It does not alone invalidate a remaining-time bracket from the final wet snapshot. Preserve the inherited pilot `limitations` field as history; the reviewed timeline explicitly states continuity is **not established**. Shared summary uncertainty and unverified affected sections remain the relevant individual-outcome restrictions.

## Observation corrections and unresolved features

Original columns and flags are preserved. Corrections appear only in `qualified_*`, `*_qualification`, review notes and grouping columns.

- **A. Policarpio, `OBS-c6115f5949d9b12d`:** the source heading supplies **San Joaquin**, and 2–3 inches exactly matches **5.08–7.62 cm**. The original missing-barangay/unit-conflict flags are parser artifacts. The source file and lines 19–21 are retained in the reviewed record/rules.
- **Fourteen Greenpark records:** raw `20 cm (8 inches)` gives 20.32 cm on conversion. Retain the source-reported **20 cm** as a feature with an explicit rounding-uncertainty qualifier; this is not an exact physical measurement or an assertion that both units agree. A model policy can omit this feature if the qualifier is unsuitable.
- **Three unresolved numeric unit conflicts:** Kabutihan `12.7 cm (6 inches)` and two Metroville `10.64cm (4 inches)` records retain wet/time evidence but have blank qualified numeric depths. Do not choose a corrected value without evidence. The two Metroville conflicts were not flagged by the original parser.
- **Karangalan Phase 2 A:** two July 21 19:00 claims give knee level and one foot. Both remain; one candidate snapshot groups them, and combined numeric depth is unresolved. The first source occurrence is a display representative only.
- **Five Kabayanihan/Karikitan records:** July 21 Dela Paz attribution conflicts with July 23 Manggahan attribution. Preserve both source localities and hold cross-day identity joining; majority voting cannot correct a barangay.
- **Four date-only records:** three RMN July 25, 2021 claims and one OneNews September 3, 2022 claim remain without observation clocks. Neither another city's noon report nor a PAGASA warning supplies their clocks.
- **Potential cross-source duplicates:** RMN Kalusugan has a possible same-location/date link to the timed GMA claim, not a verified identical snapshot. RMN Karangalan and OneNews Julia Vargas have no matching timed/same-location Pasig row identified in this export. Preserve the unresolved flags and source claims.
- **Shared upper depths:** three 2021 location claims share “up to three inches.” Keep the lower depth blank and 7.62 cm as the shared upper bound, not an exact per-road measurement.

Broad names, street extensions, court/villa branches, directions and publisher typos are kept separate unless a supported identity exists. Punctuation and explicit trailing barangay qualifiers alone may normalize for candidate grouping. No OSM geometry or DRRMO context join is established here.

## Historical records and label admission

All twelve NDRRMC rows match the Pasig heading and occurrence/status evidence on captured page 47. Their occurrence timestamps and later `Subsided` status remain usable history. The report issue clock does not supply exact location clearance or a last-confirmed-wet reference. Broad area names, including Palingon and San Nicolas, need independent identity review before local street joins.

**Training-admitted examples remain zero.** This does not mean the sources are false or useless. This pass qualifies historical evidence and exploratory report-transition windows. A predictor of **reported subsidence** could use interval bounds under an explicit target/summary-link admission policy; a claim about physically dry road sections requires additional matching/endpoint evidence. Sparse shared outcomes also prevent a defensible held-out model comparison today. No final target policy or trained model is adopted by this review.

Silence, disappearance from a list and search cutoff are missing follow-up. Right-censored time can use a last confirmed wet follow-up after a defined earlier reference, not an invented persistence period through collection cutoff. No censored labels are manufactured in this bundle. Keep all dependent summary/episode records together in later evaluation.

## Reproduction and review evidence

From the repository root, run Python 3.10+ with the standard library only:

```powershell
python backend/scripts/qualify_pasig_duration_data.py
```

The builder reads the four original CSVs, explicit review rules and both source bundles. It verifies the 27 source identities and 54 captured HTML/text/PDF hashes used by these records, checks verbatim evidence components, support IDs and interval arithmetic, and writes the five review CSVs plus a hashed manifest. It also verifies original input hashes are unchanged. A changed source/schema should require a new review version; this script does not acquire data, load application settings, access a database or publish a flood zone.

Three actual read-only agents reviewed clearance evidence, wet/history evidence and the label/grouping methodology. Independent follow-up reviewed the generated overlays and builder. Reviews distinguish supported source claims from uncertain attributes and model admission. No application tests, model fitting, schema/dependency changes, external requests, commits or pushes were performed for this task.

## Next work

1. Continue targeted acquisition for the missing 2023 reports and additional independently dated section-level wet/recession follow-ups across the requested years.
2. Define and document the prediction target and summary-link admission policy before assembling a final training CSV. Use the available reported-recession proxy honestly if selected; do not silently claim dry-road accuracy.
3. Qualify independent storm identity and predictor histories available at the reference time, then assess whether training and held-out baseline/model comparisons are feasible. Preserve the accepted evidence-based Active/Unconfirmed/Cleared lifecycle separately.
