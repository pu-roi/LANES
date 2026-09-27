# Phase 36: Three 2026 Flood Article Extraction Check

> **Checked:** September 27, 2026 by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This is a read-only check of `extract_taglish_flood_facts` against approved publisher articles from August 2026. The initial check used three short passages. On September 27, the Manila Bulletin reporting body was also replayed from its indexed public page and compared with every named location and broad locality in that body. GMA and Inquirer still have only passage-level checks. No RSS replay, Cloud SQL write, geocoding, or zone activation occurred. Historical article conditions must not be interpreted as current flooding.

## Developer-reviewed expected facts and September 27 repair

The developer compared the source pages against the initial snippets. The following are the intended claims, not proof of a routable polygon. Regression fixtures paraphrase source wording while retaining the location lists and their relationships.

| Source | Flooded location and parent | Depth evidence | Time evidence | Current read-only result |
|---|---|---|---|---|
| [GMA](https://www.gmanetwork.com/news/topstories/metro/1000340/heavy-rains-from-habagat-cause-floods-in-metro-manila/story/) | Sto. Domingo Avenue, **between Atok and Calamba Streets**, Quezon City. Calamba is a cross street here, not City of Calamba. | `waist-deep`; canonical `waist`. | `as of 1:12 p.m.` is an observation time; onset unknown. | Road, city, segment, depth, and observation time extracted; no Calamba City claim. |
| [Inquirer](https://newsinfo.inquirer.net/2287229/quezon-city-lgu-gives-evacuees-antibiotics-for-leptospirosis-treatment/) | Biak-na-Bato Street and **Mauban** Street are separate Quezon City claims. The article spells the second road Mauban, not Mabuan. | The reported maxima are 37 inches (`waist` gauge) and up to 19 inches (`knee` gauge). Upper-bound qualifiers are retained and flagged. | Flood observation time unknown. The article's 10 a.m. count concerns evacuees; publication time is not onset. | Both roads and their respective upper-bound depths extracted; no invented road time. |
| [Manila Bulletin](https://mb.com.ph/2026/08/29/several-malabon-roads-impassable-as-floods-deepen) | M.H. Del Pilar in Maysilo; Sitio 6 in Catmon; Dr. Lascano in Tugatog; Central Market area in Tañong. Malabon is the parent city. | First location: descriptive `thigh-deep` plus about 37 inches; numeric value maps to `waist` gauge, while the descriptive wording stays in evidence. The next three locations share an approximate 26-inch statement, mapping to `tires`. | `At 7 p.m.` is when the office reported the first condition; actual flood onset unknown. The second sentence has no separately stated time. | Full reporting-body replay produces 26 named-location claims and 11 broad barangay claims. Passability is kept per claim; uncertain depth and unnamed roads remain unresolved. See breakdown below. |

The numeric depth fields on a claim are **canonical gauge display measurements**, while `depth_raw` preserves the article's number and qualifier. An approximate number, upper bound, or range is not an exact measured point. `thigh-deep` alone has no canonical gauge key, and an unpaired range such as 10–19 inches remains uncertain. The explicit number 37 inches maps to the configured `waist` key; this does not mean the Manila Bulletin source described it as waist-deep. `event_time_kind` distinguishes observation from reporting time where the sentence makes that clear. No timestamp here proves when the flooding began.

The backend regression suite passes 22/22 focused tests and 41/41 across extraction, location service, and news discovery. The constructed 50-item evaluation reports 100% canonical barangay and depth recall, but its article-level negation metric is 96% because two mixed active/negated reports are counted as negated even though their dataset labels expect an active report. This benchmark is not a real-article accuracy measurement.

## Full Manila Bulletin reporting-body replay

The indexed [Manila Bulletin article](https://mb.com.ph/2026/08/29/several-malabon-roads-impassable-as-floods-deepen) contains three kinds of named-location evidence:

| Source group | Extracted claims | Preserved meaning |
|---|---:|---|
| M.H. Del Pilar in Maysilo | 1 | About 37 inches; the sentence does not independently state a vehicle-passability category for this exact road. |
| Sitio 6, Dr. Lascano, Central Market area | 3 | Around 26 inches; impassable to all vehicles. |
| Named roads in the next light-vehicle closure list | 14 | Shared 10–19-inch range; light vehicles cannot pass. M.H. Del Pilar in Tugatog and in Tinajeros becomes two locality claims. The range is not an individual measurement. |
| Named roads that remained passable | 8 | Flooding with varying, unspecified depths; passable to all vehicles. These are not closure claims. |
| Unnamed streets grouped by barangay | 11 | Area-only flood mentions with unknown street geometry; no road name or individual depth is invented. |

This yields **26 named-location claims and 11 broad area claims**, plus two city-level context mentions. An independent paraphrased full-body regression fixture checks the groups, offsets, depth handling, and passability. The source spells one area `Santulan`; the PSGC reference has no Malabon barangay under that spelling, so its raw mention is retained without an official barangay match. Exact coordinates, which portion of a passable road is affected, and the report time for the later lists remain unknown. The GMA and Inquirer pages also contain additional places and prior-day statements; they still need complete-article, date-aware checks before Gate 1 is complete.

## Initial short-passage baseline (before repairs)

| Source and publication | Passage checked | Extractor result | Manual assessment |
|---|---|---|---|
| [GMA News, August 29, 2026](https://www.gmanetwork.com/news/topstories/metro/1000340/heavy-rains-from-habagat-cause-floods-in-metro-manila/story/) | “In Quezon City, the flood was already waist-deep on Sto. Domingo Avenue between Atok and Calamba Streets” | Three claims: Quezon City with `waist`; malformed road `deep on Sto. Domingo Avenue` with `waist`; `Calamba` incorrectly resolved as City of Calamba. | Depth and flood presence were recognized. Road span is contaminated by preceding words, and `Calamba Streets` is wrongly treated as a separate city. A zone must not be published from this result. |
| [Inquirer, August 18, 2026](https://newsinfo.inquirer.net/2287229/quezon-city-lgu-gives-evacuees-antibiotics-for-leptospirosis-treatment/amp) | “Biak-na-Bato Street had flooding as high as 37 inches, or waist-deep, while Mauban Street had knee-deep flooding, or up to 19 inches.” | Two active claims with correct `waist` and `knee` depth keys, but road spans are `Bato Street` and `while Mauban Street`; neither has Quezon City context. | Both depths are associated with the intended clauses, but the road names are inaccurate and city context is lost. This passage alone cannot support a precise map zone. |
| [Manila Bulletin, August 29, 2026](https://mb.com.ph/2026/08/29/several-malabon-roads-impassable-as-floods-deepen) | “At 7 p.m., the Malabon Disaster Risk Reduction and Management Office reported thigh-deep waters along M.H. Del Pilar in Maysilo.” | One Malabon city claim; depth is unknown; no road claim; the evidence begins `m.,` and event time is unknown. | Sentence splitting at `p.m.` and initials in `M.H.` destroys the road and time evidence. Keep this for staff review, with no zone activation. |

## Required follow-up

1. Preserve abbreviations (`a.m.`, `p.m.`, road initials) and hyphenated road names during sentence splitting and place matching.
2. Bind a road to the explicit city or barangay context, and avoid interpreting `Calamba Street` in Quezon City as City of Calamba.
3. Evaluate depth, status, time, and geometry per place claim against complete articles; distinguish article publication time from the observed flood time.
4. Expand the labeled evaluation set with these and other publisher passages from Luzon, Visayas, and Mindanao. Store only short attributable excerpts or annotations as permitted; link to original articles.
5. Keep article-to-zone activation disconnected until the evidence and geometry gates are validated. A computed percentage is not yet calibrated against real articles.
