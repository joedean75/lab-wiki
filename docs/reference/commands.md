# Command cheat sheet

Set these once per shell:

```powershell
# PowerShell
$py = "C:\Users\<you>\Documents\Books\How_to_make_a_reasoning_model_from_scratch\My_work\.venv\Scripts\python.exe"
```

```bash
# Git Bash / WSL (Proxmox API)
B=https://<pve-host>:8006/api2/json
H="Authorization: PVEAPIToken=$PVE_TOKEN"
```

## GPU and processes

| Task | Command |
|---|---|
| Is the GPU free for a new job? | `powershell -ExecutionPolicy Bypass -File scripts\gpu_free.ps1` |
| What's on the GPU | `nvidia-smi` |
| Find training/serving processes | `Get-CimInstance Win32_Process -Filter "Name like '%python%'" \| Select ProcessId, CommandLine` |
| When did Windows last reboot | `(Get-CimInstance Win32_OperatingSystem).LastBootUpTime` |

## Coder pipeline

| Task | Command |
|---|---|
| Run a round | `powershell -ExecutionPolicy Bypass -File scripts\coder_round.ps1 -Round N` |
| Validate families | `wsl.exe -d Ubuntu --cd <repo> -- python3 -m lab.coder.validate --seeds 3 --fix2` |
| Tests | `wsl.exe -d Ubuntu --cd <repo> -- python3 -m unittest discover -s tests -v` |
| Read the UTF-16 round log | `python -c "print(open('runs/coder-v5/round.log','rb').read().decode('utf-16','replace'))"` |

## Assistant pipeline

| Task | Command |
|---|---|
| Build + length check | `powershell -ExecutionPolicy Bypass -File scripts\assistant_train.ps1 -Tag vN` |
| Train + pick | `... -Tag vN -Train` |
| Check the judge | `& $py -m lab.assistant.evaluate --check-judge` (with `LAB_JUDGE_BASE_URL=ant`) |

## Core

| Task | Command |
|---|---|
| Length table (seconds) | `& $py -m lab.core.train --model <profile> --train <train.jsonl> --out <run> --dry-run` |
| Serve | `& $py -m lab.core.serve --model <profile> --adapter <adapter.pt> --port 8765` |
| Pick | `& $py -m lab.core.pick --run <run> --model <profile> --every 6 --eval "<cmd with {out}>"` |
| Merge | `& $py -m lab.core.merge --model <profile> --adapter <pt> --merged <dir>` |

## llama.cpp and the model server

| Task | Command |
|---|---|
| Convert | `& $py \\wsl.localhost\Ubuntu\home\<you>\llama.cpp\convert_hf_to_gguf.py <hf dir> --outtype bf16 --outfile x.gguf` |
| Quantize | `~/llama.cpp/build/bin/llama-quantize in.gguf out.gguf Q4_K_M 8` |
| Server health | `curl http://<llm-host>:8080/health` |
| Server model | `curl http://<llm-host>:8080/v1/models` |

## Proxmox

| Task | Command |
|---|---|
| List containers | `curl -sk -H "$H" $B/nodes/server/lxc` |
| Container config | `curl -sk -H "$H" $B/nodes/server/lxc/<id>/config` |
| Start / shutdown | `curl -sk -H "$H" -X POST $B/nodes/server/lxc/<id>/status/start` · `.../status/shutdown` |
| Upload a template | `curl -sk -H "$H" -F content=vztmpl -F "filename=@x.tar" $B/nodes/server/storage/local/upload` |
| Task status | `curl -sk -H "$H" "$B/nodes/server/tasks/<UPID>/status"` |

## Forge

| Task | Command |
|---|---|
| Dev servers | `cd ~/cad && ./start.sh` |
| Tests (one session only) | `cd ~/cad/backend && .venv/bin/python -m pytest -q` |
| Is a round running | `systemctl --user is-active v19-round` |
| Keep WSL alive for a detached job | `Start-Process wsl.exe -ArgumentList '-d','Ubuntu','--','sleep','infinity' -WindowStyle Hidden` |

## This wiki

| Task | Command |
|---|---|
| Preview locally | `cd /mnt/c/Users/<you>/Documents/lab-wiki && ~/venvs/wiki/bin/mkdocs serve` → <http://127.0.0.1:8000> |
| Build | `~/venvs/wiki/bin/mkdocs build --strict` |
| Deploy | see [Runbook: this wiki](../infrastructure/wiki-deploy.md) |
