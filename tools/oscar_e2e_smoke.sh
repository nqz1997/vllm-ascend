#!/usr/bin/env bash
# OSCAR INT2 three-tier end-to-end smoke (customer e2e).
# Runs against the current PR-stack baseline: MODE B three-tier middle,
# C++ quantizer write path, rotation assets, R218ID identity banner.
set -euo pipefail

: "${MODEL:?set MODEL to the model directory}"
: "${K_ROT:?set K_ROT to the K rotation asset path}"
: "${V_ROT:?set V_ROT to the V rotation asset path}"
PORT="${PORT:-8000}"
LOG="${LOG:-/tmp/oscar_e2e_smoke_serve.log}"
MML="${MML:-4096}"

# --- product posture (matches the acceptance baseline) ---
export R109_THREETIER_MIDDLE=1
export R110_THREETIER_MIDDLE=1
export R113_QUANT_CPP=1
export R113_QUANT_SYNC=1
export R113_SCATTER_CPP=1
export SGLANG_OSCAR_K_ROTATION_PATH="$K_ROT"
export SGLANG_OSCAR_V_ROTATION_PATH="$V_ROT"
export R109_TT_PREFIX="${R109_TT_PREFIX:-128}"
export R109_TT_RECENT="${R109_TT_RECENT:-896}"

python3 -m vllm.entrypoints.cli.main serve "$MODEL" \
  --served-model-name q --port "$PORT" --max-model-len "$MML" \
  --max-num-seqs 8 >"$LOG" 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT

for i in $(seq 1 120); do
  curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1 && break
  sleep 5
done
curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null

# --- identity gate: the stack must announce itself ---
grep -q '\[R218ID\]' "$LOG" || { echo "FAIL: no [R218ID] identity banner in $LOG"; exit 2; }

ask() {
  curl -s "http://127.0.0.1:$PORT/v1/completions" \
    -H 'Content-Type: application/json' \
    -d "{\"model\":\"q\",\"prompt\":$(python3 -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$1"),\"max_tokens\":64,\"temperature\":0}" \
    | python3 -c 'import json,sys;print(json.load(sys.stdin)["choices"][0]["text"])'
}

A1=$(ask "The capital of France is")
A2=$(ask "123 + 456 = ")
A3=$(ask "Repeat after me: OSCAR-INT2-SMOKE")
for v in "$A1" "$A2" "$A3"; do
  [ "${#v}" -ge 1 ] || { echo "FAIL: empty answer"; exit 3; }
done
case "$A2" in *579*) ;; *) echo "WARN: arithmetic answer unexpected: $A2";; esac
echo "SMOKE PASS: identity banner present, 3/3 non-empty answers"
echo "A1=${A1:0:80}"
echo "A2=${A2:0:80}"
echo "A3=${A3:0:80}"
