"""Append a layer holding a local directory to an OCI archive.

    python add_layer.py BASE.tar SITE_DIR /public OUT.tar NAME

Every file under SITE_DIR lands under the given path in the image (mode 0644,
directories 0755, owned by root). The rest of the image is copied unchanged.
"""
import gzip
import hashlib
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
from pathlib import Path

base, site, prefix, out, name = sys.argv[1:6]
prefix = prefix.strip("/")
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
work = Path(tempfile.mkdtemp(dir=Path(out).resolve().parent))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


try:
    src = tarfile.open(base)
    index = json.load(src.extractfile("index.json"))
    mdig = index["manifests"][0]["digest"].split(":")[1]
    manifest = json.load(src.extractfile(f"blobs/sha256/{mdig}"))
    cdig = manifest["config"]["digest"].split(":")[1]
    config = json.load(src.extractfile(f"blobs/sha256/{cdig}"))

    raw, gz = work / "layer.tar", work / "layer.tar.gz"
    mtime = int(time.time())
    with tarfile.open(raw, "w", format=tarfile.PAX_FORMAT) as layer:
        parts = prefix.split("/")
        for i in range(len(parts)):
            d = tarfile.TarInfo("/".join(parts[:i + 1]) + "/")
            d.type, d.mode, d.mtime = tarfile.DIRTYPE, 0o755, mtime
            layer.addfile(d)
        for root, dirs, files in os.walk(site):
            dirs.sort()
            rel = os.path.relpath(root, site).replace(os.sep, "/")
            if rel != ".":
                d = tarfile.TarInfo(f"{prefix}/{rel}/")
                d.type, d.mode, d.mtime = tarfile.DIRTYPE, 0o755, mtime
                layer.addfile(d)
            for f in sorted(files):
                p = os.path.join(root, f)
                arc = f"{prefix}/{f}" if rel == "." else f"{prefix}/{rel}/{f}"
                info = tarfile.TarInfo(arc)
                info.size, info.mode, info.mtime = os.path.getsize(p), 0o644, mtime
                with open(p, "rb") as fh:
                    layer.addfile(info, fh)
    diff_id = sha(raw)
    with open(raw, "rb") as fi, gzip.GzipFile(gz, "wb", compresslevel=6, mtime=0) as fo:
        shutil.copyfileobj(fi, fo, 1 << 22)
    ldig, lsize = sha(gz), gz.stat().st_size

    config.setdefault("rootfs", {"type": "layers", "diff_ids": []})["diff_ids"].append(f"sha256:{diff_id}")
    config.setdefault("history", []).append({"created_by": f"add {name} layer at /{prefix}", "created": now})
    config["created"] = now
    cbytes = json.dumps(config, separators=(",", ":")).encode()
    cnew = hashlib.sha256(cbytes).hexdigest()
    manifest["config"] = {**manifest["config"], "digest": f"sha256:{cnew}", "size": len(cbytes)}
    manifest["layers"].append({"mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                               "digest": f"sha256:{ldig}", "size": lsize})
    mbytes = json.dumps(manifest, separators=(",", ":")).encode()
    mnew = hashlib.sha256(mbytes).hexdigest()
    index["manifests"][0].update(digest=f"sha256:{mnew}", size=len(mbytes))
    index["manifests"][0].setdefault("annotations", {})["org.opencontainers.image.ref.name"] = name

    def add_bytes(tar, path, data):
        info = tarfile.TarInfo(path)
        info.size, info.mtime = len(data), int(time.time())
        tar.addfile(info, io.BytesIO(data))

    skip = {f"blobs/sha256/{mdig}", f"blobs/sha256/{cdig}", "index.json"}
    with tarfile.open(out, "w") as dst:
        for member in src.getmembers():
            if member.name not in skip:
                dst.addfile(member, src.extractfile(member) if member.isfile() else None)
        dst.add(gz, f"blobs/sha256/{ldig}")
        add_bytes(dst, f"blobs/sha256/{cnew}", cbytes)
        add_bytes(dst, f"blobs/sha256/{mnew}", mbytes)
        add_bytes(dst, "index.json", json.dumps(index).encode())
    print(json.dumps({"out": out, "layer": ldig, "layer_size": lsize, "manifest": mnew}))
finally:
    shutil.rmtree(work, ignore_errors=True)
