# Pasig follow-up acquisition — October 7, 2026

> **Last Updated:** October 07, 2026, 8:25 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Five new sources captured, coordinator-reviewed and independently checked. No new subsidence-duration pair or model-training admission.

## Result in plain language

The search found **one new report saying a named Pasig road's flooding had subsided**, but did not recover when that road was previously flooded. That gives a useful flood-end report without enough information to calculate its duration.

Two official 2024 updates also show roads becoming passable to light vehicles. These are useful transport observations, but **passable does not mean dry**. One update explicitly reports water still present. Those observations are stored separately from the subsidence target and are not used to train the current model.

The existing 819 wet observations, 37 conditional subsidence projections, three shared subsidence summaries, all 70 original captures and the fitted October 7 model are preserved. No rows were deleted, merged into immutable inputs or substituted as model labels.

## Files and counts

| File | Records | Meaning |
| --- | ---: | --- |
| [observations.csv](observations.csv) | 33 | Thirty timed wet claims, one collective passability statement, one direct subsidence statement and one city-level flood context. A multi-road/group source label is retained as one claim. |
| [subsidence_outcomes.csv](subsidence_outcomes.csv) | 1 | C5 Ortigas Service Road southbound, October 10, 2025, subsided by 12:49. Earlier wet reference unresolved; duration fields blank. |
| [passability_followup_pairs.csv](passability_followup_pairs.csv) | 9 | Eight collective projections sharing the October 25 statement, plus one direct September 3 comparison. Two shared passability outcomes, not nine independent floods. |
| [source_register.json](source_register.json) | 5 sources | Exact publisher URLs, retrieval times, content-addressed HTML/text paths, SHA-256, publication metadata and caveats. |
| [dataset_manifest.json](dataset_manifest.json) | — | Original/new hash checks, separate counts, builder lineage and zero model/production admission. |
| [review_rules.json](review_rules.json) | — | Version-bound source line and observation-clock interpretation. |
| [independent_review.json](independent_review.json) | — | Completed second review of all five captures, evidence spans, time bounds and admission exclusions. |
| [search_log.json](search_log.json) | — | Date ranges, selected queries, archive searches, inaccessible leads and exclusion reasons. |

Ten new capture artifacts are under `official/sources/` and `publishers/sources/`. These are a **new retrospective overlay**, not an expanded validated training set. Do not concatenate the three CSVs: observations, outcomes and pairs are different record types linked by IDs.

## Source findings

### October 10, 2025: actual subsidence statement, missing reference

The [GMA report](https://www.gmanetwork.com/news/topstories/metro/961956/list-flooded-roads-in-parts-of-metro-manila-on-friday-oct-10-2025/story/) explicitly places C5 Ortigas Service Road southbound under Pasig City and reports subsidence by 12:49. The article's general advisory time is 12:55; its captured HTML `datePublished`/`dateModified` are 13:18:20, all later than the outcome. The retained gutter-depth description has no supported earlier wet clock. None can become a pre-outcome reference or predictor. The adjacent C5 Eagle Street northbound line has no status and inherits nothing.

Record the endpoint as an upper bound, not an exact measured end. No interval is calculable until a qualified earlier wet report for the same section/episode is recovered. Different-year flooding at the same road is not that reference.

### October 24–25, 2024: collective passability recovery

The [October 24 update](https://pasigcity.gov.ph/news-and-releases/flood-update-severe-tropical-storm-kristine-october-24-2024-912) contains wet/nonpassable lists at 21:15 and 23:30. The [October 25 update](https://pasigcity.gov.ph/news-and-releases/flood-update-severe-tropical-storm-kristine-october-25-2024-540) lists eight road groups nonpassable at 01:00, then all areas passable to light vehicles at 02:30. That supports eight **conditional collective passability** brackets `(0,90]` minutes after the last nonpassable reference. It does not measure first recovery, uninterrupted episode duration or physical subsidence.

The page displays October 24 while its title/body explicitly date October 25. Observation clocks follow the dated body. A [later response update](https://pasigcity.gov.ph/news-and-releases/response-update-severe-tropical-storm-kristine-as-of-0700pm-october-25-2024-707) describes a pumping station still managing remaining flooding at 15:00. This prevents interpreting the earlier passability statement as all roads dry, but does not identify recurrence at any particular earlier road.

### September 3, 2024: direct passability recovery with water present

The [official update](https://pasigcity.gov.ph/news-and-releases/flood-update-september-3-2024-201) reports Infant Jesus Street, Metroville, Manggahan nonpassable at 09:00 and already passable to light vehicles at 12:00, with 2–3 inches of water. The descriptive passability bracket is `(0,180]` minutes; it is not an exact three-hour flood duration. The source also contains earlier 02:00/06:00 wet lists. Kabutihan dropping from later lists does not establish clearance.

The source's numeric depth and gutter-depth qualifier are preserved verbatim without reconciling their mismatch. An HTML hero asset path includes September 6, reinforcing that displayed September 3 publication alone does not certify a pre-noon version. F. Manalo Bridge reopening/traffic restrictions are separate from flood subsidence.

## Verification and limits

The acquisition used existing bounded collectors, publisher/redirect and robots checks, and immutable HTML/text captures. The coordinator inspected each captured source and reconstructed reviewed lines, clocks, location scopes and outcome meanings. The builder verified all ten new artifacts, all 70 ancestor captures, the original wet/proxy export hashes, source-bound review hashes and output lineage. Raw-depth strings and missing timestamps remain explicit.

Search investigators independently reported the GMA and September 3 leads. **The final independent capture review completed on October 7 at the resumed checkpoint:** a separate reviewer checked all ten artifacts, all 33 source spans and all nine passability comparisons, the GMA time interpretation and original data/model preservation. Every new row and manifest now records `independent_capture_review_completed=true`; hashes were regenerated after that metadata update. The earlier interrupted review is superseded by the [completed record](independent_review.json). This is source-accuracy review, not prospective accuracy, verified storm independence or production training admission. No automated tests, model fitting, database writes, expiry changes, commit or push were performed in this acquisition slice.

## Rebuild offline

From the repository root:

```powershell
python backend/scripts/build_pasig_clearance_followup.py
```

The standard-library builder reads cached captures and review rules. It writes the three CSVs and source/dataset registers; it never fetches pages or changes the current model. The source manifests retain the original retrieval identities. Git attributes preserve hashed CSV/JSON/capture/builder bytes across operating systems.

## Next evidence work

1. Independent capture review is complete; preserve its scope and production exclusions when using this overlay.
2. Seek the October 10, 2025 **earlier MMDA wet observation** for the exact C5 Ortigas southbound section, including observation and publication/version clocks. The search log records approaches already attempted.
3. Use actual Pasig DRRMO/PIO incident-monitoring logs or future observations to establish same-location wet and explicit subsidence follow-ups. Required fields are below. Searching more wet lists alone cannot resolve the missing outcomes.
4. Keep missing follow-ups visible and exclude operational report expiry/admin end times from physical outcome labels. Reassess fitting/evaluation only after independent-event and temporal-availability qualification.

For an authorized incident-log export or prospective collection, preserve: source/incident ID; Pasig barangay and road section/landmark; observed wet timestamp and timezone; source publication/availability/version; measured depth with units; subsequent wet/dry/subsidence/passability observations with their own timestamps; the reporter's actual outcome wording; recovery/reflooding notes; source/capture evidence and reviewer decisions. A missing end stays blank. Separate actual subsidence from vehicle-specific passability, administrative closure and model forecasts. No personal resident information is needed for this duration target. Do not invent historical precision from annual DRRMO CSV rows.

The [model implementation plan](../../plans/pasig-subsidence-model-implementation.md) remains the governing operational gate. The current conditional model has **not** gained an additional duration-training example from this pass.
