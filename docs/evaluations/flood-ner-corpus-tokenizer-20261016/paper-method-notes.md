# Paper-method notes — tokenizer qualification blocked

The 400 AI silver location samples from 138 articles, 200 English/200 Taglish and frozen 280/60/60 partitions remain privately admitted for academic use. Forty contextual pairs are training-only linked records, not forty additional samples or a contextual test set. No independent human verification is claimed.

A versioned evaluation protocol specifies exact record/start/end/label matching, TP/FP/FN, precision/recall/F1 with support counts, language/label slices and negative-passage false-positive rates. Undefined denominators remain undefined. Pretrained LOC boundary comparison is separate from six-class classification; ORG/PER predictions are not automatically treated as locations. Model selection uses development strict micro-F1 with earlier-checkpoint tie-breaking; seed 0 is primary and 1/2 are robustness seeds. No test-driven tuning is permitted.

The actual isolated corpus-tokenizer attempt failed at a Windows Application Control error 4551 before tokenization. The protocol is frozen, but qualified-tokenizer binding is pending. There are no new model predictions, entity accuracy scores, successful corpus alignment results, exports or trained models. The historical constructed tokenizer pass does not establish alignment on this news corpus.

Final software verification is 840 passed/one skipped, including 68 new tests. These are software regression results, distinct from artifact checks and future agreement with silver references. A deterministic protocol replay reuses captured failure evidence and does not establish tokenizer replay. Current production readiness and end-to-end contextual accuracy remain unmeasured.
