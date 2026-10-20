# Phase B follow-up — one CPU / 2 GiB

> **Last Updated:** October 20, 2026, 3:10 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Result: memory headroom failed; no automatic integration or cloud change.** Following the user's authorization to proceed with the proposed local test, one newly frozen attempt used one CPU / 2 GiB, with total memory/swap capped at 2 GiB. It completed the previously failing maximum-length input, but combined peak reached **2,048 MiB**, exceeding the required **below-1,792-MiB** limit. The qualification guard stopped the run before the reviewed article. The loaded model then shut down cleanly. No automatic retry, further resource increase, model/rule change or cloud setting change followed. [Current roadmap](../../task_plan.md#phase-b--qualify-the-production-inference-runtime) · [Original 1-GiB failure](../rss-ner-runtime-phase-b-20261020/README.md) · [Runtime guide](../../guides/ner-subprocess-runtime.md) · [Aggregate](summary.json).

## What passed and what remains

| Requirement | Observed result | Disposition |
|---|---|---|
| Preserved original attempt | Original controller/runtime, source snapshots, private manifest, failed receipts and exclusive claim remain hash-identical | Pass |
| Model/tokenizer/rules | Existing authenticated v19 seed 0, six labels, v40 → v44 → v42; unchanged code identities | Pass for measured scope |
| Training passages | **345/345** exact saved neural span comparisons | Pass |
| Previously qualified complete articles | **6/6** exact saved neural span comparisons | Pass |
| Reviewed 53-prediction article | Not reached after the guard stopped the run | Pending |
| Grouping | **354** completed responses reproduce the pure adapter; **788** cached inputs / **407** saved graphs also match | Pass for completed scope |
| Cold readiness | **2.12705 s** | Within 60 s |
| Warm passage p95 | **0.04295 s**, including supervisor validation | Within 1 s |
| Six complete articles | Maximum **0.62650 s** | Within 30 s each |
| Maximum-length input | All three existing fictional stress cases complete; maximum **11.27966 s**, including validation | Within 60 s; no prediction-accuracy oracle claimed for these stress inputs |
| Response bound | The maximum-length response was accepted by the unchanged bounded IPC; its private logged record is about 5.15 MB | Within the existing 8 MiB message limit |
| Combined container peak | **2,048 MiB**; required strictly below **1,792 MiB** | **Fail** |
| Worker RSS | Maximum reported **1,883.12 MiB** across completed requests | Alone already exceeds the total-container headroom threshold |
| Normal-worker imports | **85.40 MiB** cgroup peak, current source hashes, fake storage, zero connections | Baseline only; not full collection/database/evaluation memory |
| Shutdown / cleanup | Loaded worker exits **0**, shutdown/reaping **0.35039 s**; container exits **2** to report failed qualification | Cleanup passes; full 355-request session remains incomplete |
| OOM in the measurement | `OOMKilled=false` | This failure is the memory guard, not a killed model worker |
| Constructed checks | **25 pass**: original 19 plus six profile/source-binding guard cases | Pass |
| Real fictional subprocess probes | **8 pass**, including timeout/crash/cancellation/concurrency/malformed/oversized/shutdown/parent-death containment | Pass |
| Network isolation | Real IPv4/IPv6/Unix and raw socket syscall denial observed in the model child | Local Linux pass; cloud support unmeasured |
| Separate deliberate OOM | Disposable one-CPU / 2-GiB container killed at its limit, exit 137 | Containment pass; no model or host stress |

There were **354 responses out of 355 planned requests**, **351 exact passage/article neural comparisons**, and three completed fictional stress cases. The original order/texts/publication metadata and expected spans are unchanged. Request 353 was the 100,000-character case; its successful response preceded the headroom check. Request 354, the reviewed article, was not started. No validation or holdout content, new corpus, training or reference revision was used.

## Scope and independent evidence

The follow-up adds only versioned qualification tooling: `qualify_news_ner_runtime_2g.py`, `news_ner_runtime_probe_2g.py`, `verify_news_ner_subprocess_2g.py` and six resource guard tests. It reuses the original authenticated bundle, allowlisted local image recipe, runtime subprocess, pure adapter, fake-storage baseline and fictional fault harness. It does not alter the original one-GiB controller, worker, supervisor, protocol, preview endpoint, promotion manifests or normal Dockerfile/build pipeline. No external dependency is added.

The private `rss-ner-runtime-phase-b-2g-20261020-v1` package freezes all inherited source/receipt bindings, the new tooling, exact 355-request workload, expected predictions outside worker access, limits and one exclusive attempt claim. It preserves build/container controls, output/provenance, memory/RSS/timings, successful model shutdown and the failed guard receipt. Independent verification performs no neural inference: it rechecks every frozen file and bundle, exact spans, source hashes/Unicode offsets, every returned graph, the actual stopped container, fake-storage baseline, syscall/fault evidence and deliberate OOM containment. All completed outputs reconcile.

Resource controls remain one CPU, one worker/request, 2 GiB total memory/swap, 128 PIDs, read-only root, 64 MiB tmpfs, no network, dropped capabilities, no-new-privileges and an init process. Startup/request/cleanup limits, 125 s envelope, 450 s session budget, 100,000-character bound and 8 MiB responses are unchanged. The attempted session lasted about 29.2 s at the container level; this is not a successful full-session or live-job latency claim.

## Consequence and next decision

**Phase B remains open.** Two GiB can finish the retained maximum-length case, but fails the agreed total-memory headroom requirement and leaves the reviewed-article check pending. Neither this result nor the previous one-GiB failure establishes an acceptable Cloud Run resource configuration. Cloud job resources still have their previously inspected one-CPU / 1-GiB allocation; no live reinspection or mutation was performed here. The 60/15/30 collection policy is untouched.

The measured worker RSS of 1,883.12 MiB plus the parent/import baseline explains why a 2-GiB envelope has little room. We have not profiled individual internal allocations, actual database pools or downstream pipeline overlap. Do not lower the headroom threshold, silently truncate/split articles, change the model/rules or hide this as successful NER processing.

A concrete next **proposal, not authorization**, is one CPU / **3 GiB** locally, total memory/swap 3 GiB, combined peak strictly below **2,688 MiB** (384 MiB headroom), unchanged runtime/model/rules/workload/deadlines and one frozen attempt with no retry/escalation. It must finish all 355 requests, compare the reviewed article's 53 predictions and saved graph, pass clean shutdown/resources and receive independent verification. The existing measurements make this a bounded candidate; they do not prove it will pass. A separate design review would be needed if larger resources are unacceptable. No further attempt was started.

Any eventual cloud memory change, complete-job/cloud verification and production release remain separate decisions. Schema approval is still pending, and Phase C automatic-processing wiring has not started.
