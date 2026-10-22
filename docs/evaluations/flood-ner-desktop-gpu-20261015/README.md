# RTX desktop GPU environment qualification

> **Last Updated:** October 15, 2026, 3:49 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Passed:** isolated CPython 3.11.17 / spaCy 3.7.5 on the actual RTX 3060 Ti 8 GB desktop, NVIDIA driver 610.47. CuPy kernels, PyTorch CUDA, native calamanCy inference, three six-class constructed training updates, saved-model loading and CPU replay all passed. Final focused verification: **122 tests passed**; all 73 installed packages are compatible. This qualifies the constructed research environment, not news-corpus accuracy or deployment.

[Qualification](qualification.json), [GPU execution](gpu-result.json), [CPU replay](cpu-result.json), [inventory](inventory.json), [environment](environment_manifest.json), [verification](verification.json), [setup notes](setup_notes.json).

## Environment and model

The optional recipe is `backend/training/flood_ner/requirements-gpu-qualification.in`; production requirements only comment-link it. Pins retain spaCy 3.7.5, spacy-transformers 1.2.5, transformers 4.30.2, tokenizers 0.13.3, NumPy 1.26.4, floret 0.10.5 and Click 8.5.0. GPU additions are CuPy CUDA 12.x 13.6.0, official PyTorch 2.11.0+cu128, NVIDIA CUDA runtime 12.8.90 and NVRTC 12.8.93. The shared validator also needs the existing HTTPX 0.27.0. Binary-only dependency resolution preceded hash-required installation. [GPU lock](requirements-gpu.lock), [existing test dependencies lock](requirements-test.lock).

Task-local uv 0.13.1 installed managed Python 3.11.17 with `--no-bin --no-registry` and explicit install/cache directories. The research venv excludes system site packages. The production environment and system Python/registry/PATH were not changed. DLL directories and CUDA_PATH are configured only inside each isolated worker; CUDA DLLs come from the pinned Torch/NVIDIA wheels, with no system-wide CUDA Toolkit installation. CuPy reports CUDA build 12.9, driver API 13.3, runtime wheel 12.8 and NVRTC 12.8; actual kernels and training passed with this combination. This is a measured Windows configuration, not a universal compatibility guarantee.

The original desktop had only the inventory folder. Restored the public MIT calamanCy md 0.1.0 artifact from the existing approved revision `51a40433059d8a2c25b98a48eca854f8789a491a`: all 23 files / 161,970,218 bytes matched the prior SHA-256/size manifest. Original source artifacts were reverified after both runs; no article captures or private dataset were restored or processed. [Rebased model manifest](model_manifest.json).

## Constructed trial and measurements

Exactly 24 fixed hash-bound probes (12 English / 12 Taglish) were used. Native coarse LOC/ORG/PER predictions matched CPU output exactly. A separate temporary NER head was initialized with the six LANES place labels and the pinned pretrained NER tok2vec encoder. The opt-in candidate tokenizer aligns every trial reference. Updates used the first 1, 4 and 8 constructed examples, with dropout zero; these are short capacity checks rather than trained-model results. The original model directory was never modified. Native execution reports 70 GPU parameter arrays and two CPU arrays retained by the pinned architecture.

| Batch size | Update time (ms) | Raw NER loss | CuPy reserved pool (MiB) |
|---:|---:|---:|---:|
| 1 | 2064.69 | 8.961537 | 275.3 |
| 4 | 65.80 | 54.284197 | 283.9 |
| 8 | 70.66 | 109.483234 | 283.9 |

The first update includes initialization/JIT overhead. Loss sums across different batch sizes are not comparable accuracy measurements. Final-run model load was 777.79 ms; native GPU inference p50/p95 were 17.01/17.93 ms on 24 measured calls after 24 warm-up calls. GPU-process peak working set was 1170.5 MiB. The sampled device-wide used-memory high was 1483.4 MiB across 141 samples; that includes desktop/other processes. The maximum sampled CuPy reserved pool was 283.9 MiB, not exact live tensor memory. These short constructed inputs cannot establish a safe batch size for longer real news passages.

The trial model was saved only under ignored `run-02/trial-model`, then loaded in a separate CPU process using the same GPU-capable Python environment. All 24 saved-trial entity predictions matched GPU output exactly. Both runs also produced the same entity outputs. CUDA training weights have tiny floating-point differences between runs; bit-identical training is not claimed. CPU-only package installation, Linux production operation, full-cohort tokenization, independent six-class accuracy and production release remain unqualified.

## Reproduce

See the [desktop guide](../../guides/ner-desktop-preflight.md) for setup and the exact constructed-only command. The files map in qualification.json binds the ignored local run-02 tree; metadata_hash_manifest.json separately binds the published report copies. The installed environment, task-local downloads and both trial models remain under ignored `backend/training/flood_ner/artifacts/gpu-qualification-20261015/`. Recreate environments on another machine; do not copy a venv or install the GPU recipe into `backend/.venv`. Restored pinned model files need the manifest's model_dir rebased to that machine after every hash is verified. New run destinations are required.

The initial Torch-wheel selection, missing parent HTTPX dependency and sandbox execution/cache errors are retained in setup notes. No security policy was changed. Focused tests use `--noconftest` because these offline checks need no FastAPI application or database fixture. The two test warnings are documented in verification.json; both actual isolated CPU/GPU worker stderr logs are empty.

## Remaining gates

The frozen 400 samples / 139 articles, 40 contextual v3 pairs and 280/60/60 partitions retain their existing status; this work changes no source-use decision or admission flag. Next finalize the supported source-use/project decision and apply admission separately. Then qualify the actual frozen cohort with the selected tokenizer, export the preserved partitions, measure the real training workload and run baseline/training/validation/held-out evaluation. Assess deployed inference/defense use and production CPU packaging separately. No database schema, service endpoint, UI, deployment or Git publication changed.

Official references: [CuPy 13.6 compatibility](https://docs.cupy.dev/en/v13.6.0/install.html), [spaCy GPU selection](https://spacy.io/usage#gpu), [official PyTorch CUDA wheels](https://pytorch.org/get-started/previous-versions/), [uv Python installation controls](https://docs.astral.sh/uv/reference/cli/#uv-python-install).
