# Offline flood NER preparation

> **Last Updated:** October 21, 2026, 12:46 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Reading guide for groupmates

For a consolidated explanation of model creation, data/annotation structure, training setup and measured accuracy tables, read the [NER groupmate handoff](../../../docs/guides/ner-groupmate-handoff.md). It separates the retained six-location-class model from context rules, distinguishes validation/holdout scores from software/runtime checks, and explains which private data/model assets are excluded from Git.


## C3b — controlled RSS-to-NER integration passed locally

The backend now connects guarded native RSS admission/corrections, exact capture/provenance, saved readers and downstream evidence/publication gates. [754-check report and aggregate](../../../docs/evaluations/rss-ner-rss-integration-20261021/README.md). One local one-CPU / 3-GiB attempt completes eight mocked-RSS inputs plus two pre-existing short capture controls; all 4,483 spans and 53 reviewed predictions match, with zero duplicate inference. Peak memory is 2,492.09 MiB. Historical publication remains paused; no alerts/zones are created.

Trained model/tokenizer, v40/v44/v42 rules, membership/references and all historical qualification artifacts remain unchanged. Current orchestration/read/source differences are separately frozen. No new dependency, retraining, dataset collection, schema, frontend or cloud/deployment change. Next is monitoring Phase D, then interface Phase E and 403 Phase F; scheduled production NER remains disabled. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

**Earlier checkpoints below are historical.**

## V38 fixed-reference repair — contextual gate passed, connection blocked

**Four incorrect links removed; eight contextual misses recovered**, including the lost baseline-correct status. One frozen Linux comparison processed 24 unchanged training inputs + 238 fictional cases. All **238 cases and 1,158 fresh affected tests (298 new)** pass. References, model and 345/60/60 membership remain unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Fixed-reference result: 98 TP / zero FP / seven FN; 96.55% association F1**, versus saved v37's 90.45% on the same 23 silver training references. All 90 v37-correct, 14 original-rules-correct and 70 mapped associations are retained. No new strict DEPTH/TIME span errors or qualifier losses. This exposed training-subset result is not independent system accuracy.

**Next gate:** separately assess seven missing/mistyped-neural-target links, three reference holds and unmeasured real-world Tagalog performance before proposing a read-only LANES demonstration. Contextual repair passes; overall connection remains blocked. Learned DEPTH/TIME stays unfinished. No new data, neural inference, training, integration, upload, commit or push occurred. [Outcome](../../../docs/evaluations/flood-ner-context-fixed-links-20261019/README.md) · [Metrics](../../../docs/evaluations/flood-ner-context-fixed-links-20261019/metrics.json) · [Verification](../../../docs/evaluations/flood-ner-context-fixed-links-20261019/verification.json) · [Guide](../../../docs/guides/ner-context-association-v38.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V37 grouping clarification and repair — complete, acceptance blocked

**Current stage remains offline context acceptance.** A uniform source-only review froze 14 retained/nine corrected proposals, all 168 entities and three prior holds unchanged. All 103 old relations and 70 previously correct associations are mapped. One frozen Linux successor processed **24 unchanged real inputs + 208 fictional cases**. All 208 cases and **860 fresh affected tests (299 new)** pass. No post-result tuning or retry occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Revised-reference result:** **90 TP / four FP / 15 FN; 90.45% association F1**. All 70 pre-frozen source-supported mappings and all 61 revised-reference v36-correct links are retained. One additional original-rules-correct local status under revised references is missed, so retention and zero-incorrect gates fail. Seven misses require absent/mistyped neural targets; eight are contextual omissions. TIME-span checks introduce zero FP/FN and recognition F1 is 95.65%. These are exposed silver training-subset results, not independent accuracy or learned DEPTH/TIME performance.

**Reference encodings stay separate:** saved v36 scores 66.67% and the successor 90.45% on the clarified references; under unchanged v36 references the successor scores **69.74%**, versus saved v36's 78.21%. Representation revisions are not model improvement. The isolated review's incidental generic-code/filename exposure is recorded; no actual prediction/output/score data was exposed. Pure-Tagalog real performance remains **unmeasured** despite 48 passing Tagalog fixtures.

**Next proposal:** separately repair the four wrong links and eight contextual misses, including the lost baseline-correct status; keep seven recognition-dependent misses and three contextual holds explicit. No LANES connection is cleared. Preserve **345/60/60**, trained models and completed holdout exclusion. Learned DEPTH/TIME remains unfinished; no new data, neural inference, training, integration, upload, commit or push occurred. October 25 readiness is unestablished. [Outcome](../../../docs/evaluations/flood-ner-context-grouping-20261019/README.md) · [Metrics](../../../docs/evaluations/flood-ner-context-grouping-20261019/metrics.json) · [Verification](../../../docs/evaluations/flood-ner-context-grouping-20261019/verification.json) · [Guide](../../../docs/guides/ner-context-association-v37.md) · [Representation](../../../docs/plans/ner-context-representation-v37.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V36 comprehensive association review — task complete, connection blocked

**Current stage: offline flood-context acceptance.** Runtime qualification and the location-only shadow comparison are complete; the association method is still not cleared for a LANES connection. One frozen successor processed **24 real training inputs + 160 fictional cases**. All 160 behavior cases pass; **561 fresh affected tests pass (295 new)**. Independent review retained 14/corrected nine proposals and preserved all three holds. All **13 incorrect + 43 missed** old links have evidence-bound dispositions. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Real result:** eight incorrect / 31 missed associations on 23 revised references, **78.21% association F1**. All 48 revised-reference v35-correct links are retained and 22 are gained. On unchanged v35 references, successor F1 is 78.11%; reference revisions are reported separately. There is **one newly introduced wrong link versus v35** despite six removed. TIME expression recognition declines to 84.00% F1, so aggregate association gains do not mean every component improved. Seven misses require absent exact neural targets. Passing fixtures does not override the zero-total-incorrect gate or the three reference holds.

**Language scope:** all software checks pass (English 64, Tagalog 32, Taglish 64); real references are English/Taglish only. Pure-Tagalog empirical/neural performance remains **unmeasured**, with AI-assisted language/borrowing uncertainty. Preserve **345/60/60**, saved six-class model mentions and completed holdout exclusion. Learned DEPTH/TIME remains unfinished; no neural inference, training or integration ran. No post-result tuning occurred.

**Next proposal:** separately address the eight wrong resolved links, the remaining code omissions, required missing neural targets and contextual holds. Freeze any later repair before another authorized comparison; do not silently add/resize/retag mentions or introduce fallback. A read-only LANES demonstration and its language limitations remain a later gate, not automatic next execution. October 25 readiness is unestablished. [Outcome](../../../docs/evaluations/flood-ner-context-three-language-20261019/README.md) · [Metrics](../../../docs/evaluations/flood-ner-context-three-language-20261019/metrics.json) · [Verification](../../../docs/evaluations/flood-ner-context-three-language-20261019/verification.json) · [Operator guide](../../../docs/guides/ner-context-association-v36.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V35 source-only review and repair checkpoint — acceptance remains open

**Review-first v35 task complete; read-only LANES connection is not qualified.** An isolated source-only reviewer froze nine retained / fourteen corrected / one newly held contextual proposals; two earlier holds remain unchanged. Schema/frozen-tokenizer qualification passes. One candidate worker processed 24 raw training passages plus 64 fictional inputs. **64/64 behavior cases pass; 39 correct links gained, zero supported baseline-correct links lost, seven introduced strict disagreements on 23 revised references.** All 46 revised-reference v34-correct links and all 40 previously original-reference-correct links are retained. **470 fresh tests pass (111 new)**. No post-result tuning occurred.

**Next proposal:** narrowly repair recession-time precedence and collective/gauge semantics, with independent source-only disposition of remaining status-reference coverage questions before another freeze. Preserve the three contextual holds, original and revised score reports, all 345/60/60 membership and completed holdout exclusion. No LANES connection, new data or retraining is authorized by this failed gate. Learned DEPTH/TIME remains unfinished; October 25 readiness is unestablished. [Outcome](../../../docs/evaluations/flood-ner-context-repair-20261019/README.md) · [Operator guide](../../../docs/guides/ner-context-association-v35.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Offline context association checkpoint — not qualified

**Offline association implementation and one comparison are complete; acceptance failed.** All 24 eligible training proposals and 40 fictional cases were processed with references outside extraction; the two held records remain unscored. **36/40 behavior cases pass; 34 correct links gained, zero baseline-correct links lost and 20 new strict silver-reference disagreements.** Those disagreements include demonstrated scope/time errors and separately recorded reference/grouping concerns; none was relabeled or hidden. **277 fresh tests pass (61 new)**; a broader timed-out test attempt remains incomplete. No empirical retuning occurred.

**Next proposal:** separately repair clause/time updates, collective/list scope and nearby-facility abstention, and independently resolve the recorded reference questions. Freeze a successor before a separately authorized comparison. **Read-only LANES connection is not cleared.** Preserve 345/60/60, the two holds and completed holdout exclusion; no retraining/new data is needed for this repair proposal. Learned DEPTH/TIME remains unfinished; October 25 readiness is unestablished. [Outcome](../../../docs/evaluations/flood-ner-context-association-20261019/README.md) · [Operator guide](../../../docs/guides/ner-context-association.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Current interim acceptance preparation

**Reference package qualified; no extraction repair or system connection yet.** All 26 training counterparts have separate proposals: **20 retain / four corrected / two held**. The 24 eligible references contain 35 DEPTH / 22 TIME spans; unresolved/unassigned scope remains explicit. **40 fictional cases** and behavior criteria are frozen. **753 fresh regressions pass, including 94 new checks**; a guarded CPU worker verifies the references and frozen tokenizer without pipeline inference or training.

The user selected a limited location-model + depth/time-rule demonstration as the temporary defense priority. Learned DEPTH/TIME remains open. Next separately implement and test offline association repairs using saved training-only v19 location predictions; a read-only LANES connection follows only after acceptance. Membership stays 345/60/60 and the completed holdout remains closed. No collection, applied corpus correction, neural inference, training, production change, upload or push occurred.

[Outcome](../../../docs/evaluations/flood-ner-context-acceptance-20261019/README.md) · [Frozen specification](../../../docs/plans/ner-interim-context-acceptance.md) · [Read-only verification guide](../../../docs/guides/ner-interim-context-acceptance.md). Private artifact delivery is outside this task; a Git pull transfers no ignored references. The desktop can remain off.

**Earlier checkpoints below are historical.**

## Current context gap assessment

**Audit complete; learned DEPTH/TIME remains unfinished.** All 405 development records are inventoried and one guarded rules pass completed. The active contextual pilot has 26 exact training matches: 21 supported for limited diagnostics and five held; 379 records, including all 60 validation passages, lack matching contextual references. There are no complete contextual-negative references. Rules outputs are not annotations or accuracy. **659 fresh tests pass, including 48 new audit checks.**

Next propose a fixed contextual annotation/association specification and source-bound reference completion on existing texts, before bounded rule repairs or another neural experiment. V19 remains the six-location-class control; retain 345/60/60 and keep the completed holdout closed. The interim hybrid/postponement recommendation is still proposed, not adoption or cancellation of the user's trained DEPTH/TIME goal. No collection, applied corrections, neural inference, training or live integration occurred.

[Gap report](../../../docs/evaluations/flood-ner-context-gaps-20261019/README.md) · [Audit operator guide](../../../docs/guides/ner-context-gap-audit.md). The v32 rules execution grant is consumed; default verification is read-only. The desktop can remain off.

**Earlier checkpoints below are historical.**

**Repaired offline location comparison completed.** One explicitly authorized new Linux attempt processed all **six saved training articles and eight fictional cases**. Independent verification reconciles every input/hash, Unicode span, label and comparison count. Startup **5.688 s**, slowest input **0.666 s**, peak worker RSS **450.79 MiB** and wall time **9.206 s** all pass unchanged limits. The previous failed attempt, source bindings and claim are preserved; its verified stopped-owner lock was archived. The successful attempt is stopped and its active lease is cleared. [Executed outcome](../../../docs/evaluations/flood-ner-shadow-execution-20261019/README.md).

**Next:** separately design and test how location mentions associate with clause-local flood status, time, depth and uncertainty. No live processing is connected. Preserve all **345 training / 60 validation / 60 research-holdout passages**; no new data, retraining or validation/holdout evaluation occurred. The 604 passing software checks remain preparation evidence; this task adds actual execution and independent verification, with no source change or suite rerun. [Operator guide](../../../docs/guides/ner-shadow-comparison.md).

**Earlier dated checkpoints below are historical.**

**Offline location shadow adapter implemented; comparison execution remains pending.** The single Linux attempt stopped during startup before processing any article. An ORM-import/engine-construction conflict is reproduced with a constructed probe. The repaired offline import boundary passes **604 checks / 62 new checks** and read-only preparation verification, but has not been rerun in Linux. Failed receipts, original source bindings, stopped container and lease remain preserved; no automatic retry occurred. [Outcome](../../../docs/evaluations/flood-ner-shadow-comparison-20261019/README.md).

**Next:** explicitly reconcile the stopped failed attempt and execute one new offline comparison with the repaired grant and an absent destination. Only after that comparison completes should claim-context integration be scoped. Gate 3 remains passed for its earlier frozen Linux profile; the shadow-comparison gate is still open. No new data, training, validation/holdout evaluation or live connection occurred. Membership remains **345/60/60**. [Operator guide](../../../docs/guides/ner-shadow-comparison.md).

**Earlier dated checkpoints below are historical.**

**Gate 3 Linux CPU qualification passes for the frozen local profile.** Retained v19 control seed 0 runs in the unchanged backend image on Linux/Python 3.12.15/spaCy 3.7.5. All 345 saved training predictions match exactly; tokenizer parity, runtime limits and eight executed fictional fault-containment checks pass. **475 fresh regressions pass**, including 82 versioned-runner checks. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Measured:** cold readiness 4.078 s, passage p95 36.23 ms, slowest selected article 0.507 s, 100,000-character stress 5.368 s and peak worker RSS 1.839 GiB under two CPUs / 4 GiB. These are single-worker local measurements, not deployment performance or improved accuracy. All 633 protected file hashes and stat-only validation/holdout entries remain unchanged. V19 and 345/60/60 membership are unchanged.

**Next:** separately implement the read-only shadow adapter. No retraining, new data, completed-holdout evaluation or live connection is needed for this next scope. Keep context/evidence/placement gates; durable neural processing remains separately gated by the existing `rules_only` database constraint. The desktop GPU can remain off.

[Linux execution and qualification](../../../docs/evaluations/flood-ner-linux-execution-20261019/README.md) · [Runtime guide](../../../docs/guides/ner-runtime-qualification.md). No production API, dependency or schema changes; no integration, deployment, upload, commit or push.

**Earlier dated checkpoints below are historical.**

**Clean-launch task stopped at failed graceful exit.** One normal Docker Desktop stop timed out and reported failure; six Desktop/backend processes remain, while its WSL distribution is stopped. The Linux API is unavailable. **No independent Start-menu launch occurred**, so the launch-environment hypothesis and ordinary PowerShell connectivity remain untested. Gate 3 is open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next user action:** use Docker Desktop's normal **Quit** action (tray menu or error-window Quit), then report that it has closed. Verify process exit before one independent Windows Start-menu launch. No force-stop, reset, update, socket cleanup or reboot is authorized. Stop before image builds or model execution.

[Clean-launch outcome](../../../docs/evaluations/flood-ner-docker-clean-launch-20261019/README.md) · [Runtime guide](../../../docs/guides/ner-runtime-qualification.md). All 564 protected hashes and stat-only validation/holdout entries remain unchanged. No new software tests ran; the prior 393-pass result remains historical. V19 and 345/60/60 membership are unchanged.

**Earlier dated checkpoints below are historical.**

**Linux qualification attempted: blocked before image build.** Docker's backend records an inaccessible `sailor-ingest.sock` rename, its Linux API is absent and WSL reports the engine stopped. Normal start reports already running; the single restart attempt did not return a completed receipt and was interrupted. No reset, socket deletion, reinstall, security change or reboot occurred. **Gate 3 remains open; compatibility and performance are unmeasured.** [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Delivered:** separate Linux measurement helpers, an authenticated raw-only projection of all 345 training records with expected predictions kept separate, frozen local limits and **393 fresh passing regressions / 71 new Linux checks**. These are constructed tests, not a Linux execution. The full article-use workload and actual operational fault/restart qualification remain pending. V19 control seed 0 and 345/60/60 membership remain unchanged.

**Next:** restore normal Docker Desktop startup on the laptop, then resume this qualification scope: supported article workload, pinned image, parity, latency/RSS and operational failure checks. Do not move to the shadow adapter until evidence passes. No retraining, new data or completed-holdout reuse is needed; the desktop GPU can remain off.

[Linux outcome](../../../docs/evaluations/flood-ner-linux-qualification-20261019/README.md) · [Operator guide](../../../docs/guides/ner-runtime-qualification.md). No Linux inference, production connection, deployment, upload, commit or push.

**Earlier dated checkpoints below are historical.**

**Gate 3 runtime preflight completed; Linux qualification remains blocked.** The retained v19 control seed-0 checkpoint (11 files) and pinned resources (23 files) authenticate. Existing Windows/Python 3.12.14/spaCy 3.7.5 CPU inference passes four fictional probes and 40 warm calls with deterministic predictions and frozen-tokenizer parity. Docker's Linux engine is unavailable; Linux inference, representative article latency, peak RAM and failure/restart qualification remain pending. **Gate 4 live integration has not started.** [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** finish isolated Linux CPU qualification, then separately implement a read-only shadow adapter. The [integration design](../../../docs/plans/ner-v19-shadow-integration.md) preserves context/placement gates, original-body offsets and six-class mapping. Durable processing currently has a `rules_only` database constraint; do not bypass it. No retraining, data collection or completed-holdout reuse is needed. The desktop GPU can remain off.

[Runtime preflight report](../../../docs/evaluations/flood-ner-runtime-preflight-20261019/README.md) · [Operator guide](../../../docs/guides/ner-runtime-qualification.md). Fresh **322 tests pass, including 54 new runtime checks**. V19 remains retained; 345/60/60 membership is unchanged. No dependency installation, production connection, upload, commit or push.

**Earlier dated checkpoints below are historical.**

**Training-only road-boundary study completed: no qualifying rules.** Trimming and explicit crossing separation pass fictional checks, but all 345 original control prediction records remain unchanged. Descriptor trimming abstains twice; directional trimming and explicit splitting have no observed corrective applicability. Both families are partially supported and empirically unproven. **V19 corrected control seed 0 remains retained.** [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current disposition:** close this bounded feasibility study without a validation comparison or integration proposal. An empty qualifying subset is not evidence of improvement; do not tune rules from exposed findings or combine rejected prototypes automatically. Any future development direction requires a separate scope. The desktop can remain off.

[Boundary study](../../../docs/evaluations/flood-ner-road-boundaries-20261019/README.md) · [Boundary operator guide](../../../docs/guides/ner-road-boundary-study.md). All seven training ROAD-error records and five complete saved articles were reviewed. Fresh **269 tests** pass, including **71 new checks**; 24 fictional core cases remain outside membership. Ten replay files reproduce byte-for-byte. Protected 507 hashes, prior-validation metadata and 55 stat-only holdout entries remain unchanged; no validation or holdout content was supplied to this study.

**Earlier dated checkpoints below are historical.**

**Frozen validation comparison completed: retain v19 corrected control, seed 0 primary.** The two-rule shadow method increases strict validation F1 from 71.60% to 76.54% on unchanged 60 validation passages, but **does not qualify** under the prospectively frozen zero-new-strict-FP gate. Four correct entities are gained, none lost; five typed FPs are resolved and one typed FP is introduced when an already-truncated road span changes type but remains incomplete. No new textual entity or boundary is added. References, model selection and the prototype remain unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current disposition:** keep the prototype separate from production and close this bounded comparison. Any future method, revised policy or integration proposal needs a separate scope; no automatic rule tuning, retraining or completed-holdout evaluation follows. The desktop can remain off.

[Validation comparison](../../../docs/evaluations/flood-ner-context-validation-20261019/README.md) · [Validation operator guide](../../../docs/guides/ner-context-safeguard-validation.md). All 60 records are accounted for; three changed passages and complete saved articles were reviewed. Fresh **250 tests** pass, including **52 new checks**. One comparison consumed one persistent claim; no replay or retry occurred. Protected 505 hashes and 55 stat-only holdout entries remain unchanged.

**Earlier dated checkpoints below are historical.**

**Training-only context-safeguard study completed.** V19 corrected control seed 0 remains retained. The unchanged 345 training passages support two frozen rules for a later validation proposal: named-asset typing and bounded shared identifiers. Three shadow retags resolve three typed FPs and gain three TPs, with zero introduced training FP/FN; training F1 changes from 98.09% to 98.45%. Organization/role exclusions and direct designator corrections remain empirically unproven. No validation comparison, holdout content access, neural inference, training or integration occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** separately scope a frozen validation-only comparison of the two qualifying rules using saved predictions. Do not tune further rules against validation or reopen the completed holdout. Data, annotations and the retained model stay unchanged; the desktop can remain off.

[Training-only study](../../../docs/evaluations/flood-ner-context-safeguards-20261019/README.md) · [Context-safeguard operator guide](../../../docs/guides/ner-context-safeguards.md). Fresh checks: **198 passing tests**, including **94 new context checks**; the 48 fictional cases stay outside corpus membership. Eleven output files reproduce byte-for-byte; 451 protected hashes and 55 stat-only holdout entries remain unchanged.

**Earlier dated checkpoints below are historical.**

**Current NER diagnosis completed: retain corrected v19 control, seed 0 primary.** Saved predictions reproduce candidate validation F1 69.71% versus control 71.60%. All 405 records are accounted for; 22 affected validation passages/18 complete saved captures and 33 training contexts were reviewed. Candidate gains seven correct entities, loses four, introduces eighteen FPs and resolves eight. No supported reference correction or training/scoring defect was found; one inherited boundary question remains unresolved. Fresh 197 tests/20 subtests pass. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** a separately scoped development-only feasibility task for convention/training-derived context safeguards and constructed contrasts. No additional optimizer search, data collection, model selection or training is authorized. The completed holdout stays excluded; the desktop can remain off.

[Diagnosis report](../../../docs/evaluations/flood-ner-regularization-diagnosis-20261019/README.md) · [Comparison guide](../../../docs/guides/ner-regularization-comparison.md)

**Earlier dated checkpoints below are historical.**

**Current NER handoff: the regularization experiment is verified on private Drive; matching code and instructions accompany this roi-branch publication.** The 345 training / 60 validation exports are unchanged. One L2 = 0.05 candidate has seed 0/1/2 configs and a fixed maximum-three-run protocol. All four uploaded files match authenticated readback; parent, destination and files are owner-only. Desktop receipt and GPU verification remain pending. No training, inference or holdout access occurred during delivery. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next on the desktop:** preserve local changes, pull roi-branch with --ff-only, authenticate and extract the delivered archive into an absent destination, then run read-only GPU/schema verification and STOP. Actual training is a separate explicit task after verification; the completed research holdout stays outside tuning.

[Delivery report](../../../docs/evaluations/flood-ner-regularization-delivery-20261018/README.md) · [Desktop instructions](../../../docs/guides/ner-regularization-experiment.md) · [Private Drive handoff](https://drive.google.com/drive/folders/1vKssoZurLa6WjuJPftXRbJ7GcoefimKq)

**Earlier dated checkpoints below are historical.**

**Current NER task completed: one stronger-weight-decay experiment is prepared and CPU-qualified.** The existing 345 training/60 validation records, annotations, tokenizer and grouping remain unchanged. One twelve-file package supplies seed 0/1/2 configs with only `L2: 0.01 -> 0.05` changed. Fresh 341 tests/four subtests pass; 72 new checks also pass in the pinned runtime. No inference, training or research-holdout content access occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** separately publish matching code and privately deliver the experiment bundle; then perform actual desktop read-only GPU verification. Training follows as a separate explicit task: seed 0 screening, conditional 1/2, maximum three runs, with overall improvement and ROAD/LOCAL_AREA protection required. The completed holdout stays outside tuning. Delivery/GPU verification remain pending; the desktop can remain off.

[Preparation report](../../../docs/evaluations/flood-ner-regularization-preparation-20261018/README.md) · [Operator guide](../../../docs/guides/ner-regularization-experiment.md)

**Prior checkpoints follow; their dated “current/next” wording is historical.**

**Current NER status: v19 diagnosis and the one-time frozen research evaluation are complete on the laptop.** Dataset 345/60/60 and validation-selected control/seed 0 stay unchanged. V19 seed 0 training/validation/holdout F1: **98.09% / 71.60% / 73.63%**. Historical v16 seed 0 holdout 74.74%; rules 53.49%. Holdout three-seed means: control 70.34%, v16 75.13%. These results do not establish an overall v19 improvement or authorize choosing a model using the holdout.

**Next:** a separate development plan from the existing training/validation error review; no new articles or automatic retraining. Gate 3 research measurement is complete, while operational qualification, integration and release remain open. The holdout has now been evaluated and must not be tuned against or evaluated again under this protocol. AI-assisted silver, incomplete history/accounting and no certified-fresh claim remain. No collection, new training, reference/partition change, integration, upload, commit or push occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

[Diagnosis/evaluation report](../../../docs/evaluations/flood-ner-v19-diagnosis-evaluation-20261018/README.md) · [Laptop evaluation guide](../../../docs/guides/ner-corrected-holdout-laptop.md)

**Historical checkpoints follow.** Their “current/next” wording describes earlier dated tasks and is superseded by the status above.

**Current handoff: corrected v19 packages are verified on Drive; matching public code and instructions accompany this roi-branch publication.** Dataset remains 345 training / 60 validation / 60 separate research holdout. Three twelve-file packages and the fixed future protocol are delivered; all uploaded bytes match authenticated readback and five owner-only permission checks pass. No training, inference or holdout access occurred. [Delivery report](../../../docs/evaluations/flood-ner-corrected-experiment-delivery-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: desktop receipt and read-only GPU verification for all three packages, then STOP.** Preserve local work, pull roi-branch with --ff-only and receive the new private ZIP from [Drive](https://drive.google.com/drive/folders/1LDO770D82NXHZRiYNZrHe5oyLo7-vJU7). Actual desktop receipt/GPU checks remain pending. A Git pull does not deliver ignored data; do not rerun preparation or historical v16 training commands. Actual training is a separate explicit task. [Exact commands and copyable desktop prompt](../../../docs/guides/ner-corrected-experiment-desktop.md).

**Historical completed task: corrected-data experiment preparation on the laptop.** A separate 345 training / 60 validation revision adopts only 12 supported training-boundary corrections across nine records. Validation, tokenizer and partition/group bytes remain unchanged; the 60-passage research holdout stays unopened. Three twelve-file trainer packages and all nine seed/config schemas qualify in Python 3.11.17/spaCy 3.7.5. Fresh 367 tests / 35 subtests pass, including 83 new tests. No new articles/passages, inference or training occurred. [Preparation report](../../../docs/evaluations/flood-ner-corrected-experiment-preparation-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Prior preparation next-step (delivery now completed; desktop verification still pending): publish/deliver the corrected packages and frozen experiment protocol.** At that earlier preparation checkpoint, delivery/GPU verification were pending and no upload, commit or push had occurred. The specified future study uses five runs if control wins screening, otherwise at most seven. No guaranteed score follows. The desktop can remain off. [Operator guide](../../../docs/guides/ner-corrected-experiment-preparation.md).

**Historical completed task: existing-data development audit.** All three models reproduce desktop validation scores on CPU across 345 training / 60 validation records (1215 predictions); the separate 60 research-holdout passages remain unopened. Seed 0 training F1 is 99.40% versus validation 66.67%, consistent with overfitting/example differences. Source-bound review proposes 12 training-span boundary corrections across 9 existing records; one validation-boundary question remains unresolved, with its frozen scored reference retained. No data, partitions or models changed. Fresh 209 tests / 35 subtests pass, including 53 new audit tests. [Audit report](../../../docs/evaluations/flood-ner-development-error-audit-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Prior audit next-step (now completed as preparation above): choose supported corrections and define a bounded regularization experiment using existing data only.** No new articles/passages, corpus admission, replacement export, holdout access, training, upload, commit or push occurred in this task. The desktop can remain off. [Operator guide](../../../docs/guides/ner-development-error-audit.md).

Earlier training/publication checkpoints below remain historical; the current user constraint is no new data collection.



**Publication checkpoint:** Matching combined launcher and three-seed reports are included in this `roi-branch` publication. The new [private v17 Drive backup](https://drive.google.com/drive/folders/1ZFFNL9Vu-dg5xLyWsSR2wd99_qsGTE_J) preserves the combined trainer and all three selected checkpoints/logs; all eleven uploaded files pass full SHA-256 readback and all twelve folder/file permission checks are owner-only. Older folders remain unchanged. The local `.env` change stays outside the commit. [Publication evidence](../../../docs/evaluations/flood-ner-successor-publication-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current successor v16 desktop result:** All three successor seeds complete and their selected checkpoints verify; seed 0 remains primary. 75 focused tests and combined GPU/schema verification pass. Development F1 for seeds 0/1/2: 66.67% / 65.41% / 67.46%. All 12,387 protected historical files and `.env` remain unchanged. Holdout evaluation is separate. [Execution evidence](../../../docs/evaluations/flood-ner-successor-v16-desktop-training-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier preparation, delivery, correction and failed-attempt checkpoints below are historical unless explicitly carried forward.

**Current desktop execution:** verified receipt, eleven unchanged payload files in a separately bound derivative, 23 pinned model hashes, 64 focused tests and read-only RTX GPU verification pass. Shared interpreter-local Windows DLL initialization precedes GPU imports in both subprocess paths. The seed-0 attempt then failed config validation before optimizer updates on supplied lowercase optimizer keys; no later seeds or retry. A separate versioned config repair/full registry validation and a new authorized attempt are next. Earlier delivery checkpoints below are historical. [Evidence](../../../docs/evaluations/flood-ner-successor-desktop-training-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current desktop handoff: private trainer delivery to Drive is verified; successor code and public reports accompany this handoff on `roi-branch`.** Dataset membership stays **345 training / 60 validation / 60 research-holdout**. The twelve-file trainer ZIP, checksum and instructions match authenticated readback and remain owner-only. Research-holdout content stays on the laptop. No training ran. [Delivery report](../../../docs/evaluations/flood-ner-successor-delivery-20261018/README.md) · [Private Drive folder](https://drive.google.com/drive/folders/1WuhvnWfKybY8lbKKO55aToTUQ_PY6RqJ). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: receive the package on the desktop and run read-only GPU verification.** Preserve local changes, pull `roi-branch` with `--ff-only`, verify the ZIP checksum, extract only to an absent destination, then use the successor launcher with `--verify-gpu`. A Git pull alone cannot transfer ignored data. Desktop receipt/GPU verification are unconfirmed; seeds0/1/2 training is a later explicit action. [Exact instructions](../../../docs/guides/ner-successor-desktop-training.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current successor status: configuration correction v16.** The desktop reported seed 0 failed before optimizer updates because the v15 package builder lowercased case-sensitive spaCy arguments; seeds 1/2 were not started. The generator now preserves `L2`, `L2_is_weight_decay` and `nO`, and all three configs pass real spaCy 3.7.5 schema resolution. Dataset **345 training / 60 validation / 60 research-holdout** and all eight non-config trainer files remain unchanged. No training/retry or inference ran during this correction. [Correction report](../../../docs/evaluations/flood-ner-successor-config-correction-20261018/README.md) · [Corrected private Drive package](https://drive.google.com/drive/folders/15sxU7utCM9Nf429BXWUQlXgtEoC1nTQH). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: preserve the failed run, pull the matching corrected code, receive v16-configfix into a new destination, and repeat read-only GPU verification.** Require `verified_read_only`, `configuration_schema_verified: true`, `gpu_verified: true` and `training_started: false`. Desktop receipt/GPU re-verification remain pending. A later explicit seed-0 retry needs a new output directory; do not start seeds 1/2 automatically. [Exact instructions](../../../docs/guides/ner-successor-desktop-training.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


Successor entry points: `successor_preparation.prepare` consumes a hash-bound single-use grant; `successor_export_worker` serializes only the assigned development or isolated-holdout capability using vocabulary/tokenizer only; `successor_training.py` verifies by default and requires `--start-training` for a later GPU run. `research_review.export_review` still rejects review-only export. Historical helpers are unchanged.

Earlier checkpoint counts and pending tasks below are historical unless explicitly carried forward by the current status.


**Historical v9 checkpoint:** all 27 mistaken reductions were reversed, restoring 49 and preserving 53. V10 below/above separately reconsiders metadata-only holds and latest saved windows; the old protocol comparison remains preserved.


**Superseded v8 progress reduction:** its 22-passage result omitted later source-bound review decisions. V9 reverses all 27 mistaken reductions; the v8 report remains preserved. The ten software repairs remain in force.

Earlier checkpoints below retain their historical counts; v7 readiness claims are superseded.

Replacement offline APIs: `research_review.validate_reference`, `ReviewCandidate`, `select_joint`, `run_guards`, `build_status` and `validate_safe_pair`. They operate on source-exact reviewed silver proposals and allowlisted aggregates. `research_capture.ResearchCaptureSession` requires a separate acquisition grant and verified original evidence; this review-only task cannot instantiate a live acquisition session. `export_review` always rejects review-only export. Preserve and avoid executing the defective private v7 scripts. See the [operator API and constructed-test instructions](../../../docs/guides/ner-bounded-test-discovery.md#replacement-workflow-review-only).

**V6 audit completed; collection blocked:** preserve **345 training / 60 validation / 49 conditional test**. Four Taglish members are newly exposure-quarantined; the historical 53 artifact remains unchanged. English 30/30, Taglish 19/30; **eleven Taglish positives remain missing**. Local v5 ledger replay is consistent, but complete original search-tool receipts are unavailable. Claimed 649 identities + four uncertain slots / 84 attempts do not certify remaining 47/16 headroom; additional v5 exposure is unquantified. This task sent **zero network requests**, passed 27 offline guards and preserved 6,896 protected files. Next: recover original tool receipts for isolated reconciliation; no collection, admission, seal, export or training. Desktop action none. [Current outcome](../../../docs/evaluations/flood-ner-taglish-budget-continuation-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below are historical claims and do not override this audit.

**Current successor status:** **345 training / 60 validation / 53 conditional independent-test passages**. Taglish completion round v5 closed without new captures; cumulative ledger carries 649 raw identities / 84 publisher attempts under prospective 700/100 ceilings. All 53 baseline members preserved. English testing meets 30/30 (27 pos + 3 neg); Taglish is 20/27 positive + 3 genuine negative = 23/30 (**seven Taglish positives still needed**). Next: bounded acquisition proposal for unexposed localized floods (2017–2023) or authorized source-use evidence resolution before successor admission, grouped partition freeze, qualified exports or desktop GPU training. No admission, seal, export or training. [Latest evaluation](../../../docs/evaluations/flood-ner-taglish-test-completion-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Desktop action: none yet.** The desktop history inventory has already been received and reconciled within its recorded scope. Do not rerun old restoration or fixed-400 training launchers by default. After the independent-test requirements pass, the next task is explicit successor admission/grouped freezing, qualified export and a desktop GPU handoff; actual training follows that handoff. Private successor reviews are not supplied by Git. [Current desktop status](../../../docs/guides/ner-desktop-history-inventory.md).

All following checkpoint counts and inventory requests are historical and do not override the status above.

**Current successor targets clarified: retain 345 proposed training passages and target 60 validation + 60 independent test passages (465 total if all qualify).** The reviewed development proposal still contains **345 training / 57 validation**; **three additional eligible validation passages are needed**. The independent test still has only **37 conditionally supported passages / 23 positive passages missing (10 English, 13 Taglish)** for its current joint witness. These are targets and conditional counts, not admitted/frozen records. Keep all historical fitted-source groups training-only; never use isolated test material to fill validation or validation material to fill test. **Next: run and reconcile the original desktop history inventory before further collection; then qualify additional validation/test material under separate roles and resolve the recorded acquisition-budget failure.** No new search, capture, admission, export or training is authorized by this count clarification. Previous review/design/qualification packages and their completed counts remain historical. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Desktop continuation:** Follow the [pull-and-inventory guide](../../../docs/guides/ner-desktop-history-inventory.md), including its copyable desktop Codex prompt. The helper runs directly from the pulled repository with Python 3.10+ standard libraries. Inventory the original desktop before any backup restoration or collection. Git supplies code/public reports; the linked Drive folder is the October 16 historical backup, while newer private reviews remain on the laptop. Return the private inventory/manifest for reconciliation; do not start the old training launchers. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the successor targets above are newer.

**Targeted isolated collection and desktop-history handoff completed with blockers:** Review five pre-breach captures and preserve all prior material. Nine complete positive proposals are added; the supported finite-pool joint witness after known history/use filters is **37/60**, conditional on unresolved global history and the failed acquisition gate. **Discovery reached 202/200 URLs (17 new versus at most 15); collection stopped and the entire final 11-URL batch remains held/ineligible.** Capture attempts stay **37/100**. The **402 qualified development candidates / proposed 345+57** remain unchanged. A portable, tested metadata/hash inventory and desktop instructions are ready; the original desktop has not yet been inventoried. **Next: run and reconcile the desktop inventory, resolve acquisition compliance and independent-test coverage/evidence before admission/freeze/export or desktop GPU training.** No training has started; the test remains unsealed with zero admitted/scored records. [Report](../../../docs/evaluations/flood-ner-targeted-test-history-handoff-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the targeted-collection/handoff outcome above is newer:

**Archive history and saved-test selection completed; training remains pending:** Verify all **3,863 recorded v3 payloads / 11 parts / 2,357 objects**, **seven historical ZIP entries** and metadata for **19 known Drive items**, with no missing/conflicting recorded payload. Complete isolated positive-window selection and source-only historical comparisons in a separate private curator package; retain the unchanged **60 / 30+30 / 27-positive+3-negative-per-language** target. **Unknown external cross-computer history remains unresolved; test stays unsealed with zero admitted/scored records.** The **402 qualified development candidates / proposed 345+57** remain unchanged. **Next: address the specific remaining independent-test history/evidence/coverage gaps before admission/freeze/export and desktop GPU handoff.** [Archive and saved-test outcome](../../../docs/evaluations/flood-ner-archive-history-test-selection-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the archive/selection outcome above is newer:

**Successor qualification and isolated-test reassessment complete; training remains pending:** **402 qualified proposal candidates / 149 source cases**, retaining **345 proposed training / 57 validation**; all 259 relationship entries qualify for supported conservative joint grouping without incident-identity or independence claims. Carry forward 64 exclusions and 99 holds; record 16 scoped project-use adoptions for 20 saved-source windows. **The separate 60-passage test stays unsealed: the user is unsure whether all older cross-computer article histories are represented.** Curator-specific evidence/count gaps remain in the safe report. No actual admission, freeze, export or training. **Next: resolve the concrete history/isolated-test gaps; reuse completed development qualification before a separate admission/export/desktop GPU handoff.** [Qualification and test reassessment](../../../docs/evaluations/flood-ner-successor-qualification-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the qualification status above is newer:

**Successor dataset design complete; retraining remains pending:** Use all **402 provisional candidates** in a separate **345 training / 57 validation proposal** (170/175 training English/Taglish; 37/20 validation). Actual original/A/recovery/B input bindings anchor all 280 historical training records, including now-excluded/held examples. **The old additional 240 / exact-balance quotas are prospectively superseded for this version by explicit user choice; historical specifications and results remain unchanged.** Validation has no Taglish ROAD/LANDMARK or short-code-theme examples; conservative grouping does not certify event independence. **Next: resolve proposed-member source-use/group admission qualifications and complete the separate unchanged 60-passage fresh-test boundary before admission/freeze/export and desktop training.** No actual admission or partition freeze occurs. [Successor design](../../../docs/evaluations/flood-ner-successor-design-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the successor design above is the current status:

**Current Gate 3 status:** The [pre-retraining consistency review](../../../docs/evaluations/flood-ner-consistency-review-20261016/README.md) confirms shared schema/six-class profile and unchanged original experiment. Windows source-byte checkout protection is repaired; 80 focused checks pass. Laptop work is review/validation/preparation; actual training remains on the qualified desktop GPU. New 244-record development drafts are not admitted or partitioned; final successor corpus size/conventions, current readiness gaps and the fresh independent holdout remain unresolved. Historical fixed-400 launchers/exports are not a ready new-data training path. No automatic CPU fallback or new training is introduced.

Historical qualification review: all 60 passages and 391 original/A seed 0 error events are reviewed in a separate ignored checkpoint. Fourteen passages retain unresolved AI reference/convention questions; frozen labels, scores and model roles are unchanged. The review is complete; operational qualification remains open. Next prepare the remaining Gate 3 qualification specification before runtime integration. [Review](../../../docs/evaluations/flood-ner-model-qualification-20261016/README.md).

Historical held-out evaluation: original/A seeds 0/1/2 and rules/native baselines complete one frozen test attempt on 60 passages. Original seed 0 remains primary at 63.12 strict test F1; exploratory A seed 0 scores 67.72. The test set is now exposed. Next review Gate 3 model qualification before isolated integration; no test-driven tuning or automatic promotion. [Held-out report](../../../docs/evaluations/flood-ner-heldout-test-20261016/README.md). Earlier checkpoints follow.

Historical primary-training result: primary seed 0 manually completed, selecting development F1 67.15 at step 455. Run frozen seeds 1/2 manually, one at a time, using RUN-TRAINING.ps1 -Seed 1 (or 2) -StartTraining from the repository root; omit -StartTraining for check-only. Existing outputs are refused. Seed 0 remains primary. [Result](../../../docs/evaluations/flood-ner-primary-training-20261016/README.md); [commands](../../../docs/guides/ner-first-manual-training-20261016.md). Earlier checkpoint summaries follow.

Historical desktop preparation: export and baseline/configuration preparation pass. The ignored experiment-preparation-20261016-v2 checkpoint freezes rules mapping and three GPU-initialized seed configurations; seed 0 training is next. No corpus prediction evaluation/training has run. See [preparation verification](../../../docs/evaluations/flood-ner-experiment-preparation-20261016/README.md). Earlier checkpoint summaries below preserve their historical states.

Historical laptop handoff: private Drive delivery is verified through roicambe02@gmail.com; the [owner-only folder](https://drive.google.com/drive/folders/1gnGV2wP0gNHx2LNa64fwc-U4AIQxRdkT) holds the unchanged v2 ZIP and companions. All seven files pass readback hashes. Use the [desktop instructions](../../../docs/guides/ner-desktop-handoff-20261016.md); actual desktop restoration/qualification have not run. The latest software result is 880 passed/one skipped; no software changed in this delivery. Earlier checkpoint details follow.

Historical laptop corpus-tokenizer gate: the new `qualify-corpus-tokenizer` command and evaluation protocol are delivered, but the single isolated run is blocked at import by Windows Application Control error 4551. No passages were tokenized and no predictions/export/training ran. 840 software tests pass/one skipped. Admission remains 400, original datasets are preserved, and the next step is verifying the existing desktop environment/private input paths before a separate qualification run. [Report](../../../docs/evaluations/flood-ner-corpus-tokenizer-20261016/README.md); [local failure/protocol guide](artifacts/corpus-tokenizer-qualification-20261016-v1/START-HERE.md).

Earlier completed private academic-use checkpoint: a separate admitted v5 derivative contains 400 AI silver location samples from 138 articles and 40 paired contextual records, with frozen 200/200 languages and 280/60/60 partitions. Only the three source-policy fields change; original research-only files and all twelve nonacademic outcomes remain unchanged. The ledger retains 69 explicit, 68 desktop-reported and one prior local adoption, without reconstructing the missing detailed desktop predecessor. This is scoped project admission, not publisher permission or a dataset license. Corpus qualification against the pinned calamanCy tokenizer and a frozen evaluation contract is next; no export or training has run. See the [admission report](../../../docs/evaluations/flood-ner-academic-admission-20261016/README.md) and [actual local working folder](artifacts/academic-admission-20261016-v1/START-HERE.md).

Current GPU checkpoint: the actual RTX 3060 Ti desktop passes isolated Python 3.11.17/spaCy 3.7.5/CuPy 13.6.0/Torch 2.11.0+cu128 execution, six-class constructed trial updates and exact saved-model CPU entity replay. 122 focused tests pass. See the [GPU evaluation](../../../docs/evaluations/flood-ner-desktop-gpu-20261015/README.md) and [rerun/setup guide](../../../docs/guides/ner-desktop-preflight.md#qualified-rtx-desktop-environment-october-15-2026). Source admission and full-cohort qualification remain separate.

Current desktop preparation: the standard-library-only `desktop_inventory.py` runs directly before installing research dependencies. It records local hardware/driver facts in a fresh ignored destination and never claims CUDA or training qualification. See the [desktop guide](../../../docs/guides/ner-desktop-preflight.md). Source-use decisions remain independent; publisher correspondence is optional clarification rather than a universal prerequisite when a supported exception applies.

Earlier clarification preparation: four unsent drafts and a 69-article/243-passage register are available in the [local start-here guide](artifacts/held-article-clarification-20261015-v1/START-HERE.md). Recipient identities and response fields remain blank; no hold, recommendation or admission was changed. See the [metadata report](../../../docs/evaluations/flood-ner-held-clarification-20261015/README.md).

Earlier academic-use proposals: 139 articles assessed; 70 GMA articles (157 passages) recommended for private academic use and 69 held for source-use clarification. The 400 accepted AI silver samples, 40 contextual-v3 pairs and frozen partitions remain unchanged. No recommendation is an applied project decision, publisher permission or source admission. academic_proposal.validate_decision_proposal(proposal, records, contexts, root) is a separate read-only Python interface; it does not replace the earlier review validator or add a CLI. New forms carry root-relative path/hash references to facts/guidance/reviews. See [proposals](../../../docs/evaluations/flood-ner-academic-proposals-20261015/README.md) and the [local decision brief](artifacts/academic-decision-proposal-20261015-v1/DECISION-BRIEF.md).

Earlier research checkpoint: 400 corrected AI silver location records from 139 articles, 40 contextual v3 pairs and frozen 280/60/60 partitions. The verified Drive backup is owner-only. Researcher-reported adviser guidance limits use to private research/training; no specific international ethics framework is established. Source-use project decisions remain unresolved, and this guidance does not change admission flags. Next finalize the supported academic-use basis and article-exception dispositions before admission/news-model processing. Read-only hardware inventory and constructed-only GPU environment checks can proceed independently; actual corpus/tokenizer/training and public-inference scope gates remain. Retention uncertainty alone is not a training prohibition. See [current publication audit](../../../docs/evaluations/flood-ner-publication-20261015/README.md) and [private-access record](../../../docs/evaluations/flood-ner-private-access-20261015/README.md).

Run commands from `backend/` using its existing environment (Python 3.12, spaCy 3.7.5). This package prepares research sources and annotated corpora. It does not train a model, access operational SQL, invoke news processing/publication, or change production configuration.

```powershell
.venv/Scripts/python.exe -m training.flood_ner inventory
.venv/Scripts/python.exe -m training.flood_ner capture --url 'https://publisher.example/article' --source-id 'publisher-article' --publisher 'Publisher' --language tagalog --event-group 'review-needed-event'
.venv/Scripts/python.exe -m training.flood_ner inspect-place --name 'Sitio Seis' --context 'Catmon, Malabon' --city 'Malabon'
.venv/Scripts/python.exe -m training.flood_ner collect-news training/flood_ner/artifacts/discovered_urls.json
.venv/Scripts/python.exe -m training.flood_ner import-browser-news training/flood_ner/artifacts/rendered_snapshot.json --source-id 'abs-rendered-report' --language english
.venv/Scripts/python.exe -m training.flood_ner capture-wikipedia --title 'Typhoon Noru' --language en
.venv/Scripts/python.exe -m training.flood_ner verify-news ../docs/evaluations/flood-news-corpus-100-20261014/collection_outcomes.json --output training/flood_ner/artifacts/collection100/verified
.venv/Scripts/python.exe -m training.flood_ner prepare-pilot ../docs/evaluations/flood-news-corpus-100-20261014/news_register.json --output training/flood_ner/artifacts/readiness/review-v1
.venv/Scripts/python.exe -m training.flood_ner review-passages training/flood_ner/artifacts/readiness-20261014/review-queue-v3/candidate_passages.jsonl ../docs/evaluations/flood-ner-editorial-20261014/editorial_reviews.json --output training/flood_ner/artifacts/editorial/replay-v1
.venv/Scripts/python.exe -m training.flood_ner validate training/flood_ner/artifacts/annotations.jsonl
.venv/Scripts/python.exe -m training.flood_ner export training/flood_ner/artifacts/annotations.jsonl --output training/flood_ner/artifacts/datasets/v1
.venv/Scripts/python.exe -m training.flood_ner export training/flood_ner/artifacts/location_annotations.jsonl --profile location-only-v1 --output training/flood_ner/artifacts/datasets/location-v1
```

`capture` needs an actual explicitly supplied public HTML URL. It follows bounded redirects, caps responses at 4 MiB, and refuses a page with no article/main container or JSON-LD article body. It never falls back to treating the entire page as an article. It retains raw response HTML bytes, frozen extracted text, extraction method, hashes, known timezone-qualified publication metadata and capture time. HTML-visible text is a reproducible extraction, not the raw HTML; all downstream offsets refer to the frozen text. Navigation/body pollution still needs review. Captures default to research-only with unknown reuse terms. Repeated capture preserves the same immutable record; identical bodies from different URLs retain separate source identities.

`inventory` imports preserved `docs/evaluations/**/source_manifest.json` text captures, the explicitly captured-original `mcp_saved_news.json` article texts, and locally fetched captures. It validates known text hashes, preserves URL/capture-version identities, including versions with matching body hashes, and reports missing files or unsupported manifests. It does not import the constructed 50-item rule fixture as news. Results are `sources.jsonl`, metadata-only `report.json` and research evidence pointers in `case_matrix.json`. Unknown language and timestamps remain unknown. Inventory succeeds with explicitly listed per-source issues; inspect `issues` before proceeding.

`inspect-place` reuses existing cardinal normalization, PSGC hierarchy lookup and identified OSM locality assets. `--city` is explicit source context, not inferred from a guess. It returns candidates, including ambiguity metadata; it writes no annotations and establishes no flood geometry.

The annotation contract is defined in `annotation/schema.py`, with a generated JSON Schema in `annotation/schema.json`. See the [annotation guide](../../../docs/guides/flood-ner-annotation-v1.md) and [research findings](../../../docs/research/flood-ner-semantics-20261014.md). Each JSONL line is one full `AnnotationRecord`; the source object contains the unchanged complete source text so validation can verify passage offsets without mutable external files.

`validate` checks schema/extra fields, source and passage hashes, exact spans, token alignment, non-overlapping entity spans, typed relationship references, evidence coverage, parent/override cycles and split leakage. It prints errors and exits nonzero on invalid input. It cannot prove semantic correctness, licensing, independent review or physical flooding.

`export` additionally requires complete accepted review, reviewer identity, a teacher for silver labels, explicit training admission with allowed reuse, and frozen article/event/syndication grouping and train/dev/test membership. It refuses any unqualified record rather than silently omitting it. Unsyndicated sources need their own reviewed syndication-group identifier. Copied text, URLs, article revisions and related event/syndication groups cannot cross splits. Negative passages have empty entity lists only after complete annotation review; incomplete labeling must not become negative training evidence.

Exports contain train/dev/test `.spacy` files, full records in `relationships.jsonl`, `tokenizer.bin`, and an immutable manifest with schema/annotation versions, record and split identities, quality, source hashes, tokenizer identity and file hashes. Empty splits are represented and counted; they do not establish benchmark readiness. Destination directories must be empty. `--allow-constructed` is solely for explicitly marked test exports and stamps the manifest; it does not turn test fixtures into research ground truth.

AnnotationRecord.annotation_profile is context-rich-v1 by default, preserving older records. The explicit location-only-v1 profile contains the six place labels and rejects DEPTH/TIME/facts/relations; save rich references separately. Export --profile must match every record, and its manifest records profile and vocabulary. Both profiles retain all admission/group/split/quality guards. The [developer-authorized AI pilot](../../../docs/evaluations/flood-ner-ai-pilot-20261014/README.md) has twelve research-only location records (ten same-teacher accepted, two unresolved) and twelve paired rich drafts, not 24 independent samples. Actual pilot export remains blocked by unqualified admission/group/split prerequisites. No human verification or model accuracy is claimed.

Earlier tokenizer `lanes.xx.address-v1` used spaCy's multilingual blank tokenizer with an additional final-period boundary for address codes such as `25-A.`. It changes token boundaries, never source characters. The tokenizer is saved and hashed. Switching to a future trained model's tokenizer requires revalidation and a new corpus export; this tokenizer is not a trained NER model.

All generated sources, corpus exports, checkpoints and model artifacts belong under ignored `artifacts/`; the production Docker build also excludes that directory. New sources and reports do not alter shared flood records. No runtime aliases, schema migrations or dependency upgrades are introduced.

`collect-news` consumes a JSON array of discovered public publisher URLs. It inventories existing sources, avoids known canonical article identities and records successful candidates and failed fetches explicitly in `candidates.json`. It does not approve a candidate based on keywords. Review bodies/publication evidence, language, duplicates and event/syndication relationships before marking entries accepted. The collection schema/report is `lanes-flood-news-collection-v1`; the source schema remains `lanes-flood-ner-v1`.

The capture parser prefers an explicit JSON-LD article body, decoding embedded HTML when present, and supports HTML publication meta fields. ABS-CBN static bodies use the publisher's body container; a site shell cannot qualify as a body. `import-browser-news` preserves a deliberately saved public rendered DOM snapshot with `url`, `title`, `body_text`, `headers` and timezone-qualified `captured_at`. A Published/PHT header supports an instant; a reviewed Philstar article-date header supports only a calendar day. Unknown/conflicting headers fail. It freezes the unchanged rendered body plus the hashed snapshot; import never fabricates missing bodies or publication headers. Existing snapshots cannot be overwritten with a different identity. `reextract-source` repairs a specifically supported malformed script closure in saved JSON-LD markup, writes an additional extraction version and preserves raw HTML and the original capture.

`verify-news` requires the explicit positive --expected-count (default 100) of accepted research-only articles, each backed by an inventoried source, reviewer/notes, publication evidence and hashed body offsets. It checks local text/raw files, canonical publisher identity, publication window/evidence and exact/near-copy or version duplicates before writing the news register, outcome manifest and coverage report. All paths are repository-relative and must stay within the repository. Missing files fail explicitly. Two old captured-original fixtures explicitly preserve unknown raw HTML/retrieval times; their printed date headers support publication days only. Another checkout needs matching frozen captures to verify this register.

`capture-wikipedia` uses the official revision API to freeze a revision at or before the collection cutoff, with main-slot wikitext, permanent/history links, timestamp, attribution and site license metadata. These reference records count zero toward news and remain excluded from primary training. Page-specific reuse and geographic identity checks remain separate.

The [completed-work review](../../../docs/evaluations/flood-ner-review-20261014/README.md) records stricter source-bound canonical identity, original timestamp/reuse checks, capture-bound publication evidence, actionable malformed-input errors and exact CRLF/LF preservation. Export compares normalized URL/article aliases for split leakage and rejects explicitly provisional/unresolved group names. Wikipedia revision files now include language; repeated captures preserve existing metadata and verify content, including legacy revision-only filenames. The existing 100-article register remains unchanged.

The [100-article acceptance report](../../../docs/evaluations/flood-news-corpus-100-20261014/README.md) links the metadata register, separate supporting inventory, exclusion/failure outcomes and measured gaps. Case-type counters are research cues, not reviewed training entities or fact relations. Article-level language and provisional grouping require passage-level review before the pilot.

Tests:

`review-passages` consumes original candidate JSONL plus an explicit JSON array of EditorialReview decisions. It binds source/candidate/version/hash identities to the inventory, rejects lost non-whitespace text and overlapping/corrupt ranges, and preserves separate contiguous blocks around reviewed exclusions. No cleaned-text concatenation occurs. Full sources/blocks remain under ignored artifacts; metadata carries selection/exclusion hashes/reasons, source-relative context notes and reviewer kind. AI-assisted decisions retain a research-team manual-review hold; Tagalog/unknown blocks are distinguished from the paper's English/Taglish scope. Group/reuse/annotation holds remain, and all admission/label/split counts stay zero. Prior queues cannot be overwritten. See the [editorial/paper report](../../../docs/evaluations/flood-ner-editorial-20261014/README.md); the paper's target is 400 total manually annotated samples with 280/60/60 splits, not 400 articles or 400 fitted-training examples.

`prepare-pilot` rechecks reviewed source identities and local file/evidence hashes, then creates one proposed context window per accepted article. Its candidate JSONL includes full source/passage text under ignored artifacts only; metadata registers exclude both text objects. Article-level language and provisional groups remain separate from unknown passage language and pending review. It creates no entity/fact labels, split assignments or training admission. Destinations must be empty and beneath the repository's training artifacts directory. See the [initial readiness report](../../../docs/evaluations/flood-ner-readiness-20261014/README.md) for publisher policy evidence, draft groups and measured holds. A candidate cannot be passed directly to AnnotationRecord export.

The [readiness review](../../../docs/evaluations/flood-ner-readiness-review-20261014/README.md) additionally binds candidate/article identities to the captured source/version/bounds, requires unresolved review/provenance holds and carries existing source-review notes into the draft. Interface text, captions, truncation, omitted numbered cues and known measurement-role ambiguity generate explicit review holds. These diagnostics do not establish passage correctness or admit training data. Existing draft queues are preserved; use a new output directory for a corrected proposal.

```powershell
.venv/Scripts/python.exe -m pytest --noconftest tests/test_flood_ner_editorial.py tests/test_flood_ner_preparation.py tests/test_flood_ner_collection.py tests/test_flood_ner_tooling.py tests/test_philippine_location_service.py tests/test_locality_number_service.py tests/test_news_locality_anchor.py tests/test_news_heading_context.py -q
```

`--noconftest` deliberately avoids the repository's application/database fixtures. The latest readiness review records 378 preparation, location, temporal, source and processing checks under explicit isolated source-mode settings. Earlier temporal failures were repaired in the preceding milestone; their history remains in that evaluation.

## 400-sample cohort assembly

The [400-sample report](../../../docs/evaluations/flood-ner-corpus-400-20261014/README.md) records 400 silver location records from 132 articles, 200 English/200 Taglish, exact 280/60/60 research partitions and three publishers below 200 samples. Training admission/export remains zero. Article language tags are preserved; AnnotationRecord.passage_language records reviewed sample language.

```powershell
.venv/Scripts/python.exe -m training.flood_ner verify-news training/flood_ner/artifacts/cohort400-20261014/reviewed-source-register-v2/collection_outcomes.json --expected-count 142 --output training/flood_ner/artifacts/cohort400-20261014/source-replay
.venv/Scripts/python.exe -m training.flood_ner build-cohort training/flood_ner/artifacts/cohort400-20261014/annotations-v1/location_annotations.jsonl --group-reviews training/flood_ner/artifacts/cohort400-20261014/group_reviews-v1.json --news-register training/flood_ner/artifacts/cohort400-20261014/reviewed-source-register-v2/news_register.json --pilot-records training/flood_ner/artifacts/cohort400-20261014/annotations-v1/retained_pilot_ids.json --output training/flood_ner/artifacts/cohort400-20261014/replay-new
```

Destinations must be empty. GroupReview binds source/version/body/publication evidence and records explicit reviewer/rationale. Cohort assembly preserves capture metadata, applies reviewed grouping only to derived annotations, excludes wrong-language/profile/unresolved/duplicate/overlapping records, and refuses infeasible exact quotas. Retained pilots are pinned to training. Existing SciPy/NumPy supplies constrained deterministic selection; no new dependencies. The default command targets 140/140 train and 30/30 dev/test, at least three publishers and at most 200 records per publisher. Reporting components can deliberately overgroup dependencies without declaring one physical event.

Current tokenizer lanes.xx.address-v2 separates source dateline/list delimiters and final periods, retaining internal 25-A codes and original characters. Corpus schema/tokenizer bytes and hashes are frozen. A model using another tokenizer requires revalidation; this tokenizer is not a trained model. Full annotations/context stay ignored, and all real exports still require qualified reuse/admission. Software counts, language judgments, teacher agreement and independently verified accuracy are distinct.

The [follow-up review](../../../docs/evaluations/flood-ner-corpus-400-20261014/followup_review.json) corrects auxiliary contextual serialization in context-v2/context_evidence.jsonl. The context.write_context_jsonl helper uses the existing compact JSONL writer and refuses an existing destination. All 400 original contextual objects are preserved with raw text and unreviewed cues; context-v1 remains intact. Final isolated verification passes 425 checks. Before running the broader source-mode regressions, explicitly set all auditor options rather than inheriting workstation configuration. No operational configuration was changed.

## Frozen-cohort qualification

Run this read-only diagnostic command with a new ignored output directory:

```powershell
.venv/Scripts/python.exe -m training.flood_ner qualify-cohort training/flood_ner/artifacts/cohort400-20261014/cohort-v2 --news-register ../docs/evaluations/flood-ner-corpus-400-20261014/source_register.json --model-register training/flood_ner/artifacts/qualification-20261014/model-evidence/model_register.json --reuse-register ../docs/evaluations/flood-ner-readiness-20261014/reuse_register.json --output training/flood_ner/artifacts/qualification-20261014/new-run
```

Model/reuse registers are optional; omitting them leaves those checks unperformed. The command verifies frozen artifacts and original selected source evidence, reports per-language/label support, publisher dependence and model metadata compatibility, and writes a candidate tokenizer without promoting it. It never resolves source use or admits/trains/loads a model. Default remains lanes.xx.address-v2; lanes.xx.address-v3 is explicit opt-in for research assembly/validation/export. JSONL representations escape alternate Unicode separators while decoding exact original text. See the [first qualification report](../../../docs/evaluations/flood-ner-qualification-20261014/README.md) for its historical 455-test checkpoint and the [stronger revision attempt](../../../docs/evaluations/flood-ner-revision-400-20261014/README.md) for its historical 508-test result and quota holds. The [completed continuation](../../../docs/evaluations/flood-ner-continuation-400-20261015/README.md) records 525 checks and a qualifying frozen revision.

## Bounded stronger revision

`--publication-start` and `--publication-end` configure inclusive dates on collection, verification, validation, assembly and qualification. Legacy defaults remain 2022-01-01/2026-10-14. Qualification reads a frozen manifest's window; an explicit override must match. Date-only assembly requires an accepted news-register entry whose saved publication evidence verifies. Validation with an explicit window similarly needs `--news-register` for sources without a qualified publication instant.

`build-cohort --coverage-policy` loads a strict `lanes-flood-ner-coverage-v1` JSON policy. Default policy values encode the authorized stronger publisher/article/group/label quotas. The old command without a policy retains its original publisher/selection behavior. `--report-infeasible` saves the reviewed pool, exclusions and necessary coverage failures and exits **2**, without freezing partitions. This is not a successful 400-sample selection. Invalid input still exits 1 and is not converted into an infeasibility pool. Exit 0 denotes successful assembly.

Supply `--candidate-ledger` and `--baseline-inventory` together to enforce 300 cumulative additional URLs and 200 additional admitted articles. The baseline is an immutable pre-revision array of source objects containing URLs. The ledger is a JSON URL array; collection updates it only within the cap, and assembly rechecks admitted articles against it. Tracking/version aliases do not inflate article counts. Admitted articles still require complete source reading and verified evidence.

Historical incomplete-pool replay from `backend/`:

```powershell
.venv/Scripts/python.exe -m training.flood_ner build-cohort training/flood_ner/artifacts/revision400-20261014/reviewed-v8/location_annotations.jsonl --group-reviews training/flood_ner/artifacts/revision400-20261014/reviewed-v8/group_reviews.json --news-register training/flood_ner/artifacts/revision400-20261014/reviewed-v8/news_register.json --pilot-records training/flood_ner/artifacts/cohort400-20261014/annotations-v1/retained_pilot_ids.json --coverage-policy training/flood_ner/artifacts/revision400-20261014/reviewed-v8/coverage_policy.json --publication-start 2017-01-01 --publication-end 2026-10-14 --tokenizer lanes.xx.address-v3 --candidate-ledger training/flood_ner/artifacts/revision400-20261014/candidate-ledger.json --baseline-inventory training/flood_ner/artifacts/revision400-20261014/baseline-inventory.json --report-infeasible --output training/flood_ner/artifacts/revision400-20261014/new-replay
```

The v3 rules additionally cover slash-delimited names, ordinal boundaries and punctuation/byline joins. Earlier saved v3 candidate bytes remain unchanged; reproduce a checkpoint using its actual tokenizer bytes/hash, not its name alone. The final v3 assembly tokenizer is saved before validation mutates the vocabulary. Source characters are never rewritten to fix alignment.

`review-context-pilot FROZEN_COHORT --annotations CONTEXT_JSONL --reviews CATEGORY_REVIEW_JSON --output NEW_IGNORED_FOLDER` checks exact pairing, training-only membership, 20 records per language, five articles per language, and four cases per category including both languages. It requires complete source-supported rich facts/relationships and rejects mismatched spans, evidence, overrides and fabricated clocks. Pairing adds zero independent location samples. The October 15 continuation freezes a qualifying 400-record revision and validates 40 contextual pairs; the earlier proposals remain preserved drafts.


## Completed continuation and replay

`build-cohort --selection-time-limit 300` uses an explicit optimizer bound while retaining the 60-second default. Allowed values are integer seconds 1–3600; nondefault limits are recorded in manifests. A resource-limited solve is unresolved, not evidence of infeasibility. Source inventory retains `(canonical URL, capture version)` identities, including versions with matching body hashes. Collection paths bind to the actual version. Verified Philstar pipe/hyphen publication headers and Inquirer bylines can establish date-only evidence; conflicting dates remain held.

Preserved continuation checkpoint: the corrected input was `artifacts/continuation400-20261015/reviewed-final-location_annotations.jsonl`; source/group registers are in `reviewed-v5/`, final frozen selection in `assembly-corrected-300s-v1/`, and historical superseded context in `contextual-reviewed-v1/`; that checkpoint used `artifacts/review-qualification400-20261015/contextual-reviewed-v2/`. A byte-identical replay is saved in `assembly-corrected-replay/`. The original legacy replay is byte-identical too.

The dedicated ignored `artifacts/stronger-400-continuation-20261015/` folder contains 342 article links/captures, 400 sample links, frozen location/context records and a verified hash manifest. It needs an external backup independently of Git. [Report](../../../docs/evaluations/flood-ner-continuation-400-20261015/README.md).


## Follow-up review and current qualification

Current location records are in `artifacts/annotation-correction-20261015-v1/cohort-v2/`; accepted paired contexts are in its sibling `contextual-v3/`. Earlier cohorts and contextual v1/v2 remain preserved. The existing context-review guards still apply; no runtime parser changes.

`qualification_report` binds candidate-tokenizer bytes before validation grows vocabulary, so reported SHA matches the candidate_tokenizer.bin written by qualify-cohort. The corrected saved diagnostics are in `artifacts/review-qualification400-20261015/qualification-v2/`. The dedicated `artifacts/stronger-400-reviewed-20261015/` bundle contains current contextual-pilot-v2, frozen location data, source/sample CSVs, qualification diagnostics and a verified hash manifest. A frozen silver-evaluation protocol is preparation only: no model is installed, evaluated or trained and source-use holds remain enforced. [Report](../../../docs/evaluations/flood-ner-review-qualification-20261015/README.md).


## Isolated constructed-only model preflight

Production requirements only comment-link `requirements-qualification.in`; do not install this optional recipe into backend/.venv. Bootstrap uv 0.13.1 in a new ignored research folder, install managed CPython 3.11 with explicit --install-dir plus --no-bin --no-registry, and create a separate environment with include-system-site-packages=false. Use only task-local caches. Resolve a binary-only, hash-locked recipe using an exact official CPU Torch wheel URL, then sync that lock with --require-hashes. Record interpreter build/binary hashes and package versions. Do not replace the main Python/spaCy environment.

The successful run uses Python 3.11.17, spaCy 3.7.5 and pinned calamanCy md 0.1.0 revision 51a40433059d8a2c25b98a48eca854f8789a491a. The complete artifact, current lock/environment manifests and failed/successful runs are in ignored `artifacts/preflight-use-20261015/`. `requirements-v2.lock` adds Click 8.5.0 to satisfy the observed spaCy import; earlier locks/failures remain preserved.

From backend/:

```powershell
.venv/Scripts/python.exe -m training.flood_ner preflight-model --python training/flood_ner/artifacts/preflight-use-20261015/research-env/Scripts/python.exe --model-manifest training/flood_ner/artifacts/preflight-use-20261015/model_manifest.json --cases training/flood_ner/configs/preflight_constructed_cases.jsonl --output training/flood_ner/artifacts/preflight-use-20261015/new-replay
```

The command is offline and refuses the main interpreter, nonconstructed provenance, malformed spans/hashes and existing destinations. Inputs are exactly 24 probes with 12 English/12 Taglish and all six expected place classes. Model predictions remain LOC/ORG/PER. Output uses a revalidated UTF-8 byte protocol, records one warm-up plus ten measured CPU passes and peak working set, and retains failures without fabricated resources. Exit0 means research loading/inference passed; exit2 denotes a documented execution/output failure; invalid input exits1. Alignment gaps are diagnostics, not an automatic tokenizer change. No news data is inferred, exported or trained. [Results](../../../docs/evaluations/flood-ner-preflight-use-20261015/README.md).

## Constructed model-tokenizer qualification

qualify-model-tokenizer compares the native pinned calamanCy tokenizer with a separate lanes.tl.calamancy-address-v1 candidate and the existing corpus v3 tokenizer. It requires exactly 48 hash-bound constructed cases (24 per language), preserving the original 24, with explicit reference spans and separate token-boundary controls. No news corpus is processed. Run from backend/; choose a new ignored output directory.

```powershell
.venv/Scripts/python.exe -X utf8 -m training.flood_ner qualify-model-tokenizer --python training/flood_ner/artifacts/preflight-use-20261015/research-env/Scripts/python.exe --model-manifest training/flood_ner/artifacts/preflight-use-20261015/model_manifest.json --cases training/flood_ner/configs/tokenizer_qualification_cases.jsonl --output training/flood_ner/artifacts/tokenizer-qualification-local-repeat-v1
```

Exit 0 means constructed qualification passed; 2 means execution or qualification failed with a saved report; invalid inputs exit 1. Native and candidate run in separate isolated CPU processes. Saved tokenizer bytes exclude vocabulary and are bound to verified model vocabulary hashes. Output includes tokenizers, manifests, constructed predictions, parent-recomputed controls/alignment, prediction differences, resource measurements and explicit failure evidence. The existing preflight-model command remains native with its original 24-case input contract.

The completed run has zero candidate alignment errors and 56 passing controls across 48 cases. Twelve prediction changes are reported without claiming accuracy. Corpus v3 is compared unchanged; its expanded constructed gaps do not rewrite the validated frozen dataset. Before training, admit source use and qualify the chosen model tokenizer against the actual corpus; train and infer with consistent tokenization. [Measured qualification](../../../docs/evaluations/flood-ner-tokenizer-qualification-20261015/README-v2.md).

## Private study/use-review bundle

prepare-use-bundle validates the frozen 400-record cohort, forty paired contexts, original source-use packet/forms, 139-source register, captured evidence and fifteen scoped assessments. It performs no network requests, grants no admission, and preserves source records. Use a new ignored destination.

```powershell
.venv/Scripts/python.exe -X utf8 -m training.flood_ner prepare-use-bundle --cohort training/flood_ner/artifacts/annotation-correction-20261015-v1/cohort-v2 --context training/flood_ner/artifacts/annotation-correction-20261015-v1/contextual-v3 --review-packet training/flood_ner/artifacts/annotation-correction-20261015-v1/review-packet-v3.json --output training/flood_ner/artifacts/400-sample-study-package-local-repeat-v1
```

The START-HERE.md file explains four numbered folders: private study, paper appendix draft, download candidate and use review. It includes source/sample CSV links, a balanced training-only appendix, passage-only JSONL and a local ZIP, evidence, editable unresolved forms and a hash manifest. Appendix selection greedily maximizes newly covered classes, then publishers, then record ID, with five examples per language. Its achieved coverage is reported rather than assumed.

The separate lanes-passage-share-candidate-v1 format contains raw passage text, Unicode offsets, labels, provenance and public source metadata. It excludes full-source fields/HTML, private paths and model weights. Whole-article passages become metadata-only entries with text=null; all original records remain intact privately. It is not an AnnotationRecord training export. Context pairs remain separate and do not increase the sample count. No dataset license is assigned.

Exit 0 means the private package was prepared with holds, not cleared for training or distribution. Invalid inputs/refused destinations exit 1 before copying. Copy/serialization failures save failure.json where possible, return nonzero and leave the partial folder for inspection; choose a new destination after fixing the issue. The new package is a local copy, not an external backup. [Assessment, measured limits and current folder](../../../docs/evaluations/flood-ner-study-use-20261015/README.md).


## Explicit annotation corrections

`revision.py` applies reviewed `EntityCorrection` objects to hash-bound original records. Corrections contain the complete original-record hash, passage hash, expected/replacement entities and actual review provenance. `write_cohort_revision` preserves membership, splits, immutable source metadata and saved tokenizer bytes, refreshes selection/coverage hashes and refuses existing destinations. It never invokes the selection solver. `revise_contexts` retains fact/target/override IDs and applies explicit road-segment qualifiers without assigning facts to new local-area entities.

The preserved correction checkpoint has 1,497 location spans across the same 400 samples and 139 articles. One of forty contexts changes in v3. Bundle preparation uses the explicit safe context/packet revision names, preserving v2 defaults for older manifests and copying hash-linked predecessor packets when supplied. [Correction evidence](../../../docs/evaluations/flood-ner-annotation-correction-20261015/README.md). Its preserved organized folder is `artifacts/400-sample-study-package-corrected-20261015-v1/START-HERE.md`; old folders remain unchanged.


## Academic-use review without admission

`academic_use.py` validates source-exact UTF-8 clause pointers, the corrected cohort/context/review-packet bindings, 139 distinct article reviews, three dated AI publisher conclusions and the unchanged twelve nonacademic-use outcomes. Publisher display aliases are normalized through the existing URL-based publisher identity without rewriting captures. It does not expose an admission setter or new CLI command. Completed assessments cannot change source flags or bypass export holds.

Preserved publisher-review checkpoint: `artifacts/academic-use-review-20261015-v1/START-HERE.md`, with `DECISION-SHEET.md`, three readable assessments, `academic_review-v2.json`, article exceptions, editable academic decisions and a hash manifest. Review-v2 corrects a private draft's caption-overlap description after checking source intervals; the dataset is unchanged. Raw snapshots and complete review evidence remain ignored. [Metadata report and decisions still needed](../../../docs/evaluations/flood-ner-academic-use-20261015/README.md).

## Optional reference-preserving research revisions

The existing Python `build_cohort` function accepts optional `reference_records`, `fixed_record_ids` and `max_reference_changes`. References must be validated frozen split-bound records. Hard-fixed records must remain eligible, substantively unchanged and in their original split. Removals, replacements, span/language changes and split moves consume the budget; reviewer/notes/group-overlay metadata alone do not. New boundaries require distinct IDs and supported provenance.

With references enabled, soft overlapping/near-copy alternatives remain eligible and explicit conflict constraints prevent selecting both. Hard-fixed records win eligibility conflicts. The solver prioritizes unchanged references, then its stable secondary objective. Time-limited incumbents are checked against actual integer/linear constraints and reported without claiming optimality. The 60-second default remains; bounded one-off workflows may retry once at 300 seconds after an unresolved timeout. Constrained manifests record reference hashes, fixed IDs, budget, actual changes and solver status. Without these options, legacy behavior and manifest fields stay unchanged. No CLI, production API or dependency is added.

The [bounded revision](../../../docs/evaluations/flood-ner-research-revision-20261016/README.md) is in `artifacts/research-revision-20261016-v1/START-HERE.md`: final **cohort-v4** (400/138 articles) and **contextual-v4** (40 pairs), with 54 new-boundary selections, 16 reviewed reserves and 330 preserved references. Two additional training references change; test samples/pilots remain fixed. Original checkpoints and intermediate drafts are preserved. The study-bundle command above still targets its original 139-source packet; do not substitute the new 138-source cohort into that bound interface.

Source-use assessments and a hash-bound derived index retain 12 held articles/49 passages. Source flags/export holds remain unchanged; no model processing or training occurred. The detailed desktop predecessor remains unreconciled.

## Admitted corpus tokenizer command

`python -m training.flood_ner qualify-corpus-tokenizer --python RESEARCH_PYTHON --model-manifest MODEL_MANIFEST --tokenizer-manifest TOKENIZER_MANIFEST --cohort ADMITTED_COHORT --context ADMITTED_CONTEXT --admission-manifest ADMISSION_PACKAGE_MANIFEST --output NEW_IGNORED_OUTPUT`

Use verified existing paths; placeholders are not directories to create blindly. The command validates the frozen private admission package, pinned model/vocabulary and candidate bytes before one isolated tokenizer-only worker. It preserves failures and returns nonzero unless qualification passes. It runs no NER components or model predictions and leaves legacy constructed-only commands unchanged. Never overwrite a frozen output. The evaluation protocol can be prepared while qualification is blocked; that does not qualify the tokenizer or permit the next export gate.

## Qualified location training-format export

Run the following from backend/, using the existing CLI interpreter:

    python -B -m training.flood_ner export-qualified-corpus --python RESEARCH_PYTHON --qualification PASSING_QUALIFICATION_DIRECTORY --output NEW_IGNORED_DIRECTORY

The command requires the passing qualify-corpus-tokenizer output directory, including its frozen evaluation contract and all bound inputs. It revalidates the admission ledger/evidence, 400 location records/40 contextual pairs, pinned model/vocabulary, candidate bytes and saved comparison. It refuses research-only inputs, changed or incomplete qualification, mismatched partitions/profiles and existing or unignored output destinations. It adds no constructed-data override and never falls back to a legacy corpus tokenizer.

An isolated existing Python 3.11/spaCy 3.7.5 worker uses vocabulary/tokenizer only. It writes train.spacy/dev.spacy/test.spacy with 280/60/60 location documents, preserving original text, strict six-class labels, negatives and record_id user data. The 40 contextual pairs are bound references, not extra NER samples. All documents reload with exact tokens/offsets/labels before a successful manifest is written; failures retain logs without a success manifest.

tokenizer.bin preserves the qualified candidate bytes with vocab excluded. Its manifest binds the required pinned vocabulary; do not reconstruct defaults or treat the tokenizer as independent of that vocabulary. provenance.json contains IDs, groups, hashes, language/split and silver teacher/reviewer metadata without full article bodies. Request text, DocBins and worker diagnostics stay private under ignored artifacts.

The verified desktop export/replay and metadata-only report are recorded in [qualified export verification](../../../docs/evaluations/flood-ner-qualified-export-20261016/README.md). The legacy export command and its two corpus-tokenizer choices are unchanged. This command performs no training or NER prediction evaluation.

Focused tests need no extra packages or private corpus: from backend/, run the existing CLI Python with python -B -m unittest discover -s tests -p test_flood_ner_qualified_export.py -v. No application database/conftest is loaded by this unittest invocation.

## Baseline/configuration preparation

From backend/, use the existing CLI interpreter:

    venv/Scripts/python.exe -B -m training.flood_ner prepare-experiment --python RESEARCH_PYTHON --export VERIFIED_QUALIFIED_EXPORT_DIRECTORY --output NEW_IGNORED_DIRECTORY

This separate offline command revalidates the passing export, qualification, admission/contract, model files and exact tokenizer before using the same isolated Python 3.11 research interpreter. It freezes direct rules type/Unicode-offset mappings and source/assets hashes. It initializes seed 0/1/2 fresh six-class NER heads, copies the pinned NER encoder and preserves static vocabulary. It performs no optimizer updates, corpus inference, test reading, export or saved-model creation. The existing rules mention adapter receives four constructed-only passages with database connections blocked.

The pinned architecture uses a GPU encoder/lower network and CPU upper classifier by design. The passing desktop run verifies 46 GPU arrays and two CPU upper arrays per seed. The failed v1 all-GPU assertion is preserved; v2 passes without dependency or model changes.

The frozen recipe is batch size 8, dropout 0.1, Adam learning rate 0.001, max_epochs 30, max_steps 1000, eval_frequency 35 and patience 175. It is one initial recipe, not an optimized result. Seeds 1/2 are robustness runs; seed 0 is primary. Configs exclude test.spacy. The actual held-out corpus remains hash-bound for preservation, not supplied to the initializer.

The generated configs require experiment_registry.py to be loaded with the spaCy --code option by the later trainer, using the same qualified Windows DLL/runtime setup. No training command runs as part of this preparation. The custom development selector saves strict improvements to future seed-directory/selected-checkpoint/model and retains earlier steps on equal F1. Use that path for evaluation: the default spaCy 3.7.5 model-best overwrites equal scores. Planned training output must be new; do not overwrite or resume it implicitly.

The rules baseline maps street/landmark/barangay/city/province directly to ROAD/LANDMARK/BARANGAY/CITY/PROVINCE. LOCAL_AREA is unavailable; legacy numbered-locality landmark emissions stay LANDMARK. Use original character offsets, retain diagnostics for invalid/unsupported emissions, deduplicate identical spans only and retain conflicting/overlapping outputs for transparent scoring. Do not use references to repair offsets or infer types. This is mention recognition, not the full flood-claim pipeline. The unmodified pretrained baseline remains a separate coarse native LOC task.

From backend/, run the new standard-library tests without package installation:

    venv/Scripts/python.exe -B -m unittest discover -s tests -p test_flood_ner_experiment_preparation.py -v

[Actual preparation results and next training task](../../../docs/evaluations/flood-ner-experiment-preparation-20261016/README.md).

## First manual training run

The researcher runs seed 0, then Codex reviews its output and handles later runs. From the repository root, run .\backend\training\flood_ner\RUN-SEED-0.ps1 -StartTraining in PowerShell. Without -StartTraining the script only verifies inputs. It leaves all frozen configs unchanged and streams the qualified GPU training output into a new private seed-0/training.log, recording completed/failed/interrupted status. Existing output is refused, not resumed. Seeds 1/2 never launch automatically.

[Exact commands and output guide](../../../docs/guides/ner-first-manual-training-20261016.md). Only check-only execution and launcher tests have run; actual training has not started.

## Validation-only model comparison and preregistered recipes

From backend/, run the repaired CLI interpreter with:

    venv/Scripts/python.exe -B -X utf8 -m training.flood_ner compare-validation --python RESEARCH_PYTHON --preparation PASSING_PREPARATION --training-root PRIVATE_RUN_ROOT --output NEW_IGNORED_OUTPUT

Default expected seeds are 0/1/2. --seeds selects an explicit subset; --allow-incomplete retains failed/missing runs as an explicitly partial report. It never silently claims a completed three-seed experiment. The command revalidates frozen bindings and selected model identities, uses raw development passage strings only, reproduces recorded selected F1, and scores the unchanged rules/native baselines. Native LOC remains a separate coarse task. No test prediction or training occurs.

The study_recipes helper preregisters only approved A/B changes and output-only recovery relocation. All configurations are bound before training; validation rejects any other changed setting even if someone rehashes the configuration. Default helper mode checks inputs only. An explicit --start-training opt-in and an unexpired 50-minute cutoff are required for execution. There is no authorization to bypass the experiment failure rule: preserve the failed attempt and obtain the explicit retry decision first.

Source and prediction text remains private; public reports contain metadata. Forty-three standard-library tests cover launcher, comparison, recipe and existing preparation/export behavior. Existing requirements, public APIs, schemas and legacy export behavior remain unchanged.


### Completed bounded study and safe inspection

The immutable validation-study-20261016-v2 manifest preregisters seven variant configurations; actual run-status.json records identify the five completed new runs. Its training_started:false describes preregistration time. Study recipes change only patience/rate and output identity; each initializes independently from the pinned encoder. The winner uses unrounded seed 0 strict F1 (original, then A, then B on ties). B seeds 1/2 remain unrun configurations.

The study_recipes module defaults to read-only input/output validation; --start-training is an explicit training opt-in and refuses existing outputs or the expired start deadline. Do not repeat these completed runs. Selected checkpoints use selected-checkpoint/model with the earlier-step tie rule. Private comparison requests/logs/predictions and weights remain in ignored artifacts; the completed report contains metadata only. The subsequently completed held-out evaluation is documented below.


### Frozen held-out test evaluation

Two separate offline commands preserve the validation-only command and its defaults:

- freeze-test-experiment --preparation DIR --study-report DIR --output NEW_IGNORED_DIR checks the completed development study and freezes original/A seeds 0/1/2, resolving original seed 2 to its recovery output. It binds selected-checkpoint/model files, development selections, configurations, model/tokenizer/input/contract/rules identities, evaluator code and exact test memberships. It performs no test predictions.
- evaluate-test --freeze DIR --python QUALIFIED_RESEARCH_PYTHON --output NEW_IGNORED_DIR checks the sealed freeze, then evaluates exactly 60 test passages once using the existing isolated GPU environment. Its exclusive attempt.json marker is created before rules/neural inference and survives failure. Changed inputs, existing output and another attempt on the same freeze are refused. Failed results/logs remain private; do not retry automatically.

Completed checkpoints are final-test-freeze-20261016-v1 and heldout-test-evaluation-20261016-v1; logs/audits are in heldout-test-execution-20261016-v1. Preserve them; do not recreate/re-evaluate this experiment to choose models from test scores. Tests and implementation changes must precede a freeze because evaluator hashes are bound. Original seed 0 stays primary, Recipe A exploratory, and Recipe B is excluded. The native LOC task remains separate from strict six-class scoring; rules cannot emit LOCAL_AREA. Inference receives raw strings only. Public reports contain metadata; predictions and offset errors stay ignored. Any future tuning needs a fresh untouched holdout, not another selection round against these exposed cases.
