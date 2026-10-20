# V44 source-supported junction location study

> **Last Updated:** October 20, 2026, 12:22 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Executed outcome:** The single study completes with acceptance blocked. Combined proposals restore 40 article facts, but a frozen scoring serialization defect and three preserved fixture conflicts remain. [Report](../evaluations/flood-ner-location-repair-v44-20261020/README.md) · [Guide](../guides/ner-location-repair-v44.md). No implementation promotion or retry follows.

Implement the approved offline study with three separately reported families: complete missing junction names, explicit boundary replacements and junction-context road type corrections. Clear local junction grammar may support a complete road name without a road suffix. Preserve the original neural predictions, v40 controls, v42 matcher, references and application wiring.

## Proposal contract

Accept source text, opaque identity, saved neural mentions and saved combined-control mentions. Return immutable neural/control views, effective mentions, exact source/evidence offsets, action, original ID, rule/version provenance and abstention reasons. No expected answers enter the worker. Boundary replacements affect only the effective view. Never expand names, use geography or propagate a repeated name without local evidence. Ambiguous abbreviated/numbered names and compatible but semantically uncertain landmark/local-area labels remain unchanged. Conflicting proposals abstain.

## Frozen workload and acceptance

Before candidate processing of real inputs, bind code/tests, expectations, scoring, raw workload, existing evidence and acceptance. Execute one isolated attempt over **788 raw inputs**: 345 training predictions, 24 contexts, one article, 36 preserved location cases, 346 preserved context/temporal cases and 36 new fictional cases (three families × three languages × positive/counterexample × two variations). Evaluate each family and their predeclared combination on the saved v40 combined control. Reuse saved originals; regenerate no predecessor proposals or neural predictions.

Use the qualified Linux image, two CPUs, 4 GiB memory, no network and read-only code/input. Mount no references, expectations, models or credentials. Preserve failure receipts and partial outputs; no retry or post-result tuning. Score the same 345 training recognition references and 23 eligible contextual references; retain three holds. Original fixture expectations are unchanged, including incomplete-target expectations. Any conflict between repair behavior and those expectations is a reported acceptance blocker.

Each qualifying method must pass new/preserved checks, demonstrate a source-supported real correction, introduce zero strict location false positives or incorrect associations, lose no correct locations/supported associations, and preserve source spans, qualifiers and time roles. Reconcile 34 target occurrences, 19 unresolved rows, 93 saved facts, eight previously complete article rows and seven historical misses. No depth may be invented for the unmeasured junction. Article checks are diagnostics, not gold-reference revisions or independent accuracy.

## Delivery and boundaries

Publish aggregates and independent verification under evaluations; retain individual evidence privately. Update task/progress/roadmap/index/guide/issues. Completion includes a blocked result. No application promotion, frontend, database access, plotting, new articles, retraining, reference changes, validation/holdout contents, uploads, commits or pushes. Preserve the distinction between six learned location labels, depth/time rules and matching rules. Real pure-Tagalog performance and learned DEPTH/TIME remain unfinished.
