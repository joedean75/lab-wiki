# Gotchas and fixes

Every trap hit so far, what it looked like, and the fix.

## Training and data

| Symptom | Cause | Fix |
|---|---|---|
| Replies run on with invented "user" turns; only the first action runs | Server stopped at `<|endoftext|>` only, not the template's `<|im_end|>` | `serve.stop_ids` includes the template end-of-turn (both repos). |
| A dataset version quietly lost a third of its rows | Length cap with an estimated, not measured, token count (v15: UUIDs) | Measure per source with the real tokenizer; the guard refuses > 5 % loss; `--dry-run` first. |
| 302M weights never trained for ten versions | Hand-written LoRA target list missed Qwen3.5's linear-attention projections | Discover targets (`targets: auto`). |
| Lowest validation loss ≠ best model | Loss measures imitation, not the task | Pick by eval; compare with the baseline. |
| Epoch 2 made held-out scores worse | Over-fitting to trained families | Default 1 epoch. |
| A round "improved" but was worse than its start | Pick compared only the round's own checkpoints | `pick --baseline --baseline-adapter`. |
| Self-play teaches nothing | Model already solves ~100 % | Harder kinds (`fix2`), new families, per-(family, kind) cap. |
| Model says "`X` should be `X`" and loops | It doesn't know the fix; demos always stated it | Worked fix replies from expected vs actual; two-bug demos that re-read the file. |
| 4B training OOM at 2,560 after another job | Card fragmentation / other process memory | Train at 2,048 or restart the GPU state first. |
| Assistant step unscored | One reply > the client's 300 s timeout aborted the eval | Restart, or treat a timeout as a failed item (offered fix). |

## Serving

| Symptom | Cause | Fix |
|---|---|---|
| Server uses 12–13 GB host RAM after a long prompt | GPU memory spilled to shared memory and stayed reserved | `torch.cuda.empty_cache()` after every request. |
| Unmerged adapter generates at 5 tok/s | fp32 adapter math on every layer | Merge at load. |
| Two vehicle tasks impossible for every model | `max_new_tokens` 256 truncated the reply | 768; always surface `finish_reason`. |
| CPU server slower with 8 threads than 4 | Hyperthreads share a core; generation is memory-bound | `LLAMA_ARG_THREADS=4` (+6 %). |

## Windows, WSL and shells

| Symptom | Cause | Fix |
|---|---|---|
| Background WSL job dies ~1 min after launch | WSL stops the distro when the last client exits | Hidden `wsl.exe -d Ubuntu -- sleep infinity` keep-alive. |
| systemd user unit can't find `powershell.exe` | Units have no Windows PATH | Export `/mnt/c/Windows/System32/WindowsPowerShell/v1.0`. |
| Patch script has `\n` or `\w` turned into letters | Git Bash heredoc / `sed` mangle backslashes | Write files with an editor; don't generate code through heredocs. |
| `wsl.exe --cd /mnt/...` fails from Git Bash | Git Bash rewrites the path | Run that `wsl.exe` call from PowerShell. |
| `$VARS` expand inside a quoted heredoc via `wsl.exe bash -lc` | Double expansion | Write the script to a file, run the file. |
| PowerShell treats python's stderr as an error | 5.1 wraps native stderr in error records | `$ErrorActionPreference = "Continue"`, check `$LASTEXITCODE`. |
| `Invoke-RestMethod` to Proxmox fails: "connection was closed" | PS 5.1 TLS with a self-signed cert | Use `curl -k`. |
| A round log looks like `c o d e r` | PowerShell `Tee-Object` writes UTF-16 | Decode as UTF-16. |
| The GPU looks 30 % busy at idle | The 3050 reports compositor load | Check free memory and processes, not utilization. |
| A long training round vanished overnight | Windows Update rebooted the laptop | Set active hours / pause updates during rounds; check `LastBootUpTime`. |
| Long evals killed mid-run | Claude Code's shell reaps background processes under memory pressure | Start long jobs detached (`Start-Process ... -WindowStyle Hidden`). |
| Frontend build fails with Windows node | `node_modules` has Linux bindings | Use WSL's node. |
| ~230 Forge tests fail at once | Two pytest sessions sharing a database | One session at a time. |

## Evaluation meaning

| Symptom | Cause | Fix |
|---|---|---|
| Adapter 15/16 vs base 0/16 | Measured boxed format, not correctness | Score the answer, not the wrapper. |
| "Verified" self-play runs with the wrong part | Requirement checks too loose | Reference-body check (IoU ≥ 0.995, same bores); tighter forms (F-7). |
| Word overlap ties v1 and v2 | Overlap ignores correctness | Judge model. |
| Differences of 1–3 tasks | Noise is ±4 | Don't decide on them. |
