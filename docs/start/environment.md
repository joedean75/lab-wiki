# Machine and toolchain

## How it works

Training needs CUDA, which works best natively on Windows here; the code sandboxes, C/Rust
toolchains and the Forge backend need Linux. So the laptop runs **both**:

- **Windows 11** runs the GPU work: training (`lab.core.train`, `copilot_sft.py`), model servers
  (`lab.core.serve`), merges and conversions.
- **WSL 2 (Ubuntu)** runs everything Linux: the coder sandbox, test runners (`python3`, `gcc`,
  `arm-none-eabi-gcc`, `cargo`), the Forge backend and its dataset builders, llama.cpp tools.

The two talk through the filesystem (`/mnt/c/...` from WSL, `\\wsl.localhost\Ubuntu\...` from
Windows) and through `localhost` HTTP (a Windows model server on port 8765 is reachable from WSL).

## Hardware

| Part | Detail | Why it matters |
|---|---|---|
| GPU | NVIDIA RTX 3050 Laptop, 6 GB | Caps model size and sequence length. A 2B model trains in bf16; a 4B needs 4-bit (NF4) loading. |
| RAM | 32 GB | Merging a 4B model on the CPU needs ~9 GB; a long prompt can spill GPU memory into system RAM. |
| Disk | ~950 GB, keep 50 GB+ free | Merged models are 4–9 GB each; checkpoints 120–370 MB. |

!!! note "The 3050 lies about being busy"
    At idle it reports 22–44 % "utilization" (Windows desktop compositor). Scripts check **free
    memory and running processes**, never utilization — see `scripts\gpu_free.ps1`.

## Python environments

| Environment | Where | Used for |
|---|---|---|
| Reasoning-book venv | `Books\How_to_make_a_reasoning_model_from_scratch\My_work\.venv\Scripts\python.exe` | All Windows GPU work: torch 2.9 + CUDA, transformers 5.x, bitsandbytes. **Run it; never edit or install into that folder.** |
| WSL system `python3` | `/usr/bin/python3` | The coder sandbox and pipeline tests (stdlib `unittest`, no pytest). |
| Forge backend venv | `~/cad/backend/.venv` | Forge server, tests, dataset builds. |
| Wiki venv | `~/venvs/wiki` | MkDocs, to build this site. |
| Astra venvs | `Books\Pipeline_astra\.venv`, `.venv-qwen` | Astra and its Qwen runner. |

## Shells and their traps

| Shell | Use it for | Watch out for |
|---|---|---|
| PowerShell 5.1 | Windows commands, launching training, `wsl.exe` calls | No `&&`; stderr from python becomes an error record; `Invoke-RestMethod` to self-signed HTTPS fails (use `curl.exe -k`). |
| Git Bash | Quick POSIX commands on Windows | Heredocs and `sed` mangle backslashes (`\n`, `\w`); it rewrites `/mnt/...` paths passed to `wsl.exe --cd`. Write patch files with an editor instead. |
| WSL bash | Linux work | WSL shuts the distro down ~1 minute after the last `wsl.exe` client exits, killing background jobs — long jobs keep a hidden `wsl.exe -d Ubuntu -- sleep infinity` alive. |

## Folder map

```text
C:\Users\<you>\Documents\
├── Books\
│   ├── Pipeline_assistant\   assistant pipeline (private git repo)
│   ├── Pipeline_coder\       coder pipeline    (private git repo)
│   ├── Pipeline_copilot\     Forge copilot trainer + datasets (private git repo)
│   ├── Pipeline_astra\       Astra             (private git repo)
│   ├── Pipeline_claude\      reasoning pipeline (private git repo)
│   ├── HANDOFF.md            index of all task cards
│   └── How_to_*\             the two books — read-only, venv only
└── lab-wiki\                 this wiki's source
WSL ~/
├── cad\                      Forge (private git repo, branch v18-prep)
├── llama.cpp\                llama.cpp build (convert, quantize, server)
└── venvs\wiki\               MkDocs
```

## House rules (apply everywhere)

- Never edit inside a `How_to_*` folder — only run its Python.
- Never run two test sessions at once in one repo (Forge tests share a database).
- Never edit a script while it is running (PowerShell and bash read scripts as they go).
- Don't restart Docker.
- Commit, push and delete only when the owner asks.
- `Pipeline_assistant\data\exports\` holds private conversations: never print, copy or commit from it.
