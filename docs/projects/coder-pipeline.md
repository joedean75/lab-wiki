# Coder pipeline

**Repo:** `Books\Pipeline_coder` → a private GitHub repo.
**Model:** Qwen3.5-2B + LoRA. Best so far: round 3's step 5800 (0.915, 161/176).

## How it works

An **agentic coding model**: given a task and a small project, it reads files, writes code, runs
tests and fixes failures, one action per reply, until the tests pass. Languages: Python, C
(including a Cortex-M4 build) and `no_std` Rust — robotics, AI and embedded flavoured.

It is trained by [expert iteration](../concepts/expert-iteration.md) against **sandboxed,
test-verified tasks**.

### Tasks

A **family** is a function `make(rng, kind) -> Task` that generates a fresh problem per seed, with
names, constants and policies varied so the model must read rather than recall. Each task has a
**reference solution**, **visible tests** (the model can read and run them) and **hidden tests**
(laid over a copy at verify time; the model can never see or edit them).

| Language | Families |
|---|---|
| Python | `pid`, `ring_buffer`, `smoothing`, `crc`, `cobs`, `two_link_arm`, `quaternion`, `softmax`, `grid_path`, `intervals` (new), `kalman_1d` (**held out**) |
| C | `c_ring_buffer`, `c_crc`, `c_q15`, `c_pixel`, `c_debounce` (new), `c_bitfield` (**held out**) — host build at `-Wall -Wextra -Werror` plus a freestanding `arm-none-eabi-gcc` build |
| Rust | `rs_ring_buffer`, `rs_crc`, `rs_pid` — `cargo test --offline`, no dependencies |

Kinds: `implement` (stubs + visible tests), `fix` (one injected bug), `fix2` (two bugs; asked for by
name, not in the eval set).

**Splits:** task id `family/kind/seed`. Seeds ending in 0 are eval; others train. Held-out families
appear only in eval.

### The action protocol

A small model can't escape source code inside JSON, so a reply is a short reason plus one fenced
`action` block; file content follows in an ordinary fenced block:

````text
The test calls cfg_unpack; mode needs a 3-bit mask.
```action
replace src/cfg.c
```
```c
<<<<<<< SEARCH
    g->mode = (v >> 3);
=======
    g->mode = (v >> 3) & 0x7u;
>>>>>>> REPLACE
```
````

Actions: `ls`, `read <path>`, `write <path>`, `replace <path>` (SEARCH/REPLACE), `run <command>`,
`finish`.

### The harness (what the model sees)

`agent.context` is the **single** definition of the prompt — used by demos, self-play, eval and
serving. It holds the task, older steps one line each, and the last 3 steps verbatim, so length stays
flat. Observations are written to help:

- a failed run leads with **`first error: ...`** and, when it names a visible test line, the
  **failing check's source line** (`test_cfg.c:9: assert(g.mode == 1)`);
- an edit that changes nothing says so and how to find the fix ("read the failing check in
  `<test file>` and work it out from expected vs actual");
- an edit that puts a file back as an earlier step left it gets a **cycle note** quoting that version's error;
- the same action repeated with nothing changed is flagged, then the episode stops (`repeated_failure`).

### The sandbox

Runs in WSL. Commands come from an allow-list and run **without a shell**, under `unshare -rn`
(no network), with CPU-time, file-size and wall-clock limits. It guards against accidents, not
attackers.

## How it is implemented

| File | Role |
|---|---|
| `lab/coder/tasks/` | `__init__.py` (registry, splits, `inject`, `starter`), `python_tasks.py`, `c_tasks.py`, `rust_tasks.py`. `HELD_OUT = {"kalman_1d", "c_bitfield"}`. |
| `lab/coder/protocol.py` | Parse replies into actions; SEARCH/REPLACE edits. |
| `lab/coder/sandbox.py` | `Workspace`: throwaway dir, restricted runner, `verify` with hidden tests. |
| `lab/coder/agent.py` | `context`, `execute`, `run`, `first_error`, `failing_check`, cycle note, `samples`. |
| `lab/coder/validate.py` | Every reference passes; every starter fails; each injected bug fails visibly and its fix is exact; `--fix2` checks both bugs are needed. |
| `lab/coder/demos.py` | Scripted episodes (shapes in [Expert iteration](../concepts/expert-iteration.md)); worked fix replies with expected vs actual, hex and differing bits. |
| `lab/coder/self_play.py` | Attempts per task, `--weak-below` second pass, `--cap-solved`, `--kinds`; logs every episode to `*.episodes.jsonl`. |
| `lab/coder/build.py` | Assemble the dataset; validation split **by task**; optional `--replay FILE:N`. |
| `lab/coder/evaluate.py` | Greedy pass rate over the eval split; `held_out` reported separately; per-family table. |
| `scripts/coder_round.ps1` | One whole round. |

### What a round does (`coder_round.ps1 -Round N`)

1. Start a hidden WSL keep-alive.
2. If the demos file is missing: `validate --seeds 3 --fix2`, then `demos` → `data/coder/demos-vN.jsonl`.
3. Rounds > 1: serve `runs\coder-v(N-1)\best.pt`, run the **baseline eval**, then **self-play**
   (`--start 1000·N`, kinds `implement,fix,fix2`, weak-below 0.8, cap 12) → `data/coder/self-play-r(N-1).jsonl`.
4. `build` demos + this round's self-play → `data/coder/vN/`.
5. `train --dry-run` (length guard), wait for the GPU, train 1 epoch from the previous best.
6. `pick` every 6th checkpoint + final, against the baseline → `runs\coder-vN\best.pt`.

## How to use it

```powershell
cd C:\Users\<you>\Documents\Books\Pipeline_coder
powershell -ExecutionPolicy Bypass -File scripts\coder_round.ps1 -Round 6
```

Useful pieces on their own (in WSL, from the repo folder):

```bash
python3 -m lab.coder.validate --seeds 3 --fix2
python3 -m lab.coder.demos --per-family 24 --fix2-per-family 12 --out data/coder/demos-v6.jsonl
LAB_BASE_URL=http://<windows-host>:8765/v1 python3 -m lab.coder.evaluate --out /tmp/eval.json
LAB_BASE_URL=... python3 -m lab.coder.self_play --per-family 16 --kinds implement,fix,fix2 \
    --weak-below 0.8 --cap-solved 12 --out data/coder/self-play-test.jsonl
python3 -m unittest discover -s tests -v
```

Progress of a running round: `runs\coder-vN\round.log` (UTF-16; decode it) and the growing
`data\coder\self-play-r*.episodes.jsonl`.

## Results

See [Coder rounds 1–5](coder-rounds.md).
