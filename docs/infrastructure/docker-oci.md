# Docker and OCI images

## How it works

### Containers

A **container** is a process (or a few) running with its own filesystem, network and process view,
sharing the host's Linux kernel. Unlike a virtual machine there is no second kernel, so it starts in
a second and costs little memory.

### Images and layers

A container starts from an **image**: a read-only filesystem plus settings (entrypoint, environment,
ports, working directory). An image is a **stack of layers**; each layer is a tar archive of files
added or changed. Layers are shared and cached, so a base layer (say, Ubuntu) is stored once.

### OCI: the standard format

The **Open Container Initiative** format is what Docker, Podman and Proxmox all understand. An OCI
image on disk (an "OCI layout", often tarred into one `.tar`) looks like:

```text
oci-layout                      {"imageLayoutVersion": "1.0.0"}
index.json                      → points to the manifest (by sha256)
blobs/sha256/<manifest>         → lists the config blob and each layer blob
blobs/sha256/<config>           → entrypoint, env, history, and rootfs.diff_ids
blobs/sha256/<layer-1>.tar.gz   → files
...
blobs/sha256/<layer-N>.tar.gz
```

Everything is **content-addressed**: a blob's name is the SHA-256 of its bytes. Two hashes matter
per layer:

- the **digest** in the manifest = SHA-256 of the *compressed* (`.tar.gz`) blob;
- the **diff_id** in the config = SHA-256 of the *uncompressed* tar.

Change one byte anywhere and every hash above it changes: layer → config → manifest → index.

### Dockerfile and compose

- A **Dockerfile** describes how to build an image, one layer per instruction; **multi-stage** builds
  compile in one image and copy only the results into a small final one (Forge does this).
- **docker compose** runs several containers together from `docker-compose.yml` (Forge: Postgres +
  backend + frontend, with volumes for live code reload and a named volume for the database).

## How it is implemented here

### Forge

| File | What |
|---|---|
| `~/cad/Dockerfile` | Stage 1 `node:22-alpine` builds the SPA; stage 2 `rust:1-slim-bookworm` builds the SDF wheel with maturin; stage 3 `python:3.12-slim` installs the backend and serves both. |
| `~/cad/docker-compose.yml` | `db` (postgres:16-alpine, healthcheck), `backend` (uvicorn `--reload` on 8000), `frontend` (Vite on 5173). |
| `~/cad/DEPLOY.md` | Hosting options, required production config, security posture, scaling, rollback. |

!!! warning "House rule"
    Don't restart Docker on the laptop.

### The `davinci` model images (no Docker needed)

The model server image is built **without Docker**, by editing an OCI archive directly:

1. Start from an existing OCI tar whose last layer holds `models/model.gguf` — the official llama.cpp
   server image (build b11960) plus that layer.
2. A Python script (`swap_model_layer.py`) writes a new layer tar containing `models/` and the new
   `models/model.gguf`, hashes it uncompressed (new **diff_id**), gzips it and hashes that (new
   **digest**).
3. It replaces the last diff_id and history entry in the **config**, the last layer entry in the
   **manifest**, re-hashes config and manifest, and points **index.json** at the new manifest.
4. It copies every other blob unchanged into the new tar.
5. `verify_oci.py` re-hashes every blob and checks counts before upload.

The image's settings (from the config): entrypoint `/app/llama-server`, working dir `/app`,
environment `LLAMA_ARG_MODEL=/models/model.gguf`, `LLAMA_ARG_HOST=0.0.0.0`, `LLAMA_ARG_PORT=8080`,
`LLAMA_ARG_CTX_SIZE=8192`, `LLAMA_ARG_JINJA=1`, `LLAMA_ARG_THREADS`, `LLAMA_ARG_ALIAS=davinci`.

## How to use it

Inspect an OCI tar without Docker:

```bash
tar tvf davinci-v2.tar                                  # list blobs
tar xOf davinci-v2.tar index.json                       # the index
tar xOf davinci-v2.tar blobs/sha256/<manifest-digest>   # the manifest
tar xOf davinci-v2.tar blobs/sha256/<config-digest> | python3 -m json.tool
```

Rebuild with a new model:

```powershell
& $py swap_model_layer.py davinci-llamacpp.tar davinci-v3-Q4_K_M.gguf davinci-v3.tar davinci-v3
& $py verify_oci.py davinci-v3.tar          # "ok: 6 layers; True ..."
```

The scripts are kept with this wiki's source in `lab-wiki\tools\`. Then follow the
[deploy runbook](deploy-model.md).
