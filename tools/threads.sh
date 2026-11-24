# usage: threads.sh bench | threads.sh set N
B=https://${PVE_HOST:?set PVE_HOST}:8006/api2/json; H="Authorization: PVEAPIToken=$PVE_TOKEN"
api() { curl -sk -H "$H" "$@"; }
wait_task() {
  for i in $(seq 1 60); do
    s=$(api "$B/nodes/server/tasks/$1/status" | python -c "import json,sys;d=json.load(sys.stdin)['data'];print(d['status'],d.get('exitstatus',''))")
    case "$s" in stopped*) echo "$s"; return;; esac; sleep 2
  done; echo timeout
}
upid() { python -c "import json,sys;print(json.load(sys.stdin)['data'])"; }

bench() {
  # warm-up, then 3 timed runs; greedy so every run generates the same tokens
  long=$(python -c "print('Summarise the following notes in three bullet points. ' + ' '.join(['The deploy pipeline merges the adapter, converts it to GGUF, quantizes it and swaps the model layer of the image.']*12))")
  for i in 0 1 2 3; do
    for p in "Explain how a hash map handles collisions." "$long"; do
      body=$(python -c "import json,sys;print(json.dumps({'messages':[{'role':'user','content':sys.argv[1]}],'max_tokens':128,'temperature':0,'cache_prompt':False}))" "$p")
      r=$(curl -s -m 300 http://${LLM_HOST:?set LLM_HOST}:8080/v1/chat/completions -H 'Content-Type: application/json' -d "$body" \
        | python -c "import json,sys;t=json.load(sys.stdin)['timings'];print(f\"prompt {t['prompt_n']:4} tok {t['prompt_per_second']:6.1f} tok/s   gen {t['predicted_n']:4} tok {t['predicted_per_second']:5.2f} tok/s\")")
      [ $i -gt 0 ] && echo "$r"
    done
  done
}

case "$1" in
  bench) api $B/nodes/server/lxc/101/config | python -c "import json,sys;print([e for e in json.load(sys.stdin)['data']['env'].split(chr(0)) if 'THREADS' in e])"; bench;;
  set)
    api $B/nodes/server/lxc/101/config | python -c "
import json,sys,urllib.parse
e=json.load(sys.stdin)['data']['env'].split(chr(0))
e=[('LLAMA_ARG_THREADS=$2' if x.startswith('LLAMA_ARG_THREADS=') else x) for x in e]
sys.stdout.write('env='+urllib.parse.quote(chr(0).join(e),safe=''))" > "$TEMP/env_body"
    api -X PUT "$B/nodes/server/lxc/101/config" --data-binary @"$TEMP/env_body" >/dev/null; rm -f "$TEMP/env_body"
    echo "shutdown: $(wait_task "$(api -X POST --data timeout=30 "$B/nodes/server/lxc/101/status/shutdown" | upid)")"
    echo "start: $(wait_task "$(api -X POST "$B/nodes/server/lxc/101/status/start" | upid)")"
    for i in $(seq 1 90); do curl -sf -m 3 http://${LLM_HOST:?set LLM_HOST}:8080/health >/dev/null && { echo healthy; break; }; sleep 2; done;;
esac
