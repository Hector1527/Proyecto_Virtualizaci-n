#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -eq 0 ]]; then
  python3 "$ROOT/scripts/validate-manifests.py"
elif [[ $# -eq 2 && "$1" == --kubectl ]]; then
  TEAM_ID="$2"
  python3 "$ROOT/scripts/project.py" configure "$TEAM_ID"
  python3 "$ROOT/scripts/validate-manifests.py" --team "$TEAM_ID" --directory "$ROOT/.generated/$TEAM_ID/k8s"
  # This may need a reachable API for discovery/schema; failure is not hidden.
  kubectl apply --dry-run=client -R -f "$ROOT/.generated/$TEAM_ID/k8s"
else
  echo 'Uso: ./scripts/validate-manifests.sh [--kubectl <id-equipo>]' >&2
  exit 1
fi
