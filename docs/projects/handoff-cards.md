# Handoff cards

## How it works

On 11-09 every pipeline and Forge were reviewed, and improvements written as **self-contained task
cards** that a smaller model (or a person new to the code) can carry out one at a time. Each card has:
*check first*, *steps*, *tests*, *done when* and *do not*. A card marked parked, waiting or closed
records a problem and the owner's decision and is not to be started.

## Where the cards are

| Project | File | Cards |
|---|---|---|
| Index and global rules | `Books\HANDOFF.md` | — |
| Forge copilot data | `~/cad/docs/handoff/2026-11-09-improvements.md` | F-1 … F-8 + carry-overs |
| Forge copilot research | `~/cad/docs/handoff/2026-11-23-research-cards.md` ([background](../concepts/research-trellis2.md)) | F-9 … F-15 |
| Forge product | `~/cad/docs/handoff/2026-11-10-product-improvements.md` | U-1…U-6, P-1…P-9, X-1…X-5 |
| Assistant | `Pipeline_assistant\notes\handoff.md` | A-1 … A-3 + K-1 … K-5 |
| Coder | `Pipeline_coder\notes\handoff.md` | C-1 … C-12 + K-1 … K-5 |
| Astra | `Pipeline_astra\docs\HANDOFF.md` | R-1 … R-4 |

The K cards (shared core) appear identically in both lab repos.

## Rules for every card

1. One card at a time, one card per commit.
2. Read "Check first"; if the code doesn't match, stop and report.
3. Do only what the card lists.
4. Never start training, serving, a pick or a round — the owner schedules GPU work.
5. Check nothing is running before touching code it uses (`gpu_free.ps1`, `systemctl --user is-active <round>`).
6. Never two test sessions at once.
7. Never edit inside `How_to_*`.
8. No commit, push or delete unless the owner says so.
9. Don't restart Docker.
10. Report plainly: files, tests, commands with pass/fail counts, surprises, anything left undone.

## Status of the main cards

| Card | What | Status |
|---|---|---|
| K-1 … K-5 | Shared-core robustness (dead server, base check, Astra in the GPU guard, sync test, last batch) | Done |
| A-1, A-2 | Assistant eval diagnostics + error bar; record the v1 re-score | Done |
| A-3 | Judge with Claude | Done via the `ant` CLI |
| C-1, C-2 | Worked bit-layout derivations in `c_pixel` demos; layout check | Done (round 4, no gain) |
| C-3 | Bridging mask-and-shift family | Built 2026-11-23 as `c_header` (in `Pipeline_coder-c3` until the bake-off ends) |
| C-4 | Selection rule when late checkpoints sag | Closed, no change |
| C-6, C-7, C-8 | Worked fix replies + two-bug demos; `fix2` self-play; new families | Done, in round 5 (0.9115) |
| C-9 | Failed edits as a description; refused repeats | Built (off by default), being measured |
| C-10 | Base-model bake-off (Qwen3.5-2B/4B, MiniCPM5-2B, Phi-4-mini) | Running |
| C-11 | Preference pairs + DPO (shared core) | Built, waits for C-10's base |
| C-12 | Multi-turn GRPO, tiered rewards | Later |
| F-1 … F-6 | Stated-only spec labels, hindsight rows, text numbers, give-up-after, schtasks noise, `add_hole on_circle` | Done |
| F-7 | Tighter requirement forms | Unparked 2026-11-23 as **F-10** |
| F-8 | Roll back an edit that breaks evaluation | **Parked** with the owner |
| F-9 … F-15 | Quality-ranked self-play, computed requirement forms, layout check, phrasings, mid-difficulty self-play, length curriculum, IoU preference pairs | All built 2026-11-23. F-14/F-15 runs (`f14-f15-round`) on hold until the coder bake-off picks a base |
| U/P/X | Forge product cards | All built (uncommitted) |
| R-1 … R-3 | Astra: make the eval measure correctness, not the boxed format | See `Pipeline_astra\docs\HANDOFF.md` for current status |
| R-4 | A larger Astra eval | Left for now (owner) |
