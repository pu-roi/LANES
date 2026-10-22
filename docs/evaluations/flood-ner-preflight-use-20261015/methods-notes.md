# Paper preparation: isolated preflight results

> **Last Updated:** October 15, 2026, 8:36 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The original and revised research datasets remain unchanged: current revision has 400 silver location passages from 139 articles, with 280/60/60 frozen partitions, equal English/Taglish counts and 40 corrected contextual training pairs. These labels remain AI-created and same-agent reviewed; no independent human/gold verification was performed.

A separate preliminary compatibility experiment used 24 constructed probes, 12 English and 12 Taglish, outside the news corpus. The probes cover locations, local-area number/address forms, parent ambiguity, punctuation and non-location depth/time/count contexts. Their text was authored for the experiment and is not real-source evidence or additional training data.

calamanCy md 0.1.0 at revision 51a40433059d8a2c25b98a48eca854f8789a491a was downloaded and hash-verified, then loaded in an isolated CPython 3.11.17 environment with spaCy 3.7.5. The main LANES Python 3.12 environment was unchanged. Native LOC/ORG/PER predictions were recorded, with identical outputs across ten measured passes after one warm-up pass. Only the tok2vec/ner CPU profile was run; no weights were fitted or altered.

On the short constructed probes, load time excluding module imports was 681.95 ms, warm median latency 13.66 ms, p95 15.58 ms and peak working set approximately 405 MiB. Two constructed CITY/LOCAL_AREA reference boundaries failed native tokenizer alignment around CITY—-Purok. These results establish a bounded research loading/inference check, not six-class NER accuracy, news-dataset evaluation or compatibility with the production Python 3.12 environment.

586 software regressions pass, retaining the 546 baseline and adding 40 preflight cases. The 3,668 checked prior artifact files, current contextual v2 and frozen partitions remain unchanged. The source-use packet covers all 139 articles and keeps four use decisions separate for each publisher. All outcomes remain unresolved; news-model inference, training admission, news evaluation, export, model training and deployment are zero. The shared paper was not edited.
