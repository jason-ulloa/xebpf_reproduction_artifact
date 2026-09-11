#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /path/to/research.key"
  exit 2
fi

KEY_PATH="$1"
KEY_DIR="$(dirname "$KEY_PATH")"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: execute as root so the key can be created with restrictive permissions"
  exit 1
fi

install -d -m 700 "$KEY_DIR"

if [ -e "$KEY_PATH" ]; then
  echo "ERROR: refusing to overwrite existing key: $KEY_PATH"
  exit 3
fi

umask 077
if command -v openssl >/dev/null 2>&1; then
  openssl rand 48 > "$KEY_PATH"
else
  head -c 48 /dev/urandom > "$KEY_PATH"
fi
chmod 600 "$KEY_PATH"
echo "Created experiment key: $KEY_PATH"
echo "Use the same key on all experiment hosts if cross-host pseudonym consistency is required."
echo "Never include the key in result bundles or public artifacts."
