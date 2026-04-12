#!/bin/sh
set -e

mkdir -p logs 

echo "Waiting for Redis..."
until redis-cli -h redis -p 6379 ping 2>/dev/null | grep -q PONG; do
  echo "Redis not ready, retrying..."
  sleep 1
done
echo "Redis is up."

echo "Compiling messages..."
python manage.py compilemessages || true

if [ "${BLOG_SEED_DB}" = "true" ]; then
  echo "Seeding database..."
  python manage.py seed
fi

exec "$@"