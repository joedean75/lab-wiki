"""Copy an OCI archive, replacing its last layer (models/model.gguf) with a new GGUF.

    python swap_model_layer.py BASE.tar NEW.gguf OUT.tar NAME
"""
import gzip
import hashlib
import io
import json
import shutil
import sys
import tarfile
import tempfile
import time
from pathlib import Path

base, gguf, out, name = sys.argv[1:5]
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
work = Path(tempfile.mkdtemp(dir=Path(out).parent))
try:
    src = tarfile.open(base)
    index = json.load(src.extractfile("index.json"))
    manifest_digest = index["manifests"][0]["digest"].split(":")[1]
    manifest = json.load(src.extractfile(f"blobs/sha256/{manifest_digest}"))
    config_digest = manifest["config"]["digest"].split(":")[1]
    config = json.load(src.extractfile(f"blobs/sha256/{config_digest}"))
    old_layer = manifest["layers"][-1]["digest"].split(":")[1]

    # New layer: models/ + models/model.gguf, uncompressed digest for diff_ids,
    # gzip digest for the manifest.
    raw, gz = work / "layer.tar", work / "layer.tar.gz"
    mtime = int(time.time())
    with tarfile.open(raw, "w", format=tarfile.PAX_FORMAT) as layer:
        d = tarfile.TarInfo("models/"); d.type = tarfile.DIRTYPE; d.mode = 0o755; d.mtime = mtime
        layer.addfile(d)
        f = tarfile.TarInfo("models/model.gguf"); f.size = Path(gguf).stat().st_size; f.mode = 0o644; f.mtime = mtime
        with open(gguf, "rb") as fh:
            layer.addfile(f, fh)
    def sha(path):
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 22), b""):
                h.update(chunk)
        return h.hexdigest()
    diff_id = sha(raw)
    with open(raw, "rb") as fi, gzip.GzipFile(gz, "wb", compresslevel=1, mtime=0) as fo:
        shutil.copyfileobj(fi, fo, 1 << 22)
    raw.unlink()
    layer_digest, layer_size = sha(gz), gz.stat().st_size

    config["rootfs"]["diff_ids"][-1] = f"sha256:{diff_id}"
    config["history"][-1] = {"created_by": f"add {name} model layer", "created": now}
    config["created"] = now
    config_bytes = json.dumps(config, separators=(",", ":")).encode()
    config_digest_new = hashlib.sha256(config_bytes).hexdigest()
    manifest["config"] = {**manifest["config"], "digest": f"sha256:{config_digest_new}", "size": len(config_bytes)}
    manifest["layers"][-1] = {**manifest["layers"][-1], "digest": f"sha256:{layer_digest}", "size": layer_size}
    manifest_bytes = json.dumps(manifest, separators=(",", ":")).encode()
    manifest_digest_new = hashlib.sha256(manifest_bytes).hexdigest()
    index["manifests"][0].update(digest=f"sha256:{manifest_digest_new}", size=len(manifest_bytes))
    index["manifests"][0].setdefault("annotations", {})["org.opencontainers.image.ref.name"] = name
    index_bytes = json.dumps(index).encode()

    def add_bytes(tar, path, data):
        info = tarfile.TarInfo(path); info.size = len(data); info.mtime = int(time.time())
        tar.addfile(info, io.BytesIO(data))

    skip = {f"blobs/sha256/{x}" for x in (manifest_digest, config_digest, old_layer)} | {"index.json"}
    with tarfile.open(out, "w") as dst:
        for member in src.getmembers():
            if member.name in skip:
                continue
            dst.addfile(member, src.extractfile(member) if member.isfile() else None)
        dst.add(gz, f"blobs/sha256/{layer_digest}")
        add_bytes(dst, f"blobs/sha256/{config_digest_new}", config_bytes)
        add_bytes(dst, f"blobs/sha256/{manifest_digest_new}", manifest_bytes)
        add_bytes(dst, "index.json", index_bytes)
    print(json.dumps({"out": out, "layer": layer_digest, "layer_size": layer_size, "diff_id": diff_id,
                      "manifest": manifest_digest_new}))
finally:
    shutil.rmtree(work, ignore_errors=True)
