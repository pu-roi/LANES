# Paper method: corrected context and pre-evaluation status

> **Last Updated:** October 15, 2026, 3:20 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The study dataset remains 400 AI silver location passages from 139 articles, with 280 training, 60 validation and 60 testing records and equal English/Taglish counts per partition. The 40 contextual pairs are part of training, not 40 additional independent samples. No human/gold annotation verification or model accuracy was measured.

Follow-up same-agent source review corrected 13 contextual facts across five records: nine access-negation errors, one rainfall/flood-onset role and three universal vehicle-closure assumptions. New contextual v2 preserves every original passage, location span and partition. Earlier v1 remains archived as a superseded checkpoint. Temporal-transition coverage now totals three English and eight Taglish cases; all other category requirements continue to pass.

Qualification verifies source evidence, schema/tokenizer alignment, split/coverage support and pinned model metadata. The evaluation protocol is frozen before model tuning. Any future scores against the current references measure agreement with AI silver labels, not independently verified real-world accuracy. The 40 training-only context records cannot support contextual holdout accuracy estimates.

546 software tests pass, retaining 525 previous tests and adding 21 cases for the observed defects. These are software results. A tokenizer hash-reporting error was fixed in a new diagnostic version; qualification-v2 binds the actual saved bytes. All 1,779 checked prior artifact files and earlier public metadata hashes remain unchanged.

Four calamanCy metadata snapshots were assessed without loading weights. Version 0.2.0 conflicts with retained spaCy 3.7.5; 0.1.0 declares a compatible range but lacks a declared transformer dependency in the environment. Neither result establishes working inference, tokenizer compatibility, CPU performance or sufficiency for six-class LANES NER.

Reuse remains unresolved for the three selected publishers. Training admission, exported datasets, model evaluations, trained models and model metrics are zero. The shared paper was not edited. Report these measured preparation results separately from future model evaluation and deployment.
