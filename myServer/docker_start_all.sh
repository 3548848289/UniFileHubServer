#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="/app"
MYSQL_DATA_DIR="/var/lib/mysql"
MYSQL_SOCKET="/run/mysqld/mysqld.sock"
MYSQL_MARKER="$MYSQL_DATA_DIR/.unifileserver_initialized"

export MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-Mysql20039248}"
export MYSQL_DATABASE="${MYSQL_DATABASE:-SmartDesk}"
export MYSQL_APP_USER="${MYSQL_APP_USER:-smartdesk}"
export MYSQL_APP_PASSWORD="${MYSQL_APP_PASSWORD:-smartdesk}"
export DATABASE_URL="${DATABASE_URL:-mysql+pymysql://${MYSQL_APP_USER}:${MYSQL_APP_PASSWORD}@127.0.0.1:3306/${MYSQL_DATABASE}?charset=utf8mb4}"
export SECRET_KEY="${SECRET_KEY:-dev-secret}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-jwt-secret-key}"
export SHAREDCSV_RESOURCE_DIR="${SHAREDCSV_RESOURCE_DIR:-$ROOT_DIR/SharedCSV/resources}"
export STORAGE_ROOT="${STORAGE_ROOT:-$ROOT_DIR/PersonalDrive/app/storage}"

mkdir -p \
  "$ROOT_DIR/myServer/logs" \
  "$ROOT_DIR/SharedCSV/resources" \
  "$ROOT_DIR/SharedFile/uploads" \
  "$ROOT_DIR/UserInfo/avatars" \
  "$ROOT_DIR/FIleHistory/uploads" \
  "$ROOT_DIR/PersonalDrive/app/storage" \
  /run/mysqld \
  "$MYSQL_DATA_DIR"

chown -R mysql:mysql /run/mysqld "$MYSQL_DATA_DIR"

MYSQL_FIRST_INIT=0
if [[ ! -d "$MYSQL_DATA_DIR/mysql" ]]; then
  echo "Initializing MySQL data directory..."
  mariadb-install-db --user=mysql --datadir="$MYSQL_DATA_DIR" >/dev/null
  MYSQL_FIRST_INIT=1
fi

echo "Starting MySQL..."
mysqld_safe --user=mysql --datadir="$MYSQL_DATA_DIR" --socket="$MYSQL_SOCKET" --bind-address=0.0.0.0 &
MYSQL_PID=$!

for _ in $(seq 1 60); do
  if mysqladmin --protocol=socket --socket="$MYSQL_SOCKET" ping >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! mysqladmin --protocol=socket --socket="$MYSQL_SOCKET" ping >/dev/null 2>&1; then
  echo "MySQL failed to start."
  exit 1
fi

if [[ "$MYSQL_FIRST_INIT" -eq 1 || ! -f "$MYSQL_MARKER" ]]; then
  echo "Bootstrapping MySQL users and database..."
  mysql --protocol=socket --socket="$MYSQL_SOCKET" -uroot <<SQL
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}';
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_APP_USER}'@'%' IDENTIFIED BY '${MYSQL_APP_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_APP_USER}'@'%';
FLUSH PRIVILEGES;
SQL
  touch "$MYSQL_MARKER"
else
  mysql --protocol=socket --socket="$MYSQL_SOCKET" -uroot -p"${MYSQL_ROOT_PASSWORD}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_APP_USER}'@'%' IDENTIFIED BY '${MYSQL_APP_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_APP_USER}'@'%';
FLUSH PRIVILEGES;
SQL
fi

init_userinfo_db() {
  (
    cd "$ROOT_DIR/UserInfo"
    python3 - <<'PY'
from app import create_app, db

app = create_app()
with app.app_context():
    db.create_all()
PY
  )
}

init_personaldrive_db() {
  (
    cd "$ROOT_DIR/PersonalDrive"
    python3 - <<'PY'
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
PY
  )
}

init_clipboardsync_db() {
  (
    cd "$ROOT_DIR/ClipboardSync"
    python3 - <<'PY'
from app import create_app, db
from app.schema import ensure_clipboard_schema

app = create_app()
with app.app_context():
    db.create_all()
    ensure_clipboard_schema()
PY
  )
}

echo "Initializing application tables..."
init_userinfo_db
init_personaldrive_db
init_clipboardsync_db

echo "Checking nginx config..."
nginx -t

echo "Starting Nginx..."
nginx
NGINX_PID=$(pidof nginx | awk '{print $1}')

start_service() {
  local name="$1"
  local dir="$2"
  local entry="$3"

  echo "Starting $name..."
  (
    cd "$ROOT_DIR/$dir"
    exec python3 "$entry"
  ) &
  PIDS+=($!)
}

PIDS=("$MYSQL_PID" "$NGINX_PID")
start_service "SharedFile" "SharedFile" "app.py"
start_service "UserInfo" "UserInfo" "app.py"
start_service "FIleHistory" "FIleHistory" "app.py"
start_service "PersonalDrive" "PersonalDrive" "run.py"
start_service "ClipboardSync" "ClipboardSync" "app.py"

trap 'kill "${PIDS[@]}" 2>/dev/null || true' TERM INT

while true; do
  set +e
  wait -n
  status=$?
  set -e
  kill "${PIDS[@]}" 2>/dev/null || true
  wait || true
  exit "$status"
done
