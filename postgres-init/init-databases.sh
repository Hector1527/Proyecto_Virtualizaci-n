#!/usr/bin/env bash
set -Eeuo pipefail

# Se ejecuta automáticamente la primera vez que arranca el contenedor de
# PostgreSQL. Crea una base y un usuario por microservicio, aplica los
# esquemas y carga los datos iniciales.

: "${POSTGRES_USER:=admin}"
: "${POSTGRES_DB:=postgres}"
: "${INVENTARIO_DB_NAME:=inventario_db}"
: "${INVENTARIO_DB_USER:=inventario_user}"
: "${INVENTARIO_DB_PASSWORD:=inventario_pass}"
: "${CLIENTES_DB_NAME:=clientes_db}"
: "${CLIENTES_DB_USER:=clientes_user}"
: "${CLIENTES_DB_PASSWORD:=clientes_pass}"
: "${PEDIDOS_DB_NAME:=pedidos_db}"
: "${PEDIDOS_DB_USER:=pedidos_user}"
: "${PEDIDOS_DB_PASSWORD:=pedidos_pass}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_DIR="${SCHEMA_DIR:-$SCRIPT_DIR/schema}"
SEEDS_DIR="${SEEDS_DIR:-$SCRIPT_DIR/seeds}"
PGHOST_VALUE="${PGHOST:-127.0.0.1}"

PSQL=(psql --host="$PGHOST_VALUE" --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" -v ON_ERROR_STOP=1)

require_identifier() {
  local value="$1"
  if [[ ! "$value" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "Identificador PostgreSQL no válido: $value" >&2
    exit 1
  fi
}

validate_password() {
  local value="$1"
  if [[ ! "$value" =~ ^[A-Za-z0-9._@%+=:,/-]+$ ]]; then
    echo "La contraseña contiene caracteres no soportados por el bootstrap." >&2
    exit 1
  fi
}

create_role() {
  local role="$1"
  local password="$2"
  require_identifier "$role"
  validate_password "$password"

  local exists
  exists="$("${PSQL[@]}" -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$role'" | tr -d '[:space:]')"
  if [[ "$exists" == "1" ]]; then
    "${PSQL[@]}" -c "ALTER ROLE \"$role\" LOGIN PASSWORD '$password'"
  else
    "${PSQL[@]}" -c "CREATE ROLE \"$role\" LOGIN PASSWORD '$password'"
  fi
}

create_database() {
  local database="$1"
  local owner="$2"
  require_identifier "$database"
  require_identifier "$owner"

  local exists
  exists="$("${PSQL[@]}" -tAc "SELECT 1 FROM pg_database WHERE datname = '$database'" | tr -d '[:space:]')"
  if [[ "$exists" != "1" ]]; then
    "${PSQL[@]}" -c "CREATE DATABASE \"$database\" OWNER \"$owner\""
  fi

  "${PSQL[@]}" -c "REVOKE ALL ON DATABASE \"$database\" FROM PUBLIC"
  "${PSQL[@]}" -c "GRANT CONNECT ON DATABASE \"$database\" TO \"$owner\""
}

run_as_service_user() {
  local database="$1"
  local role="$2"
  local password="$3"
  local sql_file="$4"

  PGPASSWORD="$password" psql \
    --host="$PGHOST_VALUE" \
    --username="$role" \
    --dbname="$database" \
    -v ON_ERROR_STOP=1 \
    -f "$sql_file"
}

echo "Creando roles de aplicación..."
create_role "$INVENTARIO_DB_USER" "$INVENTARIO_DB_PASSWORD"
create_role "$CLIENTES_DB_USER" "$CLIENTES_DB_PASSWORD"
create_role "$PEDIDOS_DB_USER" "$PEDIDOS_DB_PASSWORD"

echo "Creando bases de datos..."
create_database "$INVENTARIO_DB_NAME" "$INVENTARIO_DB_USER"
create_database "$CLIENTES_DB_NAME" "$CLIENTES_DB_USER"
create_database "$PEDIDOS_DB_NAME" "$PEDIDOS_DB_USER"

echo "Aplicando esquemas..."
run_as_service_user "$INVENTARIO_DB_NAME" "$INVENTARIO_DB_USER" "$INVENTARIO_DB_PASSWORD" "$SCHEMA_DIR/inventario.sql"
run_as_service_user "$CLIENTES_DB_NAME" "$CLIENTES_DB_USER" "$CLIENTES_DB_PASSWORD" "$SCHEMA_DIR/clientes.sql"
run_as_service_user "$PEDIDOS_DB_NAME" "$PEDIDOS_DB_USER" "$PEDIDOS_DB_PASSWORD" "$SCHEMA_DIR/pedidos.sql"

echo "Aplicando seeds..."
run_as_service_user "$INVENTARIO_DB_NAME" "$INVENTARIO_DB_USER" "$INVENTARIO_DB_PASSWORD" "$SEEDS_DIR/inventario.sql"
run_as_service_user "$CLIENTES_DB_NAME" "$CLIENTES_DB_USER" "$CLIENTES_DB_PASSWORD" "$SEEDS_DIR/clientes.sql"

echo "Bootstrap de El Quetzal completado."
