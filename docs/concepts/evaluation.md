# Evaluating and picking checkpoints

## How it works

### Pick by what the model does

Training saves a checkpoint every 200 steps. The obvious choice — the final one, or the one with
the lowest validation loss — was wrong again and again:

- Copilot v14, v16, v18, v19: the winner was a mid-run checkpoint (often the end of epoch 1).
- Coder round 1: epoch 2 (31 h) made held-out scores fall steadily while validation loss stayed flat.
- Coder round 3: the final adapter lost 3 tasks against step 5800, 193 steps earlier.

So every pipeline serves candidate checkpoints one at a time, runs a **task eval** on each, and
copies the best to `best.pt` with a `pick.json` table.

### Compare against where you started

Coder round 4 picked its best checkpoint — which was *worse* than the adapter the round started
from. Now `pick` scores the starting adapter first (the **baseline**) and keeps it if nothing beats
it strictly.

### Held-out families

If a model only ever sees seeds of the same task families it trains on, a high score may be
memorisation. Each pipeline holds some **families** out of training entirely (coder: `kalman_1d`,
`c_bitfield`); their score is the generalisation signal. They must never train —
`test_held_out_families_never_train` enforces it.

### Noise

Know how big a difference has to be before it means anything:

- Coder eval: about **±4 tasks** out of 176–192 (two checkpoints 26 steps apart differed by 4).
- Assistant word overlap: three v1 checkpoints were within 0.012 on 50 prompts — a tie. The eval now
  prints a **bootstrap 95 % interval**: resample the per-prompt scores many times and take the 2.5th
  and 97.5th percentile of the mean.
- Pipeline_claude: a **McNemar test** on matched problems (who flipped from wrong to right versus
  right to wrong) gave p < 0.001 for round 1.

### Metrics that measure the wrong thing

| Metric | Problem it hid |
|---|---|
| Word overlap (ROUGE-L) | Rewards sounding like the reference, not being right. v1 vs v2 overlap: 0.183 vs 0.179 (a tie); judge: 4.0 vs 7.0. |
| Boxed-answer rate (Astra 15/16 vs 0/16) | Measured whether the answer was in `\boxed{}`, not whether it was correct. |
| Verified self-play rate (Forge) | The checker accepted the wrong part. |
| Any score before 10-31 | Measured with a server that didn't stop at end-of-turn. |

### LLM as judge

For open-ended answers, a stronger model grades each reply 1–10 against the reference, **putting
correctness first**. The assistant uses Claude Opus through the `ant` CLI (its own login; no key in
the process). `score = judge mean / 10`. Always read some side-by-side answers too (`<out>.md`).

### Diagnostics beside the score

Truncated replies (`finish_reason == "length"`), empty replies, repetition rate, reply length versus
the reference, outcome counts (`solved`, `repeated_failure`, `budget`) and per-family tables. These
say *why* a score moved.

## How it is implemented

`lab/core/pick.py`:

```text
python -m lab.core.pick --run runs/coder-v5 --model configs/models/qwen3.5-2b.json \
    --every 6 --eval "<command writing JSON with a numeric 'score' to {out}>" \
    --baseline runs/coder-v5/pick/baseline.json --baseline-adapter runs/coder-v4/best.pt
```

For each candidate (end of each epoch, final, every Nth checkpoint): start `lab.core.serve`, wait for
`/health` (and notice if the server process died), run the eval, stop the server. Only one model is
ever on the card. A stale score file is never read as a new result.

## How to use it

- Coder: `wsl.exe -d Ubuntu --cd <repo> -- python3 -m lab.coder.evaluate --out runs/x/eval.json`
  against a served model (`LAB_BASE_URL=http://127.0.0.1:8765/v1`).
- Assistant: `python -m lab.assistant.evaluate --prompts data/assistant/eval_prompts.jsonl --out ...`
  with `LAB_JUDGE_BASE_URL=ant`, `LAB_JUDGE_MODEL=claude-opus-5-5`.
- Read the per-family table and three or four full failing transcripts before believing any number.
