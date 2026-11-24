# Forge copilot training

**Model:** LoRA (rank 16, alpha 32) on Qwen3.5-2B. **Data built in** WSL `~/cad/backend/datasets`;
**trained and served on Windows** in `Books\Pipeline_copilot` (a private GitHub repo).
**Current winner:** v19 step 4200 — 44/53 over four suites. Served on port 8099.

## How it works

The copilot is an agent: each turn it sees the part's state and the request, and emits one Forge
operation (`set_spec`, `add_primitive`, `add_hole`, `set_feature_params`, `finish_task`, …) as JSON.
Forge runs it and reports back; gate checks verify the body against the spec before `finish_task`
is accepted. Training data are conversations of such turns:

| Source | What it is |
|---|---|
| Recorded runs | Real successful sessions. |
| Scripted references | Programs that know the right build for a task family (ISO 273 clearance plates, DIN 974 counterbores, NEMA motor plates, pillow blocks…). |
| Repair lessons | Rejected finish → fix → re-finish. Mostly did **not** transfer on their own. |
| Self-play | The model's own runs that pass the requirement checks. |
| Hindsight rows | Runs that built the right body but wrote a wrong spec, relabelled (F-2). |
| Replay | 1,500 rows of the previous version's data, to prevent forgetting. |

### Evaluation suites

`goals-v2` (18), `edits-v2` (11), `vehicle-v2` (17) and `assembly-v2` (7) — 53 tasks. Geometry is
also scored by IoU and Chamfer distance against reference builds.

## How it is implemented

| Where | What |
|---|---|
| `~/cad/backend/datasets/build.py` | Builds a dataset into `data/ft-<tag>` (isolated `DATABASE_URL=sqlite:////tmp/...`, under `systemd-run --user --scope -p MemoryMax=8G`). |
| `datasets/self_play.py`, `assembly_play.py` | Self-play families and their scripted references. |
| `datasets/mix.py` | Specialist + replay mix (`--main`, `--replay-skip`). |
| `training/*_round.sh` | One whole round as a systemd user unit (e.g. `v19-round`). |
| `training/stage.sh` | Copies scripts and datasets to `Pipeline_copilot` with `.before-<tag>-<stamp>` backups. |
| `Pipeline_copilot/copilot_sft.py` | The trainer (head on supervised positions, OOM-stepping length probe, `--init-adapter`, `--resume`). |
| `Pipeline_copilot/serve.py` | OpenAI-compatible server with an adapter bank. |
| `Pipeline_copilot/length_report.py` | Per-source real-token guard: exit 2 if a source loses > 5 %. |
| `app/services/context_compact.py` | Compact context: last 3 steps + latest failed check verbatim; short 8-char ids. |

## How to use it

```bash
# in WSL: build a dataset
cd ~/cad/backend
DATABASE_URL=sqlite:////tmp/forge-build.db FORGE_DATA_DIR=/tmp/forge-data \
  systemd-run --user --scope -p MemoryMax=8G \
  .venv/bin/python -m datasets.build --base data/ft-v7b-20260928 --subject document --profile finetuned \
  --out data/ft-vNN-<date>
```

```powershell
# on Windows: train (refuses while another trainer runs), serve, evaluate
cd C:\Users\<you>\Documents\Books\Pipeline_copilot
powershell -ExecutionPolicy Bypass -File launch_sft.ps1 -Dataset dataset-v19 -Out runs\sft-2b-v20 `
    -InitAdapter runs\pick-sft-2b-v19-lora-step004200\lora-final.pt -Lr 0.00005 -Epochs 1 -MaxLen 3584
powershell -ExecutionPolicy Bypass -File serve_run.ps1 -Out runs\pick-sft-2b-v19-lora-step004200   # port 8099
```

Detached WSL jobs need a keep-alive (`Start-Process wsl.exe -ArgumentList '-d','Ubuntu','--','sleep','infinity' -WindowStyle Hidden`),
otherwise WSL shuts down about a minute after the last client exits and kills systemd user units.

## History and lessons

| Version | Result | Lesson |
|---|---|---|
| v9–v10 | NO_CHANGE lessons; parts model | — |
| v11 / v12 | Repair data; v12 vehicle 5/15 vs baseline 10/15 — **not shipped** | Repair lessons didn't transfer; the model "repaired" with identical values (no-op). |
| v13 → v14 | v14 harness: compact context, larger budgets, early stop on unchanged body, **LoRA on linear-attention projections** (12.1M → 15.6M trainable), `max_new_tokens` 256 → 768 | One truncation cap had made two vehicle tasks impossible for every model. |
| v15-asm | Assembly adapter, 5/7 vs v8's 6/7 | **30 % of rows silently dropped** by the length cap (UUIDs). Always measure with the real tokenizer per source. Short ids fixed it. |
| v16 | One adapter for parts *and* assemblies: vehicle 14/17, goals 14/18, edits 11/11, assembly 6/7 | The end-of-epoch-1 checkpoint won again. |
| v17 | 43/53; ten real-geometry families with metre-valued reasoning | — |
| v18 | 40/53 | Self-play failed on the model's **own spec arithmetic**, not the build; checkers passed wrong parts. |
| **v19** | **44/53** (vehicle 15/17, goals 15/18, edits 8/11, assembly 6/7) | Stated-only spec labels (F-1) and hindsight rows (F-2) helped. |

Open decisions: F-7 (tighter requirement forms) was built on 2026-11-23 as F-10; F-8 is still parked. The v19
measurement sweep found only 59 % of verified runs are the reference body.

### Serving gotchas from this project

- `serve.py` used 12–13 GB of host RAM: a 9k-token prompt spilled the 6 GB card into shared memory and
  PyTorch kept it reserved. `torch.cuda.empty_cache()` after each request fixed it (now in `lab.core.serve`).
- Claude Code's shell reaps background processes under memory pressure, killing long eval chains —
  run long jobs as detached processes or systemd units.

**2026-11-23, research cards.** F-9 to F-15 are built
([background](../concepts/research-trellis2.md)): quality-ranked self-play, requirement forms the
program computes, `check_layout` plus `add_primitive(from_layout=...)` (optional; the owner's
answers), five phrasings per scripted goal (as written, spelled out in two orders, cm, m), a second
self-play pass sized by p(1 − p), a short-first order flag in the trainer, and IoU preference pairs
with a one-model DPO stage (`datasets/pairs.py`, `training/copilot_dpo.py`). The old sweeps give only
47 pairs, so the F-15 run makes its own. The `f14-f15-round` unit was stopped before training, at the
owner's request: the coder base-model bake-off runs first, and its winner may change the copilot's
base too (Qwen3.5-2B's own card: LiveCodeBench 20.2, BFCL 43.6).
