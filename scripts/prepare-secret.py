#!/usr/bin/env python3
"""Write only validated credentials to the private temporary env file."""
import os
import re
import sys
from pathlib import Path

from project import SECRET_KEYS


def prepare(output, source=None):
    values = {}
    if source:
        for number, raw in enumerate(Path(source).read_text(encoding='utf-8').splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            key, separator, value = line.partition('=')
            if not separator or key not in SECRET_KEYS or key in values:
                raise ValueError(f'Línea {number}: clave desconocida, duplicada o formato no válido.')
            values[key] = value
    for key in SECRET_KEYS:
        value = os.environ.get(key, values.get(key, ''))
        if not value:
            raise ValueError(f'Falta {key}; no se creó el Secret.')
        # Existing Python models interpolate an unescaped URL. Limit passwords
        # to characters supported by BOTH the URL and the existing SQL bootstrap.
        pattern = r'[A-Za-z_][A-Za-z0-9_]*' if key.endswith('_USER') else r'[A-Za-z0-9._-]+'
        if not re.fullmatch(pattern, value):
            raise ValueError(f'{key}: formato incompatible con el bootstrap o URI actual; consulta README_PROYECTO2.md.')
        values[key] = value
    users = [values[k] for k in SECRET_KEYS if k.endswith('_USER')]
    if len(set(users)) != len(users):
        raise ValueError('Usa cuatro usuarios PostgreSQL distintos.')
    Path(output).write_text(''.join(f'{key}={values[key]}\n' for key in SECRET_KEYS), encoding='utf-8')


if __name__ == '__main__':
    try:
        prepare(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
