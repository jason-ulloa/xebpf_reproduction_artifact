# Controlled analysis reproduction

Run all commands from the artifact root:

```bash
cd /opt/xebpf-reproduction
source $HOME/.venvs/xebpf-analysis/bin/activate
python analysis/check_analysis_environment.py
```

The environment check must end with `RESULT: PASS`.

## Input corpora

Each acquisition host writes its validated result root to:

```text
/var/lib/ebpf-research
```

Copy the complete validated contents from each host to one controlled analysis system, for example:

```text
/opt/xebpf-reproduction-data/E1
/opt/xebpf-reproduction-data/E2
/opt/xebpf-reproduction-data/E3
```

Do not point `generate_manifest.py` at the software directory. It must receive the copied validated **result root**.

## Generate manifests

```bash
python analysis/generate_manifest.py --root /opt/xebpf-reproduction-data/E1 --host E1 --output analysis/manifest_E1.csv
python analysis/generate_manifest.py --root /opt/xebpf-reproduction-data/E2 --host E2 --output analysis/manifest_E2.csv
python analysis/generate_manifest.py --root /opt/xebpf-reproduction-data/E3 --host E3 --output analysis/manifest_E3.csv

python analysis/merge_manifests.py \
  --inputs analysis/manifest_E1.csv analysis/manifest_E2.csv analysis/manifest_E3.csv \
  --output analysis/manifest_combined.csv
```

Expected: 30 classification runs/environment and 90 rows for three environments.

## Execute the complete pipeline

```bash
python analysis/run_analysis_pipeline.py \
  --manifest analysis/manifest_combined.csv \
  --outdir analysis/reproduction_results
```

Frozen distinctions that matter:

- primary analysis duration: 120 s;
- complete windows only: 120/1=120, 120/5=24, 120/10=12, 120/30=4 windows/run;
- MODEL-1 RF: 400 trees, `class_weight="balanced_subsample"`, seed 42;
- matched I/E/B/E+B RF gate: 20 trees;
- window-sensitivity RF: 20 trees;
- feature-ablation RF sensitivity: 5 trees;
- LR: StandardScaler + LogisticRegression(max_iter=5000, class_weight="balanced", seed 42);
- bootstrap: 5,000 matched-cell resamples, seed 42;
- R01/R02 training and R03 testing.

The matched decomposition uses the **same held benign+attack pair as the I/E/B/E+B test target**. To keep training cardinality equal at eight families, the represented-behavior I/E regime excludes the next cyclic benign+attack control pair, while the unseen-behavior B/E+B regime excludes the target held pair.

The original 150-run corpus therefore contains exactly 3,600 primary 5-s windows. A three-environment reproduction with 90 classification runs must contain exactly 2,160. Complete bins with no observed events on a reproducer system are retained as zero-valued feature vectors, so window cardinality remains protocol-deterministic.

## Validate protocol execution

```bash
python analysis/validate_analysis_reproduction.py \
  --manifest analysis/manifest_combined.csv \
  --outdir analysis/reproduction_results \
  --report-prefix analysis/reproduction_results/ANALYSIS_REPRODUCTION_VALIDATION
```

Expected final line:

```text
RESULT: PASS
```

## Summarize scientific outcome

```bash
python analysis/summarize_reproduction.py \
  --outdir analysis/reproduction_results \
  --report-prefix analysis/reproduction_results/SCIENTIFIC_REPRODUCTION_SUMMARY
```

This reports the direct `delta_B_minus_delta_E` contrast and CI95% for the primary decomposition, all four window sizes, all feature-ablation representations, and the environment-shift characterization.

Scientific corroboration is **not** a protocol PASS criterion. A clean reproduction may produce different numerical scores or even a different scientific outcome on new Linux systems; the result should be reported rather than tuned away.
