# Forge CAD

**Repo:** WSL `~/cad` → a private GitHub repo. Working branch **`v18-prep`** (training history
on `training-v9-v17`; `main` untouched).

## How it works

Forge is an **agentic, browser-based CAD suite**, aimed at RC, drone and robotics work: describe a
part in plain language, refine it parametrically, check and optimise it, quote and make it — with
every step equally available to AI agents through an operation API.

### Two geometry kernels

| Kernel | Good at |
|---|---|
| **Exact B-rep** (OpenCascade) | Selectable faces and edges, exact dimensions, analytic STEP export. Tried first. |
| **SDF** (signed distance fields, marching cubes; native Rust sampler on the hot path) | What implicit geometry does better: voxel fields from the optimiser, mesh imports, smooth blends. |

The kernel tries exact first and records which one ran.

### What it does

| Area | Highlights |
|---|---|
| Text-to-CAD | Prompt → editable feature tree with validation and self-repair (needs an LLM). |
| Image-to-CAD | Vision model, or silhouette tracing into an extruded profile with holes. |
| **Copilot** | An agent loop that plans and runs multi-step edits through the same operation API. See [Forge copilot training](forge-copilot.md). |
| Parametric modelling | Feature tree (primitives, booleans, fillet/chamfer/shell/hole/pattern, sketches, revolve/mirror/sweep/loft), parameters, configurations, version history, `undo_last`. |
| Sheet metal | Flanges with real bends; flat-pattern unfold to DXF. |
| Materials | 43 grades in 12 categories, driving mass, simulation, DFM and quotes. |
| Analysis | Linear-static FEA, **modal analysis**, DFM per process, design specs, flight estimates. |
| Generative design | 3D SIMP topology optimisation folded back into the tree as an editable feature. |
| Import | STEP/IGES exact; STL/OBJ/PLY/GLB voxelised. |
| Make | CNC 2.5D toolpaths, drilling G-code, laser/plasma/waterjet profiles, slicer and printing, instant quotes. |
| Drawings | True hidden-line drawings (isometric, details, exploded assemblies), a drawn stroke font. |
| Assemblies | Mates, interference, exploded views, **enclosure kits** (snap fits checked against material strain, gaskets, vents, standoffs), **wiring harnesses** with a connector library. |

## How it is implemented

Two processes, one API: a **React/Vite** SPA talks only to a **FastAPI** backend under `/api/*`
(Vite proxies to `:8000` in development; production serves the built SPA from FastAPI).

```text
~/cad/
├── backend/
│   ├── main.py                FastAPI app
│   ├── app/services/          one module per capability (copilot.py, cad_operations/, fea.py,
│   │                          design_spec.py, context_compact.py, wiring.py, enclosure.py, ...)
│   ├── app/cad_kernel/        B-rep and SDF kernels
│   ├── datasets/              copilot training data builders (build, corpus, self_play, repairs, mix...)
│   ├── evals/                 copilot evals (agent, tasks, assembly_spec, geometry IoU/Chamfer)
│   ├── training/              trainer, server and round scripts (staged to Pipeline_copilot)
│   ├── native/forge_sdf/      Rust SDF sampler (maturin)
│   └── tests/                 ~2,500 pytest tests
├── frontend/                  React + TypeScript + Vite
├── docs/                      ARCHITECTURE, AGENT-PLATFORM, handoff/, reviews/, roadmaps/
├── CLAUDE.md                  the working reference (authoritative)
├── Dockerfile                 3-stage production image
└── docker-compose.yml         db + backend + frontend for development
```

Storage: SQLite by default, PostgreSQL via `DATABASE_URL`. Configuration: `app/settings.py` lists
every `FORGE_*` variable (for example `FORGE_COPILOT_CONTEXT=compact`, `FORGE_REPAIR_HINTS=1`,
`FORGE_SHARED_WORKER_STATE` — off by default).

### Docker

The production `Dockerfile` has three stages: build the SPA (`node:22-alpine`), build the Rust SDF
wheel (`rust:1-slim-bookworm` + maturin), then a `python:3.12-slim` runtime that serves both.
`docker-compose.yml` runs Postgres 16, the backend with live reload on 8000, and the Vite dev server
on 5173. See [Docker and OCI images](../infrastructure/docker-oci.md).

## How to use it

```bash
cd ~/cad
./start.sh                       # backend :8000 + frontend :5173 (dev)
# or with Docker:
docker compose up                # Postgres + backend + frontend

# tests (never two sessions at once — they share a database)
cd backend && .venv/bin/python -m pytest -q

# frontend build (use WSL's node; Windows node can't load the linux bindings)
cd frontend && /home/<you>/.nvm/versions/node/v22.23.3/bin/node node_modules/vite/bin/vite.js build
```

UI checks: Playwright against a throwaway uvicorn on :8000 serving `frontend/dist`; sign up via
`POST /api/auth/signup` and put the token in `localStorage['forge_token']`.

## Product cards (built 11-10 → 11-19)

Ease of use U-1…U-6, features P-1…P-9, capabilities X-1…X-5 — all built, uncommitted on `v18-prep`.
The card file `~/cad/docs/handoff/2026-11-10-product-improvements.md` has an index of statuses and an
"As built" note per card. Owner decisions: shared worker state stays off; P-4 font drawn for the
project; P-6 true line drawings; P-9 connector library + harness drawings.

!!! note "Copilot coverage"
    New model-visible operations (`add_enclosure_half`, `modal_analysis`, `flight_estimate`) are not
    in the copilot's training data until a self-play sweep records them.
