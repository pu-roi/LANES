# Pasig conditional flood-duration model experiment

> **Last Updated:** October 07, 2026, 7:30 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** A conditional research baseline has been fitted. Reliable operational subsidence prediction is not finished.

## Delivered result

The actual captured Pasig evidence now supports a reproducible **conditional sensitivity experiment**. The fitted model is a lognormal AFT baseline with two parameters: a pooled log-duration location and scale. It learns no depth, road, barangay, rainfall or DRRMO effects. Original records, captures and admission decisions remain unchanged.

The experiment uses 37 dependent location projections sharing three reported-subsidence summaries. Selecting first recorded wet observations produces 35 positive intervals under an **uninterrupted same-episode flooding assumption**, plus two upper-only intervals. The assumption and collective-scope correspondence remain unverified. This is not a verified new ground-truth dataset.

| Deliverable | File |
| --- | --- |
| 37 conditional rows with first/last evidence IDs, interval bounds, source hashes and assumptions | [conditional_training_candidates.csv](conditional_training_candidates.csv) |
| Actual fitted JSON model | [conditional_aft.json](conditional_aft.json) |
| Counts, numerical diagnostics, quantiles, hashes and limitations | [experiment_report.json](experiment_report.json) |
| Leave-one-summary-out sensitivity; all three fits converged | [summary_group_sensitivity.csv](summary_group_sensitivity.csv) |
| Original upper-only likelihood diagnostic | [upper_bound_likelihood.csv](upper_bound_likelihood.csv) |
| Evidence/identifiability graph | [duration_evidence.png](duration_evidence.png), [PDF](duration_evidence.pdf) |
| Conditional model sensitivity graph | [model_sensitivity.png](model_sensitivity.png), [PDF](model_sensitivity.pdf) |
| Manual in-sample hypothetical service preview | [research_preview_example.json](research_preview_example.json) |
| Additional official-source follow-up search and exclusion reasons | [followup-search-notes.md](followup-search-notes.md) |

## Findings

1. The original 37 last-wet bounds all begin at zero. At fixed scale, moving a hypothetical positive-time median toward zero improves every original upper-bound likelihood. The diagnostic demonstrates why those labels alone cannot identify a useful duration predictor; it is not a training result.
2. The new first-recorded-wet intervals are `(1740,2000]` for eight Maybunga locations; `(930,1050)` for Katipiran; `(510,870]` for 22 August 30 locations; `(390,750]` for four; and `(0,360]` for two. Positive lower bounds depend on no recovery/re-flooding between observations.
3. Each summary receives total weight one. The **group-balanced composite interval likelihood** fits a finite distribution, with all five optimizer starts converging. This does not make 37 rows independent or validate the assumptions.
4. The fitted p10/p50/p90 values are approximately **9.77 / 17.63 / 31.82 hours from first recorded wet evidence** in this selected conditional sample. They are model-distribution quantiles, not proven expiry durations, validated confidence limits or a Pasig-wide flood timer.
5. Leaving out one summary shifts the fitted median to approximately **13.39–22.61 hours**. Held-out mean interval negative log likelihood ranges **2.49–6.57**. This is sensitivity analysis, not validated accuracy on three independent storms. The worse Maybunga result demonstrates the limits of pooling these distinct episodes.
6. `deployment_eligible=false`, `production_training_admitted=0` and `operational_prediction_finished=false` remain explicit. No model estimate alters expiry, clearance, routing or public-map status.

No interval midpoint is used as an exact outcome, no missing publication time becomes a source clock, and no DRRMO/context record becomes a duration label. The first-recorded-wet target has a new version; the original last-wet proxy target remains unchanged. Full [implementation/method contract](../../plans/pasig-subsidence-model-implementation.md).

## Verification performed

An independent source/data agent reconstructed all 37 reference/outcome projections, checked the 35 positive/two upper-only rows, verified that weights sum to one per summary and confirmed all 70 original capture hashes and three original input hashes. It also checked builder/kernel/model lineage hashes and production restrictions. A separate runtime reviewer inspected permission checks, JSON loading, clock conditioning and absence of zone/routing writes. Its lineage-validation finding was fixed before final review.

The training command ran against real captured evidence, including all three summary-removal sensitivity fits, and generated the JSON model and scientific figures. Both figures were visually inspected. A manual service calculation using the existing Maybunga timestamps returned finite conditional remaining quantiles; its JSON explicitly marks the example in-sample, hypothetical and unavailable for prospective accuracy claims. No API/auth/browser or automated tests were added/run. HTTP endpoints are implemented locally but not exercised or deployed in this slice.

SciPy `1.14.1` is now an explicit backend dependency, compatible with the existing Python 3.12/NumPy 1.26.4 NLP environment. The local environment previously had incompatible SciPy 1.18.0; only SciPy was replaced, preserving NumPy. No database schema/migration or frontend change is needed.

## Reproduce

From `backend/`, after installing its declared requirements:

```powershell
.\venv\Scripts\python.exe -m scripts.train_pasig_duration --output ../docs/evaluations/pasig-duration-model-20261007 --runtime-output runtime_data/flood-duration/conditional_aft.json
```

Omit `--runtime-output` to keep the experiment only in the evaluation folder. `--skip-figures` omits Matplotlib exports. The command reads cached immutable sources; it does not access a database or search the web. Regeneration updates artifact lineage timestamps/hashes.

Authenticated staff research endpoints:

- `GET /api/v1/admin/news/duration-model` reports the actual fitted research model and its limitations.
- `POST /api/v1/admin/news/duration-preview` calculates a hypothetical conditional estimate or explains abstention. Its input is not verified live case evidence. The required first-recorded-wet clock differs from the latest observation clock used for evidence expiry.

## Remaining work

The statistical kernel, actual conditional fitted baseline and local research preview are delivered. **Operational prediction is still pending:** verified prospective references/outcomes, independent-event evaluation, calibrated feature-based estimates, a case-bound adapter, prospective shadow evidence and an explicit release policy. This experiment does not change evidence expiry behavior. The next data effort should establish these missing outcomes/availability facts; adding repeated wet reports alone cannot solve them.
