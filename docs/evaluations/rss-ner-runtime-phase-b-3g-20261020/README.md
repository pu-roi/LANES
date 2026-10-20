# Phase B — one CPU / 3 GiB local qualification passes

> **Last Updated:** October 20, 2026, 3:17 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Result: all declared local qualification requirements pass at one CPU / 3 GiB.** The explicitly authorized single frozen attempt completed all **355 requests**, including the maximum-length fictional case and reviewed article. Independent verification matches **352 retained neural prediction records** and all **355** proposal/graph responses. Combined container peak is **1,972.21 MiB**, below the **2,688 MiB** headroom threshold; loaded-model shutdown and reaping pass. No retry, runtime/model/rule tuning, automatic-processing connection, schema/database change, cloud resource change or deployment occurs. [Current roadmap](../../task_plan.md#phase-b--qualify-the-production-inference-runtime) · [Runtime guide](../../guides/ner-subprocess-runtime.md) · [Aggregate](summary.json).

## Acceptance evidence

| Gate | Frozen requirement | Observed result |
|---|---|---|
| Resources / concurrency | One CPU, 3 GiB RAM / total memory-swap, one model process and sequential requests | Actual container controls verified; no resource escalation |
| Whole workload | 345 training passages, six complete articles, three existing stress cases, one reviewed article | **355/355 complete**, original order/text/hash/publication bindings unchanged |
| Retained neural predictions | Exact start/end/label spans for every available retained oracle | **352/352 match**: 345 passages, six articles, one reviewed article |
| Reviewed article | All original 53 predictions, saved proposals and graph unchanged | **53/53 predictions and full saved proposal/graph match** |
| Pure adapter | Preserve v40 → v44 → v42, original/effective mentions, abstentions, grouped and unresolved facts | All **355** returned graphs reproduce; **788** cached inputs / **407** saved graphs also match |
| Cold readiness | ≤60 s, including supervisor startup/readiness | **2.28559 s** |
| Passage latency | Warm p95 ≤1 s, including supervisor graph validation | **0.04511 s** |
| Complete-article latency | Each ≤30 s | Six prior articles maximum **0.65357 s**; reviewed article **0.17172 s** |
| Maximum-length input | Existing 100,000-character fictional case ≤60 s | Stress maximum **12.27257 s**, full response retained |
| Message bounds | 100,000-character input, 1 MiB request envelope, 8 MiB response | Unchanged bounded protocol accepts all completed responses; constructed over-limit checks reject |
| Total memory | Combined cgroup peak strictly below 2,688 MiB | **1,972.21 MiB** / **2,068,013,056 bytes** |
| Worker RSS | Record independently from total container consumption | Maximum reported **1,882.71 MiB**; total-container peak remains the acceptance measure |
| Current normal-worker import baseline | Fake storage, no database connections, source-bound current CLI imports | **85.79 MiB** cgroup peak, zero connections; retained in the model container |
| Cleanup | Loaded model terminated/reaped ≤5 s | **0.33864 s**, child exit 0, container exit 0, stopped PID 0, no OOM |
| Startup/request/cleanup envelope | ≤125 s | Measured cold + longest request + cleanup **14.89679 s** |
| Session budget | <450 s; no new requests when the reserved deadline/cleanup cannot fit | Complete measured session **28.60577 s**; constructed budget rejection passes |
| Constructed checks | Assets, messages, hashes, Unicode offsets, output bindings, resource/source tamper and concurrency/deadline guards | **31 pass** |
| Real fictional subprocess failures | Timeout, crash, malformed/oversized responses, cancellation, concurrency, shutdown, abrupt parent death | **8 pass**, with observed termination/reaping |
| Child network denial | Linux syscall filter; real IPv4/IPv6/Unix and raw socket denial | EPERM denial verified before model readiness; unsupported setup fails closed |
| Deliberate memory exhaustion | Separate disposable container only | One-CPU / 3-GiB container exits 137 with `OOMKilled=true`; no model/host exhaustion |
| Preservation | Original 1-GiB and 2-GiB code, limits, claims, receipts, model/rules and V46 artifacts remain unchanged | **1,040** frozen source/context/evidence bindings verified |

Stress cases have no retained neural accuracy oracle; their source-bound outputs reproduce the pure adapter rather than being claimed as additional prediction-accuracy measurements. The reviewed article retains V46's meaning and limitations, including unresolved facts; successful runtime qualification does not resolve the prior 11 unresolved source rows, three reference holds or other recorded research limitations. No validation/holdout content, new dataset, retraining or reference revision is used.

## Implementation and independent verification

Only separate versioned qualification tooling and resource guard tests are added: `qualify_news_ner_runtime_3g.py`, `news_ner_runtime_probe_3g.py`, `verify_news_ner_subprocess_3g.py`, and `test_news_ner_runtime_3g.py`. The frozen inference worker, supervisor, protocol, authenticated tokenizer/model, pure location/context rules and preview endpoint are unchanged. The profile uses existing Python/spaCy dependencies; no external dependency or normal production Dockerfile/build edit is needed.

The private `rss-ner-runtime-phase-b-3g-20261020-v1` package freezes this profile, workload, new tooling, inherited source bindings, model assets and previous-attempt claims. It preserves source snapshots, build/container controls, private outputs, timing/RSS/cgroup measurements, clean shutdown, failure probes, expected predictions outside worker access, the one-attempt claim and independent audit. The verifier performs no neural run: it authenticates the bundle/frozen files, validates every Unicode occurrence and provenance hash, compares saved spans, reproduces every graph, checks the reviewed saved artifact, reconciles timing/resource data and inspects the actual stopped container. All 13 declared audit checks pass. Public records contain aggregate results only.

The local image derives from the same qualified image and uses allowlisted runtime code plus the authenticated bundle. The current application source is mounted read-only for the normal-worker import baseline; its inference code is byte-identical to the frozen packaged copy. Expected prediction files are not in the worker mounts. The container retains read-only root, 64 MiB tmpfs, no network, 128 PIDs, dropped capabilities, no-new-privileges and an init process. The supervisor launches Python directly inside the container; it does not invoke nested Docker.

## Earlier failures remain valid

| Profile | Outcome | Completed outputs |
|---|---|---|
| One CPU / 1 GiB, peak required below 896 MiB | Maximum-length case causes OOM | 353; reviewed article not reached |
| One CPU / 2 GiB, peak required below 1,792 MiB | Maximum-length response completes, but peak reaches 2,048 MiB; guard stops run | 354; reviewed article not reached |
| One CPU / 3 GiB, peak required below 2,688 MiB | All local requirements pass; peak 1,972.21 MiB | 355, including reviewed article |

[Original 1-GiB report](../rss-ner-runtime-phase-b-20261020/README.md) · [Authorized 2-GiB report](../rss-ner-runtime-phase-b-2g-20261020/README.md). The passing profile does not erase those failures or qualify a 1-GiB or 2-GiB production deployment. Peaks are observations for each run; no cross-run monotonic-memory claim is made.

## Gate disposition and next work

**Gate B passes for the approved local one-CPU / 3-GiB profile.** This is runtime compatibility evidence, not measured Cloud Run readiness, live article processing or deployment approval. The previously inspected cloud job uses one CPU / 1 GiB; this task neither reinspects nor changes that allocation. A later deployment resource decision must account for this local requirement and independently measure the actual cloud job.

The import baseline does not simulate real database pools, RSS retrieval, placement/evaluation/publication or overlapping stages. Actual Cloud Run syscall support/isolation, asset delivery, complete-job memory/latency and the 450 s budget's queue/downstream integration remain later acceptance/release work. Preserve the existing 60/15/30 cadence and publication/geometry/freshness/conflict/expiry/vehicle gates.

**Next: the separate schema approval and Phase C controlled integration.** The existing [schema proposal](../../plans/rss-ner-processing-mode-schema-proposal.md) requests only extending the allowed-mode check to `rules_only` / `ner_rules_v1`, preserving columns/history/uniqueness and default legacy mode. It remains unapproved; no model or migration file is edited. After explicit approval, implement/test the focused migration in disposable PostGIS and connect captured bodies, native saved results, mode-aware source checks/readers and queue/session budgets under the [integration contract](../../plans/rss-ner-integration-contract.md). No cloud migration, production method switch, historical publication or automatic reprocessing is authorized here.
