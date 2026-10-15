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

The current local result is `awaiting_target_desktop`: Windows 11, NVIDIA GeForce MX330, 2,048 MiB VRAM and driver 572.16. This is laptop evidence only.

## Continue the existing gates

1. Use the actual desktop report to select and hash-lock isolated GPU dependencies. Preserve the CPU research checkpoint and production environment. Verify both spaCy/CuPy GPU operation and any model-specific PyTorch requirements; a successful NVIDIA query alone cannot establish either.
2. Exercise constructed inputs and a constructed training step first, recording memory and failures. Keep the pinned calamanCy artifact and candidate tokenizer identities intact.
3. Finalize the case-specific source-use basis and a versioned project/admission decision before news-model processing. Publisher clarification is optional evidence, not an automatic legal prerequisite; statutory-exception and contractual questions remain distinct. Existing held articles are not silently cleared by this inventory or the defense deadline.
4. After supported admission, qualify the tokenizer on the frozen cohort, export the unchanged partitions, run the baseline/training/evaluation and then integration/release checks. Deployed inference and defense demonstration scope remain distinct from the earlier private-use assessment. Preserve the current runtime and rollback until a replacement qualifies.

The dates in [task_plan.md](../task_plan.md) are targets, not promised model scores or deployment completion. The full roadmap and current source-use records remain authoritative.

Official references: [NVIDIA query documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html), [spaCy GPU installation](https://spacy.io/usage#gpu), [IPOPHL fair-use guidance](https://www.ipophil.gov.ph/news/ipophl-releases-statutory-fair-use-guidelines-to-clarify-rules-on-copyright-exceptions/?news_page=6).
