# Pipeline_claude

**Repo:** `Books\Pipeline_claude` → a private GitHub repo.
**Model:** Qwen3 0.6B. **Benchmark:** MATH500.

## How it works

One config-driven pipeline that takes a **dataset to a reasoning model**, reusing the code of the two
books (*Build an LLM from scratch*, *Build a reasoning model from scratch*) without modifying them.
The same stage code runs a small **research** profile or a full **production** profile — only the
variables change.

```text
[pretrain] → distill → grpo → eval
 GPT from     SFT on    RLVR/   MATH500
 raw text     teacher   GRPO    verifier
              traces
```

| Stage | Does | Book code reused |
|---|---|---|
| `pretrain` (optional) | GPT-2-style base LM from raw text | `GPTModel` (LLM book) |
| `distill` | SFT on DeepSeek-R1 maths traces → a reasoning model | `reasoning_from_scratch.ch08` |
| `grpo` | RL where the reward is the maths verifier | `reasoning_from_scratch.ch06` (+ a reimplemented KL-anchored trainer from 7_6) |
| `eval` | MATH500 accuracy (boxed answer + sympy equality) | `reasoning_from_scratch.ch03` |

Concepts: [Distillation, RL and GRPO](../concepts/grpo-rl.md).

## How it is implemented

```text
Pipeline_claude/
  run.py                  CLI entry (forces UTF-8 stdout: the book prints ✓)
  configs/research.yaml   small and fast
  configs/production.yaml full scale
  pipeline/config.py      dataclass schema + YAML/CLI loader (--set section.key=value)
  pipeline/env.py         paths, device, import bootstrap
  pipeline/orchestrator.py  runs the stage list, threads one model through
  pipeline/stages/        pretrain.py, distill.py, grpo.py, evaluate.py
  GUIDE.md                the learning companion: levers and a ranked playbook
  PROGRESS.md             what has run and the numbers
```

Config highlights: `eval.method` = `greedy` | `self_consistency` | `pass_at_k`; `grpo.difficulty_filter`;
`kl_coeff`, `clip_eps`, `inner_epochs`, `format_reward_weight`; `model.checkpoint: book:...` loads the
author's published checkpoints for reference ceilings.

## How to use it

```bash
PY="../How_to_make_a_reasoning_model_from_scratch/My_work/.venv/Scripts/python.exe"
"$PY" run.py --config configs/research.yaml --dry-run          # wiring check
"$PY" run.py --config configs/research.yaml                    # distill → grpo → eval
"$PY" run.py --config configs/research.yaml --set grpo.steps=20 --set eval.limit=50
"$PY" run.py --config configs/research.yaml --set stages=eval --set model.variant=reasoning
```

Outputs go to `runs/<profile>/<timestamp>/` (checkpoints, metrics CSVs, `math500_eval.jsonl`, `summary.json`).

## Results and lessons

| Experiment | Result |
|---|---|
| GRPO round 1 (100 steps on the epoch-1 distilled model) | **37.6 % → 48.1 %** on 476 matched items (+10.5, McNemar p < 0.001); answers 2.5× shorter. 47.0 % over all 500. |
| GRPO round 2 (8 rollouts, curriculum refresh, format reward) | **54.0 % → 44.7 %** on 150 items (−9.3, p < 0.05). |

- Round 1 worked through **implicit brevity pressure**: the 640-token rollout cap only paid for
  concluding in budget.
- Round 2 overfit: the model was already concise, and the difficulty filter left 16–19 problems.
- The format reward was saturated from step 1, so it carried no signal.
- Distillation's `max_seq_len` must be ≥ 2,048 or the filter drops nearly every trace.
- Best model remains the round-1 GRPO checkpoint.
