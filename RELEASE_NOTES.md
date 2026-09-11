# Release 1.0.0

Initial public reproduction artifact for the associated TDSC manuscript.

Included:
- UID-scoped eBPF collector (`xebpf-1.3.2`, `bpftrace-common-v1.3.2`);
- controlled calibration, benign, and bounded attack-emulation workloads;
- configurable `--hmac-key-path` interface with no deployment-specific key path;
- feature extraction and MODEL-1 transfer analysis;
- matched I/E/B/E+B shift decomposition;
- window sensitivity and feature ablation;
- normalized Wasserstein environment-shift characterization;
- Security-Gym v4.1 external-validation workflows (EV2 and EV2.1).

Not included:
- original operational telemetry;
- raw, sanitized, pseudonymized, or derived host data;
- host inventories or identifiers;
- HMAC keys or pseudonyms;
- company infrastructure configuration;
- Security-Gym data itself.

The original confidential dataset is intentionally unavailable. This release supports
independent methodological reproduction on other Linux systems and external validation
using the independently public Security-Gym v4.1 dataset.
