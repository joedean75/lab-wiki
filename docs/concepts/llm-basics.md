# How a language model is trained

A plain-terms primer on the ideas every other page assumes.

## How it works

### Tokens

A model never sees letters. A **tokenizer** cuts text into **tokens** (whole words, word pieces,
punctuation, bytes) and gives each an integer id. Qwen3.5's vocabulary has 248,320 tokens.
Lengths in this wiki — "3,584 tokens", "max_len 2,560" — are always token counts measured with
the real tokenizer, because a character or word estimate was once 30 % wrong.

### Next-token prediction

A causal language model reads tokens left to right and outputs, at each position, a probability
for every possible next token. Generation repeats: pick a token, append it, predict again — until
it emits an **end-of-turn** token or hits `max_tokens`.

### Training = making the right next token more likely

Training shows the model text and nudges its weights so the actual next token gets a higher
probability. The measure of "how surprised" it was is the **cross-entropy loss**; lower is better.
One pass of nudging is an **optimizer step**; going once through all data is an **epoch**.

### Pretraining vs fine-tuning

| Stage | Data | Result |
|---|---|---|
| **Pretraining** | Trillions of tokens of web text, code, books | A *base model* that continues text. Done by Qwen; far beyond a laptop. Astra does a tiny version to learn how. |
| **Supervised fine-tuning (SFT)** | Thousands of example conversations | A model that answers in a chosen style or does a chosen job. **Everything trained in this lab is SFT** (plus GRPO in Pipeline_claude). |

### Chat templates

A chat is turned into one long string with special markers, e.g. Qwen's:

```text
<|im_start|>user
How do I list files?<|im_end|>
<|im_start|>assistant
Use `ls -la`.<|im_end|>
```

Each model family has its own **chat template**, stored with its tokenizer. Rule learned the hard
way: **train and serve must render through the same template code**, and the server must stop at
the template's end-of-turn token (`<|im_end|>`), not only the model's generic end token. Missing that
once made every reply run on with invented turns (see [the stop-token bug](../projects/coder-rounds.md#round-1)).

### Supervising only the answer

In SFT the loss is computed only on the **assistant's tokens** (plus its end-of-turn marker). The
user's words are context, not something to imitate. These positions are the "supervised" or
"trained" tokens; a **mask** marks them. Also, an agent row with many steps trains only its *last*
action — earlier steps are context.

### Memory: why long samples are expensive

Activations grow with sequence length; the vocabulary-sized output layer is huge (248k × hidden
size). Two tricks make it fit on 6 GB:

- **Gradient checkpointing**: recompute activations during the backward pass instead of storing them.
- **Head on supervised positions only**: compute the 248k-way output only where the loss needs it.

### Validation loss is not the goal

Loss on held-out text says how well the model *imitates*; it does not say whether the model can
*do the task*. In the copilot, the coder and Pipeline_claude, the checkpoint with the lowest
validation loss was repeatedly **not** the best at the task. Hence [picking by eval](evaluation.md).

## Key numbers in this lab

| Thing | Value |
|---|---|
| Base models | Qwen3.5-2B (copilot, coder, assistant v1), Qwen3.5-4B (assistant v2), Qwen3 0.6B (Pipeline_claude) |
| Typical length caps | 2,560–3,584 tokens per sample |
| Training speed on the 3050 | ~3.3 h per 1,000 steps (copilot 2B at 3,072); 15–27 s/step (4B at 2,048–2,560) |
| Learning rate | 1e-4 (5e-5 when continuing a specialist) |
| Gradient accumulation | 4–8 samples per optimizer step |
