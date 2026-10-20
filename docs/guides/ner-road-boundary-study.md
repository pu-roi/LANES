# Offline training-only road-boundary study

> **Last Updated:** October 19, 2026, 12:02 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Completed: no boundary rule qualifies for a later validation proposal.** Read the [aggregate study](../evaluations/flood-ner-road-boundaries-20261019/README.md). All 345 training prediction records remain unchanged; v19 corrected control seed 0 remains retained. The earlier validation comparison and its consumed claim stay closed.

## Interfaces and separation

- `road_boundary_rules.py`: text-only `propose(opaque_id, text, predictions, enabled=...)` and a strict three-field `raw_record` envelope. Keep/trim/split apply only to original ROAD predictions, preserve types and keep children inside their parent. No prefix recovery, retagging, unmarked crossing inference, gazetteers, article exceptions or cascading edits.
- `road_boundary_cases.py`: 24 newly authored fictional contrasts with explicit occurrence offsets. Six ambiguous cases have null references and remain unscored. No fixture becomes a passage or training member.
- `road_boundary_study.py`: authenticate a frozen grant and the existing training-only audit view; verify all ROAD-error reviews and source hashes; run constructed checks and score three fixed individual rules, their combined output and the qualifying subset. References remain outside the decision function. The helper never reopens parent development containers or runs the type-safeguard decision function.

The grant binds nine implementation files, the new tests, matching constructed-test evidence, the training-only manifest, training source reviews and two convention guides. Its protocol fixes the original control baseline, permitted actions, no-composition policy and training qualification criteria. CLI guards reject neural imports, transport and child/training processes. The existing backend interpreter performs saved-span arithmetic without installation or GPU use.

## Interpreting results

Trimming and splitting are **partially supported** because the constructed behaviors pass but no corrective action occurs on saved training predictions. Two descriptor-bearing predictions abstain because their cores lack decisive lexical road cues; the direction and explicit-crossing rules have no matching predicted spans. Ambiguous merged names cannot be safely split using a whitelist or a presumed geographic identity.

A later proposal requires passing constructed checks, actual corrective training actions and zero introduced strict training FP/FN, followed by a joint-subset no-harm check. Empty applicability is unproven. Here the qualifying set is empty, so there is no boundary candidate for another validation comparison. Do not alter rules after these results to force applicability or combine them with the previously rejected type method.

## Private artifacts and reproduction

The ignored local packages are `road-boundary-coordination-20261019-v25`, `road-boundary-study-20261019-v25` and `road-boundary-study-20261019-v25-replay` under `backend/training/flood_ner/artifacts/`. A Git pull does not transfer them. No private delivery is needed or performed for this laptop study.

The following is a structural reproduction example using authenticated private inputs and an absent destination, not authorization for a new experiment:

```powershell
& .\backend\.venv\Scripts\python.exe -B .\backend\training\flood_ner\road_boundary_study.py --checkout (Get-Location).Path --grant <verified-private-grant.json> --grant-sha256 <exact-grant-hash> --output <new-private-output>
```

Do not overwrite outputs, modify frozen inputs, install model resources or weaken stale-hash/reference checks. Competing writers are rejected. Execution failures preserve separate failure evidence and original inputs. Missing evidence or unsupported patterns remain held rather than receiving guessed labels or boundaries.

The complete source review covers seven error passages and five saved training articles. Broader predecessor preservation runs separately; completed-holdout and prior validation packages receive metadata-only checks. New scoring receives only training records. Keep validation and holdout excluded from further tuning, preserve AI-assisted silver/history limitations and leave the desktop off unless a separately authorized later task requires it.
