#!/bin/sh
set -e

echo "Waiting for database and applying migrations..."
while ! python manage.py migrate --noinput 2>/tmp/migrate.err; do
  cat /tmp/migrate.err
  echo "Database unavailable or migrate failed. Retrying in 3 seconds..."
  sleep 3
done

python manage.py collectstatic --noinput
exec "$@"
