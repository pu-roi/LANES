# Desktop readiness and source-use route alignment — October 15, 2026

Delivered a standard-library-only read-only desktop inventory collector and local handoff ZIP. A real run on the current Windows 11 machine reports NVIDIA GeForce MX330 / 2,048 MiB VRAM / driver 572.16 and correctly returns `awaiting_target_desktop`. The RTX 3060 Ti desktop has not been inspected or benchmarked. No GPU dependencies were installed; no GPU training compatibility is claimed.

The researcher reports an October 25 defense requiring integration into deployed LANES and access to the reported i7 9th-generation/16 GB/RTX 3060 Ti 8 GB desktop this week. These are goals and reported specifications, not completed training or a deployment guarantee.

[Desktop instructions](../../guides/ner-desktop-preflight.md), [current status](status.json), [verification](verification.json), [report hashes](metadata_hash_manifest.json). Local full inventory, researcher-direction record, handoff ZIP, input bindings and checkpoint hashes are under `backend/training/flood_ner/artifacts/desktop-readiness-20261015-v1/` and remain ignored; none were uploaded. The ZIP contains only the collector, guide and hashes, not news text, annotations, model weights or an environment.

## Existing task-plan alignment

Retain the frozen corrected 400-sample/139-article cohort, 40 contextual-v3 pairs, 280/60/60 partitions, calamanCy pin and tokenizer checkpoints. The existing use-basis alternatives include a supported applicable statutory exception; publisher replies are optional clarification, not a universal prerequisite. Current wording is corrected accordingly. Researcher direction to continue is not fabricated publisher permission or a determination that every held case qualifies. All 69 holds and 70 recommendations remain unchanged, with zero training admission and successful exports. The private-source assessment does not automatically cover public deployed inference or defense demonstration scope.

Source-use decision work remains the first news-processing gate. Hardware inventory and constructed environment checks can proceed independently while that decision is finalized. No new collection, replacement corpus, alternative model selection, news-model inference, training, runtime integration, deployment or Git publication occurred here.

## Verification

83 focused tests passed, one Windows symlink test was skipped because link creation was unavailable, and one existing spaCy/Click warning remains. This includes the 64 existing review/proposal tests and 19 passed inventory tests. The broader historical 702-test baseline was not rerun for this isolated addition. Prior 1,366 checkpoint files and all 23 pinned model files verified unchanged; the real-data proposal validator still reports 400 records, 139 articles, 40 contextual pairs and zero admission/export. Handoff ZIP contents match their hashes. The collector preserves failed driver queries, refuses existing/outside destinations and never claims training qualification from a hardware match.

Official references: [NVIDIA driver query](https://docs.nvidia.com/deploy/nvidia-smi/index.html), [spaCy GPU installation](https://spacy.io/usage#gpu), [IPOPHL fair-use guidance](https://www.ipophil.gov.ph/news/ipophl-releases-statutory-fair-use-guidelines-to-clarify-rules-on-copyright-exceptions/?news_page=6).
