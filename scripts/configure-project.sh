#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# Optional check only: the final manifests already live in k8s/.
if [[ $# -ne 1 ]]; then
  echo 'Uso: ./scripts/configure-project.sh glitch-tec (comprobación opcional)' >&2
  exit 1
fi
python3 "$ROOT/scripts/project.py" configure "$1"
