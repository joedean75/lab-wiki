# Research: small base models and agent failures

Read on 2026-11-23, after coder round 5, to answer two questions: is there a better base than
Qwen3.5-2B for the three models, and what does recent work say about the coder's main failure
(repeating an action that just failed)?

## Base models that fit a 6 GB card

Numbers are from the vendors' own cards (the MiniCPM5 card also reports the Qwen columns).

| Model | Size | LiveCodeBench v6 | SWE-bench Verified | Terminal-Bench 2.1 | BFCL v4 (tools) | Licence |
|---|---|---|---|---|---|---|
| **Qwen3.5-2B** (copilot, coder) | 2B | 20.2 | 5.0 | 3.0 | 43.6 | Apache-2.0 |
| **Qwen3.5-4B** (assistant v2) | 4B | 56.4 | 33.6 | 25.8 | 56.8 | Apache-2.0 |
| **MiniCPM5-2B** (OpenBMB, Sept 2026) | 2.5B | 69.1 | 46.4 | 8.6 | 66.6 | Apache-2.0 |
| **Gemma 4 E2B / E4B** | 2.3B / 4B effective | 44.0 / 52.0 | — | — | — | Gemma |
| **Phi-4-mini-instruct** | 3.8B | — | — | — | — | MIT |

- **Qwen3.5-2B is the weakest coder here.** Both the copilot and the coder are built on it.
- **Qwen3.5-4B** already trains on the 3050 in 4-bit (2,560 tokens, 5.26 GiB, 27 s/step).
- **MiniCPM5-2B** is a stock Llama architecture with a released base checkpoint, but a review found it
  falls apart in multi-turn agent harnesses (Terminal-Bench 8.6 against Qwen3.5-4B's 25.8). Agent
  work is what all three of our models do.
- **Gemma 4 E2B** is 2.3B "effective" but 5.1B with its per-layer embeddings; no LoRA memory figures.
- **Phi-4** itself is 14B and does not train on this card; Phi-4-mini (3.8B) does, in 4-bit.
- Nothing newer at these sizes: Qwen3.6 starts at 27B; Inkling 2 Mini is a 26B mixture-of-experts.

Vendor numbers are only a hint. The **bake-off** (coder card C-10) trains each candidate the same way
on the same data and scores it on our own eval: 2,000 samples, from scratch, 2,560 tokens.

## Why small agents repeat a failed action

*Feedback That Backfires* (arXiv 2608.23651, Aug 2026; six models from 135M to 1.7B): showing a small
agent its failed call and the error makes it **more** likely to send the same call again (−1.03 nats
per action token). 83 % of the effect is copying the call's own text from the context, not misreading
the error.

| Fix tried | Effect |
|---|---|
| Replace the failed call in context with a short description | removes ~76 % of the effect |
| Refuse a repeat of a failed string at decode time | exact repeats 31 % → 8 %, success unchanged |
| Both | exact repeats 7 % |
| A "do not repeat" instruction | no change in the probe |
| Delete the failed attempt | worst: repeats rise to 80 % |

Our harness did the instruction ("NOTE: you already did exactly this"), which this predicts does little.
Coder card **C-9** adds both fixes as switches (`--abstract-failed`, `--refuse-repeats N`).

## Training ideas for the coder

| Idea | Source | Card |
|---|---|---|
| Learn from a solved and a failed attempt of the same task (DPO) | CADFusion, F-15 | C-11 (built) |
| Multi-turn GRPO, crediting earlier attempts from a later success | Murphy, arXiv 2511.07833 | C-12 |
| Tiered rewards (compiles / runs / visible tests / hidden checks) and per-step scores | Signal Reshaping, arXiv 2605.07276 | C-12 |
| A small model that learns when to ask a stronger one | SWE-Protégé, arXiv 2602.22124 | not planned (needs an API teacher at run time) |
| On-policy distillation from a teacher | several 2026 papers | not planned (no teacher fits the card) |

## Sources

- [Qwen3.5-2B model card](https://huggingface.co/Qwen/Qwen3.5-2B)
- [Qwen3.5 small models (Artificial Analysis)](https://artificialanalysis.ai/articles/qwen3-5-small-models)
- [MiniCPM5-2B model card](https://huggingface.co/OpenBMB/MiniCPM5-2B)
- [The 2B model that beats 4B rivals, until you test it as an agent](https://levelup.gitconnected.com/the-2b-model-that-beats-4b-rivals-until-you-test-it-as-an-agent-94ea12aa679c)
- [Gemma 4](https://www.deepmind.google/models/gemma/gemma-4) and [Gemma 4 E2B architecture](https://sebastianraschka.com/llm-architecture-gallery/models/gemma-4-e2b/)
- [Feedback That Backfires](https://arxiv.org/abs/2608.23651)
- [Murphy: multi-turn GRPO](https://arxiv.org/abs/2511.07833)
- [Signal Reshaping for GRPO](https://arxiv.org/abs/2605.07276)
- [SWE-Protégé](https://arxiv.org/abs/2602.22124)
