# XEBPF Reproduction Artifact

This artifact contains the acquisition, validation, controlled-workload, analysis, and external-validation code for:

**Environment or Behavior? A Controlled Study of Distribution Shift in eBPF-Based Host Intrusion Detection**

This package is **v1.0.1**, prepared after clean-room reproduction on three new Linux environments and external validation against the frozen Security-Gym v4.1 stream.

The artifact is designed to answer two separate questions:

1. **Did the software run successfully?**
2. **Did the reproduced experiment match the protocol reported in the paper?**

The second question is the important one. The package therefore includes machine-readable protocol specifications and validators for environment compatibility, each acquisition phase, each host corpus, the complete multi-environment analysis, the public external validation, artifact integrity, and confidentiality hygiene.

## Reproducibility boundary

The public artifact supports independent **methodological reproduction on new Linux systems**. The original event-level telemetry and all host-derived datasets from the study remain non-public because they originate from operational infrastructure subject to confidentiality and security restrictions.

Therefore:

- the **experimental procedure, code, workload families, feature representation, splits, models, and statistical analyses are reproducible**;
- the exact numerical results from the original confidential hosts are **not** expected to be reproduced from this package alone;
- a new reproducer may obtain different F1 scores or effect sizes on different Linux systems without that constituting a reproduction failure;
- a validator PASS means that the **paper protocol was executed correctly**, not that the new systems must reproduce the original numerical outcome.

No operational telemetry, host inventories, network topology, infrastructure identifiers, original pseudonymization keys, or organization-derived datasets are included.

---

# 0. What constitutes a successful reproduction?

A complete controlled reproduction has four gates:

1. **Artifact gate** — package is internally consistent and scripts compile.
2. **Host acquisition gate** — each Linux environment completes CAL-1, BENIGN-1, and ATTACK-EMULATION-1 with protocol evidence and successful workload markers.
3. **Cross-environment analysis gate** — at least two independently collected environments contain the same 10 behavioral families and R01-R03 structure, and the complete MODEL-1 / I-E-B-E+B / sensitivity workflow executes with the frozen settings.
4. **External-validation gate** — the frozen Security-Gym v4.1 workflow executes against the verified public stream.

The recommended clean-room validation uses **three new Linux environments**. The original study used five operational environments; three clean systems are sufficient to verify that the public methodology works across multiple Linux families. Cross-environment analysis requires at least two.

The frozen public protocol is machine-readable in:

```text
protocol_spec.json
```

Do not change it during a reproduction.

---

# 1. Extract the artifact on a clean Linux host

Supported acquisition setup paths use `apt-get`, `dnf`, or `zypper`.

Use either archive format:

```bash
# ZIP; install unzip first if it is not already present
unzip xebpf-reproduction-artifact.zip

# OR tar.gz; tar is normally present on base Linux systems
tar -xzf xebpf-reproduction-artifact.tar.gz
```

Install the artifact in a location traversable by the dedicated experiment user:

```bash
sudo mkdir -p /opt/xebpf-reproduction
sudo cp -a <extracted-directory>/. /opt/xebpf-reproduction/
cd /opt/xebpf-reproduction
```

Do not place the artifact below a private home directory whose parent is mode `0700`; the non-root experiment account must be able to traverse the path and read the workload scripts.

---

# 2. Validate the artifact before touching the system

Run:

```bash
cd /opt/xebpf-reproduction
python3 ./validate_artifact.py
python3 ./confidentiality_audit.py
```

Expected result:

```text
XEBPF ARTIFACT VALIDATION
RESULT: PASS

XEBPF PUBLIC ARTIFACT CONFIDENTIALITY AUDIT
RESULT: PASS
```

If either validator fails, stop. Do not continue to acquisition.

---

# 3. Install acquisition prerequisites and verify the six required tracepoints

Run:

```bash
sudo bash ./setup.sh
```

The setup installs the acquisition prerequisites and requires all six tracepoints:

- `syscalls/sys_enter_execve`
- `sched/sched_process_exit`
- `syscalls/sys_enter_connect`
- `syscalls/sys_enter_accept4`
- `syscalls/sys_enter_openat`
- `syscalls/sys_enter_unlinkat`

`setup.sh` exits nonzero if any tracepoint is absent.

Verify again independently and persist an environment report:

```bash
sudo mkdir -p /var/lib/ebpf-research
sudo python3 ./validate_environment.py \
  --output /var/lib/ebpf-research/ENVIRONMENT_VALIDATION.json
```

Expected final line:

```text
RESULT: PASS
```

---

# 4. Create the non-root experiment account

Run:

```bash
sudo bash ./create_experiment_user.sh
```

Default account:

```text
xebpfexp
```

All controlled workloads must run as this non-root account.

---

# 5. Generate a reproduction HMAC key

Run:

```bash
sudo bash ./generate_hmac_key.sh /opt/xebpf-secrets/research.key
```

The key must remain private and must never be committed or published.

For one multi-host reproduction, use the **same newly generated reproduction key** on all participating hosts when consistent pseudonyms are required across environments. Transfer it securely and preserve restrictive permissions (`0600` or equivalent).

This reproduction key must never be derived from or confused with an original operational key.

---

# 6. Execute the complete controlled acquisition protocol

## Recommended path: one command

Choose a neutral environment label for the current clean host, for example `E1`, `E2`, or `E3`.

For the first host:

```bash
sudo bash ./run_controlled_acquisition.sh \
  xebpfexp \
  /opt/xebpf-secrets/research.key \
  /var/lib/ebpf-research \
  E1
```

The runner performs, in order:

1. environment validation;
2. CAL-1;
3. CAL-1 validation;
4. BENIGN-1;
5. BENIGN-1 validation;
6. ATTACK-EMULATION-1 safety gate;
7. ATTACK-EMULATION-1;
8. ATTACK-EMULATION-1 validation;
9. complete host-level protocol validation.

The default paper-aligned acquisition settings are fixed:

```text
Workload duration       120 s
Base rate               4 cycles/s
Collector margin        +8 s
CAL-1                   1 profile × 5 repetitions
BENIGN-1                5 profiles × 3 repetitions
ATTACK-EMULATION-1      5 profiles × 3 repetitions
Total controlled runs   35
Classification runs     30
```

The complete protocol takes roughly 70–90 minutes depending on host and package/runtime overhead.

The runner refuses to start if the selected result root already contains controlled-protocol run directories. This prevents accidental mixing of repeated experiments. Preserve the old result root or use a new empty root instead of deleting evidence silently.

Expected final line:

```text
PASS: complete controlled acquisition protocol and host-level validation completed.
```

## Manual path

If you want to execute each phase separately, use the exact commands below.

### 6.1 CAL-1

```bash
sudo bash ./run_calibration.sh \
  xebpfexp 5 120 4 \
  /opt/xebpf-secrets/research.key \
  /var/lib/ebpf-research
```

Validate:

```bash
sudo python3 ./validate_calibration1.py \
  --root /var/lib/ebpf-research \
  --reps 5
```

Expected:

```text
runs_found=5 expected=5
PASS: CAL-1 matches the frozen public reproduction protocol
```

CAL-1 is not part of the classification corpus.

### 6.2 BENIGN-1

Profiles:

- `benign-file-v1`
- `benign-process-v1`
- `benign-network-v1`
- `benign-service-v1`
- `benign-bursty-v1`

Run:

```bash
sudo bash ./run_benign1.sh \
  xebpfexp 3 120 4 \
  /opt/xebpf-secrets/research.key \
  /var/lib/ebpf-research
```

Validate:

```bash
sudo python3 ./validate_benign1.py \
  --root /var/lib/ebpf-research \
  --reps 3
```

Expected:

```text
runs=15 expected=15
PASS: BENIGN-1 matches the frozen public reproduction protocol
```

### 6.3 ATTACK-EMULATION-1

Profiles:

- `ae-file-churn-v1`
- `ae-process-chain-v1`
- `ae-loopback-beacon-v1`
- `ae-staging-v1`
- `ae-mixed-burst-v1`

The suite is a bounded, non-destructive behavioral emulation. It does not deploy malware, exploit vulnerabilities, scan external systems, establish persistence, or perform privilege escalation. Network activity is loopback-only and filesystem activity is limited to isolated `/tmp/xebpf-ae1-*` workspaces.

Run:

```bash
sudo bash ./run_attack_emulation1.sh \
  xebpfexp 3 120 4 \
  /opt/xebpf-secrets/research.key \
  /var/lib/ebpf-research
```

Validate:

```bash
sudo python3 ./validate_attack_emulation1.py \
  --root /var/lib/ebpf-research \
  --reps 3
```

Expected:

```text
runs_found=15 expected=15
PASS: ATTACK-EMULATION-1 matches the frozen public reproduction protocol and safety gate evidence is present
```

---

# 7. Verify that the current host really matches the paper protocol

Whether you used the one-command or manual path, run the complete host validator using the neutral label assigned to this environment:

```bash
sudo python3 ./validate_host_reproduction.py \
  --root /var/lib/ebpf-research \
  --host-label E1 \
  --report-prefix /var/lib/ebpf-research/HOST_REPRODUCTION_VALIDATION
```

This validator verifies, rather than merely assumes:

- schema `xebpf-1.3.2`;
- collector `bpftrace-common-v1.3.2`;
- UID-scoped collection;
- `raw_identifiers_persisted=false`;
- exactly five CAL-1 runs;
- exactly 15 BENIGN-1 runs;
- exactly 15 ATTACK-EMULATION-1 runs;
- exact workload-family identities;
- exact repetition structure;
- 120-second workload duration;
- rate 4/s;
- collector exit status 0;
- zero malformed lines;
- explicit successful workload completion markers;
- protocol JSON records;
- attack-emulation safety-gate evidence and scope;
- internally consistent OS/kernel/architecture/bpftrace fingerprint for the host corpus.

It also reports whether event counts happened to be identical between repeated runs, but exact count equality is **observational only** and is not a universal pass/fail criterion on new Linux systems.

Expected:

```text
XEBPF HOST REPRODUCTION VALIDATION
Expected runs: 35  Found: 35
CAL-1: PASS
BENIGN-1: PASS
ATTACK-EMULATION-1: PASS
Protocol files: PASS
RESULT: PASS
```

The validator writes:

```text
HOST_REPRODUCTION_VALIDATION.json
HOST_REPRODUCTION_VALIDATION.txt
```

These files are the machine-readable and human-readable evidence that the host executed the controlled protocol correctly.

---

# 8. Repeat Sections 1–7 on the other clean Linux environments

Use neutral labels:

```text
E1
E2
E3
```

Do not use operational hostnames in analysis artifacts.

For example, on the second system:

```bash
sudo bash ./run_controlled_acquisition.sh \
  xebpfexp \
  /opt/xebpf-secrets/research.key \
  /var/lib/ebpf-research \
  E2
```

and on the third:

```bash
sudo bash ./run_controlled_acquisition.sh \
  xebpfexp \
  /opt/xebpf-secrets/research.key \
  /var/lib/ebpf-research \
  E3
```

Each system must independently finish with `RESULT: PASS` from `validate_host_reproduction.py` before its data are admitted to the combined analysis.

---

# 9. Prepare the analysis environment

Analysis dependencies are intentionally separated from acquisition dependencies. **All commands in Sections 9-14 must be executed from the artifact root `/opt/xebpf-reproduction` with the `xebpf-analysis` virtual environment active.**

Run exactly:

```bash
cd /opt/xebpf-reproduction
python3 -m venv $HOME/.venvs/xebpf-analysis
source $HOME/.venvs/xebpf-analysis/bin/activate
python -m pip install --upgrade pip
python -m pip install -r analysis/requirements.txt
python analysis/check_analysis_environment.py
```

Expected final line:

```text
RESULT: PASS
```

If a later shell no longer shows the virtual environment as active, return to the artifact root and run:

```bash
cd /opt/xebpf-reproduction
source $HOME/.venvs/xebpf-analysis/bin/activate
python analysis/check_analysis_environment.py
```

Do not continue until the check passes.

---

# 10. Consolidate the validated environment corpora

The acquisition runner stores the validated result root on **each acquisition host** at:

```text
/var/lib/ebpf-research
```

That directory - not `/opt/xebpf-reproduction` - is the corpus that must be transferred to the analysis system.

Before transfer, verify on each acquisition host:

```bash
sudo cat /var/lib/ebpf-research/HOST_REPRODUCTION_VALIDATION.txt
```

The report must state:

```text
passed=True
```

or otherwise clearly show `RESULT: PASS` if produced by the current validator.

On the controlled analysis system, use one neutral destination per environment:

```text
/opt/xebpf-reproduction-data/E1
/opt/xebpf-reproduction-data/E2
/opt/xebpf-reproduction-data/E3
```

Create the destinations:

```bash
sudo mkdir -p /opt/xebpf-reproduction-data/{E1,E2,E3}
```

For each acquisition host, transfer the **complete contents** of `/var/lib/ebpf-research/` into the corresponding destination. One portable example is:

```bash
# On E1 acquisition host
sudo tar -C /var/lib -czf /tmp/xebpf-E1-results.tar.gz ebpf-research
```

Transfer `/tmp/xebpf-E1-results.tar.gz` using an authorized administrative file-transfer mechanism. Then on the analysis system:

```bash
sudo tar -xzf xebpf-E1-results.tar.gz \
  -C /opt/xebpf-reproduction-data/E1 \
  --strip-components=1
```

Repeat for E2 and E3, changing the destination label accordingly.

The final structure must resemble:

```text
/opt/xebpf-reproduction-data/
├── E1/
│   ├── CAL1-.../
│   ├── BENIGN1-.../
│   ├── AE1-.../
│   ├── CAL1_PROTOCOL.json
│   ├── BENIGN1_PROTOCOL.json
│   ├── ATTACK_EMULATION1_PROTOCOL.json
│   ├── ATTACK_EMULATION1_SAFETY_GATE.json
│   ├── HOST_REPRODUCTION_VALIDATION.json
│   └── HOST_REPRODUCTION_VALIDATION.txt
├── E2/
│   └── ...
└── E3/
    └── ...
```

Each environment contains 35 controlled runs: 5 CAL-1, 15 BENIGN-1, and 15 ATTACK-EMULATION-1. Only the 30 BENIGN-1 + ATTACK-EMULATION-1 runs enter the classification manifest; CAL-1 remains validation evidence.

Because source result roots can be restrictive, transfer them using an authorized administrative account and grant the analysis account only the local permissions required for reproduction. Do not publish newly generated event data unless your own environment permits it.

---

# 11. Generate and merge the environment manifests

Return to the artifact root and activate the analysis environment:

```bash
cd /opt/xebpf-reproduction
source $HOME/.venvs/xebpf-analysis/bin/activate
python analysis/check_analysis_environment.py
```

Generate one validated classification manifest per environment:

```bash
python analysis/generate_manifest.py \
  --root /opt/xebpf-reproduction-data/E1 \
  --host E1 \
  --output analysis/manifest_E1.csv

python analysis/generate_manifest.py \
  --root /opt/xebpf-reproduction-data/E2 \
  --host E2 \
  --output analysis/manifest_E2.csv

python analysis/generate_manifest.py \
  --root /opt/xebpf-reproduction-data/E3 \
  --host E3 \
  --output analysis/manifest_E3.csv
```

Each successful command must report:

```text
PASS: wrote 30 validated classification runs for E#
```

Merge them:

```bash
python analysis/merge_manifests.py \
  --inputs \
    analysis/manifest_E1.csv \
    analysis/manifest_E2.csv \
    analysis/manifest_E3.csv \
  --output analysis/manifest_combined.csv
```

For three environments, the expected result is:

```text
Wrote 90 rows from 3 environments to analysis/manifest_combined.csv
```

---

# 12. Execute the complete controlled analysis pipeline

From `/opt/xebpf-reproduction` with the analysis virtual environment active, run:

```bash
python analysis/run_analysis_pipeline.py \
  --manifest analysis/manifest_combined.csv \
  --outdir analysis/reproduction_results
```

This executes the paper-aligned analysis with distinct frozen RF configurations:

1. 5-second primary feature extraction using **exactly 120 s of complete windows**;
2. MODEL-1 Logistic Regression after standardizing the model features;
3. MODEL-1 Random Forest with **400 trees**;
4. matched I/E/B/E+B decomposition for LR;
5. matched I/E/B/E+B decomposition for RF with the frozen **20-tree shift gate**;
6. window sensitivity at 1, 5, 10, and 30 seconds, using the same matched design and **20-tree RF sensitivity configuration**;
7. feature ablation for counts-only, ratios-only, timing-only, and full representations, using **RF5** for the RF sensitivity analysis;
8. environment-shift characterization using pair-pooled-IQR-normalized Wasserstein-1 distance;
9. Random Forest uses `class_weight="balanced_subsample"` and seed 42;
10. 5,000 matched-cell bootstrap resamples for reported contrast intervals.

The matched decomposition controls training cardinality exactly. For each held benign+attack pair, the represented-behavior I/E regime excludes a deterministic cyclic control pair while retaining the target pair; the unseen-behavior B/E+B regime excludes the target pair itself. Both regimes therefore train on exactly eight behavioral families.

### Complete-window rule

The paper's original 150-run corpus contains exactly 3,600 5-second windows: `150 × 24`. The public extractor therefore retains only complete windows inside the frozen 120-second analysis interval and excludes any partial trailing window produced by the collector margin. Every complete bin is materialized explicitly; if a new system emits no observed event in a particular bin, that bin is represented by a zero-valued feature vector rather than being dropped.

Expected complete windows per run are:

```text
1 s  -> 120 windows
5 s  ->  24 windows
10 s ->  12 windows
30 s ->   4 windows
```

For a three-environment reproduction with 90 classification runs, the primary 5-second matrix must contain:

```text
90 × 24 = 2,160 windows
```

Expected final line from the pipeline:

```text
PASS: controlled analysis pipeline completed
```

---

# 13. Validate protocol execution

Run:

```bash
python analysis/validate_analysis_reproduction.py \
  --manifest analysis/manifest_combined.csv \
  --outdir analysis/reproduction_results \
  --report-prefix analysis/reproduction_results/ANALYSIS_REPRODUCTION_VALIDATION
```

For three environments the validator expects:

```text
Environments:                         3
MODEL-1 directed transfer cells:      6
Matched I/E/B/E+B cells per model:    150
Classification runs per environment:  30
Behavioral families:                  10
Repetitions per family:               R01-R03
Complete 5-s windows:                 2,160
MODEL-1 RF trees:                     400
Matched-shift RF trees:               20
Window-sensitivity RF trees:          20
Feature-ablation RF trees:            5
Bootstrap iterations:                 5,000
Window sensitivity:                   1,5,10,30 s
```

The matched-cell formula is:

```text
N × (N - 1) × 5 benign held families × 5 malicious held families
```

For the original five-host study this equals 500 cells/model. For three clean-room environments it equals 150 cells/model.

Expected final line:

```text
RESULT: PASS
```

A PASS means the new experiment executed the frozen controlled protocol. It does **not** require the new numerical F1 values or effect sizes to equal those from the confidential original hosts.

---

# 14. Produce the scientific reproduction summary

Protocol validation and scientific corroboration are deliberately separated. After Section 13 passes, run:

```bash
python analysis/summarize_reproduction.py \
  --outdir analysis/reproduction_results \
  --report-prefix analysis/reproduction_results/SCIENTIFIC_REPRODUCTION_SUMMARY
```

This creates:

```text
analysis/reproduction_results/SCIENTIFIC_REPRODUCTION_SUMMARY.txt
analysis/reproduction_results/SCIENTIFIC_REPRODUCTION_SUMMARY.json
```

The summary reports:

- primary I/E/B/E+B effects for LR and RF;
- `ΔE`, `ΔB`, and the direct paired contrast `ΔB-ΔE` with CI95%;
- all 1/5/10/30-second window-sensitivity contrasts;
- counts/ratios/timing/full feature-ablation contrasts;
- actual environment pairs and normalized Wasserstein-1 characterization.

Interpret outcomes as follows:

```text
Protocol PASS + ΔB-ΔE CI95% > 0
    Methodological reproduction passed and the new systems qualitatively corroborate
    the paper's central ordering.

Protocol PASS + ΔB-ΔE not supported
    Methodological reproduction still passed, but the new systems produced a different
    scientific outcome. Report that result; do not tune the protocol after inspection.

Protocol FAIL
    Do not interpret scientific scores until the protocol failure is resolved.
```

Exact numerical equality with the original confidential-host results is neither expected nor required.

---

# 15. External validation - Security-Gym v4.1

Security-Gym is used only as **external behavioral validation**. Its provenance is not a controlled Linux-environment experiment and must not be used to infer a causal environment effect.

Frozen dataset:

```text
Security-Gym v4.1
DOI: 10.5281/zenodo.21763493
Stream: exp_30d_heavy_v4.db.zst
Compressed SHA-256:
4e903e2ba8d50945070c23109079388fa318db8f995ce1c3958e1447082f8824
```

Use a non-production analysis machine. The runner performs a disk-space/writeability preflight and requires at least 12 GiB free in the external-validation working location.

Run exactly:

```bash
cd /opt/xebpf-reproduction/external_validation
bash ./run_external_validation.sh
```

The runner:

1. checks local prerequisites and disk space;
2. creates its own isolated Python environment;
3. installs the declared dependencies;
4. downloads the frozen stream;
5. verifies its SHA-256;
6. builds 5-second features;
7. runs EV2;
8. runs EV2.1 strict temporal + family holdout;
9. runs `validate_external_validation.py`.

Expected completion includes:

```text
INTEGRITY GATE: PASS
FEATURE EXTRACTION GATE: PASS
EXTERNAL-VALIDATION-2: PASS
EV2.1 STRICT TEMPORAL + FAMILY HOLDOUT: PASS
Structural/frozen-dataset result: PASS
External validation complete and structurally validated.
```

The frozen stream should produce 457,786 windows, including 6,180 malicious windows and the five expected attack families. Small numerical model variation is treated as a warning when dataset identity and structural protocol checks still pass.

---

# 16. Final release-readiness gate

Return to the artifact root:

```bash
cd /opt/xebpf-reproduction
python3 ./validate_artifact.py
python3 ./confidentiality_audit.py
```

A complete paper reproduction is ready to close only when all of the following are true:

```text
Artifact integrity                         PASS
Public-artifact confidentiality audit      PASS
E1 host reproduction                       PASS
E2 host reproduction                       PASS
E3 host reproduction                       PASS
Combined controlled-analysis validation    PASS
Scientific summary generated               YES
Security-Gym integrity                     PASS
Security-Gym EV2                           PASS
Security-Gym EV2.1                         PASS
Security-Gym structural validator          PASS
```

The scientific summary may corroborate or differ from the original outcome; that does not change a protocol PASS. Release readiness concerns executable protocol fidelity, artifact integrity, and confidentiality hygiene.

A new artifact version is justified only by a substantive implementation, protocol, confidentiality, or documentation defect - not merely because different Linux systems produce different scores.

---

# Output and evidence files

Default acquisition root:

```text
/var/lib/ebpf-research
```

Each successful run directory contains at least:

- `events.jsonl` — privacy-preserving event stream;
- `metadata.json` — run metadata;
- `stats.json` — event counts, malformed-line count, collector exit code;
- `collector_stderr.log` — collector diagnostics;
- `workload_status.json` — explicit successful workload completion evidence, workload identity, duration, rate, and experiment user.

Protocol/evidence files include:

- `ENVIRONMENT_VALIDATION.json`
- `CAL1_PROTOCOL.json`
- `BENIGN1_PROTOCOL.json`
- `ATTACK_EMULATION1_PROTOCOL.json`
- `ATTACK_EMULATION1_SAFETY_GATE.json`
- `HOST_REPRODUCTION_VALIDATION.json`
- `HOST_REPRODUCTION_VALIDATION.txt`

Analysis evidence includes:

- `PIPELINE_COMPLETE.json`
- `ANALYSIS_REPRODUCTION_VALIDATION.json`
- `ANALYSIS_REPRODUCTION_VALIDATION.txt`

These files make it possible to distinguish a successful command from a successful reproduction of the paper protocol.

---

# Frozen scientific semantics

The v1.0.1 remediation does not alter the paper's scientific semantics:

- schema `xebpf-1.3.2`;
- collector identifier `bpftrace-common-v1.3.2`;
- six intended tracepoints;
- UID-scoped capture;
- HMAC-SHA256 source pseudonymization;
- five benign workload families;
- five attack-emulation families;
- primary 5-second feature representation;
- R01-R02 training and R03 testing split;
- LR configuration with StandardScaler preprocessing;
- MODEL-1 400-tree RF configuration with balanced-subsample class weighting and seed 42;
- matched I/E/B/E+B design with equal eight-family training cardinality;
- matched-shift 20-tree RF gate;
- 20-tree RF window-sensitivity configuration;
- 5,000 matched-cell bootstrap resamples;
- complete-window extraction over the 120-second analysis interval;
- 1/5/10/30-second window sensitivity;
- counts/ratios/timing/full feature ablation;
- 5-tree RF feature-ablation sensitivity;
- pair-pooled-IQR normalized Wasserstein-1 environment characterization;
- Security-Gym external behavioral-validation role.

Changes from v1.0.0 are reproducibility engineering, validation, packaging, and documentation.

---

# Public software record

Repository:

```text
https://github.com/jason-ulloa/xebpf_reproduction_artifact
```

Immutable v1.0.0 archive DOI:

```text
10.5281/zenodo.22699421
```

The **v1.0.1 release has completed clean-room protocol validation on three new Linux environments**. Its version-specific Zenodo DOI is intentionally not embedded in this package because Zenodo assigns that DOI only after the GitHub release is archived. Until that DOI exists, cite the GitHub v1.0.1 release together with the immutable v1.0.0 archive DOI above as the prior archived software record. After Zenodo archives v1.0.1, use the DOI shown on the v1.0.1 Zenodo record.

License: MIT  
Author: Jason Ulloa Hernández  
ORCID: `0009-0003-0445-6697`  
Affiliation: Universidad CENFOTEC, San José, Costa Rica
