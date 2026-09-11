#!/usr/bin/env bash
set -euo pipefail
NAME="${1:-xebpfexp}"
if id "$NAME" >/dev/null 2>&1; then
  echo "$NAME already exists uid=$(id -u "$NAME")"
  exit 0
fi
if command -v useradd >/dev/null 2>&1; then
  useradd -r -M -s /sbin/nologin "$NAME" 2>/dev/null || useradd -r -M -s /bin/false "$NAME"
else
  echo "ERROR: useradd not found"; exit 1
fi
echo "created $NAME uid=$(id -u "$NAME")"
