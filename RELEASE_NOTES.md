# Release notes - v1.0.1

v1.0.1 is the reproducibility-remediation release following clean-room execution on three new Linux environments and external validation against the frozen Security-Gym v4.1 stream.

## Scientific status

The paper's scientific claims are unchanged. This release corrects the public implementation and documentation so that the artifact executes the protocol actually reported by the manuscript and original frozen analyses.

## Final protocol-alignment corrections

The final audit identified three public-artifact mismatches that were corrected before v1.0.1:

- **Complete-window extraction:** the original controlled corpus used exactly 120 s of complete analysis windows (24 five-second windows/run; 3,600 windows for 150 runs). v1.0.0/early v1.0.1 candidates could retain a partial trailing collector-margin window. The extractor now enforces complete windows only and materializes any empty complete bin as a zero-valued feature vector instead of dropping it.
- **Matched I/E/B/E+B design:** the represented-behavior I/E regime now uses the same held target pair as the test set while excluding a deterministic cyclic control benign+attack pair. The unseen B/E+B regime excludes the target pair. Both regimes therefore train on exactly eight families, matching the frozen design.
- **RF/statistical configurations:** MODEL-1 uses RF400; the primary matched-shift and window-sensitivity RF gate uses RF20; feature-ablation RF uses RF5; Random Forest uses balanced-subsample class weighting with seed 42; Logistic Regression uses StandardScaler preprocessing; matched-cell bootstrap intervals use 5,000 resamples. These roles are now distinct in `protocol_spec.json`, the executable pipeline, validators, and documentation.

These corrections align the public reproduction artifact with the already reported manuscript protocol/results; they do not change the acquisition collector, workload families, original operational data, or paper claims.

## Reproducibility engineering improvements

- Machine-readable `protocol_spec.json`.
- Artifact integrity and confidentiality gates.
- Enforced six-tracepoint environment validation.
- Explicit CAL-1 validation.
- Workload-completion evidence independent of collector exit status.
- Persisted attack-emulation safety-gate evidence.
- Complete host-level validator for all 35 runs.
- One-command controlled acquisition runner.
- Strict validated manifest generation and multi-environment merge.
- One-command controlled analysis pipeline.
- Analysis-environment preflight.
- Protocol validator with exact complete-window and RF-configuration checks.
- Automated scientific reproduction summary separating protocol PASS from scientific corroboration.
- External-validation disk/writeability preflight and structural validator.
- End-to-end README with explicit source/destination paths, working directories, virtualenv requirements, expected outputs, and final release gates.

## Confidentiality boundary

No original operational telemetry, host-derived datasets, infrastructure identifiers, pseudonymization keys, or organization-derived data are included. Original numerical replication is not possible from the public artifact alone; methodological reproduction on new Linux systems is the intended reproducibility target.

## Release policy

v1.0.0 remains immutable. The corrected v1.0.1 analysis was rerun on the already collected three-environment clean-room corpora. The analysis environment, 90-run manifest, complete-window extraction (2,160 primary 5-second windows), MODEL-1, matched I/E/B/E+B decomposition, window sensitivity, feature ablation, environment characterization, and final protocol validator all passed. The scientific reproduction summary supported the paper's qualitative ordering for LR and RF, across all eight model/window combinations and all eight model/representation ablation combinations. The frozen Security-Gym external-validation workflow also passed. v1.0.1 is therefore cleared for tagging and archival; no new acquisition is required.
