# Clean Docker launch: blocked at graceful exit

> **Last Updated:** October 19, 2026, 12:50 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The independent Windows launch was not performed.** One normal Docker Desktop stop failed, so this task stopped at the approved boundary. Linux qualification and Gate 3 remain open; no image build or model execution occurred.

## Observed outcome

| Check | Result |
|---|---|
| Installed Docker Desktop | 4.91.0.239619; unchanged. |
| Normal shutdown | One `docker desktop stop --timeout 30`, without `--force`. |
| Receipt | The 35-second wrapper deadline expired; captured output says “Failed to stop Docker Desktop.” |
| Desktop/backend process inventory | Six processes remain after the stop attempt. |
| WSL | `docker-desktop` is Stopped. This does not establish that the Windows Desktop/backend processes exited. |
| Agent server connectivity | Linux engine API remains unavailable. |
| Ordinary independent Windows PowerShell | Not tested. PowerShell subprocesses used for process inspection were agent descendants. |
| Independent Start-menu launches | Zero. The startup waiting/polling stage was not reached. |

The earlier log excerpt still records an inaccessible `sailor-ingest.sock` rename. This task does not establish its underlying cause or prove a launch-environment defect. A failed quit is not a failed independent-launch experiment.

Raw stdout/stderr, command reservations, completed timeout receipt, before/after process and WSL inventories, installed-version evidence and relevant prior error excerpts remain in the ignored private v28 diagnostic package. No existing receipts were overwritten. [Aggregate outcome and verification hashes](verification.json).

## Required user action

Use Docker Desktop's **normal Quit** action in its tray menu, or **Quit** in the error window. Do not choose factory reset, data cleanup or force termination. Tell the agent once it is closed; process exit must be verified before a new launch.

After shutdown is verified, launch Docker Desktop once from the Windows Start menu, outside the agent. Allow at most 60 seconds, then check the Linux server from an ordinary independently opened PowerShell and from the agent:

```powershell
docker --context desktop-linux info --format '{{.OSType}} {{.ServerVersion}}'
```

Require a successful exit, `linux` and a nonempty server version. If graceful exit still cannot be obtained, retain the blocker; do not keep issuing stop/start commands. No update, reinstall, socket operation, permission/security change, WSL unregister or system reboot is authorized by this task. [Runtime guide](../../guides/ner-runtime-qualification.md).

## Preservation and completion

All **564 protected file hashes** remain unchanged; **55 holdout and 27 prior-validation entries** match size/mtime through metadata-only checks. Preserved research helpers retain their implementation hashes. No annotation, partition, dataset, tokenizer, model, result, production API, dependency or schema was changed. Dataset membership remains **345 training / 60 validation / 60 completed research-holdout passages**, with v19 control seed 0 retained.

No new software tests were run: source code did not change. The earlier **393 passing regressions** remain historical evidence, distinct from this live failed shutdown attempt. New checks were the bounded process/status diagnostics, preservation verification, documentation links and whitespace checks.

Completion is a documented blocked outcome at graceful exit. No Desktop/backend process was force-killed, no socket was renamed/deleted, and no Docker data/settings reset was performed. No independent launch, image build, model execution, training, holdout access, live integration, upload, commit or push occurred. The desktop GPU can remain off.
