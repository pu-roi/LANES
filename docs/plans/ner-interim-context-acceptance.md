# Interim flood-context acceptance specification

> **Last Updated:** October 19, 2026, 3:55 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Decision and purpose

The user selected a **limited interim demonstration using the retained v19 location model plus depth/time rules** as the temporary October 25 defense priority. Additional neural DEPTH/TIME training is deferred on this interim path; its original requirement remains open and is not fulfilled by rules. Demonstration readiness and release are not implied by this scheduling decision.

Prepare expected results before repairing extraction. This specification uses the **26 existing contextual training counterparts** identified by the v32 gap audit and **40 fictional cases**. It neither changes corpus membership nor reopens validation or the completed research holdout. References are AI-assisted silver and retain incomplete-history/accounting limitations. Prior exposure to development findings means this work is not blinded or independent generalization evidence.

## Source and annotation conventions

- Preserve original text, Unicode offsets, source/window hashes, language, record identity, partition and **current six-class location references**, including LOCAL_AREA. Historical contextual references remain immutable; revised references are separate proposals.
- DEPTH includes the source-exact meaningful gauge/measurement and attached modifiers: approximation, upper bound, relative above/below, and range. Adjacent alternative units may remain one expression; do not create overlapping aliases. Record a comparison to a physical object without inventing its height. A vague descriptor can remain recognized with unspecified scale and unresolved target; it does not establish a numerical depth.
- Retained pilot spans follow their existing source-supported boundary choices. Gauge aliases or omitted modifiers that conflict with this specification require a separate proposed revision or hold; do not force token alignment by changing source text. Record rhetorical or nonspecific language excluded from the concrete-expression profile with its reason. A repeated translation is still a source occurrence and must be accounted for.
- TIME keeps an explicit clock, date, day, duration or qualified relative expression. An introductory cue can remain in supporting evidence when the annotated expression is narrower. Roles are **onset, observation, report, publication, recession, clearance or unspecified**, using the existing schema. Weather/rain start/end, class suspension and report dates are not automatically flood onset/clearance. Missing year, timezone, heading or reference day stays unresolved. Publication metadata alone supplies no observation or onset.
- Status/access facts retain exact evidence and restrictions. Forecasts, negation, historical/prevention/habitual statements and active observations remain distinct. Receding or subsided water can still have depth; only explicit dry/cleared flood evidence supports clearance. No casualty or damage does not negate flooding. Access for one vehicle class does not establish access for all vehicles.
- Every proposed depth/time occurrence needs a fact; every fact must have either an evidenced relation or an explicit unassigned-fact disposition. This is annotation completeness, not permission to guess a relationship. Unknown target/role remains explicitly unknown. Missing or incomplete references are held, never genuine negatives.

## Location association rules

**Local** links apply only to an explicitly supported target occurrence and spatial extent. Indoor/house depth and street/area depth can coexist; the more specific fact does not override another spatial scope by default. Parent cities and evacuation destinations do not inherit depth. Road/junction or directional observations do not assert full road lengths or geometry.

**Shared** means the same supported fact applies to multiple explicit targets. A shared observation time can accompany distinct per-road depths. **Collective** preserves a source-listed set, intersection, group summary or range without asserting identical independent scalar facts for every target. A null collective value remains null. Never distribute a range endpoint, mean or inferred exact gauge to all roads. Existing collective conventions are not silently relabeled as shared.

**Unresolved** links preserve candidate contextual targets and uncertainty but are unscored as resolved assertions. Unassigned facts have no supported location link; the expected action is abstention. Missing antecedents, bare adjacency and proximity are insufficient. Repeated names retain their own offsets; strings alone do not establish one event or geographic identity.

**Updates** retain prior evidence and their observation scopes. An override requires explicit support for replacement of the same place, fact kind and spatial context. Different house/street scopes, timestamps or source versions cannot be collapsed merely to obtain one answer. No rule infers coordinates, flood geometry, route eligibility or current operational validity.

## Fixed future adapter and scoring contract

The offline adapter will receive **opaque ID, unchanged text/hash, supported publication metadata or null, and authenticated location mentions**. Each mention carries its own ID, exact start/end/text, one of the six labels and a provenance hash. Reference entities/facts, expected labels, saved rules output and article identities are not extraction inputs. `validate_raw_input` in the new research helper defines this internal contract; no public endpoint or production claim schema changes.

Future outputs must distinguish recognized depth/time evidence from location links, preserve raw spans/qualifiers, explicit temporal role, scope, status/access and uncertainty, and carry source offsets. No canonical number or absolute instant may be invented from a verbal gauge or missing temporal evidence. Neural/rules provenance must remain distinct; no hidden fallback or rejected postprocessor is permitted.

Freeze the private references, fixtures, protocol and implementation hashes before any repair experiment. A future task must:

1. Test every one of the **40 fictional cases**: ten families × English/Taglish × supported/counterexample. These cover row measurements, separate depths/shared time, genuinely shared depth, ranges/qualifiers, scope boundaries, forecasts, negation, historical updates, observation/onset and recession/clearance. Unicode, repeated names and all six location labels are included.
2. Require all specified positive associations and exact evidence, while rejecting forbidden inferences and unsupported links. An always-abstaining implementation fails positive cases. The case records and explicit expected/unassigned relations are the fixed oracle; a successful schema check alone is not a behavioral pass.
3. Assess location recognition, DEPTH/TIME span recognition and association separately on eligible references. Strict contextual span matching uses exact offsets/type. Resolved association tuples bind the exact target occurrence/label, fact kind and source expression, temporal role or depth scope, status/access value and relation scope. Free-text reasons are explanation, not fuzzy matching authority. Qualifiers encoded in source spans/semantics must survive. Collective links remain grouped; do not score them as uniform per-target point measurements.
4. Keep held records and unresolved/unassigned relations outside resolved positive denominators, but report their counts and abstention violations. Report support, failures, retained baseline-correct links, corrections and coverage; do not hide decreases by excluding difficult cases.
5. Freeze and authenticate the existing-rules baseline for the same eligible passages in that later task, without references supplied to extraction. The current v32 raw fields do not establish a full association oracle by themselves. A repair must retain previously supported correct associations and introduce **zero incorrect resolved associations**. Require at least one demonstrated targeted correction before calling a method supported; otherwise label it unproven. Do not tune from validation or the completed holdout.

The current task qualifies references and software fixtures only. It runs no extractor, model or repair comparison. Any missing baseline/semantic binding remains a blocker in the next experiment instead of being reconstructed from expected answers.

## Completion and next gate

Each of the 26 historical counterparts receives one retain/correct/hold proposal with exact source evidence, correction history, field completeness and unresolved-fact accounting. The 40 cases and all known gaps are frozen. Shared schema/tokenizer checks, privacy guards and predecessor preservation must pass. Passing means a **bounded acceptance package**, not accuracy, human gold annotation, corpus admission or a complete system.

Next implement separately scoped offline association repairs using saved v19 location predictions. A read-only LANES connection follows only after those checks and an explicit acceptance decision; live routes/zones/persistence remain separate. Preserve the `rules_only` durable constraint. No collection, new corpus passages, applied corrections, partition changes, export, neural inference, training, validation/holdout access, deployment, upload, commit or push belongs to this preparation task. The desktop can remain off.

[Gap audit](../evaluations/flood-ner-context-gaps-20261019/README.md) · [Acceptance package outcome](../evaluations/flood-ner-context-acceptance-20261019/README.md) · [Current tasks](../task_plan.md#current-ner-scope-and-defense-checkpoint).
