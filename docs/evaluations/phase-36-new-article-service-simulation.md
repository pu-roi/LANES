# Phase 36: Three full-article backend simulation

> **Run:** September 28, 2026, 1:20 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This is a read-only simulation through LANES's registered publisher/domain check, `fetch_article_text`, `NewsArticleExtractorInput`, and `HybridExtractionService.extract_hybrid(mode="rules_only")`. It uses the real deterministic extractor, PSGC hierarchy resolver, location ranking, and action evaluator. It does not use the interface, Cloud SQL, Gemini, the ingestion writer, or the live map. Article publication times were supplied from the source pages. All three articles are historical as of the run date.

Run from `backend/`:

```powershell
.\venv\Scripts\python.exe scripts/simulate_phase36_articles.py --check --output ..\data\phase36_article_simulation_results.json
```

The JSON output is ignored local data and contains derived claim fields, not copied article bodies. The tracked `backend/tests/fixtures/phase36_expected_sites.json` lists all 51 source-checked sites with expected city, barangay, reported depth, passability, status, and report time where available. `--check` matches each entry to a distinct extracted claim and exits nonzero if any required fact is missing or wrong. This is an offline *expected-facts* acceptance set applied to a live fetch/extraction run, not an accuracy estimate for unseen articles. `claim_count` includes incidental place mentions and warnings; it is **not** a count of valid flood zones.

## Manual source-to-output completeness check

After repair, I manually compared each named flood location in the publisher's reporting list with the derived claim and encoded those facts in the tracked acceptance fixture. The September 28 live rerun matched **all 51 entries and their stated fields**. This is a three-article diagnostic, not proof of general accuracy or verified map geometry.

- **Philstar:** All 27 listed locations are represented, including NS Amoranto intersections, West Riverside Interior, Guirayan/Baloy, Aurora Hilltop, numbered Kapiligan sites, and G. Araneta/Kitanlad. Claims retain the list's `as of 4:30 p.m.` time, own depth, and passability. Source: [Philstar list](https://qa.philstar.com/headlines/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9/amp/).
- **PNA, August 17:** All 16 listed sites are represented, including A. Bonifacio Cloverleaf, the Araneta Avenue span, EDSA White Plains, and Malabon's San Agustin and Ibaba. Claims retain the `as of 6:20 p.m.` time and travel direction where stated. Source: [PNA flood teams report](https://www.pna.gov.ph/articles/1282103).
- **PNA, August 8:** All eight listed sites are represented, with US Embassy, Parañaque National High School, KayTalices, and Sitio 6 attached to their main roads. Individual list times, the all-passable status, and Malabon's later subsidence are preserved. Source: [PNA NCR report](https://www.pna.gov.ph/articles/1281410).

The full output still includes incidental photo/weather place mentions, so claim totals are larger than the number of listed flood sites. These listed sites are **textual location claims**, not verified polygons.

| Full article | Listed flood sites | Matched sites | All claims | Decision results |
| --- | ---: | ---: | ---: | --- |
| [Philstar, September 9](https://qa.philstar.com/headlines/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9/amp/) | 27 | 27 | 40 | 31 flagged, 9 suppressed forecast |
| [PNA, August 17](https://www.pna.gov.ph/articles/1282103) | 16 | 16 | 29 | 27 flagged, 2 suppressed forecast |
| [PNA, August 8](https://www.pna.gov.ph/articles/1281410) | 8 | 8 | 13 | 10 flagged, 3 suppressed subsided |

Changes made during this simulation:

- Preserve paragraph and list-item boundaries in the existing news article fetcher so one item's depth does not flow into the next item.
- Treat `Metro Manila` as a region rather than a mention of the City of Manila.
- Carry standalone city, barangay, and passability list headings into subsequent claims. A city heading takes priority over the article title.
- Stop whole-article city ranking from assigning one city's roads to another city when a story mentions several cities.
- Keep intersections as one main-road claim, parse `from X to Y`, service-road and named-landmark notation, preserve stated travel direction, and recognize suffixless roads in grouped advisories.
- Prefer an explicit parent city over a same-named province/barangay elsewhere. Match city names at word boundaries, and retain city-qualified barangays during geometry ranking.
- Carry grouped report times, bare bullet times, flood status, and passability while preserving later subsidence. Add focused regression tests for these cases.

Verification: the live `--check` run matched 27/27, 16/16, and 8/8 expected sites. The focused discovery/extraction/geometry/ingestion suite, including three acceptance-check tests, passed 73/73.

## Follow-up: incidental mentions and conflicting updates (September 28, 1:45 PM)

The deterministic extractor now retains flood-road mentions before an early article dateline as `photo_caption_only` review claims instead of discarding potentially real evidence. Such a caption cannot approve an automatic zone by itself; metadata-only leads are also explicitly review-only. Explicit photo credits, dateline city labels, and rainfall-only sentences with no flood observation are excluded. The article's reported flood list remains intact. When the same city and bounded road section is reported flooded and later cleared in the article, both evidence claims remain visible, the earlier active claim receives `contradictory_update`, and the action gate requires staff review even if the auditor and geometry would otherwise approve it. The existing single-item Malabon subsidence remains suppressed.

The initial command inherited `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` values pointing to `127.0.0.1:9`, a non-listening local proxy. Those values exist only in this Codex process, not the saved Windows user or machine environment. With those variables removed for the command, the actual registered-source fetcher and extraction service loaded all three publisher pages and matched **27/27, 16/16, and 8/8** cited list sites again. Current claim totals are **29/25/9**; the extra Philstar UN Avenue and PNA EDSA-Kamuning photo-road mentions are explicitly review-only. Rainfall-only locations no longer produce claims. Remaining extra city-level mentions are review-only, not verified flood sites. Five new targeted regression tests passed, along with the 65-test focused backend suite. This confirms behavior on these three historical pages, not unseen-article accuracy. A separate real article with contradictory updates is still needed before this Gate 1 prerequisite is complete.

The article's report/update time is not a proven flood onset. The Malabon item has an earlier report and later subsidence time, while the current claim exposes one primary event-time field and retains the original evidence sentence. Gate 3 must still match the named road sections and landmarks against OSM and exact NOAH intersections. No active map zone or route change was made, and these historical reports cannot justify a current zone on September 28.
