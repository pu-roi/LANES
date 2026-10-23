#!/bin/sh
# Disposable test service only. Never bind this gate to Cloud SQL.
set -eu
image=${1:?A built API image is required}
container_id=''
cleanup() {
  if [ -n "$container_id" ]; then docker rm -f "$container_id" >/dev/null; fi
}
trap cleanup EXIT HUP INT TERM
POSTGRES_PASSWORD=$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')
POSTGRES_DB="lanes_settings_test_$(od -An -N8 -tx1 /dev/urandom | tr -d ' \n')"
export POSTGRES_PASSWORD POSTGRES_DB
container_id=$(docker run -d --env POSTGRES_PASSWORD --env POSTGRES_DB=postgres postgis/postgis:15-3.4)
ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
  if docker exec "$container_id" pg_isready -h 127.0.0.1 -U postgres -d postgres >/dev/null 2>&1; then
    ready=1; break
  fi
  sleep 1
done
if [ "$ready" != 1 ]; then echo 'Disposable history PostGIS did not become ready' >&2; exit 1; fi
# The image initializes PostGIS in postgres. Migrations must start from a truly
# empty template0 database, not one with pre-created spatial_ref_sys tables.
docker exec "$container_id" createdb -U postgres -T template0 "$POSTGRES_DB"
docker run --rm --network "container:$container_id" \
  --env POSTGRES_PASSWORD --env POSTGRES_DB --env ENVIRONMENT=test \
  --env LANES_REQUIRE_HISTORY_MEDIA_TESTS=1 "$image" sh -c \
  'pip install --no-cache-dir pytest==8.2.2 pytest-asyncio==0.23.7 && python -m scripts.run_history_media_tests'
