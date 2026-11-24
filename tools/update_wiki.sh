# Replace the running wiki container with one built from build/lab-wiki.tar.
#   bash tools/update_wiki.sh <new ct> <old ct> <tag>
# Uploads the image as local:vztmpl/lab-wiki-<tag>.tar, creates <new ct> with the old
# one's address, stops the old one, starts the new one and checks it answers. On success
# the old container and its template are destroyed; on failure the old one is restarted.
# Needs PVE_TOKEN. Run from the lab-wiki folder.
set -e
NEW=$1; OLD=$2; TAG=$3; IP=${WIKI_HOST:?set WIKI_HOST}
B=https://${PVE_HOST:?set PVE_HOST}:8006/api2/json; H="Authorization: PVEAPIToken=$PVE_TOKEN"
api() { curl -sk -H "$H" "$@"; }
upid() { python -c "import json,sys;print(json.load(sys.stdin)['data'])"; }
wait_task() {
  for i in $(seq 1 90); do
    s=$(api "$B/nodes/server/tasks/$1/status" | python -c "import json,sys;d=json.load(sys.stdin)['data'];print(d['status'],d.get('exitstatus',''))")
    case "$s" in stopped*) echo "$s"; return;; esac; sleep 2
  done; echo timeout
}
OLDTMPL=$(api $B/nodes/server/lxc/$OLD/config | python -c "import json,sys;print(json.load(sys.stdin)['data'].get('description',''))" | grep -o 'template=[^ ]*' | cut -d= -f2 || true)
FILE=build/lab-wiki-$TAG.tar
cp build/lab-wiki.tar "$FILE"
echo "upload: $(wait_task "$(api -F content=vztmpl -F "filename=@$FILE" "$B/nodes/server/storage/local/upload" | upid)")"
rm -f "$FILE"
echo "create $NEW: $(wait_task "$(api -X POST "$B/nodes/server/lxc" \
  --data-urlencode vmid=$NEW --data-urlencode hostname=wiki \
  --data-urlencode ostemplate=local:vztmpl/lab-wiki-$TAG.tar \
  --data-urlencode rootfs=local-lvm:1 --data-urlencode memory=256 --data-urlencode swap=256 --data-urlencode cores=1 \
  --data-urlencode unprivileged=1 --data-urlencode onboot=0 \
  --data-urlencode "net0=name=eth0,bridge=vmbr0,host-managed=1,ip=$IP/24,type=veth" \
  --data-urlencode "description=Lab wiki (MkDocs on static-web-server) template=local:vztmpl/lab-wiki-$TAG.tar" | upid)")"
echo "stop $OLD: $(wait_task "$(api -X POST --data timeout=20 "$B/nodes/server/lxc/$OLD/status/shutdown" | upid)")"
echo "start $NEW: $(wait_task "$(api -X POST "$B/nodes/server/lxc/$NEW/status/start" | upid)")"
ok=0
# The shell does the redirect, not curl: with MSYS_NO_PATHCONV=1 set, Windows curl gets
# "-o /dev/null" literally, fails to write it (exit 23) and the check always failed (2026-11-23).
for i in $(seq 1 30); do curl -sf -m 3 "http://$IP/" >/dev/null && { ok=1; break; }; sleep 2; done
if [ $ok = 1 ]; then
  api -X PUT --data onboot=1 "$B/nodes/server/lxc/$NEW/config" >/dev/null
  echo "destroy $OLD: $(wait_task "$(api -X DELETE "$B/nodes/server/lxc/$OLD" | upid)")"
  [ -n "$OLDTMPL" ] && api -X DELETE "$B/nodes/server/storage/local/content/$OLDTMPL" >/dev/null && echo "deleted $OLDTMPL"
  echo "OK: wiki is CT $NEW at http://$IP/"
else
  echo "FAILED: restoring $OLD"
  api -X POST "$B/nodes/server/lxc/$NEW/status/stop" >/dev/null; sleep 5
  echo "start $OLD: $(wait_task "$(api -X POST "$B/nodes/server/lxc/$OLD/status/start" | upid)")"
  exit 1
fi
