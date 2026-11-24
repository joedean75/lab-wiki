# Lab Wiki

Everything built in this lab so far: the model-training pipelines, the Forge CAD program and its
copilot, the home server that runs the models, and the ideas underneath all of it.

Each project article follows the same shape:

| Section | What it answers |
|---|---|
| **How it works** | The idea, in plain terms, and why it is built that way. |
| **How it is implemented** | Where the code lives, the main files, and the important decisions. |
| **How to use it** | Step-by-step commands to run it yourself. |
| **Results and lessons** | What happened when it ran, and what was learned. |

## Where to start

<div class="grid cards" markdown>

- **New to all of it?** Read [The big picture](start/overview.md), then
  [How a language model is trained](concepts/llm-basics.md) and [LoRA and QLoRA](concepts/lora-qlora.md).
- **Want to run something?** The [command cheat sheet](reference/commands.md) has every command in one place.
- **Something broke?** [Gotchas and fixes](reference/gotchas.md) lists every trap hit so far and its fix.
- **Deploying a model?** Follow the [deploy runbook](infrastructure/deploy-model.md).

</div>

## The projects at a glance

| Project | What it is | Where it lives |
|---|---|---|
| [Assistant pipeline](projects/assistant-pipeline.md) | Fine-tunes a general chat assistant on your own conversations. Current model: **v2** (Qwen3.5-4B), judge score 7.0/10, served as `davinci`. | `Books\Pipeline_assistant` |
| [Coder pipeline](projects/coder-pipeline.md) | Trains an agentic coding model (Python, C, Rust) by letting it solve sandboxed, test-checked tasks. Round 5 in progress. | `Books\Pipeline_coder` |
| [Shared core](projects/shared-core.md) | The model-agnostic training, serving and picking code both pipelines use. | `lab/core` in both repos |
| [Forge CAD](projects/forge-cad.md) | A browser-based, agent-driven CAD suite (exact B-rep + SDF kernels, FEA, CAM, printing). | WSL `~/cad` |
| [Forge copilot](projects/forge-copilot.md) | The fine-tuned model that drives Forge's copilot, trained v4 to v19. | `~/cad` + `Books\Pipeline_copilot` |
| [Pipeline_claude](projects/pipeline-claude.md) | Dataset to reasoning model: distillation then GRPO on MATH500 (+10.5 points). | `Books\Pipeline_claude` |
| [Astra](projects/astra.md) | A from-scratch PyTorch pipeline: tokenizer, pretraining, SFT, GRPO, export. | `Books\Pipeline_astra` |
| [Home server](infrastructure/proxmox.md) | Proxmox host running the `davinci` model container and this wiki. | `<pve-host>` (model `<llm-host>:8080`, wiki `<wiki-host>`) |

## Conventions used here

- Paths like `Books\Pipeline_coder` are under `C:\Users\<you>\Documents\`. Paths starting with `~/` are
  inside WSL (Ubuntu), home `/home/<you>`.
- Hosts are placeholders: `<pve-host>` (Proxmox API, port 8006), `<llm-host>` (model container) and
  `<wiki-host>` (this wiki), all on the home LAN. The scripts in `tools/` read them from the
  `PVE_HOST`, `LLM_HOST` and `WIKI_HOST` environment variables, like `PVE_TOKEN`.
- "The 3050" is the laptop's RTX 3050 6 GB GPU; it does all training.
- Numbers are as measured on the day; the [timeline](start/timeline.md) dates them.
- Secrets (API tokens, passwords) never appear in this wiki. Where one is needed, the page says
  where it is kept, not what it is.
