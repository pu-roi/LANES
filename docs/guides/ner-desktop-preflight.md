# NER desktop hardware preflight

This is the hardware-inventory step in the existing NER roadmap. It preserves the frozen 400-sample cohort, calamanCy identity, tokenizer candidates and isolated Python 3.11/spaCy 3.7.5 research requirements. It does not install dependencies, admit sources, load a model or train anything.

The researcher confirmed an October 25, 2026 defense target requiring integration into deployed LANES, and availability of the i7 9th-generation/16 GB/RTX 3060 Ti 8 GB desktop this week. These are project targets and reported hardware, not verified GPU benchmarks or release readiness.

## Run on the RTX desktop

Use Python 3.10 or later for this standard-library-only collector. The collector's Python is not automatically the eventual research interpreter; the research environment remains pinned to Python 3.11 and spaCy 3.7.5.

From the desktop's LANES repository root, run in Windows PowerShell:

```powershell
py -3 backend/training/flood_ner/desktop_inventory.py --output backend/training/flood_ner/artifacts/desktop-preflight/run-01
```

On Linux, use `python3` instead of `py -3`. If no suitable Python is installed, record that fact before provisioning the isolated managed Python from the existing research recipe. Do not install GPU packages into `backend/.venv` or copy an existing virtual environment between machines.

The collector is included in the requested `roi-branch` publication. On the desktop, pull `roi-branch` before running it. The earlier local handoff ZIP under `backend/training/flood_ner/artifacts/desktop-readiness-20261015-v1/` remains an unchanged historical alternative containing only the collector, its earlier guide and hashes. No news dataset or model is needed for inventory. Full captures, annotations, weights and Python environments are ignored by Git; pulling the branch does not transfer those files. Restore required study artifacts separately from the owner-only backup when the later training/admission steps require them, and recreate environments on the desktop.

For a second run, choose a new output folder such as `run-02`; existing destinations are refused. No report is uploaded automatically. Keep reports private because they include local interpreter and executable paths.

## Interpret the result

| Result | Exit | Meaning |
|---|---:|---|
| `target_inventory_ready` | 0 | A driver query reports an RTX 3060 Ti with at least 7,680 MiB total VRAM. This permits dependency planning, not a training-readiness claim. |
| `awaiting_target_desktop` | 2 | The driver reports another GPU. The actual RTX desktop still needs checking. |
| `inventory_failed` | 2 | The NVIDIA tool, driver or query output could not be verified. The report retains the error. |
| Invalid or existing destination | 1 | No inventory report overwrites an existing checkpoint. |

The output contains `inventory.json` and a file-hash `manifest.json`. It records OS, CPU description, RAM where readable, disk free space, driver, GPU model and total/free VRAM. It does not infer CUDA Toolkit installation, compatible PyTorch/CuPy wheels, model loading, training memory or six-class accuracy. `gpu_training_qualified` always remains false at this inventory stage.

The earlier laptop result was `awaiting_target_desktop`: Windows 11, NVIDIA GeForce MX330, 2,048 MiB VRAM and driver 572.16. The actual desktop inventory now reports `target_inventory_ready`: Windows 10, RTX 3060 Ti, 8,192 MiB VRAM and driver 610.47. Constructed GPU environment qualification is complete as described below.

## Continue the existing gates

1. Completed for this desktop: selected and hash-locked isolated GPU dependencies using the actual report. Preserve the CPU research checkpoint and production environment. Verify both spaCy/CuPy GPU operation and any model-specific PyTorch requirements; a successful NVIDIA query alone cannot establish either.
2. Completed for this desktop: exercised constructed inputs and three training updates, recording memory and failures. Keep the pinned calamanCy artifact and candidate tokenizer identities intact.
3. Finalize the case-specific source-use basis and a versioned project/admission decision before news-model processing. Publisher clarification is optional evidence, not an automatic legal prerequisite; statutory-exception and contractual questions remain distinct. Existing held articles are not silently cleared by this inventory or the defense deadline.
4. After supported admission, qualify the tokenizer on the frozen cohort, export the unchanged partitions, run the baseline/training/evaluation and then integration/release checks. Deployed inference and defense demonstration scope remain distinct from the earlier private-use assessment. Preserve the current runtime and rollback until a replacement qualifies.

The dates in [task_plan.md](../task_plan.md) are targets, not promised model scores or deployment completion. The full roadmap and current source-use records remain authoritative.

Official references: [NVIDIA query documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html), [spaCy GPU installation](https://spacy.io/usage#gpu), [IPOPHL fair-use guidance](https://www.ipophil.gov.ph/news/ipophl-releases-statutory-fair-use-guidelines-to-clarify-rules-on-copyright-exceptions/?news_page=6).

## Qualified RTX desktop environment (October 15, 2026)

The actual RTX 3060 Ti 8 GB desktop now passes constructed GPU qualification on driver 610.47. The isolated environment is under `backend/training/flood_ner/artifacts/gpu-qualification-20261015/research-env/`. Python 3.11.17 / spaCy 3.7.5 / CuPy 13.6.0 / Torch 2.11.0+cu128 pass CUDA kernels, native inference, temporary six-class updates at batch sizes 1/4/8, serialization and exact CPU entity replay. Both actual runs pass; 122 focused tests pass. [Measurements, exact locks and limitations](../evaluations/flood-ner-desktop-gpu-20261015/README.md).

On this desktop, rerun from the repository's `backend/` folder, choosing a new destination:

```powershell
& 'training/flood_ner/artifacts/gpu-qualification-20261015/research-env/Scripts/python.exe' -X utf8 -m training.flood_ner.gpu_preflight --python training/flood_ner/artifacts/gpu-qualification-20261015/research-env/Scripts/python.exe --model-manifest training/flood_ner/artifacts/gpu-qualification-20261015/model_manifest.json --output training/flood_ner/artifacts/gpu-qualification-20261015/run-03
```

Exit 0 means the constructed GPU environment and CPU replay pass. Exit 2 retains an execution/qualification failure in report.json and worker logs. Invalid inputs or an existing destination return exit 1. The command accepts only the fixed 24 constructed probes, verifies the complete pinned model before and after execution and writes its temporary trial model only under ignored artifacts. The trial uses the opt-in tokenizer candidate and a fresh six-class head with the pretrained NER tok2vec encoder copied from the pinned artifact; the original disk model stays unchanged. It never opens a news corpus or alters admission.

For a fresh Windows machine, provision an explicit task-local folder and recreate the environment:

1. Bootstrap task-local uv 0.13.1 and use a task-local cache. Install managed CPython 3.11.17 using an explicit `--install-dir`, `--no-bin` and `--no-registry`. Create a venv with that exact interpreter and `include-system-site-packages=false`.
2. Resolve `backend/training/flood_ner/requirements-gpu-qualification.in` with `uv pip compile --python <research-python> --generate-hashes --no-build --no-config --output-file <new-lock>`. The recipe pins an official Windows CPython 3.11 Torch CUDA wheel. Retain the resolver output and lock, then install using `uv pip sync <new-lock> --python <research-python> --require-hashes --no-build --no-config`. To reproduce the measured dependency versions, use the [recorded GPU lock](../evaluations/flood-ner-desktop-gpu-20261015/requirements-gpu.lock).
3. Restore the public pinned calamanCy model from the [model manifest](../evaluations/flood-ner-desktop-gpu-20261015/model_manifest.json), verifying every recorded file size and SHA-256. Save a separate manifest with model_dir rebased into the new ignored artifacts folder. Git contains the metadata, not the model weights or environment.
4. Run the constructed command above with the new paths. The worker adds CUDA DLL search directories and CUDA_PATH only within its own process. No system-wide CUDA Toolkit, driver change or permanent PATH change is needed for this measured configuration.

The existing Python `py` launcher did not discover the desktop's uv-managed Python 3.14.6. That interpreter was sufficient for inventory; the research environment uses its own explicit Python 3.11.17 executable. Windows sandbox restrictions initially denied the new interpreter's output/cache access; the permitted execution route succeeded without changing Windows security policies.

The small trial confirms execution and short-input capacity. It does not choose a safe real-news batch size or establish NER accuracy. The CPU replay used the same GPU-capable wheel on Windows; a clean CPU-only/Linux production environment still needs qualification. Source-use/admission, actual-cohort tokenizer checks and deployment gates remain as listed in task_plan.md.
