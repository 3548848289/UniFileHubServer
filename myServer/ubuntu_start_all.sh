#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/myServer/logs"
PID_DIR="$ROOT_DIR/myServer/pids"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$LOG_DIR" "$PID_DIR"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python not found: $PYTHON_BIN"
  echo "You can override it like this: PYTHON_BIN=python ./myServer/start_all_ubuntu_python.sh"
  exit 1
fi

DATABASE_URL_DEFAULT="mysql+pymysql://root:Mysql20039248@127.0.0.1:3306/SmartDesk?charset=utf8mb4"
export DATABASE_URL="${DATABASE_URL:-$DATABASE_URL_DEFAULT}"
export SECRET_KEY="${SECRET_KEY:-dev-secret}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-jwt-secret-key}"
export SHAREDCSV_RESOURCE_DIR="${SHAREDCSV_RESOURCE_DIR:-$ROOT_DIR/SharedCSV/resources}"

start_service() {
  local service_name="$1"
  local service_dir="$2"
  local entry_file="$3"
  local log_file="$LOG_DIR/${service_name}.log"
  local pid_file="$PID_DIR/${service_name}.pid"

  if [[ -f "$pid_file" ]]; then
    local old_pid
    old_pid="$(cat "$pid_file")"
    if kill -0 "$old_pid" >/dev/null 2>&1; then
      echo "$service_name is already running (PID $old_pid)"
      return
    fi
    rm -f "$pid_file"
  fi

  echo "Starting $service_name ..."
  (
    cd "$ROOT_DIR/$service_dir"
    nohup "$PYTHON_BIN" "$entry_file" >"$log_file" 2>&1 &
    echo $! >"$pid_file"
  )

  sleep 1
  local new_pid
  new_pid="$(cat "$pid_file")"
  if kill -0 "$new_pid" >/dev/null 2>&1; then
    echo "$service_name started successfully (PID $new_pid)"
  else
    echo "$service_name failed to start. Check log: $log_file"
    rm -f "$pid_file"
    exit 1
  fi
}

start_service "SharedFile" "SharedFile" "app.py"
start_service "UserInfo" "UserInfo" "app.py"
start_service "FIleHistory" "FIleHistory" "app.py"
start_service "PersonalDrive" "PersonalDrive" "run.py"

echo
echo "All Python services are running."
echo "Logs: $LOG_DIR"
echo "Stop script: $ROOT_DIR/myServer/stop_all_ubuntu_python.sh"
