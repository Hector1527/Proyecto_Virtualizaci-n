#!/usr/bin/env bash
set -Eeuo pipefail
# Do not run this script with bash -x: credentials must never be echoed.
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo 'Uso: ./scripts/create-secret.sh <id-equipo> [archivo.secret]' >&2
  exit 1
fi
TEAM_ID="$1"
python3 "$ROOT/scripts/project.py" configure "$TEAM_ID"
umask 077
SECRET_TEMP="$(mktemp "${TMPDIR:-/tmp}/elquetzal-credentials.XXXXXX.secret")"
trap 'rm -f -- "$SECRET_TEMP"' EXIT
if [[ $# -eq 2 ]]; then
  python3 "$ROOT/scripts/prepare-secret.py" "$SECRET_TEMP" "$2"
else
  python3 "$ROOT/scripts/prepare-secret.py" "$SECRET_TEMP"
fi
# Namespace must exist before a namespaced Secret can be created.
kubectl apply -f "$ROOT/.generated/$TEAM_ID/k8s/namespace.yaml"
kubectl -n "proyecto-2-$TEAM_ID" create secret generic "db-credentials-$TEAM_ID" \
  --from-env-file="$SECRET_TEMP" --dry-run=client -o yaml | kubectl apply -f -
echo "Secret db-credentials-$TEAM_ID creado/actualizado; valores no mostrados."
