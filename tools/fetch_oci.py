"""Download a public Docker Hub image (linux/amd64) as an OCI archive, without Docker.

    python fetch_oci.py joseluisq/static-web-server:2 base.tar

Docker-format manifests and configs are rewritten with OCI media types; layer and
config bytes are unchanged, so their digests stay the same.
"""
import hashlib
import io
import json
import sys
import tarfile
import time
import urllib.request

ref, out = sys.argv[1], sys.argv[2]
repo, tag = ref.rsplit(":", 1)
if "/" not in repo:
    repo = "library/" + repo
REG = "https://registry-1.docker.io/v2/" + repo

token = json.load(urllib.request.urlopen(
    f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull"))["token"]
ACCEPT = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])


def get(path, accept=ACCEPT):
    req = urllib.request.Request(REG + path, headers={"Authorization": f"Bearer {token}", "Accept": accept})
    return urllib.request.urlopen(req).read()


top = json.loads(get(f"/manifests/{tag}"))
if "manifests" in top:
    entry = next(m for m in top["manifests"]
                 if m.get("platform", {}).get("os") == "linux" and m["platform"].get("architecture") == "amd64")
    manifest = json.loads(get(f"/manifests/{entry['digest']}"))
else:
    manifest = top

LAYER = "application/vnd.oci.image.layer.v1.tar+gzip"
blobs = {}
config_bytes = get(f"/blobs/{manifest['config']['digest']}", "*/*")
blobs[manifest["config"]["digest"]] = config_bytes
layers = []
for layer in manifest["layers"]:
    data = get(f"/blobs/{layer['digest']}", "*/*")
    assert "sha256:" + hashlib.sha256(data).hexdigest() == layer["digest"], layer["digest"]
    blobs[layer["digest"]] = data
    layers.append({"mediaType": LAYER, "digest": layer["digest"], "size": len(data)})

oci_manifest = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "config": {"mediaType": "application/vnd.oci.image.config.v1+json",
               "digest": manifest["config"]["digest"], "size": len(config_bytes)},
    "layers": layers,
}
mbytes = json.dumps(oci_manifest, separators=(",", ":")).encode()
mdigest = "sha256:" + hashlib.sha256(mbytes).hexdigest()
blobs[mdigest] = mbytes
index = {"schemaVersion": 2, "mediaType": "application/vnd.oci.image.index.v1+json",
         "manifests": [{"mediaType": "application/vnd.oci.image.manifest.v1+json", "digest": mdigest,
                        "size": len(mbytes), "platform": {"architecture": "amd64", "os": "linux"},
                        "annotations": {"org.opencontainers.image.ref.name": tag}}]}


def add(tar, name, data):
    info = tarfile.TarInfo(name)
    info.size, info.mtime = len(data), int(time.time())
    tar.addfile(info, io.BytesIO(data))


with tarfile.open(out, "w") as tar:
    add(tar, "oci-layout", b'{"imageLayoutVersion":"1.0.0"}')
    for digest, data in blobs.items():
        add(tar, "blobs/sha256/" + digest.split(":")[1], data)
    add(tar, "index.json", json.dumps(index).encode())
cfg = json.loads(config_bytes)
print(json.dumps({"out": out, "layers": len(layers), "config": cfg.get("config")}, indent=1))
