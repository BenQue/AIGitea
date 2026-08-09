#!/usr/bin/env bash
set -euo pipefail

wrapper_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config_root="$wrapper_root/docker-config"
real_docker_path="$config_root/issue65-real-docker-path"
timeout_path="$config_root/issue65-timeout-path"
timeout_mode_path="$config_root/issue65-timeout-mode"
mode_path="$config_root/issue65-docker-mode"
argv_log="$config_root/issue65-docker-argv.log"

[[ -f "$real_docker_path" && ! -L "$real_docker_path" ]] || exit 94
[[ -f "$timeout_path" && ! -L "$timeout_path" ]] || exit 94
[[ -f "$timeout_mode_path" && ! -L "$timeout_mode_path" ]] || exit 94
real_docker="$(<"$real_docker_path")"
timeout_client="$(<"$timeout_path")"
timeout_mode="$(<"$timeout_mode_path")"
[[ "$real_docker" == /* && -x "$real_docker" ]] || exit 95
[[ "$timeout_client" == /* && -x "$timeout_client" ]] || exit 95
case "$timeout_mode" in
  isolated|foreground) ;;
  *) exit 96 ;;
esac
mode="normal"
if [[ -f "$mode_path" && ! -L "$mode_path" ]]; then
  mode="$(<"$mode_path")"
fi
case "$mode" in
  normal|wrong-compose|wrong-store) ;;
  *) exit 96 ;;
esac

jq -cn --args '$ARGS.positional' -- "$@" >>"$argv_log"
if [[ "$mode" == "wrong-compose" && "${1:-}" == "compose" && "${2:-}" == "version" ]]; then
  printf '%s\n' '5.1.5'
  exit 0
fi
if [[ "$mode" == "wrong-store" && "${1:-}" == "info" && "${3:-}" == "{{.Driver}}" ]]; then
  printf '%s\n' 'overlay2'
  exit 0
fi
if [[ "$mode" == "wrong-store" && "${1:-}" == "info" && "${3:-}" == "{{json .DriverStatus}}" ]]; then
  printf '%s\n' 'null'
  exit 0
fi
if [[ "$timeout_mode" == "foreground" ]]; then
  exec "$timeout_client" --foreground -k 5 120 "$real_docker" "$@"
fi
exec "$timeout_client" -k 5 120 "$real_docker" "$@"
