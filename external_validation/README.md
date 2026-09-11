# External validation reproduction — Security-Gym v4.1

This directory reproduces the **external behavioral validation** portion of the study
without redistributing Security-Gym data.

Dataset:
- Security-Gym v4.1
- Frozen DOI: `10.5281/zenodo.21763493`
- Stream: `exp_30d_heavy_v4.db.zst`
- Expected SHA-256:
  `4e903e2ba8d50945070c23109079388fa318db8f995ce1c3958e1447082f8824`

The stream is independently public under Apache-2.0. The downloader obtains it from the
official Hugging Face mirror and verifies the exact compressed-file SHA-256 before use.

## Run

Use a non-production analysis machine with sufficient disk space (the decompressed
30-day SQLite stream is approximately 8.5 GB):

```bash
chmod +x run_external_validation.sh
./run_external_validation.sh
```

The workflow:
1. downloads and integrity-checks the frozen 30-day Security-Gym stream;
2. extracts only eBPF process/network/file events into 5-second windows;
3. runs EV2 forward-temporal and pure Leave-One-Attack-Family-Out evaluation;
4. runs EV2.1 with a strict first-70% train / final-30% test split, excluding the held
   family from early training and testing only on pure held-family positives plus late
   benign negatives.

No Security-Gym database, raw events, identifiers, paths, IPs, usernames, commands,
campaign IDs, or absolute timestamps are included in the public artifact.

## Interpretation guardrail

Security-Gym is used only as **external behavioral validation**. Its provenance is not a
controlled Linux-environment experiment, so these results must not be interpreted as
causal evidence for an operating-system, kernel, or infrastructure environment effect.

## Expected EV2.1 values reported in the study

For the frozen v4.1 30-day stream, the reported family-mean EV2.1 values are:

- Logistic Regression: F1 `0.248549`, PR-AUC `0.224268`, MCC `0.232865`
- Random Forest 100-tree sensitivity: F1 `0.212647`, PR-AUC `0.212965`, MCC `0.176863`

Small numerical variation can occur across numerical-library/platform versions, but the
protocol, split, family exclusion, and deterministic sampling seeds are fixed.
