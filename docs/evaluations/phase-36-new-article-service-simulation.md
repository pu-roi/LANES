# Phase 36: Three full-article backend simulation

> **Run:** September 28, 2026, 1:40 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This is a read-only simulation through LANES's registered publisher/domain check, `fetch_article_text`, `NewsArticleExtractorInput`, and `HybridExtractionService.extract_hybrid(mode="rules_only")`. It uses the real deterministic extractor, PSGC hierarchy resolver, location ranking, and action evaluator. It does not use the interface, Cloud SQL, Gemini, the ingestion writer, or the live map. Article publication times were supplied from the source pages. All three articles are historical as of the run date.

Run from `backend/`:

```powershell
.\venv\Scripts\python.exe scripts/simulate_phase36_articles.py --output ..\data\phase36_article_simulation_results.json
```

The JSON output is ignored local data and contains derived claim fields, not copied article bodies. `claim_count` includes incidental place mentions and warnings; it is **not** a count of valid flood zones.

## Manual source-to-output completeness check

After repair, I manually compared each named flood location in the publisher's reporting list with the derived claim. **Every named list entry in these three articles now has a location claim.** This is a three-article diagnostic, not proof of general accuracy or verified map geometry.

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

Remaining work: turn the 27/16/8 manually checked expected entries into an offline acceptance set; filter incidental photo/weather claims; and test contradictory updates. The article's report/update time is not a proven flood onset. The Malabon item has an earlier report and later subsidence time, while the current claim exposes one primary event-time field and retains the original evidence sentence. Gate 3 must still match the named road sections and landmarks against OSM and exact NOAH intersections. No active map zone or route change was made, and these historical reports cannot justify a current zone on September 28.
