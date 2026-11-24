# Timeline

All dates 2026. "Round" = one build → train → pick cycle.

## September

| Date | Event |
|---|---|
| 09-21 | **Pipeline_claude** built: one config-driven pipeline (pretrain → distill → GRPO → eval) reusing the two books' code. |
| 09-28 | Forge copilot data baseline `ft-v7b` built; the v7 dataset becomes the reference for later versions. |

## October

| Date | Event |
|---|---|
| 10-04 → 10-06 | Copilot v9 (NO_CHANGE lessons) and v10 "parts". Split-copilot experiment (separate part and assembly adapters). |
| 10-09 | Pipeline_claude: **GRPO round 1 gives +10.5 points on MATH500** (37.6 % → 48.1 %, p < 0.001); round 2 regresses (−9.3). |
| 10-14 → 10-17 | Copilot v11 baseline vs repair data; v12 (hole repair families) — not shipped; repair hints; v13 stopped; v14 harness (compact context, budgets, linear-attention LoRA targets). |
| 10-19 → 10-21 | v15 assembly adapter (fails: 30 % of rows silently over the length cap). Short ids fix; **v16 = one adapter for parts and assemblies**, best assembly score yet. |
| 10-23 → 10-26 | v17: ten real-geometry self-play families (ISO/DIN/NEMA parts). Forge gains face-seated primitives, unit guards. |
| 10-25 | **Assistant and coder pipelines** created as two private repos sharing `lab/core`. |
| 10-28 → 10-31 | **Coder round 1** (62 h, 2 epochs). Assistant v1 (2B). v1 merged to GGUF (Q4_K_M and Q8_0) and packaged as llama.cpp images for Proxmox (`davinci`, CT 100). |
| 10-31 | **The stop-token bug** found: the server never stopped at `<|im_end|>`. Fix alone: coder 0.552 → 0.768. |

## November

| Date | Event |
|---|---|
| 11-02 | **Coder round 2**: 0.881 (148/168). Recovery demos work; `c_bitfield` implement still 0. |
| 11-04 → 11-06 | **Coder round 3**: 0.915 (161/176). New `c_pixel` bit-layout family 0/8 → 8/8. Forge Sprint 1–3 (undo, harness stamp, approvals, direct editing). |
| 11-07 → 11-09 | Copilot v18 round. Assistant v1 re-scored with the stop fix. Handoff cards (F/K/A/C/R) written for a smaller model. |
| 11-10 → 11-19 | Forge product cards U-1…U-6, P-1…P-9, X-1…X-5 all built (enclosures, modal analysis, drawings, wiring…). |
| 11-13 → 11-15 | Copilot **v19 round: 44/53**, the best so far. |
| 11-19 | Coder round 4 launched; assistant judge switched to Claude Opus via the `ant` CLI. |
| 11-20 | **Coder round 4: no gain**; round 3's best kept. Assistant v2 (4B) trained. |
| 11-21 | `c_bitfield` diagnosed; two-bug demos, worked fixes, `fix2` self-play and two new families built. **Assistant v2 judge 7.0/10 vs v1 4.0/10.** v2 merged, quantized and deployed (CT 101). Laptop reboot kills round 5; restarted. Threads 8 → 4 on the server (+6 %). |
| 11-22 | Round 5 self-play second pass; this wiki written and deployed. |
| 11-23 | TRELLIS.2 and CADFusion read; copilot cards **F-9 to F-15 all built** (F-14/F-15 runs on hold). **Coder round 5: 0.9115 (175/192)**, best of any round; `c_bitfield` implement still 0/12. Research on small base models and agent failures → coder cards C-9 to C-12; C-3 built as `c_header`; C-11 (DPO) built; **base-model bake-off started** (Qwen3.5-2B/4B, MiniCPM5-2B, Phi-4-mini). Assistant eval timeout fixed. |
