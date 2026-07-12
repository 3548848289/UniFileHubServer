#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/myServer/pids"

stop_service() {
  local service_name="$1"
  local pid_file="$PID_DIR/${service_name}.pid"

  if [[ ! -f "$pid_file" ]]; then
    echo "$service_name is not running (no pid file)"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"

  if kill -0 "$pid" >/dev/null 2>&1; then
    echo "Stopping $service_name (PID $pid) ..."
    kill "$pid"
    sleep 1

    if kill -0 "$pid" >/dev/null 2>&1; then
      echo "Force killing $service_name (PID $pid) ..."
      kill -9 "$pid"
    fi
  else
    echo "$service_name pid file exists, but process $pid is not running"
  fi

  rm -f "$pid_file"
}

stop_service "SharedFile"
stop_service "UserInfo"
stop_service "FIleHistory"
stop_service "PersonalDrive"
stop_service "ClipboardSync"

echo "All managed Python services have been stopped."
