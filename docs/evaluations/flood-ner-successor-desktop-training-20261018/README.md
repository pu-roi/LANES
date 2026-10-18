# Successor desktop GPU repair and three-seed training

> **Last Updated:** October 18, 2026, 3:46 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Desktop receipt, Windows GPU repair and read-only GPU verification pass. Seed 0 was attempted but failed configuration validation before pipeline initialization or optimizer updates. Seeds 1 and 2 were not started, and no retry occurred.** The user authorized sequential training only if each preceding run succeeds. Seed 0 remains primary. The frozen membership is 345 training / 60 validation / 60 research-holdout; holdout content remains on the laptop and is not accessed by this task.

## Receipt and unchanged inputs

The desktop fast-forwarded `roi-branch` from `d266a48` to `adffbb8` after confirming no incoming file overlaps the existing `backend/.env` change. The original ZIP is 153,734 bytes, SHA-256 `7fb4f16f4726f9dc104c5236a5151543a7831cf64987e356dfe165b060ce334a`. Its twelve files and manifest `ec3abd74e2201f116a90a90a3dc203877c3f511284b11374d7beb381c1faa11a` pass full checksum verification. The original package stays unchanged.

The versioned `successor-desktop-handoff-20261018-v15-run02-windows-runtime-v1` derivative changes only the launcher's implementation binding. All eleven payload files, including train/dev DocBins, tokenizer, seed configurations and qualification contracts, are byte-identical. Derived manifest SHA-256: `3236f9c5f097633506e7cd84ad01f9104d1ada92e26bedce6b7fe1c55edc781e`. The private receipt records both manifests, the exact source patch and passing regression evidence. Dataset admission, grouping and serialization were not repeated.

## Windows runtime repair and checks

The old probe imported spaCy before initializing Windows CUDA DLL search. Thinc cached CuPy as unavailable, producing `Cannot use GPU, CuPy is not installed` despite the installed packages. The actual training subprocess separately lacked DLL setup. A shared launcher helper now registers only the selected interpreter's Torch/CUDA runtime/NVRTC directories, retains DLL handles, and imports Torch before spaCy in both subprocess paths. Errors expose bounded diagnostics and retain the existing no-CPU-fallback behavior. No dependencies, model bytes, recipe, production APIs or schemas changed.

**64 focused tests pass:** successor preparation/launcher checks plus nine constructed Windows runtime cases. Tests cover setup/import order in both paths, retained handles, non-Windows behavior, missing libraries, partial registration cleanup, timeout/failure diagnostics, unchanged read-only behavior, stale/tampered bindings, held-out capability rejection and concurrent destinations. The first application-fixture run could not import FastAPI in the isolated training environment; the next run found an inaccessible default pytest temporary directory. Final checks use `--noconftest` and a new private `--basetemp`, without installation or permission changes. An intermediate diagnostic-message regression was fixed; failed-run evidence is retained privately.

The actual successor launcher reports `verified_read_only`, `gpu_verified=true`, `training_started=false` with Python 3.11.17, spaCy 3.7.5, Torch 2.11.0+cu128, CuPy 13.6.0 and RTX 3060 Ti compute capability 8.6. All 23 pinned model files match. The complete model is under `gpu-qualification-20261015/model`; the guide's earlier preflight model example is absent on this desktop.

## Training outcome

| Seed | Outcome | Optimizer updates | Selected checkpoint / validation F1 |
|---|---|---:|---|
| 0 (primary) | Failed configuration validation, exit code 1 | 0 | None |
| 1 | Not started after seed 0 failure | 0 | None |
| 2 | Not started after seed 0 failure | 0 | None |

The actual GPU subprocess reached spaCy's initialization entry point, then rejected `training.optimizer.l2` and `training.optimizer.l2_is_weight_decay` as extra fields. The pinned `Adam.v1` signature requires case-sensitive `L2` and `L2_is_weight_decay`. Those lowercase keys already exist in the received seed templates; the successful historical configuration uses uppercase keys. The earlier structural template checks do not resolve the spaCy registry schema, so they did not catch this supplied-config defect. Its upstream serialization origin is not established in the available code; no producer behavior is inferred.

The failed `successor-training-seed-0-v1` directory, rendered config, request, stdout/stderr and exit receipt remain intact. There is no selected checkpoint and no numerical validation result. The launcher released its own lock after the subprocess exited; no active lock was removed manually. Seeds 1/2 remain absent. The recipe and original/derived payloads were not edited, and no automatic retry occurred, as required by the approved stop-on-failure rule.

**Next task:** repair case-preserving portable-config preparation in a new versioned package, verify full spaCy config/registry resolution in addition to structural checks, then separately authorize a new seed-0 attempt before seeds 1/2. Preserve the failed destination and all source evidence. A new attempt must use an absent output path; successful training would still require the frozen earliest-development-F1 checkpoint checks. No held-out scoring or hyperparameter change is proposed.

## Research limits and preservation

These remain AI-assisted silver references under the adopted limited-provenance research standard. Historical history/accounting flags stay false; validation lacks Taglish ROAD support and the research holdout lacks LOCAL_AREA support. No holdout evaluation, model-improvement claim, deployment, commit or push occurs. All **12,343 persistent predecessor files (4,869,899,963 bytes)** verify unchanged after the attempt; the inventory excludes environments, dependency caches and bytecode. The original ZIP/package, all eleven derivative payload files and `.env` are unchanged. [Machine-readable verification](verification.json).
