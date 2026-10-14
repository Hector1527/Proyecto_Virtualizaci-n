#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
DOCKERHUB_USER="${DOCKERHUB_USER:-javierini}"
IMAGE_TAG="${IMAGE_TAG:-2.0}"
ACTION="${1:-build}"
if [[ $# -gt 1 || ! "$ACTION" =~ ^(build|push)$ ]]; then
  echo 'Uso: ./scripts/build-push-images.sh [build|push]' >&2
  exit 1
fi
if [[ ! "$DOCKERHUB_USER" =~ ^[a-z0-9][a-z0-9_-]*$ || ! "$IMAGE_TAG" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
  echo 'DOCKERHUB_USER o IMAGE_TAG inválido.' >&2
  exit 1
fi
docker info >/dev/null
SERVICES=(catalogo clientes inventario pedidos reportes frontend gateway)
if [[ "$ACTION" == push ]]; then
  # Read available credentials without printing, saving or refreshing them.
  python3 - <<'PY'
import base64, json, os, shutil, subprocess
from pathlib import Path
config = Path(os.environ.get('DOCKER_CONFIG', str(Path.home() / '.docker'))) / 'config.json'
data = json.loads(config.read_text()) if config.exists() else {}
hosts = ('https://index.docker.io/v1/', 'index.docker.io', 'docker.io')
auth = data.get('auths', {})
helpers = data.get('credHelpers', {})
available = False
for host in hosts:
    entry = auth.get(host, {})
    helper = helpers.get(host) or data.get('credsStore')
    if helper:
        executable = shutil.which('docker-credential-' + helper)
        if executable:
            result = subprocess.run([executable, 'get'], input=host + '\n', text=True, capture_output=True)
            if result.returncode == 0:
                try:
                    credential = json.loads(result.stdout)
                    available = bool(credential.get('Username') and credential.get('Secret'))
                except ValueError:
                    pass
    else:
        if entry.get('identitytoken'):
            available = True
        elif entry.get('auth'):
            try:
                username, password = base64.b64decode(entry['auth']).decode().split(':', 1)
                available = bool(username and password)
            except (ValueError, UnicodeError):
                pass
    if available:
        break
if not available:
    raise SystemExit('No hay entrada de credenciales Docker Hub. Autentícate manualmente antes del push.')
PY
  for service in "${SERVICES[@]}"; do
    docker image inspect "$DOCKERHUB_USER/elquetzal-$service:$IMAGE_TAG" >/dev/null
  done
  for service in "${SERVICES[@]}"; do
    docker push "$DOCKERHUB_USER/elquetzal-$service:$IMAGE_TAG"
  done
else
  for service in catalogo clientes inventario pedidos reportes; do
    docker build -t "$DOCKERHUB_USER/elquetzal-$service:$IMAGE_TAG" "services/$service"
  done
  docker build -t "$DOCKERHUB_USER/elquetzal-frontend:$IMAGE_TAG" frontend
  docker build -f gateway/Dockerfile -t "$DOCKERHUB_USER/elquetzal-gateway:$IMAGE_TAG" .
fi
