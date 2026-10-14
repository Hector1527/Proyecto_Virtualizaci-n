#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -ne 1 ]]; then
  echo 'Uso: ./scripts/configure-project.sh <id-equipo>' >&2
  exit 1
fi
python3 "$ROOT/scripts/project.py" configure "$1"
