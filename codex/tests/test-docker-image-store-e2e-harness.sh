#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
harness="$root/codex/tests/integration/test-docker-image-store-e2e.sh"
test_root="$(mktemp -d)"
trap 'rm -rf -- "$test_root"' EXIT

mkdir -p "$test_root/bin"
cat >"$test_root/bin/docker" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' "$*" >>"${FAKE_DOCKER_LOG:?}"
[[ "${1:-}" == "--host" && -n "${2:-}" ]] || exit 98
host="$2"
shift 2

if [[ "${1:-}" == "version" && "${2:-}" == "--format" ]]; then
  printf '%s\n' '{"Version":"29.0.1","Os":"linux","Arch":"amd64"}'
elif [[ "${1:-}" == "compose" && "${2:-}" == "version" ]]; then
  printf '%s\n' 'v2.40.3'
elif [[ "${1:-}" == "info" && "${3:-}" == "{{.Driver}}" ]]; then
  printf '%s\n' 'overlayfs'
elif [[ "${1:-}" == "info" && "${3:-}" == "{{json .DriverStatus}}" ]]; then
  printf '%s\n' '[["driver-type","io.containerd.snapshotter.v1"]]'
elif [[ "${1:-}" == "info" && "${3:-}" == "{{.ID}}" ]]; then
  if [[ "${FAKE_SAME_DAEMON:-0}" == "1" || "$host" == "${FAKE_PRODUCER_HOST:?}" ]]; then
    printf '%s\n' 'PRODUCER:DAEMON:1'
  else
    printf '%s\n' 'CONSUMER:DAEMON:2'
  fi
elif [[ "${1:-}" == "info" && "${3:-}" == "{{.DockerRootDir}}" ]]; then
  if [[ "$host" == "${FAKE_PRODUCER_HOST:?}" ]]; then
    printf '%s\n' '/var/lib/docker-producer'
  else
    printf '%s\n' '/var/lib/docker-consumer'
  fi
elif [[ "${1:-}" == "image" && "${2:-}" == "inspect" && "${3:-}" == "--format" &&
  "${4:-}" == "{{json .}}" && "${5:-}" == "${FAKE_REGISTRY_IMAGE:?}" ]]; then
  printf '%s\n' '{"Id":"sha256:2222222222222222222222222222222222222222222222222222222222222222","Os":"linux","Architecture":"amd64"}'
elif [[ "${1:-}" == "image" && "${2:-}" == "inspect" ]]; then
  if [[ "${3:-}" == "${FAKE_REGISTRY_IMAGE:?}" ]]; then
    printf '%s\n' '{}'
    exit 0
  fi
  exit 1
elif [[ "${1:-}" == "container" && "${2:-}" == "inspect" ]]; then
  exit 1
elif [[ "${1:-}" == "ps" ]]; then
  exit 0
else
  exit 97
fi
SH
cat >"$test_root/bin/go" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' 'preflight unexpectedly called go' >>"${FAKE_GO_LOG:?}"
exit 99
SH
chmod 0755 "$test_root/bin/docker" "$test_root/bin/go"

export PATH="$test_root/bin:$PATH"
export FAKE_DOCKER_LOG="$test_root/docker.log"
export FAKE_GO_LOG="$test_root/go.log"
export FAKE_PRODUCER_HOST="ssh://aisoft-27-producer@orb"
export FAKE_CONSUMER_HOST="ssh://aisoft-27-consumer@orb"
FAKE_REGISTRY_IMAGE="registry.example/library/registry@sha256:$(printf '1%.0s' {1..64})"
export FAKE_REGISTRY_IMAGE

default_output="$(bash "$harness")"
grep -Fq 'NOT RUN: Docker image-store E2E' <<<"$default_output"
test ! -e "$FAKE_DOCKER_LOG"
test ! -e "$FAKE_GO_LOG"

preflight_output="$(
  AISOFT_E2E_READONLY_AUTHORIZED=issue-27-disposable-preflight-approved \
    AISOFT_E2E_PRODUCER_DOCKER_HOST="$FAKE_PRODUCER_HOST" \
    AISOFT_E2E_CONSUMER_DOCKER_HOST="$FAKE_CONSUMER_HOST" \
    AISOFT_E2E_PRODUCER_ID=producer-fixture \
    AISOFT_E2E_CONSUMER_ID=consumer-fixture \
    AISOFT_E2E_RELEASE_ID="$(printf 'a%.0s' {1..40})" \
    AISOFT_E2E_EXPECTED_STORE=containerd \
    AISOFT_E2E_REGISTRY_IMAGE="$FAKE_REGISTRY_IMAGE" \
    AISOFT_E2E_REGISTRY_PORT=5001 \
    bash "$harness" --preflight
)"
jq -e '
  .result == "PASS_READ_ONLY" and
  .mutations == 0 and
  .producer.daemon_id == "PRODUCER:DAEMON:1" and
  .consumer.daemon_id == "CONSUMER:DAEMON:2" and
  .producer.docker_root_dir == "/var/lib/docker-producer" and
  .consumer.docker_root_dir == "/var/lib/docker-consumer"
' <<<"$preflight_output" >/dev/null
test ! -e "$FAKE_GO_LOG"
if rg -n '(image (pull|tag|save|load|rm)|container (run|rm)|compose .* (up|down)|network rm)' \
  "$FAKE_DOCKER_LOG"; then
  printf '%s\n' 'read-only preflight emitted a mutating Docker command' >&2
  exit 1
fi

same_daemon_error="$test_root/same-daemon.error"
if FAKE_SAME_DAEMON=1 \
  AISOFT_E2E_READONLY_AUTHORIZED=issue-27-disposable-preflight-approved \
  AISOFT_E2E_PRODUCER_DOCKER_HOST="$FAKE_PRODUCER_HOST" \
  AISOFT_E2E_CONSUMER_DOCKER_HOST="$FAKE_CONSUMER_HOST" \
  AISOFT_E2E_PRODUCER_ID=producer-fixture \
  AISOFT_E2E_CONSUMER_ID=consumer-fixture \
  AISOFT_E2E_RELEASE_ID="$(printf 'a%.0s' {1..40})" \
  AISOFT_E2E_EXPECTED_STORE=containerd \
  AISOFT_E2E_REGISTRY_IMAGE="$FAKE_REGISTRY_IMAGE" \
  AISOFT_E2E_REGISTRY_PORT=5001 \
  bash "$harness" --preflight >"$test_root/same-daemon.output" 2>"$same_daemon_error"; then
  printf '%s\n' 'same-daemon preflight unexpectedly passed' >&2
  exit 1
fi
grep -Fq 'resolve to the same Docker daemon' "$same_daemon_error"
test ! -e "$FAKE_GO_LOG"

unsafe_endpoint_error="$test_root/unsafe-endpoint.error"
if AISOFT_E2E_READONLY_AUTHORIZED=issue-27-disposable-preflight-approved \
  AISOFT_E2E_PRODUCER_DOCKER_HOST='ssh://user:password@orb' \
  AISOFT_E2E_CONSUMER_DOCKER_HOST="$FAKE_CONSUMER_HOST" \
  AISOFT_E2E_PRODUCER_ID=producer-fixture \
  AISOFT_E2E_CONSUMER_ID=consumer-fixture \
  AISOFT_E2E_RELEASE_ID="$(printf 'a%.0s' {1..40})" \
  AISOFT_E2E_EXPECTED_STORE=containerd \
  AISOFT_E2E_REGISTRY_IMAGE="$FAKE_REGISTRY_IMAGE" \
  AISOFT_E2E_REGISTRY_PORT=5001 \
  bash "$harness" --preflight >"$test_root/unsafe-endpoint.output" 2>"$unsafe_endpoint_error"; then
  printf '%s\n' 'credential-bearing SSH endpoint unexpectedly passed' >&2
  exit 1
fi
grep -Fq 'SSH endpoint must contain only a username and host' "$unsafe_endpoint_error"
grep -Fq -- "container rm --force --volumes \"\$registry_container\"" "$harness"
grep -Fq -- "--tmpfs \"/var/lib/registry:rw,nosuid,nodev,noexec,size=67108864\"" "$harness"
grep -Fq -- 'volume ls --quiet' "$harness"
grep -Fq -- 'image ls --all --no-trunc --quiet' "$harness"
grep -Fq -- 'memory:"268435456"' "$harness"
grep -Fq -- 'consumer state: exit={{.State.ExitCode}} oom={{.State.OOMKilled}}' "$harness"

printf '%s\n' 'docker image-store E2E harness fake preflight tests passed'
