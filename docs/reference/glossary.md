# Glossary

**Accumulation (gradient)** — summing gradients over several samples before one optimizer step; a large effective batch with the memory of one sample.

**Adapter** — the small trained LoRA weights (`.pt`), loaded on top of a frozen base model.

**Alpha (LoRA)** — scales the adapter's contribution: `scale = alpha / rank`.

**Baseline** — the adapter a round started from, scored by the same eval so the round can be judged against it.

**bf16** — 16-bit "brain float": same range as fp32, less precision; the training dtype here.

**Bootstrap interval** — resample per-item scores with replacement many times; the middle 95 % of the means is the uncertainty.

**Chat template** — the model's rule for turning messages into one string with role markers.

**Checkpoint** — saved weights at a training step (`lora-step000200.pt`).

**CT / LXC** — a Proxmox container: isolated processes on the host kernel.

**diff_id / digest** — SHA-256 of an OCI layer uncompressed / compressed.

**Distillation** — training a small model to reproduce a large model's outputs.

**Demo (scripted)** — a training episode driven by a program that knows the answer, executed for real.

**Epoch** — one pass over the training data.

**Expert iteration** — train on the model's own verified successes, repeat.

**Family (task)** — a generator of parameterised problems with reference solutions and tests.

**`fix2`** — a coder task with two injected bugs.

**GGUF** — llama.cpp's single-file model format.

**GRPO** — RL that scores each sampled answer against its group's average.

**Held-out family** — a task family never trained on; measures generalisation.

**Hidden tests** — tests the agent can't see, applied at verify time.

**Hindsight row** — a run relabelled with the goal it actually achieved.

**imatrix** — importance matrix guiding low-bit quantization.

**KL penalty** — keeps an RL policy close to a reference model.

**K-quant** — llama.cpp's two-level block quantization (`Q4_K_M`, `Q3_K_M`).

**LoRA / QLoRA** — low-rank adapters on a frozen base / the same with a 4-bit base.

**Loss (cross-entropy)** — how surprised the model is by the correct next token.

**Merge** — fold the adapter into the base weights to get a standalone model.

**NF4** — 4-bit "normal float" storage for a frozen base model.

**NO_CHANGE** — the harness's message when an edit left the file or body unchanged.

**OCI** — the open container image standard (index → manifest → config + layers).

**Pick** — choosing `best.pt` by eval.

**Quantization** — storing weights in fewer bits.

**Rank (LoRA)** — the inner size `r` of the adapter matrices (16 here).

**`repeated_failure`** — coder outcome: the same action repeated with nothing changed, so the episode stopped.

**Replay** — mixing earlier data into a specialist's training to prevent forgetting.

**Round** — one build → train → pick cycle.

**ROUGE-L** — word-overlap score based on the longest common subsequence.

**Sandbox** — restricted runner: allow-listed commands, no shell, no network, resource limits.

**Self-play** — the served model attempting new tasks to produce verified training data.

**SFT** — supervised fine-tuning on example conversations.

**Supervised tokens** — positions the loss is computed on (the assistant's reply and end marker).

**Token** — the unit a model reads and writes.

**UPID** — a Proxmox task id for a long-running operation.

**vztmpl** — Proxmox storage content type for container templates (OCI images included).

**Window (sample)** — a slice of a long conversation that fits the length cap.
