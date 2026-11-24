# Upload build/lab-wiki.tar and run it as a new container.
#   bash tools/deploy_wiki.sh <ctid> <ip>        e.g. bash tools/deploy_wiki.sh 102 <wiki-host>
# Needs PVE_TOKEN in the environment. Run from the lab-wiki folder.
set -e
CT=$1; IP=$2
B=https://${PVE_HOST:?set PVE_HOST}:8006/api2/json; H="Authorization: PVEAPIToken=$PVE_TOKEN"
api() { curl -sk -H "$H" "$@"; }
upid() { python -c "import json,sys;print(json.load(sys.stdin)['data'])"; }
wait_task() {
  for i in $(seq 1 90); do
    s=$(api "$B/nodes/server/tasks/$1/status" | python -c "import json,sys;d=json.load(sys.stdin)['data'];print(d['status'],d.get('exitstatus',''))")
    case "$s" in stopped*) echo "$s"; return;; esac; sleep 2
  done; echo timeout
}

echo "upload: $(wait_task "$(api -F content=vztmpl -F "filename=@build/lab-wiki.tar" "$B/nodes/server/storage/local/upload" | upid)")"
echo "create: $(wait_task "$(api -X POST "$B/nodes/server/lxc" \
  --data-urlencode vmid=$CT --data-urlencode hostname=wiki \
  --data-urlencode ostemplate=local:vztmpl/lab-wiki.tar \
  --data-urlencode rootfs=local-lvm:1 --data-urlencode memory=256 --data-urlencode swap=256 --data-urlencode cores=1 \
  --data-urlencode unprivileged=1 --data-urlencode onboot=1 \
  --data-urlencode "net0=name=eth0,bridge=vmbr0,host-managed=1,ip=$IP/24,type=veth" \
  --data-urlencode "description=Lab wiki (MkDocs static site on static-web-server)" | upid)")"
api $B/nodes/server/lxc/$CT/config | python -c "import json,sys;d=json.load(sys.stdin)['data'];[print(' ',k,'=',repr(v)[:160]) for k,v in d.items() if k in ('entrypoint','env','net0','memory','onboot')]"
echo "start: $(wait_task "$(api -X POST "$B/nodes/server/lxc/$CT/status/start" | upid)")"
for i in $(seq 1 30); do curl -sf -m 3 -o /dev/null "http://$IP/" && { echo "serving http://$IP/"; break; }; sleep 2; done
