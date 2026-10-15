# Paper-method notes: corrected annotation revision

The study corpus still comprises 400 distinct passages from 139 selected Philippine news articles: 200 English/200 Taglish, with 280 training, 60 validation and 60 testing records. Forty contextual training pairs do not add samples. No source text, passage boundary, record membership, publisher allocation or partition assignment changed.

A source-backed AI correction pass changed three location annotations: one omitted province mention was added and two compound road/local-area mentions were separated to match the existing pilot convention. Location-span totals increased from 1,494 to 1,497. These are annotation counts, not model accuracy results. One paired contextual record was updated in contextual v3; its road target IDs and overrides remain intact, with explicit segment qualifiers on three existing facts. No new fact or independent locality-wide flood assertion was added.

The corrections include one validation record. They were made before model training/tuning and preserve frozen partition membership. Earlier annotation and context checkpoints remain available with their original hashes; report the corrected revision hashes when identifying the current dataset. No model was used to generate or evaluate predictions on these news passages during this correction.

The actual method remains AI-created, same-agent-reviewed silver labeling. Neither human verification, independent gold quality nor measured model accuracy is established. Mechanical tests verify contracts and preservation; they do not prove that every semantic annotation is correct.

All fifteen scoped source-use decisions remain unresolved. Training admission and successful DocBin exports remain zero. The organized private package is locally available; the appendix and download candidates retain research-only/distribution-unresolved status. The download candidate contains 391 passage texts and nine metadata-only records, rather than a published 400-text corpus. Its forty contextual identities include 38 texts and two metadata-only records. Collection effort and annotation correction do not transfer rights in the underlying news wording or grant a public dataset license.

Current software verification records 638 focused tests, a different selection from the historical 666-test result. Do not convert software test counts into NER accuracy claims. Independent language/label review, broader real-source coverage, source-use decisions, model-tokenizer cohort qualification and GPU preparation remain future work.
