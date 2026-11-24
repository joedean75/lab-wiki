# Astra

**Repo:** `Books\Pipeline_astra` → a private GitHub repo.

## How it works

Astra is a **from-scratch PyTorch pipeline**, written independently from reading the books' code
(nothing from them is imported at runtime):

**Text/JSONL → tokenizer and splits → pretraining → reasoning SFT/distillation → GRPO → evaluation → inference bundle.**

It is a learning and research tool: every stage, its data format and its checkpoints are explicit,
reproducible and resumable. A separate optional runner fine-tunes Qwen3.5-2B with QLoRA on reasoning traces.

| Book idea | Astra implementation |
|---|---|
| GPT architecture (LLM book ch. 4) | Learned positions, pre-norm causal attention, GELU MLPs (`astra/model.py`) |
| Pretraining objective (ch. 5) | Shifted next-token loss (`astra/data.py`, `astra/training.py`) |
| GRPO rollouts and rewards (reasoning ch. 6) | `astra/grpo.py` |
| Frozen reference + KL (ch. 7) | KL regularisation |
| Distillation (ch. 8) | Response-only SFT |

## How it is implemented

- **Data preparation** streams documents into indexed SQLite; automatic splits hash normalised text
  with the seed so matching SFT and RL prompts stay together; cross-split duplicates fail.
- **Tokenizers:** UTF-8 bytes (offline, no dependencies) or a BPE trained on the training partitions only.
- **Fingerprints** reject reusing prepared data with an incompatible tokenizer, seed or context.
- **Checkpoints:** atomic `latest.pt`, validation-selected `best.pt`, `final.pt` only on completion;
  `--resume` restores optimizer, scaler, RNG and sampler (bit-exact on CPU).
- **Verifiers** need `<answer>…</answer>` or `\boxed{…}`; `numeric` and `exact` comparisons.
- **Production gate:** minimum answer accuracy and maximum SFT loss before automatic export.
- **Export bundle:** weights, tokenizer, config and a hash manifest; loaded with `weights_only=True`.
- Performance: KV-cached generation, logits only where needed, optional replay, majority voting.

Docs in the repo: `docs/CONFIGURATION.md`, `PERFORMANCE.md`, `VERIFICATION.md`, `QWEN35.md`, `HANDOFF.md`.

## How to use it

```powershell
cd C:\Users\<you>\Documents\Books\Pipeline_astra
python -m astra run --config configs/smoke.json                 # wiring check (nonsense answers)
python scripts/make_arithmetic_demo.py
python -m astra run --config examples/arithmetic/config.json    # learns addition
python -m astra generate --model examples/arithmetic/run/export --prompt "What is 3 + 4?" --max-new-tokens 64

python -m astra validate --config configs/research.json
python -m astra prepare  --config configs/research.json
python -m astra run      --config configs/research.json --set output_dir=../runs/my-run --set sft.learning_rate=0.00005
python -m astra evaluate --checkpoint runs/research/grpo/final.pt --split test
python -m astra export   --checkpoint runs/research/grpo/final.pt --output runs/research/deploy
python -m unittest discover -s tests -v
```

Qwen3.5-2B runner (separate venv):

```powershell
.\.venv-qwen\Scripts\python.exe -u scripts/train_qwen35.py --output runs/qwen35-2b-local-reasoning-v1
.\.venv-qwen\Scripts\python.exe -u scripts/evaluate_qwen35.py --run runs/qwen35-2b-local-reasoning-v1
```

## Results and lessons

| Check | Result |
|---|---|
| Arithmetic demo | 10/10 held-out correct; export gate passed. |
| Production architecture capacity | 111M parameters at 2,048 tokens with BF16 + activation checkpointing fits. |
| Qwen3.5-2B QLoRA (rank 8, 100 steps, 602 s, 3.5 GiB peak) | Held-out response loss 0.622 → 0.461 (−25.9 %). |
| Adapter vs base, boxed answers | 15/16 vs 0/16 — **but this measures the format**: the base's answers were right, just not boxed (card R-1..R-3). |

Lesson: check what a metric actually counts before celebrating it.
