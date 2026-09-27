# Phase 36: Three 2026 Flood Article Extraction Check

> **Checked:** September 27, 2026 by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This is a read-only check of `extract_taglish_flood_facts` on three short passages from approved publisher websites. The articles were published in August 2026 during heavy Habagat flooding. The passages below were verified through indexed public article excerpts; this check did not fetch or process the full article bodies. Each passage was passed as `article_text` to test extraction on the exact quoted words. No RSS replay, Cloud SQL write, geocoding, or zone activation occurred. Historical article conditions must not be interpreted as current flooding.

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
