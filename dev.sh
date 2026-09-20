#!/usr/bin/env bash
set -euo pipefail
SEMA_SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$SEMA_SOURCE_DIR/scripts/dev.py" "$@"
