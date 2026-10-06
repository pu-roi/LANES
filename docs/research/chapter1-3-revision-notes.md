# Research documentation follow-up notes

> **Last Updated:** October 04, 2026, 10:13 PM (Asia/Manila)
> **Status:** Working notes only. Do not treat as approved thesis wording or as a replacement for the research document.

These notes preserve items to revisit after the LANES AI, automatic flood plotting, and automatic expiry work reaches an evaluable state. The Google Doc remains the authoritative research document; it was reviewed but not edited for this task.

## Confirmed by the developer

- Chapter III's technical/system test data and reported technical results are fabricated placeholders prepared for the adviser submission deadline.
- The user evaluation/survey is the only part of Chapter III currently based on real collected data.
- Do not report placeholder technical test outcomes, extraction scores, routing rates, or response times as measured findings. Preserve the real user-evaluation/survey material; before reusing its results, match the exact tables, respondent groups, counts, and calculations to the actual response data.
- System implementation is the immediate priority. Research-document revision follows implementation and actual feature evaluation.

## Scope alignment to revisit

- Preserve **Pasig City as the primary thesis development/evaluation area**, consistent with the current proposal.
- LANES news collection and automatic flood plotting may cover **Metro Manila** to supply broader operational coverage and regional news. Report that system coverage separately from the thesis evaluation scope; do not imply that all Metro Manila localities have been evaluated.
- Revisit Chapter I's problem statement, objectives/questions, scope, limitations, and Chapter II methods after the AI/news publication and expiry workflow is implemented. The current text emphasizes processing followed by authorized validation and does not yet describe automatic news-to-map publication or expiry.
- Define automatic expiry accurately. A freshness timer can move stale flood evidence to **Unconfirmed**; it cannot prove that water has subsided. **Cleared** requires a credible, matched clearance observation. Keep estimated subsidence separate from observed clearance.

## Data and results integrity

- The repository contains a separate, source-linked Pasig/NCR flood-report collection. Its captured source evidence is not the same thing as the fabricated Chapter III system-test results.
- The current combined register reports 753 evidence records (739 report observations and 14 historical-document records), including 482 Pasig records (470 report observations and 12 historical-document records). These are records, not independent flood events.
- The existing duration pilot has 37 candidate clearance bounds across three shared clearance episodes; they are not training-admitted outcomes. Repeated streets, updates, and copied stories from one flood must be grouped and must not be counted as independent floods.
- A later cleaning/evaluation pass should preserve raw captures and provenance while resolving duplicates/syndication, locality and road identity, observation versus publication time, chronology conflicts, incident continuity, and the distinction between flooding, clearance, and passability. Mark uncertain or unsupported labels as such; do not infer a clearance from a missing later report.
- Do not claim that the record count alone is enough for duration ML. Admit examples only after incident/section-level label review and an evaluation split that holds out storms/incidents. If available independent outcomes remain insufficient, report lifecycle behavior (including Active-to-Unconfirmed) as a system test and omit predictive-accuracy claims.

## Chapter II checks after implementation

Use the College's Chapter 2 guide to ensure the final methods state what was actually done and could be repeated:

- Research design and why it fits the actual system objectives.
- Actual population, participants, sampling method, and sample size; distinguish planned numbers from those who participated.
- Data sources and collection steps; test instruments, annotation and adjudication procedure, and any pilot.
- Data cleansing/processing rules, exclusions, grouping, and handling of missing, conflicting, or synthetic data.
- Analysis methods and metrics mapped to each research question, plus consent, privacy, and other ethics procedures.

The current Chapter II describes a planned 60–100 mixed real/simulated text sample, while Chapter III currently states a 400-sample NER dataset. Confirm what was genuinely collected and tested before retaining either number.

## Chapter III and IV checks after implementation

The College's Chapter 3/4 guide calls for results organized by the approved study questions/objectives, clear tables/figures with captions, and reporting that follows the test plan. Replace every fabricated Chapter III technical result with measured, reproducible evidence or remove it. Keep results distinct from their interpretation. Ensure Chapter IV conclusions answer the actual study questions and rely only on verified Chapter III findings; do not introduce new results there.

For the updated system evaluation, capture real test cases and outputs for:

- AI extraction from real, cited English/Taglish reports, scored against reviewed annotations.
- Automatic plotting eligibility, location/section matching, safe zone publication, and exception handling.
- Expiry/freshness state transitions, explicit clearance matching, stale or missing updates, and independent supporting reports.
- Map/routing effects and mobile/desktop behavior, with clear separation between functional tests and stakeholder survey results.

If duration prediction is later evaluated, report the admitted incident count and label limits, hold out complete storms/incidents, compare against simple baselines, and avoid accuracy claims unsupported by those outcomes.

## Source material reviewed

- [Current research document](https://docs.google.com/document/d/1yW8qmoYagU9tVZkW1cuC4I3E3Eklbvw83OMq3vcaSBE/edit?tab=t.0), Chapters I–III.
- `docs/how-to-write/How to write Chapter 2.pdf`.
- `docs/how-to-write/How to Write Chapter 3 and 4.pdf`.
- [Pasig and Metro Manila flood-evidence collection](../evaluations/metro-manila-flood-duration-20261004/README.md).
- [Pasig duration pilot](../evaluations/flood-duration-pilot-20261004/README.md).
