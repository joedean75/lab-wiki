import hashlib, json, sys, tarfile
t = tarfile.open(sys.argv[1])
names = set(t.getnames())
def blob(d):
    return t.extractfile("blobs/sha256/" + d.split(":")[1])
def check(d):
    h = hashlib.sha256()
    f = blob(d)
    for chunk in iter(lambda: f.read(1 << 22), b""):
        h.update(chunk)
    return h.hexdigest() == d.split(":")[1]
index = json.load(t.extractfile("index.json"))
m = index["manifests"][0]
assert check(m["digest"]), "manifest digest"
manifest = json.load(blob(m["digest"]))
assert check(manifest["config"]["digest"]), "config digest"
config = json.load(blob(manifest["config"]["digest"]))
for layer in manifest["layers"]:
    assert check(layer["digest"]), layer["digest"]
assert len(config["rootfs"]["diff_ids"]) == len(manifest["layers"])
print("ok:", len(manifest["layers"]), "layers;", "oci-layout" in names, config["history"][-1])
