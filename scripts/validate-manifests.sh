#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -eq 0 ]]; then
  python3 "$ROOT/scripts/validate-manifests.py"
elif [[ $# -ge 1 && $# -le 2 && "$1" == --kubectl ]]; then
  TEAM_ID="${2:-glitch-tec}"
  python3 "$ROOT/scripts/validate-manifests.py" --team "$TEAM_ID"
  # This may need a reachable API for discovery/schema; failure is not hidden.
  kubectl apply --dry-run=client -R -f "$ROOT/k8s"
else
  echo 'Uso: ./scripts/validate-manifests.sh [--kubectl [glitch-tec]]' >&2
  exit 1
fi
