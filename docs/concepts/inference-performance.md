# Inference speed on a CPU

## How it works

Serving has two phases with different bottlenecks:

| Phase | What happens | Limited by |
|---|---|---|
| **Prompt processing** ("prefill") | All prompt tokens go through the model together, as big matrix-matrix multiplies. | **Arithmetic** — more cores help. |
| **Generation** ("decode") | One token at a time; each token multiplies by *every* weight once. | **Memory bandwidth** — reading the whole model from RAM per token. |

Rule of thumb: `tokens/s ≲ memory bandwidth ÷ model size`. The server's Xeon E3-1240 v3 uses
older DDR3; with a 2.6 GB model the measured 4 tok/s means ~10 GB/s actually achieved.

### Why fewer threads can be faster

The E3-1240 v3 has **4 physical cores / 8 hardware threads** (hyperthreading). Two hyperthreads
share one core's arithmetic units and caches. During generation:

- the extra thread adds **no memory bandwidth** — the bottleneck;
- the two threads **compete for the same cache**, evicting each other's data;
- llama.cpp **synchronises all threads after each layer**, so more threads means more waiting for
  the slowest one.

Measured on `davinci` (Q4_K_M 4B, 3 runs each after warm-up, greedy):

| Threads | Generation | Prompt (323 tokens) |
|---|---|---|
| 8 | 3.77 tok/s | 35.2 tok/s |
| **4 (kept)** | **4.00 tok/s (+6 %)** | 34.0 tok/s (−3 %) |

Prompt processing is compute-bound, so it lost a little; generation dominates chat time, so 4 won.

### Other levers

| Lever | Effect |
|---|---|
| Smaller quant (Q4_0, Q3_K_M) | ~10–30 % faster, some quality loss. |
| Smaller model (2B vs 4B) | ~2× faster; v1 (2B) judged 4.0/10 vs v2's 7.0. |
| Context size (`LLAMA_ARG_CTX_SIZE`, 8192) | Mostly memory; speed matters only for long chats. |
| Parallel slots | The server has 4 slots; simultaneous users share the same bandwidth. |
| A GPU | The only big jump. |

## How to measure

```bash
# greedy, no prompt cache, same prompt each time; first run is warm-up
curl -s http://<llm-host>:8080/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explain how a hash map handles collisions."}],
       "max_tokens":128,"temperature":0,"cache_prompt":false}' | python3 -c \
  "import json,sys; t=json.load(sys.stdin)['timings']; print(t['prompt_per_second'], t['predicted_per_second'])"
```

The response's `timings` object reports prompt and generation tokens per second.
