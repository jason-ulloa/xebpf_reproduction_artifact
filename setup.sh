#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: execute as root"
  exit 1
fi

echo "== Detecting operating system =="
. /etc/os-release
echo "${PRETTY_NAME:-$ID}"

echo "== Installing dependencies =="
if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y bpftrace python3 zip
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y bpftrace python3 zip || {
    echo "ERROR: bpftrace could not be installed from enabled repositories."
    exit 2
  }
elif command -v zypper >/dev/null 2>&1; then
  zypper --non-interactive refresh
  zypper --non-interactive install bpftrace python3 zip
else
  echo "ERROR: unsupported package manager"
  exit 3
fi

echo "== Tracepoint capability validation =="
for e in \
  syscalls/sys_enter_execve \
  sched/sched_process_exit \
  syscalls/sys_enter_connect \
  syscalls/sys_enter_accept4 \
  syscalls/sys_enter_openat \
  syscalls/sys_enter_unlinkat
do
  if [ -d "/sys/kernel/tracing/events/$e" ]; then
    echo "PASS $e"
  else
    echo "FAIL $e"
  fi
done

echo
bpftrace --version
python3 --version
echo
echo "Setup complete."
echo "Next: create your own key with ./generate_hmac_key.sh /path/to/research.key"
