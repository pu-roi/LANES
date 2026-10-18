# Recover the existing Gemini collection evidence

> **Last Updated:** October 18, 2026, 10:14 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)
The proposal contains **345 training / 60 validation / 60 conditional test passages**. The passage shortage is complete. This step requests evidence for earlier searches and source history; it does not collect articles or start training.

## Adopted limited-provenance standard

The user accepted the documented limitations. The [preparation specification](../plans/ner-successor-preparation-20261018.md) is now the next implementation task. Keep missing evidence recorded; do not repeat the Gemini request or declare global history/accounting verified. The older decision proposal below is historical and is superseded by the recorded user choice.

## Historical clearance assessment and decision

The saved-evidence assessment is complete; the [protocol decision](../plans/ner-provenance-standard-decision-20261018.md) is still unadopted. Do not repeat the Gemini recovery request or treat inaccessible records as verified. No admission or training is authorized here.

## Recovery response received

The user has returned Gemini's explicit statement that original tool records are inaccessible in its current environment. **Do not repeat the request below without new original evidence.** This is an access-limitation report, not native receipts or verified history. The claim that source-stats.json resides solely on the desktop remains unverified. Preserve the 345/60/60 conditional proposal and follow the [response outcome](../evaluations/flood-ner-gemini-recovery-response-20261018/README.md).

## Original recovery instructions (historical)

Open the **original Gemini conversation that performed the LANES article searches** and paste the request below. Use that existing conversation, where the original records may still be available. Do not start a new research session.

If an existing conversation export or original tool-record download is available, preserve the original file unchanged in a private local folder. Give the LANES coordinator its local file path and explain where it came from. Do not paste an entire conversation, article text, annotations or account secrets into this chat. Whole exports must stay outside the curator context; only deterministically extracted, relevant original request/result records may be supplied to it.

Gemini may expose only answers and citations rather than complete original tool results. If so, report that limitation. A fresh Gemini answer, an answer saying records are complete, or a citation list is not an original search receipt.

## Copyable request for the original Gemini chat

```text
We are recovering evidence from the EXISTING LANES article-collection work in this conversation. This is an evidence-recovery request only.

Do not browse, search, open publisher pages, retry requests, collect articles, run training or regenerate the earlier research.

Please identify whether you can access and provide the original records that already exist for:

1. The eleven searches associated with LANES round v5 (the saved search-01-response.json through search-11-response.json summaries).
2. Their exact original query/request arguments, original tool name or provider, original timestamps or request IDs where recorded, and complete unfiltered original tool results, including all returned URLs and aliases, failures, partial results and any truncation indicators.
3. Any already-existing publisher-request records for that round and subsequent LANES acquisition work through v7: requested URL, timestamp, HTTP outcome, redirects or aliases, failures/retries, and original raw receipt files where available. We need these to reconcile inherited counters, not to repeat the requests.

Provide original downloadable files or an existing native export if the interface actually supports it. Clearly distinguish those files from ordinary conversation text, search citations and saved summaries. Do not create new JSON files that pretend to be the original tool responses, reconstruct missing results, infer timestamps, regenerate article lists, or invent request IDs.

If an original record or complete backend result is inaccessible, explicitly say which category is unavailable and what you can actually access. Partial original evidence is still useful when identified as partial, but it cannot be called complete.

Do not include fresh-test passages, individual annotations, model predictions, scores, unrelated conversations, credentials or account secrets in your reply. Keep any source-bearing original files private for scoped extraction and review. Your newly written reply is a recovery status message, not an original receipt or a certification that the dataset is ready.
```

## Separate historical file request

The missing collection-scope file is recorded under the old desktop backup workspace:

`backend/training/flood_ner/artifacts/desktop-to-laptop-backup-20261016-v3/source-stats.json`

Required identity: **673,184 bytes**, SHA-256:

```text
a5b458502bed712f8887de0768fcc3aa3ba44289905f173df2c4a94b161d52f3
```

If that exact file is available in the original backup workspace, preserve it and supply its private local path. Do not replace an existing project file, restore an archive over the checkout, execute archived helpers or manufacture a file with the same name. The eleven other missing transport/helper payloads remain separately listed in the private recovery ledger. Their filenames alone do not establish additional article collections.

## How returned evidence will be handled

- Preserve original bytes and bind their origin, size and SHA-256 before parsing. Inspect export structure without exposing conversation content to model development; unsupported formats remain pending until a scoped extractor is qualified.
- Match the eleven saved query fingerprints privately. Existing summaries identify what needs matching; they are not proof of original request/result completeness.
- Record incomplete, unmatched, duplicate, truncated and regenerated records separately. Do not canonicalize away raw mobile, query-string or other URL aliases.
- `receipt_evidence.py` checks exact byte-bound query/result fragments for later isolated provenance review. Even a matching pair does not certify provider completeness, cumulative accounting, history or readiness.
- Use an isolated curator for source-bearing evidence. Preserve all 60 conditional test members unless new substantive evidence requires an explicitly reported hold.

The recorded **765 identities + four uncertain slots / 89 publisher requests** remain unverified. No allowance is certified and no new network authorization is created. If original evidence is unavailable, the recovery task ends with that exact missing-evidence status; it does not silently weaken the requirements or restart collection.

After history and independent-test evidence requirements pass, a separate task can prepare admission, grouped partition freezing, isolated sealing, qualified exports and the desktop GPU handoff. Actual training follows that preparation. The desktop can remain off unless locating the named historical file specifically requires access to its original workspace.
