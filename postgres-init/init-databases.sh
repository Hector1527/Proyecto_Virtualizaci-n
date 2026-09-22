#!/bin/bash
# Corre automáticamente la primera vez que arranca el contenedor de Postgres
# (carpeta /docker-entrypoint-initdb.d). Crea una base y un usuario por
# microservicio, todo dentro del mismo motor Postgres, como pide el
# enunciado ("un solo motor... una base de datos independiente por
# microservicio, cada una con su propio usuario").
#
# NOTA para área 4 (Datos): esto es un borrador funcional para que el
# desarrollo no se detenga. Si ustedes ya tienen su propio script de
# init/seeds, reemplacen este archivo por el suyo — la única condición
# es que terminen creando estas mismas bases (o las que acuerden) para
# que los microservicios de esta carpeta no tengan que cambiar su
# configuración.

set -e

crear_base_y_usuario() {
  local db=$1
  local user=$2
  local password=$3

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER $user WITH PASSWORD '$password';
    CREATE DATABASE $db OWNER $user;
    GRANT ALL PRIVILEGES ON DATABASE $db TO $user;
EOSQL
}

crear_base_y_usuario "inventario_db" "inventario_user" "${INVENTARIO_DB_PASSWORD:-inventario_pass}"
crear_base_y_usuario "clientes_db" "clientes_user" "${CLIENTES_DB_PASSWORD:-clientes_pass}"
crear_base_y_usuario "pedidos_db" "pedidos_user" "${PEDIDOS_DB_PASSWORD:-pedidos_pass}"
