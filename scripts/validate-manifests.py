#!/usr/bin/env python3
"""Offline consistency checks against the application's actual contracts."""
import argparse
import ast
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit('Falta PyYAML: python3 -m pip install -r scripts/requirements.txt')
from project import ROOT, TEAM_ID, SECRET_KEYS, generated_maps, postgres_entries, validate_id


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(team=TEAM_ID, directory=None):
    validate_id(team)
    require(team == TEAM_ID, f'El ID final de esta entrega es {TEAM_ID}.')
    sources = directory or ROOT / 'k8s'
    objects = []
    for source in sorted(sources.rglob('*.yaml')):
        raw = source.read_text(encoding='utf-8')
        require(not re.search(r'__[A-Z][A-Z0-9_]*__', raw), f'Placeholder sin sustituir: {source}')
        objects.extend(yaml.safe_load_all(raw))
    require(all(isinstance(o, dict) for o in objects), 'Documento YAML vacío o no válido.')
    index = {(o['kind'], o['metadata']['name']): o for o in objects}
    require(len(index) == len(objects), 'Recursos duplicados.')
    namespace = f'proyecto-2-{team}'
    require(('Namespace', namespace) in index, 'Namespace ausente.')
    require(not any(o['kind'] == 'Secret' for o in objects), 'No se versionan Secrets reales.')
    for obj in objects:
        meta = obj['metadata']
        name = meta['name']
        require(len(name) <= 63 and re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?', name), f'Nombre DNS inválido: {name}')
        if obj['kind'] != 'Namespace':
            require(meta.get('namespace') == namespace, f'Namespace incorrecto: {name}')
        require(meta['labels']['team'] == team and meta['labels']['project'] == 'el-quetzal', f'Labels incorrectos: {name}')

    deployments = [o for o in objects if o['kind'] == 'Deployment']
    require(len(deployments) == 8, 'Se requieren ocho Deployments.')
    for dep in deployments:
        app = dep['metadata']['labels']['app']
        spec = dep['spec']['template']['spec']
        pod_labels = dep['spec']['template']['metadata']['labels']
        require(dep['spec']['selector']['matchLabels'] == pod_labels, f'Selector Deployment incorrecto: {app}')
        require(spec['hostname'] == f'{app}-{team}', f'Hostname incorrecto: {app}')
        container = spec['containers'][0]
        expected_image = 'postgres:16' if app == 'postgres' else f'javierini/elquetzal-{app}:2.0'
        require(container['image'] == expected_image, f'Imagen incorrecta: {app}')
        expected_port = 5432 if app == 'postgres' else (80 if app in ('gateway', 'frontend') else 5000)
        require(container['ports'][0]['containerPort'] == expected_port, f'Puerto incorrecto: {app}')
        if directory:
            require(dep['spec']['replicas'] >= 1, f'Réplicas inválidas: {app}')
        else:
            require(dep['spec']['replicas'] == 1, f'Inicialmente una réplica: {app}')
        for c in spec.get('initContainers', []) + spec['containers']:
            for env in c.get('env', []):
                refs = env.get('valueFrom', {})
                if 'configMapKeyRef' in refs:
                    ref = refs['configMapKeyRef']
                    require(('ConfigMap', ref['name']) in index and ref['key'] in index['ConfigMap', ref['name']]['data'], f'ConfigMap/key ausente: {app}/{env["name"]}')
                if 'secretKeyRef' in refs:
                    ref = refs['secretKeyRef']
                    require(ref['name'] == f'db-credentials-{team}' and ref['key'] in SECRET_KEYS, f'Secret/key incorrecto: {app}')
                if 'PASSWORD' in env['name'] or env['name'] == 'DB_USER':
                    require('secretKeyRef' in refs, f'Credencial fuera de Secret: {app}')
        volumes = {v['name']: v for v in spec.get('volumes', [])}
        for vol in volumes.values():
            require('hostPath' not in vol, 'No se permite hostPath.')
            if 'configMap' in vol:
                ref = vol['configMap']
                require(('ConfigMap', ref['name']) in index, f'Volume ConfigMap inexistente: {app}')
                for item in ref.get('items', []):
                    require(item['key'] in index['ConfigMap', ref['name']]['data'], f'Key de montaje ausente: {app}')
            if 'persistentVolumeClaim' in vol:
                require(('PersistentVolumeClaim', vol['persistentVolumeClaim']['claimName']) in index, 'PVC inexistente.')
        for mount in container.get('volumeMounts', []):
            require(mount['name'] in volumes, f'Mount sin volumen: {app}')
        if app != 'postgres':
            path = '/' if app == 'frontend' else ('/health' if app == 'gateway' else f'/api/{app}/health')
            for key in ('readinessProbe', 'livenessProbe', 'startupProbe'):
                require(container[key]['httpGet'] == {'path': path, 'port': 'http'}, f'Probe incorrecta: {app}')
            if app not in ('frontend', 'gateway'):
                code = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / 'services' / app).glob('*.py'))
                require(path in code, f'Health no existe en código: {app}')
                tree = ast.parse(code)
                variables = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Subscript) and ast.unparse(node.value) == 'os.environ' and isinstance(node.slice, ast.Constant):
                        variables.add(node.slice.value)
                    if isinstance(node, ast.Call) and ast.unparse(node.func) == 'os.environ.get' and node.args and isinstance(node.args[0], ast.Constant):
                        variables.add(node.args[0].value)
                env_names = {e['name'] for e in container.get('env', [])}
                require(variables <= env_names, f'Variables de código sin configurar: {app}: {variables - env_names}')
        if app in ('clientes', 'inventario', 'pedidos'):
            require(spec['initContainers'][0]['name'] == 'wait-postgres', f'Falta espera PostgreSQL: {app}')
        if app == 'postgres':
            require(dep['spec']['replicas'] == 1 and dep['spec']['strategy']['type'] == 'Recreate', 'PostgreSQL debe ser único/Recreate.')
            env = {e['name']: e for e in container['env']}
            require(env['PGHOST']['value'] == '/var/run/postgresql', 'PGHOST debe conservar socket.')
            mounts = {m['mountPath']: m for m in container['volumeMounts']}
            require(mounts['/var/lib/postgresql/data']['name'] == 'data', 'Montaje de datos incorrecto.')
            require(mounts['/docker-entrypoint-initdb.d']['readOnly'], 'Inicialización debe ser solo lectura.')
            expected_paths = {'init-databases.sh', 'schema/clientes.sql', 'schema/inventario.sql', 'schema/pedidos.sql', 'seeds/clientes.sql', 'seeds/inventario.sql'}
            require({i['path'] for i in volumes['init']['configMap']['items']} == expected_paths, 'Rutas de bootstrap incorrectas.')
            require('-h 127.0.0.1' in container['startupProbe']['exec']['command'][-1], 'Probe no debe aceptar servidor temporal de bootstrap.')

    services = [o for o in objects if o['kind'] == 'Service']
    require(len(services) == 9, 'Se requieren siete ClusterIP, un NodePort y un LoadBalancer.')
    for svc in services:
        matches = [d for d in deployments if all(d['spec']['template']['metadata']['labels'].get(k) == v for k, v in svc['spec']['selector'].items())]
        require(len(matches) == 1, f'Service sin Deployment único: {svc["metadata"]["name"]}')
        ports = matches[0]['spec']['template']['spec']['containers'][0]['ports']
        for p in svc['spec']['ports']:
            require(any(p['targetPort'] in (c['name'], c['containerPort']) for c in ports), 'targetPort incorrecto.')
        if svc['spec']['type'] == 'NodePort':
            require(svc['spec']['ports'][0]['nodePort'] == 30080, 'NodePort incorrecto.')
        if svc['spec']['type'] == 'LoadBalancer':
            require(svc['spec']['ports'][0]['port'] == 8080, 'LoadBalancer incorrecto.')

    config = index['ConfigMap', f'app-config-{team}']['data']
    require(config['DB_HOST'] == f'postgres-{team}' and config['DB_PORT'] == '5432', 'Host/puerto DB incorrectos.')
    for app in ('inventario', 'clientes', 'pedidos'):
        require(config[f'{app.upper()}_DB_NAME'] == f'{app}_db', f'Base incorrecta: {app}')
    require(config['UMBRAL_STOCK_BAJO'] == '10', 'Umbral incorrecto.')
    for app in ('inventario', 'pedidos'):
        require(config[f'{app.upper()}_URL'] == f'http://{app}-{team}:5000', 'URL interna incorrecta.')
    nginx = index['ConfigMap', f'gateway-config-{team}']['data']['nginx.conf']
    for host, port in re.findall(r'proxy_pass http://([^:;]+):(\d+);', nginx):
        require(('Service', host) in index and int(port) == index['Service', host]['spec']['ports'][0]['port'], f'DNS/puerto nginx incorrecto: {host}')
    require(len(re.findall('proxy_pass', nginx)) == 6 and 'location = /health' in nginx, 'Rutas nginx incompletas.')
    for app in ('catalogo', 'clientes', 'inventario', 'pedidos', 'reportes'):
        require(f'location /api/{app}' in nginx, f'Ruta nginx ausente: {app}')
    require(index['ConfigMap', f'postgres-init-{team}']['data'] == postgres_entries(), 'SQL/bootstrap desincronizado.')
    for relative, expected in generated_maps().items():
        if not directory:
            require((ROOT / 'k8s' / relative).read_text(encoding='utf-8') == expected, f'ConfigMap desincronizado: {relative}; ejecuta project.py sync-configmaps.')
    pvc = index['PersistentVolumeClaim', f'postgres-data-{team}']['spec']
    require(pvc['accessModes'] == ['ReadWriteOnce'] and pvc['storageClassName'] == 'local-path' and pvc['resources']['requests']['storage'] == '1Gi', 'PVC incorrecto.')
    require('try_files $uri $uri/ /index.html;' in (ROOT / 'frontend/nginx.conf').read_text(), 'Falta SPA fallback.')
    for source in (ROOT / 'frontend/src').rglob('*.vue'):
        require(not re.search(r'fetch\([\s]*[\'"`]https?://', source.read_text(encoding='utf-8')), 'Frontend usa backend absoluto.')
    seed = (ROOT / 'postgres-init/seeds/clientes.sql').read_text(encoding='utf-8')
    for carne in ('1072123', '1185023', '1207022', '1184523', '1304223', '1143323'):
        require(carne in seed, f'Carné sin seed: {carne}')
    require('1234567' not in seed and '7654321' not in seed, 'Carnés ficticios en seed.')
    print(f'OK: {len(objects)} manifiestos; DNS, selectors, puertos, imágenes, probes, variables, credenciales, PVC, mounts, SQL, SPA y carnés coherentes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--team', default=TEAM_ID, help='ID final confirmado: glitch-tec; no se sustituyen valores.')
    parser.add_argument('--directory', type=Path)
    args = parser.parse_args()
    try:
        validate(args.team, args.directory)
    except (ValueError, KeyError, yaml.YAMLError) as exc:
        raise SystemExit(f'ERROR: {exc}') from exc
