# Research: TRELLIS.2 and CADFusion

Read on 2026-11-22 to find improvement ideas for the [Forge copilot](../projects/forge-copilot.md).
The resulting task cards (F-9 to F-15) are in WSL `~/cad/docs/handoff/2026-11-23-research-cards.md`.

!!! note "The mismatch to keep in mind"
    TRELLIS.2 turns **an image into a mesh**. The copilot is a **language model that sends exact
    parametric operations** (`add_primitive`, `add_hole`, …). The model cannot be dropped into Forge;
    its *training and data methods* carry over.

## TRELLIS.2 — how it works

**Paper:** "TRELLIS.2: Native and Compact Structured Latents for 3D Generation", Xiang et al.,
Microsoft Research / Tsinghua / USTC, arXiv 2512.14692 (Dec 2025). MIT licence. Successor to
TRELLIS (arXiv 2412.01506, CVPR 2025).

### The shape representation: O-Voxel

A sparse voxel grid: only cells the surface passes through are stored. Each active cell holds:

| Field | Meaning |
|---|---|
| dual vertex `v` ∈ [0,1]³ | One surface point inside the cell |
| edge flags `δ` ∈ {0,1}³ | Whether the surface crosses the cell's x / y / z edge (one quad per crossed edge) |
| split weight `γ` | How each quad is split into two triangles |
| material `(c, m, r, α)` | Base colour, metallic, roughness, opacity |

This is **dual contouring** without a signed distance field: the vertex position comes from a
small least-squares fit (a QEF) to the mesh's own triangles, so **sharp edges and normal
discontinuities survive**, and open, non-manifold or enclosed surfaces need no "make it watertight"
step. Mesh → O-Voxel takes a few seconds on one CPU; O-Voxel → mesh takes tens of milliseconds.

### Compression: SC-VAE

A fully sparse-convolutional autoencoder (~800M parameters) shrinks the grid **16×** per axis:
a 1024³ textured asset becomes about **9.6K tokens** (512³: 2.2K). Two of them: one for shape,
one for material.

### Generation: three flow-matching transformers (~1.3B each, ~4B total)

```mermaid
flowchart LR
  I[Image<br/>DINOv3 features] --> S1[1 Sparse structure<br/>which voxels are occupied]
  S1 --> S2[2 Shape latents<br/>detail inside those voxels]
  S2 --> S3[3 Material latents]
  S3 --> D[Decode to mesh + PBR textures]
```

All three are rectified-flow transformers (the same family as Stable Diffusion 3), conditioned on
the image. **The layout is decided first, the detail second.**

### Training

| Item | Value |
|---|---|
| Data | ~800K assets (Objaverse-XL, ABO, HSSD, TexVerse) |
| Curation | **Assets with an estimated quality score below 4.5 thrown out** |
| Views | 16 renders per asset, random field of view (10–70°) and lighting |
| Curriculum | Low resolution first (512³), then high (1024³) |
| Optimiser | AdamW, lr 1e-4, classifier-free guidance by dropping the condition 10 % of the time |
| Hardware | 32 × H100 for the generators |

### Results and limits

- Beats TRELLIS, Hunyuan3D 2.1, Direct3D-S2 and others on CLIP/ULIP scores and in a user study
  (66.5 % preference).
- 512³ in ~3 s, 1024³ in ~17 s, 1536³ in ~60 s on an H100. **Needs ≥ 24 GB of GPU memory.**
- Accuracy bounded by voxel size; small holes sometimes; **no notion of dimensions, tolerances or
  CAD** — the paper never mentions CAD.

## CADFusion — the closer relative

**Paper:** "Text-to-CAD Generation Through Infusing Visual Feedback in Large Language Models",
Wang, Yuan, Sun, Bian (Microsoft Research Asia), ICML 2025, arXiv 2501.19054, code
`github.com/microsoft/CADFusion`.

An LLM writes CAD command sequences from text. Training **alternates** two stages:

1. **Sequential learning** — ordinary supervised fine-tuning on correct sequences.
2. **Visual feedback** — sequences are rendered; ones that render into better objects are preferred
   over worse ones (preference optimisation, as in DPO).

The argument: rendering is many-to-one — many sequences make the same part — so training only to
copy one exact sequence is limiting. That is what the copilot's hindsight rows (F-2) ran into.

## How it maps onto the copilot

| Idea | Our problem it speaks to | Card |
|---|---|---|
| Quality filter (score < 4.5 dropped) | 48 of 118 verified v19 runs are **not** the reference body | F-9 |
| No lossy conversion between shape and training target | Requirement checks pass the wrong part (`pillow_block` bored down Z) | F-10 (was F-7) |
| Layout first, detail second | Weak families fail on the model's own placement arithmetic | F-11 |
| 16 random views per asset | mm-vs-m unit errors; one wording per family | F-12 |
| Most training at mid difficulty | 0/32 families waste runs; 32/32 families teach little | F-13 |
| Low-resolution first | 21 h epochs at 3,584 tokens | F-14 |
| CADFusion preference stage | Pass/fail throws away "this run came closer" | F-15 |

Not adopted: running TRELLIS.2 itself (no 24 GB GPU here; the Proxmox box has no GPU) or an
image-to-mesh "photo import" in Forge (its meshes look right but are not dimensionally exact) —
parked as a possible product feature.

## How to use these ideas

1. Read the cards file; each card states its goal, why, what to check first, the steps, the tests,
   and what not to touch.
2. Data-only cards (F-9, F-12, F-13) can land any time no round is running.
3. Model-visible cards (F-10, F-11) change what the model sees: land them **between** sweeps and
   stamp the harness.
4. F-14 and F-15 are experiments that need a free GPU; judge them on the four-suite table.

## Sources

- TRELLIS.2 project page: <https://microsoft.github.io/TRELLIS.2>
- TRELLIS.2 paper: <https://arxiv.org/abs/2512.14692>
- TRELLIS.2-4B model card: <https://huggingface.co/microsoft/TRELLIS.2-4B>
- TRELLIS (v1): <https://arxiv.org/abs/2412.01506>
- CADFusion: <https://arxiv.org/abs/2501.19054>
- Related B-rep generators: BrepGen <https://arxiv.org/abs/2401.15563>, HoLa <https://arxiv.org/abs/2504.14257>
