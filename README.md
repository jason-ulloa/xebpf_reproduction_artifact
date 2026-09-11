# XEBPF Reproduction Code — Public Candidate

This package contains the collector and controlled workload generators used to reproduce
the experimental protocol for the study:

**Environment or Behavior? A Controlled Study of Distribution Shift in eBPF-Based Host Intrusion Detection**

## Privacy-preserving key handling

The public collector does **not** contain or assume an infrastructure-specific key path.
The HMAC key path is supplied explicitly at execution time with:

```bash
--hmac-key-path /path/to/research.key
```

The key itself must never be committed, packaged, or published.

Generate a fresh key on a reproduction environment:

```bash
sudo ./generate_hmac_key.sh /opt/xebpf-secrets/research.key
```

For experiments requiring consistent pseudonyms across multiple hosts, securely copy the
same newly generated reproduction key to each participating host and pass the local path
with `--hmac-key-path`.

## Setup

```bash
sudo ./setup.sh
sudo ./create_experiment_user.sh
sudo ./generate_hmac_key.sh /opt/xebpf-secrets/research.key
```

## Collector example

```bash
sudo python3 collector.py \
  --experiment-id REPRO-001 \
  --workload-id controlled-mixed-v1 \
  --label benign \
  --duration 120 \
  --target-uid "$(id -u xebpfexp)" \
  --hmac-key-path /opt/xebpf-secrets/research.key
```

## Controlled calibration

Arguments: user, repetitions, duration, rate, key path.

```bash
sudo ./run_calibration.sh xebpfexp 5 120 4 /opt/xebpf-secrets/research.key
```

## BENIGN-1

```bash
sudo ./run_benign1.sh xebpfexp 3 120 4 /opt/xebpf-secrets/research.key
```

Profiles:
- benign-file-v1
- benign-process-v1
- benign-network-v1
- benign-service-v1
- benign-bursty-v1

## ATTACK-EMULATION-1

These are bounded, non-destructive behavioral emulations. They do not deploy malware,
exploit vulnerabilities, scan external systems, establish persistence, or perform
privilege escalation. Network activity is loopback-only and filesystem activity is
restricted to experiment-owned temporary workspaces.

```bash
sudo ./run_attack_emulation1.sh xebpfexp 3 120 4 /opt/xebpf-secrets/research.key
```

Profiles:
- ae-file-churn-v1
- ae-process-chain-v1
- ae-loopback-beacon-v1
- ae-staging-v1
- ae-mixed-burst-v1

## Frozen collector semantics

- Schema: `xebpf-1.3.2`
- Collector: `bpftrace-common-v1.3.2`
- UID-scoped collection supported through `--target-uid`
- Pseudonymization: HMAC-SHA256
- Tracepoints:
  - `syscalls/sys_enter_execve`
  - `sched/sched_process_exit`
  - `syscalls/sys_enter_connect`
  - `syscalls/sys_enter_accept4`
  - `syscalls/sys_enter_openat`
  - `syscalls/sys_enter_unlinkat`

Changing the key-path interface does **not** change capture semantics, event schema, or
pseudonymization algorithm. It only removes the original deployment-specific key location.

## Data availability

No event-level telemetry, host-derived dataset, pseudonymized operational data, keys,
host inventories, infrastructure identifiers, network topology, or operational logs are
included in this package.

Security-Gym v4.1, used for external behavioral validation, is independently public:
DOI `10.5281/zenodo.21763493`.

## Reproduction note

A reproducer should generate their own key and run the controlled protocols on Linux
systems satisfying the tracepoint prerequisites. The original operational dataset is not
required to reproduce the methodology, but exact numerical replication of the paper's
confidential host-derived results is not possible without the non-public original data.


## External validation (Security-Gym v4.1)

The `external_validation/` directory reproduces EV2 and the stricter EV2.1
temporal+held-family validation using the independently public Security-Gym v4.1
30-day stream. The dataset itself is **not** bundled. The downloader verifies the frozen
stream SHA-256 and the analysis uses only the public dataset.

See `external_validation/README.md`.



## Release metadata

- Software release: `1.0.0`
- Repository: `https://github.com/jason-ulloa/xebpf_reproduction_artifact`
- License: MIT
- Author: Jason Ulloa Hernández
- ORCID: `0009-0003-0445-6697`
- Affiliation: Universidad CENFOTEC, San José, Costa Rica

A `CITATION.cff` and `.zenodo.json` are included for GitHub/Zenodo archival. The
repository URL and software DOI should be inserted only after those persistent identifiers
exist; no identifier is fabricated in this release candidate.

## Reproducibility boundary

This artifact supports independent **methodological reproduction** and replication on
other Linux systems. It cannot provide exact numerical replication of the confidential
host-derived results because the original operational telemetry and all host-derived
datasets remain non-public under organizational confidentiality and security restrictions.
