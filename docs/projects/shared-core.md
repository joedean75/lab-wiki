# Shared core (`lab/core`)

## How it works

The Forge copilot trainer worked, but it was hard-wired to one model family and one task. The
**core** is those lessons rebuilt as small, model-agnostic modules that any pipeline can use:
render a chat with the model's own template, measure lengths with the real tokenizer, train LoRA
on a 6 GB card, serve over the OpenAI API, pick checkpoints by eval, export.

Swapping to a better base model is **a new JSON profile, not a code change**.

!!! important "Two copies, kept identical"
    `lab/core` is duplicated in `Pipeline_assistant` and `Pipeline_coder` (each repo stands alone).
    Every core fix is made in **both**; `tests/test_core_sync` fails if they differ.

## How it is implemented

| Module | Job | Key decisions |
|---|---|---|
| `chat.py` | Render conversations; mark trained tokens; `windows()` splits long chats. | Uses the **tokenizer's chat template**, then locates each assistant message in the rendered text (in order, with a cursor) and includes the end-of-turn marker. **Train and serve call the same `Renderer`.** |
| `samples.py` | Rows → token samples; the length guard. | Real-tokenizer lengths **per source**; refuses if any source loses > `max_loss` (5 %). Agent rows (`train_on`) are dropped whole if too long; conversations are windowed instead. |
| `model.py` | Load any HF causal LM for a 6 GB card; the loss. | Profiles in `configs/models/`; 4-bit via bitsandbytes when the profile says so; head only on supervised positions. |
| `lora.py` | LoRA without `peft`. | **Discovered targets** (`auto`); strict loading; merge; PEFT export. |
| `train.py` | LoRA SFT. | Frozen bf16 base + fp32 adapters; gradient checkpointing; accumulation; longest sample first so OOM shows up on step 1 (then the cap steps down and the guard re-runs); checkpoint every 200 steps + `latest.pt`; `--resume` at the same offset; `summary.json` written only at the end; `--dry-run` prints the length table in seconds. |
| `serve.py` | OpenAI-compatible server (port 8765). | Adapter **merged at load** (unmerged fp32 adapters ran at 5 tok/s); `stop_ids` = template end-of-turn **and** eos; `torch.cuda.empty_cache()` after every request; `POST /admin/adapter` hot-swaps. |
| `client.py` | Minimal OpenAI chat client (stdlib only). | Works with `lab.core.serve`, llama.cpp, Ollama, vLLM, LM Studio via `LAB_BASE_URL`, `LAB_MODEL`, `LAB_API_KEY`; reports `finish_reason` so truncation is visible. |
| `pick.py` | Choose `best.pt` by eval. | One server at a time; notices a dead server; never reads a stale score; `--baseline` keeps the starting adapter if nothing beats it. |
| `merge.py` | Export merged HF weights or a PEFT adapter. | CPU only, so it never needs the GPU. |
| `jsonl.py` | Read/write JSONL. | — |

Scripts beside it:

- `scripts/gpu_free.ps1` — exit 0 only when no trainer or server from **any** pipeline (copilot,
  lab, Astra) is running and ≥ 5,000 MiB of video memory is free. Every launcher waits on it.

### The data row format

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
 "train_on": [5],
 "meta": {"source": "coder:self_play", "task": "c_crc/fix/1003"}}
```

`train_on` lists which assistant messages are trained (agent rows train only the last action);
without it every assistant message in the conversation is trained. `meta.source` drives the
per-source length guard and reports.

## How to use it

```powershell
$py = "C:\Users\<you>\Documents\Books\How_to_make_a_reasoning_model_from_scratch\My_work\.venv\Scripts\python.exe"

# check lengths before any real run (seconds, tokenizer only)
& $py -m lab.core.train --model configs\models\qwen3.5-2b.json --train data\coder\v5\train.jsonl --out runs\coder-v5 --dry-run

# train
& $py -m lab.core.train --model configs\models\qwen3.5-2b.json --train data\coder\v5\train.jsonl `
    --val data\coder\v5\val.jsonl --out runs\coder-v5 --epochs 1 --lr 0.0001 --accumulate 4 `
    --init-adapter runs\coder-v4\best.pt

# serve a checkpoint
& $py -m lab.core.serve --model configs\models\qwen3.5-2b.json --adapter runs\coder-v4\best.pt --port 8765

# is the GPU free?
powershell -ExecutionPolicy Bypass -File scripts\gpu_free.ps1
```

Tests: `python -m unittest discover -s tests -v` (Windows) or the same via `wsl.exe` for the coder.

## Cards that shaped it (K-1 … K-5)

| Card | Change |
|---|---|
| K-1 | `pick` notices a dead server at once (it used to wait 15 minutes) and never reads an old score file. |
| K-2 | `pick` checks the adapter's base model before serving it. |
| K-3 | `gpu_free.ps1` also sees Astra's trainer and evaluator. |
| K-4 | A test fails when the two core copies differ. |
| K-5 | `train` no longer drops the last partial gradient batch. |
