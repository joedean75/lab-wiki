# Assistant pipeline

**Repo:** `Books\Pipeline_assistant` → a private GitHub repo.
**Current model:** v2, Qwen3.5-4B + LoRA, judge 7.0/10, served on the home server as `davinci`.

## How it works

It fine-tunes a general chat assistant on **your own conversation history**, so it answers in your
domains (networking, hardware, code, the projects here) and your preferred style.

1. **Import** every export it is pointed at, detecting the format per file.
2. **Scrub** secrets and identifiers *before anything is written*.
3. **Filter** noise; **dedup**; **split by time** (newest 5 % of conversations held out).
4. **Train** a LoRA adapter.
5. **Evaluate** checkpoints on held-out first turns with a **judge model** and pick the best.

### What goes in

| Source | Handling |
|---|---|
| Claude Code logs (`~/.claude/projects`, Windows and WSL) | Only turns you typed (`origin.kind == "human"`); exchanges whose answer used tools are dropped (the final text reports results the model never saw). |
| claude.ai export (`conversations.json`) | Content as JSON or Python-repr strings; only the **active branch** (`parent_message_uuid`), so abandoned regenerations are left out; tool-using answers dropped (v1 learned to narrate "Let me build…" from them); artifacts inlined. |
| ChatGPT export | Follows `current_node` up the tree. |
| Any JSONL with `messages` or `turns` | Generic. |

### Scrubbing

API keys, tokens, passwords, private keys, emails and **public** IP addresses are masked. Private
ranges, netmasks and resolvers are kept — they are the substance of networking chats. Your own
strings go in `scrub.extra`. A model memorises rare strings, so this is on by default and counted in
`scrub-report.json`.

!!! danger "Privacy"
    `data/exports/` holds your private conversations. Never print, copy or commit from it. `data/`,
    `runs/` and `*.zip` are git-ignored. Eval prompts are derived from them — report numbers only.

## How it is implemented

| File | Role |
|---|---|
| `lab/assistant/importers.py` | Format detection and the importers above. |
| `lab/assistant/scrub.py` | `Scrubber`; `_identifying_ip` keeps private ranges. |
| `lab/assistant/build.py` | Import → scrub → filter → dedup → time split → `train/val/eval_prompts/prompts.jsonl` + `report.json`. |
| `lab/assistant/evaluate.py` | ROUGE-L overlap, judge (OpenAI-compatible or `ant`), repeat rate, length ratio, bootstrap interval; writes `<out>.md` side by side. |
| `lab/assistant/regenerate.py` | Keep your prompts, re-answer them with an endpoint whose terms allow training. |
| `configs/assistant.json` | Inputs, `exclude`, `trusted_sources`, scrub extras, split fractions. |
| `configs/models/qwen3.5-4b-4bit.json` | Default base (NF4, max_len 2,560). `qwen3.5-2b.json` for the faster 2B. |
| `scripts/assistant_train.ps1` | Build → length check → (with `-Train`) judge preflight → train → pick. |

### The judge through `ant`

`LAB_JUDGE_BASE_URL=ant` sends each grading request to Claude via the `ant` CLI in WSL
(`/usr/local/bin/ant`), which uses its own OAuth login (`ant auth login`) — no API key passes
through the pipeline. `--check-judge` makes one tiny call first, so a login or billing problem stops
the run before hours of training. Grading puts correctness first.

## How to use it

```powershell
cd C:\Users\<you>\Documents\Books\Pipeline_assistant
# 1. put exports in data\exports\<name>\ ; then build and check lengths (no GPU)
powershell -ExecutionPolicy Bypass -File scripts\assistant_train.ps1 -Tag v3
# 2. read data\assistant\report.json and a sample of train.jsonl
# 3. train and pick (waits for the GPU)
powershell -ExecutionPolicy Bypass -File scripts\assistant_train.ps1 -Tag v3 -Train
```

Options: `-Model configs\models\qwen3.5-2b.json`, `-Judge none|ant|anthropic|<url>`,
`-JudgeModel claude-opus-5-5`, `-Epochs 1`, `-Lr 0.0001`, `-Init <adapter>`, `-RepetitionPenalty 1.1`.

Evaluate a served model by hand:

```powershell
$env:LAB_BASE_URL = "http://127.0.0.1:8765/v1"
$env:LAB_JUDGE_BASE_URL = "ant"; $env:LAB_JUDGE_MODEL = "claude-opus-5-5"
& $py -m lab.assistant.evaluate --prompts data/assistant/eval_prompts.jsonl --out runs\assistant-v2\eval.json
```

Export and deploy: see [Quantization and GGUF](../concepts/quantization-gguf.md) and the
[deploy runbook](../infrastructure/deploy-model.md).

## Results and lessons

| | v1 (2B, step 800) | v2 (4B, final) |
|---|---|---|
| Judge (Opus, 50 prompts) | 4.0 / 10 | **7.0 / 10** |
| Word overlap | 0.183 | 0.179 |
| Replies cut off at the limit | 5 | 0 |
| Repetition (mean) | 0.086 | 0.0003 |
| Length vs reference (median) | 0.65 | 0.82 |

- v1 (10-28): 402 samples at 3,584 tokens from 247 conversations. Its original pick was scored with
  the stop-token bug; re-scored 11-07 on overlap only, the three checkpoints tied.
- v2 (11-20): 665 samples, 4B in NF4; trained at 2,048 tokens (2,560 hit OOM after the coder
  round), 706 steps. Step 600 went unscored: one reply exceeded the client's 300 s timeout.
- **Word overlap cannot tell v1 from v2; the judge clearly can.** Use the judge.
- Merged v2 → Q4_K_M runs on the home server at ~4 tok/s.
