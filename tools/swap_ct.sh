B=https://${PVE_HOST:?set PVE_HOST}:8006/api2/json; H="Authorization: PVEAPIToken=$PVE_TOKEN"
api() { curl -sk -H "$H" "$@"; }
wait_task() {
  for i in $(seq 1 60); do
    s=$(api "$B/nodes/server/tasks/$1/status" | python -c "import json,sys;d=json.load(sys.stdin)['data'];print(d['status'],d.get('exitstatus',''))")
    case "$s" in stopped*) echo "$s"; return;; esac; sleep 2
  done; echo "timeout"
}
upid() { python -c "import json,sys;print(json.load(sys.stdin)['data'])"; }
status() { api "$B/nodes/server/lxc/$1/status/current" | python -c "import json,sys;print(json.load(sys.stdin)['data']['status'])"; }

echo "stop 100: $(wait_task "$(api -X POST --data timeout=30 "$B/nodes/server/lxc/100/status/shutdown" | upid)") -> $(status 100)"
echo "start 101: $(wait_task "$(api -X POST "$B/nodes/server/lxc/101/status/start" | upid)") -> $(status 101)"
ok=0
for i in $(seq 1 90); do curl -sf -m 3 http://${LLM_HOST:?set LLM_HOST}:8080/health >/dev/null && { ok=1; break; }; sleep 2; done
if [ $ok = 1 ]; then
  curl -s -m 10 http://${LLM_HOST:?set LLM_HOST}:8080/props | python -c "import json,sys;d=json.load(sys.stdin);print('build',d.get('build_info'),'n_params',d.get('model_path'))"
  curl -s -m 10 http://${LLM_HOST:?set LLM_HOST}:8080/v1/models | python -c "import json,sys;m=json.load(sys.stdin)['data'][0]['meta'];print('n_params',m['n_params'],'size',m['size'],m['ftype'])"
  curl -s -m 180 http://${LLM_HOST:?set LLM_HOST}:8080/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"messages":[{"role":"user","content":"In two sentences, what is a LoRA adapter?"}],"max_tokens":200}' \
    | python -c "import json,sys;d=json.load(sys.stdin);c=d['choices'][0];print(c['finish_reason']);print(c['message']['content']);print(round(d['timings']['predicted_per_second'],1),'tok/s')" || ok=0
fi
if [ $ok = 1 ]; then
  api -X PUT --data onboot=1 "$B/nodes/server/lxc/101/config" >/dev/null
  api -X PUT --data onboot=0 "$B/nodes/server/lxc/100/config" >/dev/null
  echo "SWAPPED: 101 onboot=1, 100 onboot=0 (stopped, kept)"
else
  echo "FAILED: rolling back"
  api -X POST "$B/nodes/server/lxc/101/status/stop" >/dev/null; sleep 5
  echo "start 100: $(wait_task "$(api -X POST "$B/nodes/server/lxc/100/status/start" | upid)") -> $(status 100)"
fi
