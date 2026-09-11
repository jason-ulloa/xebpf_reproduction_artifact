# Analysis reproduction

These scripts reproduce the paper's analysis **procedure** on newly collected data.

They intentionally contain no original host-derived telemetry, feature matrices, pseudonyms,
environment identifiers, or operational results. Consequently, they enable independent
methodological reproduction but cannot reproduce the exact numerical values reported in the
paper without the confidential original host-derived dataset.

## 1. Build a manifest

Copy `manifest_template.csv` and use neutral environment labels (for example E1-E5).
Each row points to one locally collected `events.jsonl`.

## 2. Extract 5-second features

```bash
python3 feature_extract.py --manifest manifest.csv --window 5 --output features_5s.csv
```

The feature representation contains counts and ratios for the event types observed in the
controlled corpus (`FILE_OPEN`, `NET_ACCEPT`, `NET_CONNECT`, `PROCESS_EXEC`, `PROCESS_EXIT`),
`total_events`, `unique_pids`, and interarrival mean/std/median. No pseudonym identifiers
are model features.

## 3. Known-behavior cross-environment transfer (MODEL-1)

```bash
python3 model1.py --features features_5s.csv --model LR --output model1_lr.csv
python3 model1.py --features features_5s.csv --model RF --rf-trees 400 --output model1_rf.csv
```

Runs R01-R02 are used for training and R03 for target testing.

## 4. Matched I/E/B/E+B decomposition

```bash
python3 shift_decomposition.py --features features_5s.csv --model LR --output-prefix shift_lr
python3 shift_decomposition.py --features features_5s.csv --model RF --rf-trees 400 --output-prefix shift_rf
```

- I: same environment, represented behavioral families
- E: different environment, represented behavioral families
- B: same environment, held-out benign/malicious behavioral-family pair
- E+B: different environment, same held-out pair

The implementation holds out one benign and one malicious workload family at a time and
uses the same represented family set for the matched conditions.

## 5. Window sensitivity

```bash
python3 window_sensitivity.py --manifest manifest.csv --outdir window_sensitivity --windows 1 5 10 30
```

## 6. Feature ablation

```bash
python3 feature_ablation.py --features features_5s.csv --outdir ablation --rf-trees 5
```

The 5-tree RF is explicitly a computational sensitivity analysis and does not replace the
primary RF configuration.

## 7. Environment-shift characterization

```bash
python3 environment_shift.py --features features_5s.csv --rep 3 --output environment_shift.csv
```

For each matched workload, host pair, and feature, the script computes Wasserstein-1 and
normalizes it by the IQR of the **two compared R03 distributions pooled together**. If that
IQR is <= 1e-12, the denominator falls back to
`max(median(abs(pooled_values)), 1e-9)`.

## Statistical unit

Windows are observations used by the classifiers; they should not be interpreted as
independent experimental subjects. Matched transfer cells/workload-family comparisons are
the level summarized for the shift decomposition.
