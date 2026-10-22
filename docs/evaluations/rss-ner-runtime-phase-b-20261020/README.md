# Phase B — one CPU / 1 GiB runtime qualification

> **Last Updated:** October 20, 2026, 3:02 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Result: failed memory gate; automatic integration must wait.** The separate supervised Linux runtime is implemented. One frozen neural attempt reached the 1 GiB container limit on the existing 100,000-character fictional input. The kernel killed the model child; the supervisor retained partial results, reaped it and exited with failure. No retry, resource increase, model/rule change, schema write, cloud change or deployment followed. This is a local compatibility attempt, not measured Cloud Run readiness. [Roadmap](../../task_plan.md#phase-b--qualify-the-production-inference-runtime) · [Operating guide](../../guides/ner-subprocess-runtime.md).

## Separate outcomes

| Requirement | Observed result | Disposition |
|---|---|---|
| Authenticated assets / code | Qualified base image, inference-only bundle, tokenizer and frozen V46 code authenticated; original files preserved | Pass for measured inputs |
| Training prediction compatibility | All **345/345** retained training passages match exact neural start/end/label spans | Pass for training workload; no validation/holdout reuse |
| Complete-article prediction compatibility | All **6/6** previously qualified complete articles match saved neural spans | Pass for these articles |
| Reviewed article with 53 saved predictions | Scheduled after the maximum-length stress case; not reached | Pending; no substituted inference |
| Pure grouping parity | **788** cached inputs and **407** saved graphs match; all **353** completed live responses reproduce the frozen proposal/graph adapter | Pass for completed scope; full live workload incomplete |
| Cold readiness | **2.298 s**, including supervisor launch/readiness | Within 60 s |
| Warm passage p95 | **0.04272 s**, including response transfer and supervisor graph validation | Within 1 s |
| Six complete articles | Slowest **0.63465 s**, including supervisor validation | Within 30 s each |
| Maximum-length fictional input | Child OOM; no response or successful timing | Fail |
| Total memory | **1,024 MiB** peak at failure; required peak is **below 896 MiB** | Fail |
| Memory before failed input | Last completed-response peak **479.99 MiB**; last completed worker RSS **370.12 MiB** | Partial measurements, not whole-attempt RSS maxima |
| Current news-worker import baseline | **85.83 MiB** cgroup peak, fake storage, zero connections; current imported source hashes verified | Baseline established; not a full live database/collection workload |
| Constructed software checks | **19 passed** | Missing/corrupt assets, message/input bounds, hashes, Unicode offsets, graph tampering, state/concurrency and deadline classification |
| Real fictional subprocess checks | **8 passed** | Timeout, crash, malformed output, oversized output, cancellation, concurrent-request rejection, normal shutdown and abrupt parent death; cleanup/reaping observed |
| Syscall isolation | IPv4, IPv6, Unix sockets and a direct raw socket syscall denied with EPERM inside child | Local Linux amd64 pass; unsupported isolation fails closed |
| Deliberate OOM containment | Separate disposable one-CPU / 1-GiB container exited 137 with `OOMKilled=true` | Pass; no host memory exhaustion |
| Measurement failure cleanup | Child exit `-9`; supervisor reaped it; container exited 2, stopped with PID 0 and `OOMKilled=true` | Pass for this failure path; successful full model-session shutdown not reached |
| Remaining cloud qualification | No Cloud Run execution or settings changed | Pending separate release verification |

The workload contains **355 requests**: 345 passages, six articles, three existing fictional stress cases and one reviewed article. It produced **353 responses** and **351 exact neural comparisons**; the two smaller stress cases have no retained neural oracle, so their returned mentions support pure-adapter binding checks rather than a prediction-accuracy claim. Request index 353, the 100,000-character case, failed; index 354 was not attempted. The saved 53-prediction article remains authenticated predecessor evidence, not a Phase B measurement.

## Implemented boundary and measured environment

`backend/app/services/news_ner_runtime/` is separate from the unchanged preview package. It uses a CPU-only authenticated loader, reconstructed tokenizer, original six labels, unchanged v40 → v44 → v42 behavior and source-bound predictions/proposals/abstentions/graphs. One isolated Python subprocess loads once and handles sequential messages. The supervisor validates source/provenance and recomputes the pure adapter. State errors, deadlines and worker failures stop the session without rules-only fallback or inference retry.

Child environment is allowlisted, inherited descriptors are closed, and Linux amd64 seccomp denies networking including direct socket syscalls and io_uring. The child installs a parent-death signal. These protections are tested locally; they are not a claim that the same syscall setup has been exercised in Cloud Run. Raw text, predictions, model files, paths and receipts stay private. Public diagnostics expose bounded codes/types.

The separate local image derives from qualified image `sha256:a51ce2a6b0f19f382ce96bf63c265e060b37112098176c97c66c23e887794680`, with only allowlisted runtime/preview code, two qualification scripts and the authenticated bundle added. No package install or model download occurs. The current application source is mounted read-only at its normal path for the import baseline; its inference code is byte-identical to the frozen packaged copy. Expected predictions remain outside the worker mounts. The parent imports the actual normal news CLI with fake storage; no CLI collection function is called.

Inspected container controls are one CPU, 1 GiB RAM, 1 GiB total memory/swap, one worker, 128 PIDs, read-only root, bounded 64 MiB tmpfs, no network, dropped capabilities, no-new-privileges and an init process. Cgroup peak includes supervisor, child, page cache and temporary storage; worker RSS alone is not the acceptance metric. No measurement above these limits occurred. Frozen deadlines remain 60 s startup, at most 60 s per request and 5 s cleanup, with a 125 s startup/request/cleanup envelope and 450 s session budget. The budget is not yet connected to queue leases, downstream processing or the 600 s cloud job.

## Preservation and independent verification

The private `rss-ner-runtime-phase-b-20261020-v5` package contains the frozen workload/limits/source snapshots, build and container receipts, partial responses, baseline, failure receipt, controller verification, final private manifest and independently implemented receipt audit. The independent verifier does not load the neural model: it authenticates frozen files and bundle, validates every returned Unicode occurrence, compares saved neural spans, recomputes every completed graph, reconciles counts/timings/cgroup values and checks the stopped Docker container and fault receipts. It confirms exactly one neural attempt and no automatic retry. [Public aggregate](summary.json).

Preparations v1–v4 remain preserved: manifest path resolution, Docker's interpretation of an untagged image ID, the older image config baseline and a source-mount path assumption were corrected before the frozen neural attempt. These are preparation/build/software checks, not repeated neural attempts. A verified local base tag resolves to the original qualified image ID. V46's worker, endpoint, pure rules, promotion manifest and historical receipts are unchanged.

No external dependency was added; Python standard-library subprocess/asyncio/ctypes implement the runtime controls. Normal Dockerfile/build/artifact exclusions, schemas, production job and 60/15/30 scheduling policy are unchanged. No new dataset, retraining, reference revision or publication of historical fixtures occurred.

## Bounded follow-up and gate disposition

**Gate B remains open and failed for the selected resource envelope.** Do not start Phase C, shorten the accepted input, silently split articles, tune the frozen model/rules, add fallback, or call this runtime qualified from its completed short-input results.

The following is the concrete **proposed follow-up, awaiting separate authorization**:

| Item | Proposed new local attempt |
|---|---|
| CPU / concurrency | Preserve one CPU, one model process and sequential requests |
| Container memory / total memory-swap | 2 GiB / 2 GiB |
| Combined peak requirement | Strictly below 1,792 MiB, reserving 256 MiB headroom |
| Model, tokenizer, proposals and grouping | Exact existing identities and behavior; no tuning, chunking or truncation |
| Workload | All 355 existing requests, exact saved spans, 788 cached inputs / 407 saved graphs; no new data |
| Time, message and session limits | Preserve all existing declared limits, including 100,000 characters, 8 MiB, 125 s envelope and 450 s session budget |
| Attempt policy | One newly frozen attempt in an absent private destination; stop/preserve on first unexpected failure; no escalation |
| Implementation scope | Separate versioned qualification controller/probe for the new resource thresholds; preserve this attempt's implementation and receipts, with no extraction/runtime behavior change |
| Acceptance | Every pending original Phase B requirement, including reviewed-article parity, maximum-length output, model-session shutdown, failure/isolation and independent resource/receipt verification |

**2 GiB is a candidate to measure, not an established sufficient allocation.** This proposal does not authorize execution or resize Google Cloud. A local pass at that larger profile would still leave a later explicit deployment-resource decision and actual cloud qualification. If the existing 1 GiB production allocation must remain mandatory, a separate design decision is required; no algorithm or admission change is implied by this failure.

Schema approval remains separate. Cloud runtime/isolation/asset delivery, complete job memory, actual queue/session-budget behavior, downstream gates and production rollout still require their later acceptance work.
