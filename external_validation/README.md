# External validation reproduction - Security-Gym v4.1

This directory reproduces the **external behavioral validation** portion of the study. It does not redistribute Security-Gym data.

Frozen dataset:

- Security-Gym v4.1
- DOI `10.5281/zenodo.21763493`
- stream `exp_30d_heavy_v4.db.zst`
- compressed SHA-256 `4e903e2ba8d50945070c23109079388fa318db8f995ce1c3958e1447082f8824`

The downloader obtains the stream from the official Hugging Face mirror and rejects a hash mismatch.

Use a non-production analysis system. The runner checks writeability and requires at least 12 GiB free in this working location; the decompressed SQLite stream is approximately 8.5 GB.

## Execute and validate

Run from this exact directory:

```bash
cd /opt/xebpf-reproduction/external_validation
bash ./run_external_validation.sh
```

The script:

1. performs a local preflight;
2. creates an isolated Python environment;
3. installs the declared analysis dependencies;
4. downloads and SHA-256 verifies the frozen 30-day stream;
5. builds 5-second eBPF features;
6. executes EV2 temporal and pure leave-one-attack-family-out evaluation;
7. executes EV2.1 strict 70/30 temporal + family holdout with the reported RF100 sensitivity configuration;
8. runs `validate_external_validation.py`.

Expected completion includes:

```text
INTEGRITY GATE: PASS
FEATURE EXTRACTION GATE: PASS
EXTERNAL-VALIDATION-2: PASS
EV2.1 STRICT TEMPORAL + FAMILY HOLDOUT: PASS
Structural/frozen-dataset result: PASS
```

The validator checks frozen dataset identity, 457,786 windows, 6,180 malicious windows, the five expected attack families, expected result files, and the reported EV2.1 family-mean values within a numerical tolerance. A larger numerical deviation is surfaced as a warning for investigation rather than automatically treated as a structural protocol failure.

## Interpretation guardrail

Security-Gym is **external behavioral validation only**. Its provenance is not a controlled Linux-environment experiment, so it must not be used as causal evidence for an operating-system, kernel, or infrastructure environment effect.

No Security-Gym database, raw events, identifiers, paths, IPs, usernames, commands, campaign IDs, or absolute timestamps are bundled in this artifact.
