#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="${1:-xebpfexp}"
REPS="${2:-5}"
DURATION="${3:-120}"
RATE="${4:-4}"
KEY_PATH="${5:-}"
[ -n "$KEY_PATH" ] || { echo "Usage: $0 [user] [reps] [duration] [rate] /path/to/research.key"; exit 2; }
[ -r "$KEY_PATH" ] || { echo "ERROR: HMAC key is not readable: $KEY_PATH"; exit 1; }
UID_NUM="$(id -u "$USER_NAME")" || { echo "ERROR: user $USER_NAME does not exist"; exit 1; }
if [ "$UID_NUM" -eq 0 ]; then echo "ERROR: do not use root as workload user"; exit 1; fi

CPID=""
cleanup_collector() {
  if [ -n "${CPID:-}" ] && kill -0 "$CPID" 2>/dev/null; then
    kill -TERM "$CPID" 2>/dev/null || true
    sleep 1
    kill -KILL "$CPID" 2>/dev/null || true
    wait "$CPID" 2>/dev/null || true
  fi
  CPID=""
}
trap cleanup_collector EXIT INT TERM

for i in $(seq 1 "$REPS"); do
  EXP="CAL1-R$(printf '%02d' "$i")"
  echo "=== $EXP uid=$UID_NUM duration=${DURATION}s rate=${RATE}/s ==="
  python3 "$SCRIPT_DIR/collector.py" \
    --experiment-id "$EXP" \
    --workload-id controlled-mixed-v1 \
    --label benign \
    --attack-id none \
    --target-uid "$UID_NUM" \
    --duration "$((DURATION + 8))" \
    --hmac-key-path "$KEY_PATH" &
  CPID=$!
  sleep 4
  if command -v runuser >/dev/null 2>&1; then
    runuser -u "$USER_NAME" -- python3 "$SCRIPT_DIR/controlled_workload.py" --duration "$DURATION" --rate "$RATE"
  else
    su -s /bin/sh "$USER_NAME" -c "python3 '$SCRIPT_DIR/controlled_workload.py' --duration '$DURATION' --rate '$RATE'"
  fi
  wait "$CPID"
  CPID=""
  sleep 4
done

trap - EXIT INT TERM
