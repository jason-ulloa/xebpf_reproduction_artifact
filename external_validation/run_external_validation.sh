#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

python download_security_gym_30d.py --outdir data
mkdir -p results/ev2 results/ev21
python build_features_30d.py --db data/exp_30d_heavy_v4.db --window 5 --out results/features_30d.csv
python ev2_external_validation.py --features results/features_30d.csv --outdir results/ev2 --rf-trees 400
python ev21_strict_temporal_family_holdout.py --features results/features_30d.csv --outdir results/ev21 --rf-trees 100

echo "External validation complete."
echo "The downloaded Security-Gym database is third-party data and is not part of this artifact."
