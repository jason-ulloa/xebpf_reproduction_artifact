#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="${1:-xebpfexp}"
KEY_PATH="${2:-/opt/xebpf-secrets/research.key}"
RESULT_ROOT="${3:-/var/lib/ebpf-research}"
HOST_LABEL="${4:-E1}"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: execute with sudo/root because eBPF collection requires privileges"
  exit 1
fi

mkdir -p "$RESULT_ROOT"
chmod 700 "$RESULT_ROOT"
if find "$RESULT_ROOT" -maxdepth 1 -type d \( -name 'CAL1-*' -o -name 'BENIGN1-*' -o -name 'AE1-*' \) | grep -q .; then
  echo "ERROR: $RESULT_ROOT already contains controlled-protocol run directories."
  echo "Use a new empty result root or preserve/move the previous result set before rerunning."
  exit 2
fi

echo "== Environment gate =="
python3 "$SCRIPT_DIR/validate_environment.py" --output "$RESULT_ROOT/ENVIRONMENT_VALIDATION.json"

echo "== CAL-1: 5 x 120 s, rate 4/s =="
bash "$SCRIPT_DIR/run_calibration.sh" "$USER_NAME" 5 120 4 "$KEY_PATH" "$RESULT_ROOT"
python3 "$SCRIPT_DIR/validate_calibration1.py" --root "$RESULT_ROOT" --reps 5

echo "== BENIGN-1: 5 profiles x 3 x 120 s, rate 4/s =="
bash "$SCRIPT_DIR/run_benign1.sh" "$USER_NAME" 3 120 4 "$KEY_PATH" "$RESULT_ROOT"
python3 "$SCRIPT_DIR/validate_benign1.py" --root "$RESULT_ROOT" --reps 3

echo "== ATTACK-EMULATION-1: 5 profiles x 3 x 120 s, rate 4/s =="
bash "$SCRIPT_DIR/run_attack_emulation1.sh" "$USER_NAME" 3 120 4 "$KEY_PATH" "$RESULT_ROOT"
python3 "$SCRIPT_DIR/validate_attack_emulation1.py" --root "$RESULT_ROOT" --reps 3

echo "== Host-level paper-protocol validation =="
python3 "$SCRIPT_DIR/validate_host_reproduction.py" --root "$RESULT_ROOT" --host-label "$HOST_LABEL" --report-prefix "$RESULT_ROOT/HOST_REPRODUCTION_VALIDATION"

echo
echo "PASS: complete controlled acquisition protocol and host-level validation completed."
echo "Next: generate a neutral-labeled analysis manifest with analysis/generate_manifest.py."
