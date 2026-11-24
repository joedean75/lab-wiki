cd ~/llama.cpp
M=/mnt/c/Users/<you>/Documents/Books/Pipeline_assistant/out/davinci-v2-Q4_K_M.gguf
LLAMA_ARG_REASONING=off build/bin/llama-server -m "$M" --host 127.0.0.1 --port 8181 -c 4096 --jinja -t 8 -ngl 0 > /tmp/davinci-v2-smoke.log 2>&1 &
PID=$!
for i in $(seq 1 120); do curl -sf http://127.0.0.1:8181/health >/dev/null && break; sleep 2; done
curl -s http://127.0.0.1:8181/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"In two sentences, what is a LoRA adapter?"}],"max_tokens":200,"temperature":0.7}' \
  | python3 -c "import json,sys;d=json.load(sys.stdin);c=d['choices'][0];print(c['finish_reason']);print(c['message']['content']);print(d['timings']['predicted_per_second'],'tok/s')"
kill $PID
