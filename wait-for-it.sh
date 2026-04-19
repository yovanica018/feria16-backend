#!/usr/bin/env bash
# wait-for-it.sh

host="$1"
shift
cmd="$@"

until nc -z "$host" 5432; do
  echo "Esperando a que la base de datos esté disponible..."
  sleep 2
done

echo "Base de datos lista. Iniciando aplicación..."
exec $cmd
