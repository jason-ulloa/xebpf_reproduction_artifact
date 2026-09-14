#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: required command not found: $1" >&2; exit 2; }; }
need_cmd python3
need_cmd df

# Conservative local-space preflight. The frozen stream is ~686 MiB compressed and ~8.5 GiB decompressed.
avail_kb=$(df -Pk . | awk 'NR==2 {print $4}')
min_kb=$((12 * 1024 * 1024))
if [ "${avail_kb:-0}" -lt "$min_kb" ]; then
  echo "ERROR: external validation requires at least 12 GiB free in $HERE" >&2
  df -h . >&2
  exit 2
fi
if [ ! -w . ]; then
  echo "ERROR: external-validation directory is not writable: $HERE" >&2
  exit 2
fi

echo "EXTERNAL VALIDATION PREFLIGHT: PASS"
df -h . | tail -n 1

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python download_security_gym_30d.py --outdir data
mkdir -p results/ev2 results/ev21
python build_features_30d.py --db data/exp_30d_heavy_v4.db --window 5 --out results/features_30d.csv
python ev2_external_validation.py --features results/features_30d.csv --outdir results/ev2 --rf-trees 400
python ev21_strict_temporal_family_holdout.py --features results/features_30d.csv --outdir results/ev21 --rf-trees 100
python validate_external_validation.py --results-root results

echo "External validation complete and structurally validated."
echo "The downloaded Security-Gym database is third-party data and is not part of this artifact."
