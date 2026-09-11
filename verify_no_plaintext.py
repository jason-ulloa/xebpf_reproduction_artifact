#!/usr/bin/env python3
import argparse
import json
import os
import socket
from pathlib import Path

ap = argparse.ArgumentParser(
    description="Validate that persistent XEBPF output does not expose tested plaintext identifiers."
)
ap.add_argument("run_dir")
args = ap.parse_args()

root = Path(args.run_dir)

# Values we expect NEVER to appear as persisted identifiers.
# Do NOT treat generic words such as "root" as leaks because values like
# uid_class="root" and path_class="root_home" are intentional schema categories.
sensitive_values = set()

hostname = socket.gethostname()
if hostname:
    sensitive_values.add(hostname)

fqdn = socket.getfqdn()
if fqdn and fqdn != hostname:
    sensitive_values.add(fqdn)

# Include login/user names only when they are non-generic and sufficiently specific.
for name in (
    os.environ.get("SUDO_USER"),
    os.environ.get("LOGNAME"),
    os.environ.get("USER"),
):
    if name and name.lower() not in {"root", "admin", "administrator"} and len(name) >= 4:
        sensitive_values.add(name)

# Known raw-field names must not exist in event records.
forbidden_event_fields = {
    "hostname", "host", "fqdn", "username", "user", "login", "account",
    "uid", "gid", "process_name", "comm", "executable", "exe",
    "file_path", "filename", "path", "cwd",
    "cmdline", "command_line", "environment", "env", "payload",
    "file_content", "content", "src_ip", "dst_ip", "source_ip",
    "destination_ip", "mac", "mac_address", "domain", "dns_name"
}

issues = []

events = root / "events.jsonl"
if not events.exists():
    print(f"FAIL: missing {events}")
    raise SystemExit(2)

with events.open(errors="replace") as f:
    for lineno, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception as e:
            issues.append(f"events.jsonl:{lineno}: invalid JSON: {e}")
            continue

        present_forbidden = sorted(forbidden_event_fields.intersection(obj.keys()))
        if present_forbidden:
            issues.append(
                f"events.jsonl:{lineno}: forbidden raw fields present: "
                + ",".join(present_forbidden)
            )

        serialized = json.dumps(obj, ensure_ascii=False)
        for value in sensitive_values:
            if value and value in serialized:
                issues.append(
                    f"events.jsonl:{lineno}: tested plaintext identifier found: {value!r}"
                )

# Metadata may legitimately contain os_pretty_name/kernel details, but not raw hostname.
metadata = root / "metadata.json"
if metadata.exists():
    try:
        obj = json.loads(metadata.read_text(errors="replace"))
        for forbidden in ("hostname", "host", "fqdn", "username", "user"):
            if forbidden in obj:
                issues.append(f"metadata.json: forbidden raw field present: {forbidden}")
        serialized = json.dumps(obj, ensure_ascii=False)
        for value in sensitive_values:
            if value and value in serialized:
                issues.append(
                    f"metadata.json: tested plaintext identifier found: {value!r}"
                )
    except Exception as e:
        issues.append(f"metadata.json: invalid JSON: {e}")

if issues:
    print("FAIL: privacy validation found potential issues:")
    for issue in issues[:50]:
        print(" -", issue)
    if len(issues) > 50:
        print(f" - ... {len(issues)-50} additional issue(s)")
    raise SystemExit(2)

print("PASS: no tested plaintext identifiers or forbidden raw fields found.")
