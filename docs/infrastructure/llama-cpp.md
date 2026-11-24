# llama.cpp

## How it works

**llama.cpp** is a C/C++ inference engine for language models. It runs quantized **GGUF** models
fast on ordinary CPUs (and GPUs), with no Python. Its pieces used here:

| Tool | Job |
|---|---|
| `convert_hf_to_gguf.py` | Hugging Face folder → GGUF (bf16/f16/q8_0). Supports Qwen3.5 (`qwen35` architecture). |
| `llama-quantize` | GGUF → smaller quant types (Q4_K_M, Q4_0, Q3_K_M, …). |
| `llama-imatrix` | Builds an importance matrix for better low-bit quants. |
| `llama-server` | HTTP server with an OpenAI-compatible API and a built-in chat web UI. |
| `llama-bench`, `llama-cli` | Benchmark; command-line chat. |

## How it is implemented here

- **Laptop:** WSL `~/llama.cpp`, built at commit `e09a78a` (2026-10-29), binaries in `build/bin/`.
  The converter runs with the Windows venv's Python (it has torch and transformers), reading the
  script over `\\wsl.localhost\Ubuntu\home\<you>\llama.cpp\`.
- **Server:** the official llama.cpp server image, build **b11960**, as a Proxmox container
  ([Proxmox](proxmox.md)). Configured entirely by `LLAMA_ARG_*` environment variables:

| Variable | Value | Meaning |
|---|---|---|
| `LLAMA_ARG_MODEL` | `/models/model.gguf` | The model file baked into the image. |
| `LLAMA_ARG_HOST` / `_PORT` | `0.0.0.0` / `8080` | Listen on all interfaces. |
| `LLAMA_ARG_CTX_SIZE` | `8192` | Context window (shared across 4 slots). |
| `LLAMA_ARG_JINJA` | `1` | Use the model's own Jinja chat template from the GGUF. |
| `LLAMA_ARG_THREADS` | `4` | Physical cores (see [CPU speed](../concepts/inference-performance.md)). |
| `LLAMA_ARG_ALIAS` | `davinci` | The model name clients see. |
| `LLAMA_ARG_REASONING` | `off` | No thinking block (the assistant was trained with thinking off). |

## How to use it

### Talk to the server

- Web UI: <http://<llm-host>:8080>
- Health: `curl http://<llm-host>:8080/health` → `{"status":"ok"}`
- Model info: `/v1/models` (parameter count, size, quant type), `/props` (build, settings, template)
- Chat (OpenAI-compatible):

```bash
curl http://<llm-host>:8080/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"davinci","messages":[{"role":"user","content":"Hello"}],"max_tokens":200}'
```

Any OpenAI client works with base URL `http://<llm-host>:8080/v1`. The lab pipelines can use it
directly: `LAB_BASE_URL=http://<llm-host>:8080/v1`.

### Run a model locally (smoke test)

```bash
cd ~/llama.cpp
LLAMA_ARG_REASONING=off build/bin/llama-server -m /mnt/c/.../davinci-v2-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8181 -c 4096 --jinja -t 8 -ngl 0
```

`-ngl 0` keeps everything on the CPU (the GPU is usually busy training). The laptop ran the 4B Q4_K_M
at ~13.5 tok/s.
