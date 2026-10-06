# September 9 production-day News Intelligence replay

> **Last Updated:** October 03, 2026, 7:25 PM
> Author: [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Scope and evidence

**Subsequent checkpoint:** this document preserves the initial v7/v1.5 results. The [v8/v1.6 follow-up](phase-36-news-workflow-follow-up.md) fixes the caution limitation and additional attribution/update defects, retains all 33 sites, and records the verified three-hour production schedule.

The LANES team captured three actual September 9, 2026 publisher pages, independently compared their reporting bodies with extraction, and replayed discovery through saved News Intelligence reads in private loopback PostgreSQL database `lanes_news_test`. The pipeline is local v7 (`rules-psgc-osm-2026-10-03-v7`) with extractor `taglish-rules-v1.5`. Production remains v4; no deployment, schema change, dependency addition or automatic map publication is part of this work.

| Source | Original publication (Philippine time) | Readable locations | Observation facts |
| --- | --- | --- | --- |
| [Philstar list](https://www.philstar.com/nation/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9/amp/) | September 9, 5:03 PM | 27, Quezon City | Shared 4:30 PM list clock; each row keeps its own depth, barangay, intersection/direction and passability evidence |
| [GMA flood alert](https://www.gmanetwork.com/news/topstories/metro/1001693/list-flooded-roads-in-metro-manila-wednesday-sept-9-2026/story/) | September 9, 9:19:06 AM; updated 3:09 PM | 3, Malabon and Marikina | Explicit 2:47 PM reports; gutter depth and passable to all vehicles |
| [GMA evening report](https://www.gmanetwork.com/news/weather/content/1001808/several-metro-manila-areas-flood-due-to-habagat/story/) | September 9, 9:24:42 PM | 3, Manila and Quezon City | España Boulevard, Blumentritt, N.S. Amoranto; separate time/depth/passability not stated |

These are 33 source-backed location records, not 33 deduplicated independent incidents. Photo captions, broad summaries and ambiguous pump/prevention narrative remain evidence context or questionable mentions rather than additional displayed flood sites. Missing facts remain unknown; publication is not an observation clock. The Philstar visible publication header is used because its JSON-LD timestamp incorrectly says 1970.

The day simulation freezes its clock at **September 9, 2026, 11:00 PM Philippine time**. It reconstructs two RSS feeds from verified article metadata and serves captured publisher HTML to the normal fetcher through a bounded fixture transport. It is **not an archived live RSS replay**: the current source registry is temporarily reconstructed as enabled/verified for that day inside the test process, and historical feed availability is unverified. The GMA updated snapshot is available no earlier than 3:09 PM; the test does not pretend that afternoon observations were present at 9:19 AM. Live seven-day age filtering remains unchanged.

## Defects corrected

- Recognize suffixless names in coordinated flooded-street reporting, restoring Blumentritt without adding an invented road alias.
- Recognize the source's singular wording, “all type of Vehicles,” for explicit passability.
- Validate inline/prefix barangays against their actual PSGC parent city; preserve San Agustin and Tañong separately from their road names and keep exact source offsets.
- Keep a depthless list road readable through contiguous original list-introduction evidence, without borrowing another row's depth.
- Resolve GMA afternoon observations only through a narrowly approved, matching original-publication/update header on an exact GMA host. Missing, mismatched, conflicting, backward, different-day, spoofed-domain or narrative updates cannot authorize the clock. Original publication remains unchanged.
- Carry forecast, drill, negated, historical and prevention list context into measured rows, retaining raw measurements while excluding them as live observations.
- End inherited list context at unrelated narrative, including short finite-verb road sentences. Explicit status rows and telegraphic depthless list locations remain supported.
- Make the private replay launcher use a stable worker without auto-reload. Windows reload lost its inherited socket after an edit; restarting the guarded launcher restores the correct private API. Restart explicitly after backend edits.

All changes remain server-side and versioned; earlier source inputs and extraction history are preserved. No frontend filtering or API/schema contract change is required.

## Verification

- **410 related backend tests passed**, with one existing `python_multipart` deprecation warning. Coverage includes discovery, durable processing/retries, reader eligibility, temporal scope, forecast/drill exclusion, original evidence offsets, update-header guards, historical replay, fallback, telemetry, placement and activation gates.
- Independent comparison against all three captured reporting bodies matches all **33 expected locations and their audited facts**, with zero mismatches. Baseline readable counts were 26/3/2; corrected counts are 27/3/3. This is a bounded evidence audit, not a general extraction accuracy claim.
- Persisted September 9 subset: three articles, four source versions, five extraction runs and four feed entries. Prior local Philstar input/run is preserved. New current runs are 10 (27 sites), 11 (3 sites) and 12 (3 sites).
- Recollection/reprocessing repeats create no new candidates or completed work and leave article/version/run counts unchanged. Zero flood reports and zero zones remain unchanged; no historical activation or routing effect occurs.
- Actual authenticated HTTP reads through both backend port 8000 and frontend proxy port 3000 returned all 33 record keys and matching detail evidence. Unauthenticated requests returned 401. The existing September 24 article remains present with five additional readable roads.
- Collection across the four local articles reports one ready article (September 24) and three needing checks (September 9), because caption/context/unknown mentions are retained. This does not mean all 33 displayed facts are missing or that the replay has zero attention items.
- Final visual verification is **incomplete**: after repeated explicit chat permission, the browser tool still rejected the loopback page due to a saved user permission setting. No alternate browser, raw browser commands or security bypass was attempted. The local page and its actual API/proxy are ready for a manual display check.

Full captured publisher bodies, HTML, detailed derived comparisons and replay outputs remain Git-ignored under `data/news-replay/september9/`. Tracked regression fixtures are paraphrased. See the [local replay guide](../guides/local-news-replay.md) for commands.

## RSS and fallback audit

All six enabled feeds were successfully parsed using the existing LANES feed probe on October 3: GMA general news (15 entries), Inquirer (20), Rappler (10), Philstar headlines (10), BusinessWorld (30) and Interaksyon (10), total 95. These are current probe results, not evidence of September 9 feed contents.

Additional publisher feeds verified through the same parser:

| Feed | October 3 probe |
| --- | --- |
| [GMA Metro](https://data.gmanetwork.com/gno/rss/news/metro/feed.xml) | HTTP 200, 15 entries |
| [GMA Weather](https://data.gmanetwork.com/gno/rss/weather/feed.xml) | HTTP 200, 15 entries |
| [Philstar Nation](https://www.philstar.com/rss/nation) | HTTP 200, 10 entries |
| [Pilipino Star Ngayon Metro](https://www.philstar.com/rss/pilipino-star-ngayon/metro) | HTTP 200, 10 entries |
| [GMA Ulat Filipino](https://data.gmanetwork.com/gno/rss/news/ulatfilipino/feed.xml) | HTTP 200, 15 entries |
| [GMA Nation](https://data.gmanetwork.com/gno/rss/news/nation/feed.xml) | HTTP 200, 15 entries |
| [GMA SciTech](https://data.gmanetwork.com/gno/rss/scitech/feed.xml) | HTTP 200, 15 entries |

GMA lists RSS categories in its [publisher directory](https://www.gmanetwork.com/news/rss/). Other checked leads were unusable in this probe: selected Manila Standard/BusinessMirror/PNA feeds returned 403; Manila Times returned 404; selected Abante/Tribune responses were HTML; Tempo redirected outside its approved HTTPS destination; Eagle parsed but its newest item was November 3, 2024. These observations do not establish that every feed for those publishers is permanently unavailable.

GDELT is implemented in `news_open_search_service.py`, the protected staff `/api/v1/admin/news/candidates/{article_id}/open-leads` endpoint, and the read-only `--open-leads` CLI. The scheduled `run_news_discovery --discover --process --limit 50` path **does not call GDELT**. With retrieval requested, staff fallback can probe up to five approved feeds and retrieve up to three alternate bodies for same-event review. Bodies remain response-only; operational attempt/lead metadata is persisted. Index dates cannot substitute for publication or flood observation dates.

A real lookup for the September 9 Philstar title returned HTTP 429 with a 60-second retry indication and zero leads on October 3. Existing ten-second pacing, bounded cache and cooldown are process-local; cross-instance coordination is not implemented. Newly blocked/unreadable stories are rejected before candidate collection, so current fallback is not an automatic rescue of every skipped story. Current seven-day checks also reject September 9 alternates when evaluated on October 3.

## Recommendations awaiting discussion

1. Add the verified GMA Metro/Weather and Philstar Nation/PSN Metro feeds to improve targeted coverage. Same-publisher feeds improve discovery but do not constitute independent corroboration. Source registration was not changed.
2. Preserve “passable with caution” as an explicit conservative status in the eventual passability contract. The existing extractor maps the 20 Philstar caution rows to `passable_all`; raw source wording remains available. This known semantic limitation is not a new routing authorization and was not silently redesigned.
3. If automatic fallback is required, agree on collector integration, bounded provider retries and shared rate limiting first. GDELT is not currently an automatic scheduled source. Automatic map placement/publication remains the next separate integration task.
