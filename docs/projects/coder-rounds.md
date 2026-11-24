# Coder rounds 1–5

Score = solved fraction of the eval split (greedy). "Seen" = families trained on; "held_out" =
`kalman_1d` + `c_bitfield`. Noise ≈ ±4 tasks.

## Summary

| Round | Dates | Data | Best | Score | Held-out | Key lesson |
|---|---|---|---|---|---|---|
| 1 | 10-28 → 10-31 | Demos only, 2 epochs, 62 h | step 3000 (by hand) | 0.552 → **0.768** after the stop fix | 0.50 | Epoch 2 wasted; the serving bug was the biggest "gain". |
| 2 | 10-31 → 11-02 | + recovery demos, self-play, 1 epoch | final | **0.881** (148/168) | 0.583 | Recovery demos worked; failure moved to "same failed replace ×3". |
| 3 | 11-03 → 11-06 | + failing-check line, cycle note, `trace_fix`, `c_pixel` | step 5800 | **0.915** (161/176) | 0.688 | A new family taught bit layouts (`c_pixel` 0 → 8/8). |
| 4 | 11-19 → 11-20 | + worked derivations in `c_pixel` demos | *round 3 kept* | 0.892 best | 0.625 | No gain; self-play solved 766/768 — no signal left. |
| 5 | 11-21 → 11-23 | + two-bug demos, worked fixes, `fix2` self-play, 2 new families | step 9600 | **0.9115** (175/192) | 0.667 | New families learned (8/8 each); `c_bitfield` implement still 0/12 — no family teaches varied layouts. |

## Round 1

Scripted demos only (5,804 rows), 2 epochs, 11,542 steps, 62 h.

| Checkpoint | Score (old harness) | Held-out |
|---|---|---|
| step 3000 | 0.552 | 0.500 |
| step 9000 (auto pick) | 0.559 | 0.375 |
| final | 0.471 | 0.313 |

**The stop-token bug.** `serve.py` stopped only at the config's `<|endoftext|>`, never at the chat
template's `<|im_end|>`, because no `generation_config.json` was cached. Every reply ran on with
invented user turns and extra actions until `max_tokens`; only the first action executed, so the
model often "wrote" files that were never written. Fixed (`serve.stop_ids`) in both pipelines.
Re-measured, step 3000 went **0.552 → 0.768** with no retraining. Lesson: **read full transcripts
before blaming the model.**

## Round 2

Changes: failed runs lead with `first error:`; failed edits say nothing changed; repeat guard;
recovery demos `wrong_api` (84) and `bad_edit` (153) with the mistake untrained; 48 held-out tasks;
self-play 646/720 solved; 1 epoch, 6,426 steps, 49 h.

- `kalman_1d` 16/24 → 24/24 at step 1200; the model now reads the header before writing C.
- New commonest failure: the **same failed replace three times** — traced: the model writes "`X` is
  the bug: it should be `X`" (no change), because it **doesn't know the fix**. Demos always stated
  the fix as already known.
- It never read the failing test; it cycled one shift 6 → 7 → 8 → 6 → 8.
- `c_bitfield` implement 0/12; no training family mapped "bits a..b" to shifts and masks.

## Round 3

Harness shows the failing check's source line, catches cycles, and NO_CHANGE says how to find the
fix; demos quote the failing check and the function it calls; `trace_fix` reads the test first; new
**`c_pixel`** family (RGB565-style pack/unpack from "bits a..b"); self-play second pass and cap.

| Checkpoint | Score | Solved | Held-out |
|---|---|---|---|
| baseline (round 2 final) | 0.847 | 149 | 0.625 |
| step 1200 | 0.801 | 141 | 0.542 |
| **step 5800** | **0.915** | **161** | **0.688** |
| final | 0.898 | 158 | 0.625 |

`c_pixel` 0/8 → 8/8 even though self-play solved only 5/96 of it — the demos carried it. `c_bitfield`
fix 6 → 9/12, but **implement still 0/12**. Early checkpoints were *worse* than the start; the gain
came late in the epoch.

## Round 4

Demos-v4 added a worked derivation from the bit layout to `c_pixel` implement demos (cards C-1, C-2).

| Checkpoint | Score | Held-out |
|---|---|---|
| **baseline (round 3 best, kept)** | **0.915** | **0.688** |
| step 1200 | 0.659 | 0.313 |
| step 4800 | 0.892 | 0.625 |
| final | 0.886 | 0.604 |

Nothing beat the start; `pick` then lacked a baseline rule and copied step 4800. Corrected by hand,
and `pick --baseline` added. Self-play solved 766/768: no new signal.

### Diagnosis of `c_bitfield` implement (11-21)

All 12 eval tasks, every reply saved:

- **No pack masks the value** in any of the 12 ("values wider than their field are masked").
- Shift by the field's top bit in 5/12; invented macros in 2/12; wrong unpack mask width in 5/12.
- After failing, no reply works from expected vs actual; 4/12 propose `X` should be `X`; none re-reads
  the file after an edit, so it re-sends an edit already made.
- Cause: every demo had **one** bug fixed in **one** edit; the recover reply named the line with no working.

## Round 5 (11-21 → 11-23)

Built from the diagnosis (cards C-6, C-7, C-8):

- **Worked fix replies** — expected vs actual, and for integers both in hex with the differing bits:
  "In hex it expects 0x0010 and gets 0x0210: bit 9 is set, should be 0."
- **Two-bug demos** (`recover2`, `fix2`) that re-read the file before the second fix; the first fix is
  the one that clears the failing check (tried in a scratch workspace).
- **`fix2` tasks in self-play**, with the second pass and cap per (family, kind).
- **New families** `c_debounce` (button debouncer, polarity and stable count) and `intervals`
  (merge/total/gaps with a touching policy).
- Demos-v5: 1,080 episodes, 6,606 rows.

Baseline (round 3's best on the new 192-task eval): **161/192 = 0.839**, held-out 0.688,
`c_debounce` 0/8, `intervals` 0/8, `c_bitfield` 9/24.

Self-play first pass: implement and one-bug fix ~100 % on the 16 older families; two-bug fix about half
(hardest `grid_path` 12/83 attempts); new families nearly unsolved (`c_debounce` fix 11/88,
`intervals` fix 7/83, all else 0) — so they will be learned from demos. A laptop reboot (Windows
Update, 11-21 07:04) killed the first attempt; it was restarted at 10:50.

**Result.** Pick: step 9600, **0.9115 (175/192)**, held-out 0.667, against the re-scored baseline 0.839.

| checkpoint | score | solved | held-out |
|---|---|---|---|
| baseline (round 3 best) | 0.839 | 161 | 0.688 |
| step 2400 | 0.370 | 71 | 0.229 |
| step 7200 | 0.885 | 170 | 0.646 |
| **step 9600** | **0.9115** | **175** | **0.667** |
| final | 0.859 | 165 | 0.500 |

- `c_debounce` 0 → 8/8 and `intervals` 0 → 8/8; `kalman_1d` 24/24 throughout.
- **`c_bitfield` implement 0/12 at every checkpoint** (fifth round). The first write now masks, but
  shifts are wrong and fields overlap; then edits cycle until stopped. `c_bitfield` fix: 9/12
  (baseline) → 8/12 (step 9600) → **0/12 at the final**.
- Unstable mid-epoch (step 2400: 110 repeated failures) and a sag at the end, as in round 4.

**Why `c_pixel` did not transfer:** its layouts are 9 fixed pixel formats, packed tight and listed
from the top — learnable by heart. `c_bitfield` draws a new layout every time (20 in 20 seeds), with
gaps. Nothing in training showed "shift by the low bit, mask with 2^width − 1" on varied layouts.

## After round 5 (11-23)

| Card | What | State |
|---|---|---|
| C-3 | `c_header`: get/set accessors on a 16/32-bit word, random layouts with gaps, given as "starts at bit L, W bits wide" — never `c_bitfield`'s wording, names or pack/unpack API (a test guards it); worked derivations in demos | Built in `Pipeline_coder-c3`; 180 tasks validate |
| C-9 | Failed edits shown as a one-line description; a repeat of a failed action refused and re-asked (seeded sample). From *Feedback That Backfires* | Built, off by default; being measured on round 5's best |
| C-10 | Base-model bake-off: Qwen3.5-2B, MiniCPM5-2B, Phi-4-mini, Qwen3.5-4B, 2,000 samples each from scratch, same eval | Running (`scripts\bakeoff.ps1`) |
| C-11 | Preference pairs from self-play retries + a DPO stage in the shared core (`lab/core/dpo.py`) | Built in `Pipeline_coder-c3` |
| C-12 | Multi-turn GRPO with tiered rewards | Later |

C-3 and C-11 were built in a copy because the bake-off scores with the repo's live eval; they are
copied back when it ends. Background: [Research: small base models](../concepts/research-small-models.md).
