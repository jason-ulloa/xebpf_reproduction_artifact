#!/usr/bin/env python3
import argparse
import json
import os
import pwd
import shutil
import subprocess
import time
from pathlib import Path


def latest_run_dir(root: Path, experiment_id: str) -> Path:
    candidates = []
    for d in root.glob(f"{experiment_id}_*"):
        if not d.is_dir():
            continue
        mp = d / "metadata.json"
        try:
            meta = json.loads(mp.read_text())
            if meta.get("experiment_id") != experiment_id:
                continue
            started = float(meta.get("started_at_epoch", 0.0))
        except Exception:
            continue
        candidates.append((started, d))
    if not candidates:
        raise SystemExit(f"ERROR: no run directory found for experiment {experiment_id!r} under {root}")
    candidates.sort(key=lambda x: x[0])
    return candidates[-1][1]


def cmd_preflight(args):
    try:
        pw = pwd.getpwnam(args.user)
    except KeyError:
        raise SystemExit(f"ERROR: user {args.user!r} does not exist")
    if pw.pw_uid == 0:
        raise SystemExit("ERROR: experiment workload user must be non-root")

    workload = Path(args.workload).resolve()
    if not workload.is_file():
        raise SystemExit(f"ERROR: workload file does not exist: {workload}")

    if shutil.which("runuser"):
        cmd = ["runuser", "-u", args.user, "--", "test", "-r", str(workload)]
    elif shutil.which("su"):
        quoted = str(workload).replace("'", "'\\''")
        cmd = ["su", "-s", "/bin/sh", args.user, "-c", f"test -r '{quoted}'"]
    else:
        raise SystemExit("ERROR: neither runuser nor su is available for experiment-user preflight")
    rc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    if rc != 0:
        raise SystemExit(
            f"ERROR: experiment user {args.user!r} cannot read/traverse workload file {workload}. "
            "Place the artifact in a shared location such as /opt/xebpf-reproduction or adjust parent-directory traversal permissions."
        )
    print(f"PREFLIGHT PASS user={args.user} uid={pw.pw_uid} workload={workload}")


def cmd_mark(args):
    root = Path(args.root)
    run_dir = latest_run_dir(root, args.experiment_id)
    obj = {
        "experiment_id": args.experiment_id,
        "workload_id": args.workload_id,
        "workload_completed": True,
        "workload_exit_code": 0,
        "workload_duration_seconds": args.duration,
        "rate_per_second": args.rate,
        "experiment_user": args.user,
        "recorded_at_epoch": time.time(),
    }
    p = run_dir / "workload_status.json"
    p.write_text(json.dumps(obj, indent=2) + "\n")
    os.chmod(p, 0o600)
    print(f"WORKLOAD STATUS PASS {p}")


def main():
    ap = argparse.ArgumentParser(description="Internal runner helpers for the XEBPF reproduction artifact")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("preflight", help="Verify the experiment user can access a workload script")
    p.add_argument("--user", required=True)
    p.add_argument("--workload", required=True)
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("mark", help="Record successful workload completion for the latest matching run")
    p.add_argument("--root", default="/var/lib/ebpf-research")
    p.add_argument("--experiment-id", required=True)
    p.add_argument("--workload-id", required=True)
    p.add_argument("--duration", type=int, required=True)
    p.add_argument("--rate", type=int, required=True)
    p.add_argument("--user", required=True)
    p.set_defaults(func=cmd_mark)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
