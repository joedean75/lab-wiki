# LoRA and QLoRA

## How it works

### The problem

A 2B-parameter model has 2 billion weights. Fine-tuning all of them needs the weights, their
gradients and the optimizer state (two more copies for AdamW) in memory — tens of GB. The 3050 has 6.

### LoRA: train a small correction instead

**Low-Rank Adaptation** freezes every original weight matrix `W` and learns a small correction
beside it:

```text
output = W·x  +  scale · B·(A·x)
```

- `A` is `r × in`, `B` is `out × r`, with a small **rank** `r` (16 here). For a 2048×2048 layer that is
  65k trainable numbers instead of 4.2 million.
- `scale = alpha / r` (alpha 32, rank 16 → scale 2). `B` starts at zero, so training begins exactly at
  the base model.
- Only `A` and `B` get gradients and optimizer state. The saved **adapter** is ~120 MB (4B model) or
  less, not gigabytes.

### Which layers get adapters ("targets")

Every large `nn.Linear` inside the language model: attention projections, MLP projections, and in
Qwen3.5 also the **linear-attention input projections** (`in_proj_qkv`, `in_proj_z`). The copilot's
hand-written list missed those for ten versions (302M weights left frozen). Since then
`lab/core/lora.py` **discovers** targets: every linear layer whose smaller side is ≥ 256, except the
output head and vision/audio towers.

### QLoRA: a 4-bit frozen base

To fit the 4B model, the frozen base is loaded in **NF4** (4-bit "normal float", via
`bitsandbytes`), computing in bf16. The LoRA adapters stay in higher precision. This is QLoRA.
Measured on the 3050 (assistant v2): 2,048 tokens → 4.77 GiB, 15.5 s/step; 2,560 → 5.26 GiB,
27 s/step; 3,072 spills into system RAM (44 s/step).

### Merging

At serving time `W + scale·B·A` can be computed once and stored as an ordinary weight — the
**merged** model is a normal model with no adapter, so any runtime (llama.cpp, Ollama, vLLM) can run
it. An adapter trained on a 4-bit base is merged into the **bf16** base weights for export; this is
standard practice and the small mismatch is harmless in practice.

!!! warning "An adapter belongs to one base"
    A 2B adapter cannot load on the 4B base; the shapes differ. `pick` checks the adapter's base
    before serving (card K-2).

## How it is implemented

`lab/core/lora.py` (no `peft` dependency):

| Function | Does |
|---|---|
| `LoRALinear` | Wraps a frozen linear layer; adapters in fp32. |
| `find_targets(model, "auto", min_features)` | Discovers which layers to wrap. |
| `apply` | Freezes everything, wraps targets. |
| `save` / `read` / `load(strict=True)` | Adapter files (`.pt`); strict load fails if any key is missing either way. |
| `merge` | Folds every adapter into its weight and unwraps it. |
| `export_peft` | Writes `adapter_model.safetensors` + `adapter_config.json` for PEFT / llama.cpp's `convert_lora_to_gguf.py`. |

Model profiles (`configs/models/*.json`) carry rank, alpha, targets and the length cap:

```json
{
  "hf": "Qwen/Qwen3.5-4B",
  "dtype": "bfloat16",
  "load_in_4bit": true,
  "template_kwargs": {"enable_thinking": false},
  "max_len": 2560,
  "lora": {"rank": 16, "alpha": 32, "targets": "auto", "min_features": 256}
}
```

## How to use it

```powershell
# merge an adapter into full weights (CPU, ~2 bytes RAM per parameter)
python -m lab.core.merge --model configs\models\qwen3.5-4b-4bit.json `
    --adapter runs\assistant-v2\best.pt --merged out\davinci-v2-merged

# or export PEFT format only
python -m lab.core.merge --model configs\models\qwen3.5-2b.json `
    --adapter runs\coder-v4\best.pt --peft out\coder-v4-peft
```

Merging a 4B model took ~10 minutes and printed `merged layers: 200`.
