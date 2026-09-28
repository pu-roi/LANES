# Phase 36: Publisher Body and Pagination Audit

> **Checked:** September 28, 2026, 11:20 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This read-only check used the registered fetcher against the first two current RSS entries from each of the six enabled publishers. The RSS feed and article page were requested separately. No database rows or map zones were changed. Ten article pages returned usable HTML; two Inquirer article pages returned a Cloudflare challenge. The samples establish behavior for those pages only, not every template or future publisher change.

| Enabled source | Two sampled article results | Body extraction finding |
|---|---|---|
| GMA News Online | 2,699 / 3,610 parsed characters | The existing article/main parser reached the story; the related-story, video, popularity, and lazy-load widgets needed exclusion. |
| INQUIRER.net | HTTP 403 / HTTP 403 | The RSS feed returned 200 with 20 entries, but article subdomains returned a Cloudflare challenge. No full body was accepted. |
| Rappler | 4,982 / 13,770 parsed characters | Broad `<main>` parsing included other stories. The current parser requires the `post-single__content` body container and omits related-article cards and an “Also on Rappler” link list. |
| Philstar.com | 2,043 / 1,151 parsed characters | Current pages have no `<article>` or `<main>` body. They use `sports_article_writeup`; the generic parser previously returned zero characters. The `related_block` is omitted. |
| BusinessWorld | 4,529 / 4,422 parsed characters | The `entry-content` body container excludes unrelated content from `<main>`. |
| Interaksyon | 4,097 / 2,633 parsed characters | The existing `<article>` container yielded text for both samples. |

The sampled [Philstar story](https://www.philstar.com/headlines/2026/09/28/2559554/romualdez-seeks-bail-says-p744-b-plunder-case-rests-weak-proof) also has a `lazy_section.php?page=1` “next” link. That link loads another story, not page two of the same article; treating every “next” label as article pagination would wrongly reject this article. No sampled accessible page had a same-article `?page=2`, `/page/2`, or `/2` link. The fetcher now rejects these common same-article continuation patterns even without `rel=next`, while preserving the earlier explicit `rel=next` and size-limit rejection. It does not claim to assemble a multipage article.

## Inquirer access diagnosis

The registered `https://www.inquirer.net/fullfeed/` returned HTTP 200 and 20 entries. The homepage also returned 200. Current article URLs on `cebudailynews.inquirer.net` and `sports.inquirer.net`, plus the previously checked [newsinfo flood article](https://newsinfo.inquirer.net/2287229/quezon-city-lgu-gives-evacuees-antibiotics-for-leptospirosis-treatment/amp), returned HTTP 403. The response had `server: cloudflare`, `cf-mitigated: challenge`, a “Just a moment...” page, and a challenge-platform path. A browser-style User-Agent did not change the two sampled current article results. The feed provides short descriptions and no `content:encoded` full body. This is article-page bot protection; the exact Cloudflare rule or reason for this client being challenged is not visible to LANES. The earlier Inquirer evaluation used a short passage, not a successful registered-fetcher full-body request.

The collector now records these as incomplete article leads with `Article access blocked by publisher challenge (HTTP 403)`. A permitted publisher feed or authorized content access path is needed before Inquirer full-body evaluation can close; a feed summary must not be presented as a complete article.

## Five-entry follow-up

A second read-only pass checked the first five current entries from each enabled feed (30 entries total). All six RSS feeds returned HTTP 200. The registered fetcher obtained text from 25 article pages across GMA, Rappler, Philstar, BusinessWorld, and Interaksyon; all five Inquirer article pages returned the same Cloudflare challenge. The sampled pages were general news, not a flood-report acceptance set.

One [Rappler rolling-updates page](https://www.rappler.com/philippines/vice-president-sara-duterte-impeachment-trial-updates-videos/) exposed an unrecognized continuation link, `?next=2`, followed by `?next=3` on the second page. Before the repair, the fetcher accepted the first page's 4,353 parsed characters as a complete body, although the visible “Load more” section continued. The same-article continuation check now recognizes a numeric `next` query parameter and returns an incomplete-article error with no body for this page. The page-two response was checked for pagination behavior only; the collector does not assemble its contents. After the repair, 24 of the 25 accessible sampled pages return text and this one remains an incomplete lead.

An additional read-only look at pages one through three found that each page repeats the same introduction but presents different update blocks; page three links onward to `?next=4`. Joining the full parsed pages would duplicate the introduction and still miss later updates. This rolling page remains incomplete until its update blocks and terminal page can be identified and checked within a bounded retrieval path.

A bounded follow-up checked the publisher responses for `?next=4`, `?next=8`, `?next=16`, and `?next=32`. Each returned ten update cards, and page 32 still linked to page 33. This rolling page cannot be verified as a complete ordinary article under the collector's 100,000-character body limit, so the explicit incomplete result remains the safe outcome. No attempt was made to bypass publisher access rules.

The next five feed positions from each of the five accessible publishers also returned usable article text without another detected continuation pattern (25 additional article responses). Five additional Inquirer feed positions returned the same article-page challenge, including one URL repeated as the feed changed. Across the two samples, these are 50 accessible article responses and ten challenged Inquirer requests, not 60 distinct articles or proof of every template. After the Rappler continuation check, 49 accessible responses were accepted as text and its rolling page remained incomplete.

The other sampled pages did not expose a recognized same-article continuation. This sample does not prove that all publisher templates or dynamically loaded content are complete. The replacement-looking glyphs in terminal output from BusinessWorld and Rappler were checked against decoded response code points; the UTF-8 text contained ordinary typographic punctuation, so no source-decoding defect was established.

The historical three-article replay was attempted again after this change. Philstar still matched 27/27 cited sites. Two PNA cases first stopped at the runtime source allowlist because PNA was removed from the six active feeds; the replay script now identifies PNA only as a fixed historical test source, without enabling its RSS feed. Both PNA article requests then returned HTTP 500, so the 16/16 and 8/8 historical results could not be revalidated live on this run. Their earlier results remain historical evidence, not a fresh pass.

## Verification and remaining limit

The offline fetcher regressions cover missing publisher body containers, sidebar exclusion, Philstar's separate next-story loader, and unlabeled same-article page-two URLs, including Rappler's `?next=2` pattern. The current historical replay matched 27/27 Philstar sites; PNA returned HTTP 500 for both older articles. Other publisher templates, pagination schemes, embedded recommendation blocks, and Inquirer full-body access remain open. Consequently Phase 36 Gate 1 publisher completeness is still an active task, and no automatic flood zone should be inferred from an incomplete lead.
