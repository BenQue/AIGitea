#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
harness="$root/codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh"
test_root="$(mktemp -d)"
wrapper_group_pid=""
evidence_ancestor_link=""
cleanup() {
  if [[ -n "$wrapper_group_pid" ]] &&
    { kill -0 -- "-$wrapper_group_pid" >/dev/null 2>&1 || kill -0 "$wrapper_group_pid" >/dev/null 2>&1; }; then
    kill -KILL -- "-$wrapper_group_pid" >/dev/null 2>&1 || true
    kill -KILL "$wrapper_group_pid" >/dev/null 2>&1 || true
    wait "$wrapper_group_pid" >/dev/null 2>&1 || true
  fi
  if [[ -n "$evidence_ancestor_link" ]]; then
    rm -f -- "$evidence_ancestor_link"
  fi
  rm -rf -- "$test_root"
}
trap cleanup EXIT

mkdir -p "$test_root/bin"
cat >"$test_root/bin/docker" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' "$*" >>"${FAKE_65_DOCKER_LOG:?}"
[[ "${1:-}" == "--host" && -n "${2:-}" ]] || exit 98
host="$2"
shift 2

if [[ "${1:-}" == "version" && "${2:-}" == "--format" ]]; then
  printf '%s\n' '{"Version":"29.7.1","Os":"linux","Arch":"amd64","Components":[{"Name":"Engine","Version":"29.7.1"},{"Name":"containerd","Version":"2.2.6"}]}'
elif [[ "${1:-}" == "compose" && "${2:-}" == "version" ]]; then
  printf '%s\n' "${FAKE_65_COMPOSE_VERSION:-5.1.4}"
elif [[ "${1:-}" == "info" && "${3:-}" == "{{.Driver}}" ]]; then
  printf '%s\n' 'overlayfs'
elif [[ "${1:-}" == "info" && "${3:-}" == "{{json .DriverStatus}}" ]]; then
  printf '%s\n' '[["driver-type","io.containerd.snapshotter.v1"]]'
elif [[ "${1:-}" == "info" && "${3:-}" == "{{.ID}}" ]]; then
  if [[ "${FAKE_65_SAME_DAEMON:-0}" == "1" || "$host" == "${FAKE_65_PRODUCER_HOST:?}" ]]; then
    printf '%s\n' 'ISSUE65:PRODUCER:DAEMON'
  else
    printf '%s\n' 'ISSUE65:CONSUMER:DAEMON'
  fi
elif [[ "${1:-}" == "info" && "${3:-}" == "{{.DockerRootDir}}" ]]; then
  if [[ "${FAKE_65_SAME_DAEMON:-0}" == "1" || "$host" == "${FAKE_65_PRODUCER_HOST:?}" ]]; then
    printf '%s\n' '/var/lib/docker-issue65-producer'
  else
    printf '%s\n' '/var/lib/docker-issue65-consumer'
  fi
elif [[ "${1:-}" == "image" && "${2:-}" == "inspect" && "${3:-}" == "--format" ]]; then
  if [[ "${5:-}" == *'/registry@sha256:'* ]]; then
    printf '%s\n' '{"Id":"sha256:1111111111111111111111111111111111111111111111111111111111111111","Os":"linux","Architecture":"amd64"}'
  else
    printf '%s\n' '{"Id":"sha256:2222222222222222222222222222222222222222222222222222222222222222","Os":"linux","Architecture":"amd64"}'
  fi
elif [[ "${1:-}" == "container" && "${2:-}" == "ls" ]] ||
  [[ "${1:-}" == "image" && "${2:-}" == "ls" ]] ||
  [[ "${1:-}" == "network" && "${2:-}" == "ls" ]] ||
  [[ "${1:-}" == "volume" && "${2:-}" == "ls" ]]; then
  :
else
  exit 97
fi
SH
chmod 0755 "$test_root/bin/docker"

export PATH="$test_root/bin:$PATH"
export FAKE_65_DOCKER_LOG="$test_root/docker.log"
export FAKE_65_PRODUCER_HOST='ssh://issue65-producer@aisoft-65-producer'
export FAKE_65_CONSUMER_HOST='ssh://issue65-consumer@aisoft-65-consumer'
registry_image="registry.example/library/registry@sha256:$(printf '1%.0s' {1..64})"
postgres_image="registry.example/library/postgres@sha256:$(printf '2%.0s' {1..64})"
release_id='97445947fff79a4c2db6fa764feb21660e281556'
evidence_path="$root/docs/changes/65/fake-evidence-${release_id}.json"
duplicate_evidence_path="$test_root/duplicate-daemon-negative.json"

FAKE_65_SAME_DAEMON=1 \
  AISOFT_65_E2E_READONLY_AUTHORIZED=issue-65-disposable-preflight-approved \
  AISOFT_65_E2E_PRODUCER_DOCKER_HOST="$FAKE_65_PRODUCER_HOST" \
  AISOFT_65_E2E_CONSUMER_DOCKER_HOST="$FAKE_65_CONSUMER_HOST" \
  AISOFT_65_E2E_PRODUCER_ID=aisoft-65-producer \
  AISOFT_65_E2E_CONSUMER_ID=aisoft-65-consumer \
  AISOFT_65_E2E_SOURCE_SHA="$release_id" \
  bash "$harness" --duplicate-daemon-negative >"$duplicate_evidence_path"
chmod 0444 "$duplicate_evidence_path"
jq -e '
  .result == "REJECTED_BEFORE_MUTATION" and .mutations == 0 and
  .shared_daemon_id == "ISSUE65:PRODUCER:DAEMON" and
  .inventory.producer_before == .inventory.producer_after and
  .inventory.consumer_before == .inventory.consumer_after
' "$duplicate_evidence_path" >/dev/null

wrapper_root="$test_root/wrapper-case"
wrapper_config="$wrapper_root/docker-config"
wrapper_exec_log="$wrapper_root/wrapper-exec.json"
mkdir -p "$wrapper_config"
cp "$root/codex/tests/fixtures/docker-release-v2-lifecycle/docker-wrapper.sh" "$wrapper_root/docker-wrapper"
chmod 0755 "$wrapper_root/docker-wrapper"
cat >"$wrapper_root/real-docker" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
script_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
jq -cn --args '$ARGS.positional' -- "$@" >"$script_root/wrapper-exec.json"
if [[ "${1:-}" == "issue65-group-probe" ]]; then
  sleep 30 &
  child_pid="$!"
  jq -n \
    --argjson self_pid "$$" \
    --argjson self_pgid "$(python3 -I -S -c 'import os; print(os.getpgrp())')" \
    --argjson child_pid "$child_pid" \
    --argjson child_pgid "$(python3 -I -S -c 'import os, sys; print(os.getpgid(int(sys.argv[1])))' "$child_pid")" \
    '{self_pid:$self_pid,self_pgid:$self_pgid,child_pid:$child_pid,child_pgid:$child_pgid}' \
    >"${FAKE_65_GROUP_PROBE_PATH:?}"
  trap 'kill "$child_pid" >/dev/null 2>&1 || true; wait "$child_pid" >/dev/null 2>&1 || true; exit 143' TERM INT
  wait "$child_pid"
  exit 0
fi
if [[ "${1:-}" == "image" && "${2:-}" == "inspect" ]]; then
  printf '%s\n' '{"Id":"sha256:3333333333333333333333333333333333333333333333333333333333333333","Os":"linux","Architecture":"amd64"}'
fi
SH
chmod 0755 "$wrapper_root/real-docker"
printf '%s\n' "$wrapper_root/real-docker" >"$wrapper_config/issue65-real-docker-path"
command -v timeout >"$wrapper_config/issue65-timeout-path"
printf '%s\n' isolated >"$wrapper_config/issue65-timeout-mode"
printf '%s\n' normal >"$wrapper_config/issue65-docker-mode"
"$wrapper_root/docker-wrapper" \
  compose --project-name issue65 config --format json
jq -e '. == ["compose","--project-name","issue65","config","--format","json"]' \
  "$wrapper_exec_log" >/dev/null
jq -s -e 'length == 1 and .[0] == ["compose","--project-name","issue65","config","--format","json"]' \
  "$wrapper_config/issue65-docker-argv.log" >/dev/null
printf '%s\n' wrong-compose >"$wrapper_config/issue65-docker-mode"
wrong_compose_wrapper_output="$(
  "$wrapper_root/docker-wrapper" compose version --short
)"
[[ "$wrong_compose_wrapper_output" == "5.1.5" ]]
printf '%s\n' normal >"$wrapper_config/issue65-docker-mode"
group_probe="$test_root/wrapper-process-group.json"
printf '%s\n' foreground >"$wrapper_config/issue65-timeout-mode"
FAKE_65_GROUP_PROBE_PATH="$group_probe" python3 -I -S -c '
import os
import sys
os.setpgrp()
os.execv(sys.argv[1], [sys.argv[1], "issue65-group-probe"])
' "$wrapper_root/docker-wrapper" &
wrapper_group_pid="$!"
for _ in {1..50}; do
  if [[ -f "$group_probe" ]] &&
    jq -e --argjson pgid "$wrapper_group_pid" \
      '.self_pgid == $pgid and .child_pgid == $pgid' "$group_probe" >/dev/null 2>&1; then
    break
  fi
  kill -0 "$wrapper_group_pid" >/dev/null 2>&1 || break
  sleep 0.1
done
jq -e --argjson pgid "$wrapper_group_pid" \
  '.self_pgid == $pgid and .child_pgid == $pgid' "$group_probe" >/dev/null
kill -TERM -- "-$wrapper_group_pid"
wait "$wrapper_group_pid" >/dev/null 2>&1 || true
if kill -0 -- "-$wrapper_group_pid" >/dev/null 2>&1; then
  printf '%s\n' 'foreground timeout wrapper left its owned process group running' >&2
  exit 1
fi
wrapper_group_pid=""
printf '%s\n' isolated >"$wrapper_config/issue65-timeout-mode"
DOCKER_HOST="$FAKE_65_CONSUMER_HOST" PYTHONDONTWRITEBYTECODE=1 \
  python3 -I -S -c '
import sys
sys.path.insert(0, sys.argv[2])
from aisoft_release.docker import DockerAdapter
value = DockerAdapter(__import__("sys").argv[1]).inspect_image("aisoft.local/admin/aisoft-platform/web:97445947fff79a4c2db6fa764feb21660e281556")
assert value["Id"] == "sha256:" + "3" * 64
' "$wrapper_root/docker-wrapper" "$root/codex/runtime"

process_group_ready="$test_root/process-group-ready.json"
PYTHONDONTWRITEBYTECODE=1 python3 -I -S -B \
  "$root/codex/tests/integration/docker-release-v2-lifecycle-driver.py" \
  verify-artifact --new-process-group --process-group-ready-file "$process_group_ready" \
  --release-id "$release_id" --release-root "$test_root/missing-release-root" \
  --compatibility-matrix "$root/docker-release/compatibility/image-stores-v1.json" \
  --docker "$wrapper_root/docker-wrapper" --hostname aisoft-65-consumer \
  >"$test_root/process-group.output" 2>"$test_root/process-group.error" &
process_group_pid="$!"
for _ in {1..50}; do
  if [[ -f "$process_group_ready" ]] &&
    jq -e --argjson pid "$process_group_pid" '.pid == $pid and .pgid == $pid' \
      "$process_group_ready" >/dev/null 2>&1; then
    break
  fi
  kill -0 "$process_group_pid" >/dev/null 2>&1 || break
  sleep 0.1
done
jq -e --argjson pid "$process_group_pid" '.pid == $pid and .pgid == $pid' \
  "$process_group_ready" >/dev/null
if wait "$process_group_pid"; then
  printf '%s\n' 'process-group handshake probe unexpectedly completed a missing release' >&2
  exit 1
fi
grep -Fq 'INVALID_CONTRACT' "$test_root/process-group.error"
grep -Fq 'PYTHONDONTWRITEBYTECODE=1 exec python3 -I -S -B' "$harness"

default_log_lines="$(wc -l <"$FAKE_65_DOCKER_LOG" | tr -d ' ')"
default_output="$(bash "$harness")"
grep -Fq 'NOT RUN: Docker release v2 lifecycle E2E requires separate Issue #65 authorization.' <<<"$default_output"
[[ "$(wc -l <"$FAKE_65_DOCKER_LOG" | tr -d ' ')" == "$default_log_lines" ]]

expect_input_rejected_before_docker() {
  local case_name="$1"
  local expected_error="$2"
  shift 2
  local before_lines
  before_lines="$(wc -l <"$FAKE_65_DOCKER_LOG" | tr -d ' ')"
  if env \
    AISOFT_65_E2E_READONLY_AUTHORIZED=issue-65-disposable-preflight-approved \
    AISOFT_65_E2E_PRODUCER_DOCKER_HOST="$FAKE_65_PRODUCER_HOST" \
    AISOFT_65_E2E_CONSUMER_DOCKER_HOST="$FAKE_65_CONSUMER_HOST" \
    AISOFT_65_E2E_PRODUCER_ID=aisoft-65-producer \
    AISOFT_65_E2E_CONSUMER_ID=aisoft-65-consumer \
    AISOFT_65_E2E_SOURCE_SHA="$release_id" \
    AISOFT_65_E2E_REGISTRY_IMAGE="$registry_image" \
    AISOFT_65_E2E_POSTGRES_IMAGE="$postgres_image" \
    AISOFT_65_E2E_REGISTRY_PORT=5065 \
    AISOFT_65_E2E_EVIDENCE_PATH="$evidence_path" \
    AISOFT_65_E2E_DUPLICATE_DAEMON_EVIDENCE_PATH="$duplicate_evidence_path" \
    "$@" bash "$harness" --preflight \
    >"$test_root/${case_name}.output" 2>"$test_root/${case_name}.error"; then
    printf 'input gate unexpectedly passed: %s\n' "$case_name" >&2
    exit 1
  fi
  grep -Fq "$expected_error" "$test_root/${case_name}.error"
  [[ "$(wc -l <"$FAKE_65_DOCKER_LOG" | tr -d ' ')" == "$before_lines" ]]
}

expect_input_rejected_before_docker authorization 'authorization marker is missing' \
  AISOFT_65_E2E_READONLY_AUTHORIZED=
expect_input_rejected_before_docker endpoint 'must contain only a username and host' \
  AISOFT_65_E2E_PRODUCER_DOCKER_HOST=ssh://issue65-producer:secret@aisoft-65-producer
expect_input_rejected_before_docker logical-id 'AISOFT_65_E2E_PRODUCER_ID is invalid' \
  AISOFT_65_E2E_PRODUCER_ID=Issue65Producer
expect_input_rejected_before_docker source-sha 'must match the Issue #65 fresh-main source SHA' \
  AISOFT_65_E2E_SOURCE_SHA=0000000000000000000000000000000000000000
expect_input_rejected_before_docker digest 'AISOFT_65_E2E_REGISTRY_IMAGE must be digest-pinned' \
  AISOFT_65_E2E_REGISTRY_IMAGE=registry.example/library/registry@sha256:1234
expect_input_rejected_before_docker port 'Registry port is out of range' \
  AISOFT_65_E2E_REGISTRY_PORT=80
expect_input_rejected_before_docker evidence-path 'must be an absolute normalized path' \
  AISOFT_65_E2E_EVIDENCE_PATH=docs/changes/65/fake.json
mkdir -p "$test_root/evidence-outside/subdir"
evidence_ancestor_link="$root/docs/changes/65/fake-ancestor-link-${release_id}"
ln -s "$test_root/evidence-outside" "$evidence_ancestor_link"
expect_input_rejected_before_docker evidence-ancestor-symlink \
  'evidence parent physical path must remain under docs/changes/65' \
  AISOFT_65_E2E_EVIDENCE_PATH="$evidence_ancestor_link/subdir/evidence.json"
rm -f -- "$evidence_ancestor_link"
evidence_ancestor_link=""

tampered_duplicate_evidence="$test_root/tampered-duplicate-daemon-negative.json"
jq '.consumer.daemon_id = "FORGED:DIFFERENT:DAEMON"' "$duplicate_evidence_path" \
  >"$tampered_duplicate_evidence"
chmod 0444 "$tampered_duplicate_evidence"
if AISOFT_65_E2E_READONLY_AUTHORIZED=issue-65-disposable-preflight-approved \
  AISOFT_65_E2E_PRODUCER_DOCKER_HOST="$FAKE_65_PRODUCER_HOST" \
  AISOFT_65_E2E_CONSUMER_DOCKER_HOST="$FAKE_65_CONSUMER_HOST" \
  AISOFT_65_E2E_PRODUCER_ID=aisoft-65-producer \
  AISOFT_65_E2E_CONSUMER_ID=aisoft-65-consumer \
  AISOFT_65_E2E_SOURCE_SHA="$release_id" \
  AISOFT_65_E2E_REGISTRY_IMAGE="$registry_image" \
  AISOFT_65_E2E_POSTGRES_IMAGE="$postgres_image" \
  AISOFT_65_E2E_REGISTRY_PORT=5065 \
  AISOFT_65_E2E_EVIDENCE_PATH="$evidence_path" \
  AISOFT_65_E2E_DUPLICATE_DAEMON_EVIDENCE_PATH="$tampered_duplicate_evidence" \
  bash "$harness" --preflight \
  >"$test_root/tampered-duplicate.output" 2>"$test_root/tampered-duplicate.error"; then
  printf '%s\n' 'forged duplicate-daemon evidence unexpectedly passed' >&2
  exit 1
fi
grep -Fq 'duplicate-daemon negative evidence is invalid' "$test_root/tampered-duplicate.error"

preflight_output="$(
  AISOFT_65_E2E_READONLY_AUTHORIZED=issue-65-disposable-preflight-approved \
    AISOFT_65_E2E_PRODUCER_DOCKER_HOST="$FAKE_65_PRODUCER_HOST" \
    AISOFT_65_E2E_CONSUMER_DOCKER_HOST="$FAKE_65_CONSUMER_HOST" \
    AISOFT_65_E2E_PRODUCER_ID=aisoft-65-producer \
    AISOFT_65_E2E_CONSUMER_ID=aisoft-65-consumer \
    AISOFT_65_E2E_SOURCE_SHA="$release_id" \
    AISOFT_65_E2E_REGISTRY_IMAGE="$registry_image" \
    AISOFT_65_E2E_POSTGRES_IMAGE="$postgres_image" \
    AISOFT_65_E2E_REGISTRY_PORT=5065 \
    AISOFT_65_E2E_EVIDENCE_PATH="$evidence_path" \
    AISOFT_65_E2E_DUPLICATE_DAEMON_EVIDENCE_PATH="$duplicate_evidence_path" \
    bash "$harness" --preflight
)"
jq -e --arg release "$release_id" '
  .result == "PASS_READ_ONLY" and
  .mutations == 0 and
  .source_sha == $release and
  .candidate_bounds.engine.minimum == "29.7.1" and
  .candidate_bounds.engine.maximum_exclusive == "29.7.2" and
  .candidate_bounds.compose.minimum == "5.1.4" and
  .candidate_bounds.compose.maximum_exclusive == "5.1.5" and
  .producer.engine == "29.7.1" and
  .producer.compose == "5.1.4" and
  .producer.containerd == "2.2.6" and
  .producer.daemon_id == "ISSUE65:PRODUCER:DAEMON" and
  .consumer.daemon_id == "ISSUE65:CONSUMER:DAEMON" and
  .producer.docker_root_dir == "/var/lib/docker-issue65-producer" and
  .consumer.docker_root_dir == "/var/lib/docker-issue65-consumer" and
  .prerequisites.registry_image_id == "sha256:1111111111111111111111111111111111111111111111111111111111111111" and
  .prerequisites.postgres_image_id == "sha256:2222222222222222222222222222222222222222222222222222222222222222" and
  .resources.registry_container == "aisoft-65-97445947fff7-registry" and
  .resources.postgres_container == "aisoft-65-97445947fff7-postgres" and
  .resources.compose_project == "aisoft-65-97445947fff7-consumer" and
  .resources.database_network == "aisoft-65-97445947fff7-database" and
  .resources.compose_backend_network == "aisoft-65-97445947fff7-backend" and
  .resources.database_volume == "aisoft-65-97445947fff7-pgdata" and
  (.approval_plan_sha256 | test("^[0-9a-f]{64}$")) and
  .approval_plan.source.sha == $release and
  (.approval_plan.source.candidate_matrix.sha256 | test("^[0-9a-f]{64}$")) and
  .approval_plan.source.candidate_matrix.document.rows[-1].compose.minimum == "5.1.4" and
  (.approval_plan.source.architecture_input.sha256 | test("^[0-9a-f]{64}$")) and
  (.approval_plan.source.docker_client.sha256 | test("^[0-9a-f]{64}$")) and
  (.approval_plan.source.timeout_client.sha256 | test("^[0-9a-f]{64}$")) and
  .approval_plan.mutations.consumer.networks == ["aisoft-65-97445947fff7-database","aisoft-65-97445947fff7-backend"] and
  .approval_plan.baseline_inventory.producer == .inventory.producer and
  .approval_plan.baseline_inventory.consumer == .inventory.consumer and
  .approval_plan.cleanup.prune == false
' <<<"$preflight_output" >/dev/null
canonical_plan="$(jq -cS '.approval_plan' <<<"$preflight_output")"
canonical_plan_sha="$(printf '%s' "$canonical_plan" | shasum -a 256 | awk '{print $1}')"
[[ "$canonical_plan_sha" == "$(jq -er '.approval_plan_sha256' <<<"$preflight_output")" ]]
[[ "$(jq -er '.approval_plan.duplicate_daemon_negative.sha256' <<<"$preflight_output")" == \
  "$(shasum -a 256 "$duplicate_evidence_path" | awk '{print $1}')" ]]

if AISOFT_65_E2E_EXECUTE_AUTHORIZED=issue-65-disposable-e2e-approved \
  AISOFT_65_E2E_APPROVED_PLAN_SHA256="$(printf '0%.0s' {1..64})" \
  AISOFT_65_E2E_PRODUCER_DOCKER_HOST="$FAKE_65_PRODUCER_HOST" \
  AISOFT_65_E2E_CONSUMER_DOCKER_HOST="$FAKE_65_CONSUMER_HOST" \
  AISOFT_65_E2E_PRODUCER_ID=aisoft-65-producer \
  AISOFT_65_E2E_CONSUMER_ID=aisoft-65-consumer \
  AISOFT_65_E2E_SOURCE_SHA="$release_id" \
  AISOFT_65_E2E_REGISTRY_IMAGE="$registry_image" \
  AISOFT_65_E2E_POSTGRES_IMAGE="$postgres_image" \
  AISOFT_65_E2E_REGISTRY_PORT=5065 \
  AISOFT_65_E2E_EVIDENCE_PATH="$evidence_path" \
  AISOFT_65_E2E_DUPLICATE_DAEMON_EVIDENCE_PATH="$duplicate_evidence_path" \
  bash "$harness" --execute >"$test_root/plan-drift.output" 2>"$test_root/plan-drift.error"; then
  printf '%s\n' 'execute with an unapproved Issue #65 plan unexpectedly passed' >&2
  exit 1
fi
if ! grep -Fq 'do not match the separately approved preflight plan SHA-256' "$test_root/plan-drift.error"; then
  sed -n '1,20p' "$test_root/plan-drift.error" >&2
  exit 1
fi
test ! -e "$root/docs/changes/65/.issue65-${release_id}.execution-lock"
if rg -n '(image (pull|tag|save|load|rm|build)|container (run|rm)|compose .* (up|run|down)|network (create|rm)|volume (create|rm)|prune)' \
  "$FAKE_65_DOCKER_LOG"; then
  printf '%s\n' 'Issue #65 read-only preflight emitted a mutating Docker command' >&2
  exit 1
fi

if FAKE_65_SAME_DAEMON=1 \
  AISOFT_65_E2E_READONLY_AUTHORIZED=issue-65-disposable-preflight-approved \
  AISOFT_65_E2E_PRODUCER_DOCKER_HOST="$FAKE_65_PRODUCER_HOST" \
  AISOFT_65_E2E_CONSUMER_DOCKER_HOST="$FAKE_65_CONSUMER_HOST" \
  AISOFT_65_E2E_PRODUCER_ID=aisoft-65-producer \
  AISOFT_65_E2E_CONSUMER_ID=aisoft-65-consumer \
  AISOFT_65_E2E_SOURCE_SHA="$release_id" \
  AISOFT_65_E2E_REGISTRY_IMAGE="$registry_image" \
  AISOFT_65_E2E_POSTGRES_IMAGE="$postgres_image" \
  AISOFT_65_E2E_REGISTRY_PORT=5065 \
  AISOFT_65_E2E_EVIDENCE_PATH="$evidence_path" \
  AISOFT_65_E2E_DUPLICATE_DAEMON_EVIDENCE_PATH="$duplicate_evidence_path" \
  bash "$harness" --preflight >"$test_root/same.output" 2>"$test_root/same.error"; then
  printf '%s\n' 'same-daemon Issue #65 preflight unexpectedly passed' >&2
  exit 1
fi
grep -Fq 'resolve to the same Docker daemon' "$test_root/same.error"

if FAKE_65_COMPOSE_VERSION=5.1.5 \
  AISOFT_65_E2E_READONLY_AUTHORIZED=issue-65-disposable-preflight-approved \
  AISOFT_65_E2E_PRODUCER_DOCKER_HOST="$FAKE_65_PRODUCER_HOST" \
  AISOFT_65_E2E_CONSUMER_DOCKER_HOST="$FAKE_65_CONSUMER_HOST" \
  AISOFT_65_E2E_PRODUCER_ID=aisoft-65-producer \
  AISOFT_65_E2E_CONSUMER_ID=aisoft-65-consumer \
  AISOFT_65_E2E_SOURCE_SHA="$release_id" \
  AISOFT_65_E2E_REGISTRY_IMAGE="$registry_image" \
  AISOFT_65_E2E_POSTGRES_IMAGE="$postgres_image" \
  AISOFT_65_E2E_REGISTRY_PORT=5065 \
  AISOFT_65_E2E_EVIDENCE_PATH="$evidence_path" \
  AISOFT_65_E2E_DUPLICATE_DAEMON_EVIDENCE_PATH="$duplicate_evidence_path" \
  bash "$harness" --preflight >"$test_root/compose.output" 2>"$test_root/compose.error"; then
  printf '%s\n' 'wrong Compose Issue #65 preflight unexpectedly passed' >&2
  exit 1
fi
grep -Fq 'Docker Compose must be exact 5.1.4' "$test_root/compose.error"

grep -Fq 'issue-65-disposable-e2e-approved' "$harness"
grep -Fq 'verify-artifact verify-target stage migrate activate status same-sha-noop' "$harness"
grep -Fq '29.7.1' "$harness"
grep -Fq '5.1.4' "$harness"
grep -Fq '2.2.6' "$harness"
grep -Fq 'started' "$harness"
grep -Fq 'completed' "$harness"
grep -Fq 'migration-noop' "$harness"
PYTHONDONTWRITEBYTECODE=1 python3 -c \
  'import pathlib, sys; path = pathlib.Path(sys.argv[1]); compile(path.read_text(encoding="utf-8"), str(path), "exec")' \
  "$root/codex/tests/integration/docker-release-v2-lifecycle-driver.py"
bash -n "$root/codex/tests/fixtures/docker-release-v2-lifecycle/docker-wrapper.sh"
sh -n "$root/codex/tests/fixtures/docker-release-v2-lifecycle/migrate.sh"
if grep -Eq 'docker[^\n]*prune|system prune|image prune|volume prune|network prune' "$harness"; then
  printf '%s\n' 'Issue #65 harness must never use Docker prune' >&2
  exit 1
fi

printf '%s\n' 'docker release v2 lifecycle E2E harness fake preflight tests passed'
