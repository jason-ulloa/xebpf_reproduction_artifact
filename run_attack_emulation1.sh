#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="${1:-xebpfexp}"; REPS="${2:-3}"; DURATION="${3:-120}"; RATE="${4:-4}"; KEY_PATH="${5:-}"
[ -n "$KEY_PATH" ] || { echo "Usage: $0 [user] [reps] [duration] [rate] /path/to/research.key"; exit 2; }
[ -r "$KEY_PATH" ] || { echo "ERROR: HMAC key is not readable: $KEY_PATH"; exit 1; }
UID_NUM="$(id -u "$USER_NAME")" || { echo "ERROR: user $USER_NAME does not exist"; exit 1; }
[ "$UID_NUM" -ne 0 ] || { echo "ERROR: do not use root"; exit 1; }
python3 "$SCRIPT_DIR/production_safety_gate.py" --user "$USER_NAME" --duration "$DURATION" --rate "$RATE" --hmac-key-path "$KEY_PATH"
PROFILES=(ae-file-churn-v1 ae-process-chain-v1 ae-loopback-beacon-v1 ae-staging-v1 ae-mixed-burst-v1)
ATTACK_IDS=(file-churn-emulation process-chain-emulation loopback-beacon-emulation staging-emulation mixed-burst-emulation)
mkdir -p /var/lib/ebpf-research; chmod 700 /var/lib/ebpf-research
python3 - /var/lib/ebpf-research/ATTACK_EMULATION1_PROTOCOL.json "$REPS" "$DURATION" "$RATE" <<'PY2'
import json,platform,subprocess,sys,time
out,reps,duration,rate=sys.argv[1:]
def cmd(a):
 try:
  p=subprocess.Popen(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True); so,se=p.communicate(timeout=10); return (so or se or '').strip()
 except Exception:return 'unknown'
obj={'protocol':'ATTACK-EMULATION-1','safety_class':'non-destructive behavioral emulation','collector_schema_frozen':'xebpf-1.3.2','workload_suite':'xebpf-attack-emulation1-v1','repetitions_per_profile':int(reps),'duration_seconds':int(duration),'base_rate_per_second':int(rate),'network_scope':'127.0.0.1 only','filesystem_scope':'isolated /tmp/xebpf-ae1-* only','privilege_policy':'workload runs as non-root xebpfexp','python_version':cmd(['python3','--version']),'bpftrace_version':cmd(['bpftrace','--version']),'kernel_release':platform.release(),'architecture':platform.machine(),'created_at_epoch':time.time(),'profiles':['ae-file-churn-v1','ae-process-chain-v1','ae-loopback-beacon-v1','ae-staging-v1','ae-mixed-burst-v1']}
open(out,'w').write(json.dumps(obj,indent=2)+'\n')
PY2
chmod 600 /var/lib/ebpf-research/ATTACK_EMULATION1_PROTOCOL.json
CPID=""
cleanup(){ if [ -n "${CPID:-}" ] && kill -0 "$CPID" 2>/dev/null; then kill -TERM "$CPID" 2>/dev/null || true; sleep 1; kill -KILL "$CPID" 2>/dev/null || true; wait "$CPID" 2>/dev/null || true; fi; CPID=""; }
trap cleanup EXIT INT TERM
for idx in "${!PROFILES[@]}"; do
 PROFILE="${PROFILES[$idx]}"; ATTACK="${ATTACK_IDS[$idx]}"; SHORT="${PROFILE#ae-}"; SHORT="${SHORT%-v1}"; SHORT="$(echo "$SHORT"|tr '[:lower:]-' '[:upper:]_')"
 for i in $(seq 1 "$REPS"); do
  EXP="AE1-${SHORT}-R$(printf '%02d' "$i")"
  echo "=== $EXP workload=$PROFILE attack_id=$ATTACK uid=$UID_NUM duration=${DURATION}s rate=${RATE}/s ==="
  python3 "$SCRIPT_DIR/collector.py" --experiment-id "$EXP" --workload-id "$PROFILE" --label malicious --attack-id "$ATTACK" --target-uid "$UID_NUM" --duration "$((DURATION+8))" --hmac-key-path "$KEY_PATH" & CPID=$!
  sleep 4
  if command -v runuser >/dev/null 2>&1; then
    runuser -u "$USER_NAME" -- python3 "$SCRIPT_DIR/attack_emulation_workloads.py" --profile "$PROFILE" --duration "$DURATION" --rate "$RATE"
  else
    su -s /bin/sh "$USER_NAME" -c "python3 '$SCRIPT_DIR/attack_emulation_workloads.py' --profile '$PROFILE' --duration '$DURATION' --rate '$RATE'"
  fi
  wait "$CPID"; CPID=""; sleep 2
 done
done
trap - EXIT INT TERM
echo "ATTACK-EMULATION-1 complete: ${#PROFILES[@]} profiles x $REPS repetitions"
