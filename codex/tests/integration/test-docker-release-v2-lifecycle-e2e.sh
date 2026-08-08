#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
expected_source_sha="97445947fff79a4c2db6fa764feb21660e281556"
fixture_root="$root/codex/tests/fixtures/docker-release-v2-lifecycle"
web_fixture_root="$root/codex/tests/fixtures/docker-image-store-e2e"
driver="$root/codex/tests/integration/docker-release-v2-lifecycle-driver.py"
driver_source="$driver"
wrapper_source="$fixture_root/docker-wrapper.sh"
web_source="$web_fixture_root/server.go"
migration_source="$fixture_root/migrate.sh"
mode="${1:---not-run}"

# Required public lifecycle order: verify-artifact verify-target stage migrate activate status same-sha-noop

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

not_run() {
  printf '%s\n' 'NOT RUN: Docker release v2 lifecycle E2E requires separate Issue #65 authorization.'
  printf '%s\n' 'Use --preflight for an approved read-only probe or --execute for the exact approved disposable fixture.'
}

validate_docker_host() {
  local side="$1"
  local host="$2"
  [[ "$host" != *$'\n'* && "$host" != *$'\r'* ]] ||
    fail "$side Docker host endpoint contains invalid characters"
  if [[ "$host" == ssh://* ]]; then
    [[ "$host" =~ ^ssh://[A-Za-z0-9][A-Za-z0-9._-]{0,127}@[A-Za-z0-9][A-Za-z0-9.-]{0,252}$ ]] ||
      fail "$side Docker SSH endpoint must contain only a username and host"
  else
    [[ "$host" != *"@"* ]] || fail "$side Docker host endpoint must not embed credentials"
  fi
}

safe_id() {
  [[ "$1" =~ ^[a-z0-9][a-z0-9.-]{0,63}$ ]]
}

sha256_file() {
  shasum -a 256 "$1" | awk '{print $1}'
}

file_mode() {
  stat -c '%a' "$1" 2>/dev/null || stat -f '%Lp' "$1"
}

case "$mode" in
  --not-run)
    not_run
    exit 0
    ;;
  --preflight|--duplicate-daemon-negative|--execute) ;;
  *) fail 'usage: test-docker-release-v2-lifecycle-e2e.sh [--not-run|--preflight|--duplicate-daemon-negative|--execute]' ;;
esac

if [[ "$mode" == "--preflight" || "$mode" == "--duplicate-daemon-negative" ]]; then
  [[ "${AISOFT_65_E2E_READONLY_AUTHORIZED:-}" == "issue-65-disposable-preflight-approved" ]] ||
    fail 'Issue #65 read-only preflight authorization marker is missing'
else
  [[ "${AISOFT_65_E2E_EXECUTE_AUTHORIZED:-}" == "issue-65-disposable-e2e-approved" ]] ||
    fail 'Issue #65 execute authorization marker is missing'
fi

for command in awk date docker git jq shasum sort stat timeout; do
  command -v "$command" >/dev/null 2>&1 || fail "required command is unavailable: $command"
done

resolve_executable_path() {
  local executable_path
  executable_path="$(command -v "$1")"
  [[ "$executable_path" == /* ]] ||
    executable_path="$(cd -- "$(dirname -- "$executable_path")" && pwd -P)/$(basename -- "$executable_path")"
  [[ -f "$executable_path" && -x "$executable_path" ]] || fail "$1 must resolve to a regular executable file"
  printf '%s\n' "$executable_path"
}

docker_client_path="$(resolve_executable_path docker)"
timeout_client_path="$(resolve_executable_path timeout)"
docker_client_sha="$(sha256_file "$docker_client_path")"
timeout_client_sha="$(sha256_file "$timeout_client_path")"

producer_host="${AISOFT_65_E2E_PRODUCER_DOCKER_HOST:-}"
consumer_host="${AISOFT_65_E2E_CONSUMER_DOCKER_HOST:-}"
producer_id="${AISOFT_65_E2E_PRODUCER_ID:-}"
consumer_id="${AISOFT_65_E2E_CONSUMER_ID:-}"
source_sha="${AISOFT_65_E2E_SOURCE_SHA:-}"
registry_image="${AISOFT_65_E2E_REGISTRY_IMAGE:-}"
postgres_image="${AISOFT_65_E2E_POSTGRES_IMAGE:-}"
registry_port="${AISOFT_65_E2E_REGISTRY_PORT:-}"
evidence_path="${AISOFT_65_E2E_EVIDENCE_PATH:-}"
duplicate_evidence_path="${AISOFT_65_E2E_DUPLICATE_DAEMON_EVIDENCE_PATH:-}"

[[ -n "$producer_host" && -n "$consumer_host" ]] || fail 'two Docker hosts are required'
[[ "$producer_host" != "$consumer_host" ]] || fail 'producer and consumer Docker hosts must differ'
validate_docker_host producer "$producer_host"
validate_docker_host consumer "$consumer_host"
safe_id "$producer_id" || fail 'AISOFT_65_E2E_PRODUCER_ID is invalid'
safe_id "$consumer_id" || fail 'AISOFT_65_E2E_CONSUMER_ID is invalid'
[[ "$producer_id" != "$consumer_id" ]] || fail 'producer and consumer IDs must differ'
[[ "$source_sha" =~ ^[0-9a-f]{40}$ ]] || fail 'AISOFT_65_E2E_SOURCE_SHA must be a full Git SHA'
[[ "$source_sha" == "$expected_source_sha" ]] || fail 'AISOFT_65_E2E_SOURCE_SHA must match the Issue #65 fresh-main source SHA'
if [[ "$mode" != "--duplicate-daemon-negative" ]]; then
  [[ "$registry_image" =~ ^[a-z0-9][a-z0-9./:_-]*@sha256:[0-9a-f]{64}$ ]] ||
    fail 'AISOFT_65_E2E_REGISTRY_IMAGE must be digest-pinned'
  [[ "$postgres_image" =~ ^[a-z0-9][a-z0-9./:_-]*@sha256:[0-9a-f]{64}$ ]] ||
    fail 'AISOFT_65_E2E_POSTGRES_IMAGE must be digest-pinned'
  [[ "$registry_port" =~ ^[0-9]+$ ]] || fail 'AISOFT_65_E2E_REGISTRY_PORT must be numeric'
  ((registry_port >= 1024 && registry_port <= 65535)) || fail 'Registry port is out of range'
  [[ "$evidence_path" == /* && "$evidence_path" != *".."* ]] ||
    fail 'AISOFT_65_E2E_EVIDENCE_PATH must be an absolute normalized path'
  [[ "$evidence_path" == "$root/docs/changes/65/"* ]] ||
    fail 'AISOFT_65_E2E_EVIDENCE_PATH must remain under docs/changes/65'
  evidence_parent="$(dirname -- "$evidence_path")"
  [[ -d "$evidence_parent" && ! -L "$evidence_parent" ]] ||
    fail 'evidence parent must be an existing non-symlink directory'
  evidence_root_physical="$(cd -P -- "$root/docs/changes/65" && pwd -P)"
  evidence_parent_physical="$(cd -P -- "$evidence_parent" && pwd -P)"
  [[ "$evidence_parent_physical" == "$evidence_root_physical" ||
    "$evidence_parent_physical" == "$evidence_root_physical/"* ]] ||
    fail 'evidence parent physical path must remain under docs/changes/65'
  [[ ! -e "$evidence_path" && ! -L "$evidence_path" ]] || fail 'immutable evidence path already exists'
  [[ "$duplicate_evidence_path" == /* && -f "$duplicate_evidence_path" && ! -L "$duplicate_evidence_path" ]] ||
    fail 'AISOFT_65_E2E_DUPLICATE_DAEMON_EVIDENCE_PATH must be an absolute regular file'
  [[ "$(file_mode "$duplicate_evidence_path")" == "444" ]] ||
    fail 'duplicate-daemon negative evidence mode must be 0444'
fi

prefix="aisoft-65-${source_sha:0:12}"
registry_container="$prefix-registry"
postgres_container="$prefix-postgres"
compose_project="$prefix-consumer"
database_network="$prefix-database"
compose_backend_network="$prefix-backend"
database_volume="$prefix-pgdata"
migration_seed_container="$prefix-migration-seed"
producer_build_web="$prefix-web-build:fixture"
producer_build_migrate="$prefix-migrate-build:fixture"
registry_web_tag="127.0.0.1:${registry_port}/admin/aisoft-platform/web:${source_sha}"
registry_migrate_tag="127.0.0.1:${registry_port}/admin/aisoft-platform/migrate:${source_sha}"
runtime_web="aisoft.local/admin/aisoft-platform/web:${source_sha}"
runtime_migrate="aisoft.local/admin/aisoft-platform/migrate:${source_sha}"
orchestrator_log=""

log_orchestrator_argv() {
  local side="$1"
  shift
  [[ -z "$orchestrator_log" ]] ||
    jq -cn --arg side "$side" --args \
      '{side:$side,argv:$ARGS.positional}' -- "$@" >>"$orchestrator_log"
}

docker_producer() {
  log_orchestrator_argv producer "$@"
  "$timeout_client_path" -k 5 30 "$docker_client_path" --host "$producer_host" "$@"
}

docker_consumer() {
  log_orchestrator_argv consumer "$@"
  "$timeout_client_path" -k 5 30 "$docker_client_path" --host "$consumer_host" "$@"
}

detect_capability() {
  local side="$1"
  local server compose_version driver driver_status daemon_id docker_root_dir
  local engine_version containerd_version marker_count driver_type_count
  if [[ "$side" == "producer" ]]; then
    server="$(docker_producer version --format '{{json .Server}}')"
    compose_version="$(docker_producer compose version --short)"
    driver="$(docker_producer info --format '{{.Driver}}')"
    driver_status="$(docker_producer info --format '{{json .DriverStatus}}')"
    daemon_id="$(docker_producer info --format '{{.ID}}')"
    docker_root_dir="$(docker_producer info --format '{{.DockerRootDir}}')"
  else
    server="$(docker_consumer version --format '{{json .Server}}')"
    compose_version="$(docker_consumer compose version --short)"
    driver="$(docker_consumer info --format '{{.Driver}}')"
    driver_status="$(docker_consumer info --format '{{json .DriverStatus}}')"
    daemon_id="$(docker_consumer info --format '{{.ID}}')"
    docker_root_dir="$(docker_consumer info --format '{{.DockerRootDir}}')"
  fi
  compose_version="${compose_version#v}"
  engine_version="$(jq -er '.Version' <<<"$server")"
  containerd_version="$(
    jq -er '[.Components[]? | select(.Name == "containerd") | .Version] |
      if length == 1 then .[0] else error("containerd component count") end' <<<"$server"
  )"
  jq -e '.Os == "linux" and .Arch == "amd64"' <<<"$server" >/dev/null ||
    fail "$side Docker server must report linux/amd64"
  [[ "$engine_version" == "29.7.1" ]] || fail "$side Docker Engine must be exact 29.7.1"
  [[ "$compose_version" == "5.1.4" ]] || fail "$side Docker Compose must be exact 5.1.4"
  [[ "$containerd_version" == "2.2.6" ]] || fail "$side containerd must be exact 2.2.6"
  jq -e '(. == null) or (type == "array")' <<<"$driver_status" >/dev/null ||
    fail "$side Docker DriverStatus is invalid"
  marker_count="$(jq '[.[]? | select(.[0] == "driver-type" and .[1] == "io.containerd.snapshotter.v1")] | length' <<<"$driver_status")"
  driver_type_count="$(jq '[.[]? | select(.[0] == "driver-type")] | length' <<<"$driver_status")"
  [[ "$marker_count" == "1" && "$driver_type_count" == "1" && "$driver" == "overlayfs" ]] ||
    fail "$side Docker image store must be exact containerd overlayfs marker"
  [[ -n "$daemon_id" && ${#daemon_id} -le 256 && "$daemon_id" != *$'\n'* ]] ||
    fail "$side Docker daemon ID is invalid"
  [[ "$docker_root_dir" == /* && ${#docker_root_dir} -le 4096 && "$docker_root_dir" != *$'\n'* ]] ||
    fail "$side Docker data root is invalid"
  jq -n \
    --arg engine "$engine_version" \
    --arg compose "$compose_version" \
    --arg containerd "$containerd_version" \
    --arg daemon_id "$daemon_id" \
    --arg docker_root_dir "$docker_root_dir" \
    '{engine:$engine,compose:$compose,containerd:$containerd,os:"linux",architecture:"amd64",image_store:"containerd",daemon_id:$daemon_id,docker_root_dir:$docker_root_dir}'
}

inspect_preloaded() {
  local side="$1"
  local image="$2"
  local metadata
  if [[ "$side" == "producer" ]]; then
    metadata="$(docker_producer image inspect --format '{{json .}}' "$image" 2>/dev/null)" ||
      fail "$side digest-pinned prerequisite image is not preloaded"
  else
    metadata="$(docker_consumer image inspect --format '{{json .}}' "$image" 2>/dev/null)" ||
      fail "$side digest-pinned prerequisite image is not preloaded"
  fi
  jq -e 'type == "object" and (.Id | type == "string" and test("^sha256:[0-9a-f]{64}$")) and .Os == "linux" and .Architecture == "amd64"' \
    <<<"$metadata" >/dev/null || fail "$side prerequisite image metadata is invalid"
  printf '%s\n' "$metadata"
}

inventory() {
  local side="$1"
  local containers images image_ids repo_digests networks volumes
  if [[ "$side" == "producer" ]]; then
    containers="$(docker_producer container ls --all --no-trunc --format '{{.ID}} {{.Names}}' | LC_ALL=C sort)"
    images="$(docker_producer image ls --all --digests --no-trunc --format '{{.ID}} {{.Repository}}:{{.Tag}}@{{.Digest}}' | LC_ALL=C sort)"
    image_ids="$(docker_producer image ls --all --quiet --no-trunc | LC_ALL=C sort -u)"
    repo_digests="$({
      while IFS= read -r image_id; do
        [[ -n "$image_id" ]] || continue
        docker_producer image inspect --format '{{json .RepoDigests}}' "$image_id" | jq -r '.[]?'
      done <<<"$image_ids"
    } | LC_ALL=C sort -u)"
    networks="$(docker_producer network ls --no-trunc --format '{{.ID}} {{.Name}}' | LC_ALL=C sort)"
    volumes="$(docker_producer volume ls --format '{{.Name}}' | LC_ALL=C sort)"
  else
    containers="$(docker_consumer container ls --all --no-trunc --format '{{.ID}} {{.Names}}' | LC_ALL=C sort)"
    images="$(docker_consumer image ls --all --digests --no-trunc --format '{{.ID}} {{.Repository}}:{{.Tag}}@{{.Digest}}' | LC_ALL=C sort)"
    image_ids="$(docker_consumer image ls --all --quiet --no-trunc | LC_ALL=C sort -u)"
    repo_digests="$({
      while IFS= read -r image_id; do
        [[ -n "$image_id" ]] || continue
        docker_consumer image inspect --format '{{json .RepoDigests}}' "$image_id" | jq -r '.[]?'
      done <<<"$image_ids"
    } | LC_ALL=C sort -u)"
    networks="$(docker_consumer network ls --no-trunc --format '{{.ID}} {{.Name}}' | LC_ALL=C sort)"
    volumes="$(docker_consumer volume ls --format '{{.Name}}' | LC_ALL=C sort)"
  fi
  jq -n \
    --arg containers "$containers" \
    --arg images "$images" \
    --arg repo_digests "$repo_digests" \
    --arg networks "$networks" \
    --arg volumes "$volumes" \
    '{containers:$containers,images:$images,repo_digests:$repo_digests,networks:$networks,volumes:$volumes}'
}

assert_resource_absent() {
  docker_producer container inspect "$registry_container" >/dev/null 2>&1 &&
    fail 'fixture Registry container already exists'
  docker_producer container inspect "$migration_seed_container" >/dev/null 2>&1 &&
    fail 'fixture migration seed container already exists'
  docker_consumer container inspect "$postgres_container" >/dev/null 2>&1 &&
    fail 'fixture PostgreSQL container already exists'
  docker_consumer network inspect "$database_network" >/dev/null 2>&1 &&
    fail 'fixture database network already exists'
  docker_consumer network inspect "$compose_backend_network" >/dev/null 2>&1 &&
    fail 'fixture Compose backend network already exists'
  docker_consumer volume inspect "$database_volume" >/dev/null 2>&1 &&
    fail 'fixture database volume already exists'
  docker_producer image inspect "$runtime_web" >/dev/null 2>&1 && fail 'fixture web runtime tag exists on producer'
  docker_producer image inspect "$runtime_migrate" >/dev/null 2>&1 && fail 'fixture migration runtime tag exists on producer'
  docker_producer image inspect "$producer_build_web" >/dev/null 2>&1 && fail 'fixture web build tag exists on producer'
  docker_producer image inspect "$producer_build_migrate" >/dev/null 2>&1 && fail 'fixture migration build tag exists on producer'
  docker_producer image inspect "$registry_web_tag" >/dev/null 2>&1 && fail 'fixture Registry web tag exists on producer'
  docker_producer image inspect "$registry_migrate_tag" >/dev/null 2>&1 && fail 'fixture Registry migration tag exists on producer'
  docker_consumer image inspect "$runtime_web" >/dev/null 2>&1 && fail 'fixture web runtime tag exists on consumer'
  docker_consumer image inspect "$runtime_migrate" >/dev/null 2>&1 && fail 'fixture migration runtime tag exists on consumer'
  [[ -z "$(docker_consumer container ls --all --quiet --filter "label=com.docker.compose.project=$compose_project")" ]] ||
    fail 'fixture Compose project already exists on consumer'
}

producer_capability="$(detect_capability producer)"
consumer_capability="$(detect_capability consumer)"
producer_daemon_id="$(jq -er '.daemon_id' <<<"$producer_capability")"
consumer_daemon_id="$(jq -er '.daemon_id' <<<"$consumer_capability")"
producer_docker_root="$(jq -er '.docker_root_dir' <<<"$producer_capability")"
consumer_docker_root="$(jq -er '.docker_root_dir' <<<"$consumer_capability")"
if [[ "$mode" == "--duplicate-daemon-negative" ]]; then
  [[ "$producer_daemon_id" == "$consumer_daemon_id" ]] ||
    fail 'duplicate-daemon negative requires two aliases that resolve to one daemon ID'
  [[ "$producer_docker_root" == "$consumer_docker_root" ]] ||
    fail 'duplicate-daemon aliases returned inconsistent Docker data roots'
  duplicate_producer_before="$(inventory producer)"
  duplicate_consumer_before="$(inventory consumer)"
  duplicate_producer_after="$(inventory producer)"
  duplicate_consumer_after="$(inventory consumer)"
  [[ "$duplicate_producer_before" == "$duplicate_producer_after" && "$duplicate_consumer_before" == "$duplicate_consumer_after" ]] ||
    fail 'duplicate-daemon negative changed Docker inventory'
  jq -n \
    --arg source_sha "$source_sha" \
    --arg harness_sha256 "$(sha256_file "$root/codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh")" \
    --arg producer_host "$producer_host" \
    --arg consumer_host "$consumer_host" \
    --arg daemon_id "$producer_daemon_id" \
    --arg docker_root_dir "$producer_docker_root" \
    --argjson producer "$producer_capability" \
    --argjson consumer "$consumer_capability" \
    --argjson producer_before "$duplicate_producer_before" \
    --argjson consumer_before "$duplicate_consumer_before" \
    --argjson producer_after "$duplicate_producer_after" \
    --argjson consumer_after "$duplicate_consumer_after" '
    {contract_version:"aisoft-issue-65-duplicate-daemon-negative/v1",result:"REJECTED_BEFORE_MUTATION",mutations:0,
     source_sha:$source_sha,harness_sha256:$harness_sha256,producer_endpoint:$producer_host,consumer_endpoint:$consumer_host,producer:$producer,consumer:$consumer,shared_daemon_id:$daemon_id,shared_docker_root_dir:$docker_root_dir,
     inventory:{producer_before:$producer_before,consumer_before:$consumer_before,producer_after:$producer_after,consumer_after:$consumer_after}}
  '
  exit 0
fi
[[ "$producer_daemon_id" != "$consumer_daemon_id" ]] ||
  fail 'producer and consumer endpoints resolve to the same Docker daemon'
[[ "$producer_docker_root" != "$consumer_docker_root" ]] ||
  fail 'producer and consumer Docker data roots must differ'
duplicate_daemon_evidence="$(<"$duplicate_evidence_path")"
jq -e \
  --arg source_sha "$source_sha" \
  --arg harness_sha256 "$(sha256_file "$root/codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh")" '
  (keys | sort) == ["consumer","consumer_endpoint","contract_version","harness_sha256","inventory","mutations","producer","producer_endpoint","result","shared_daemon_id","shared_docker_root_dir","source_sha"] and
  .contract_version == "aisoft-issue-65-duplicate-daemon-negative/v1" and
  .result == "REJECTED_BEFORE_MUTATION" and .mutations == 0 and .source_sha == $source_sha and
  .harness_sha256 == $harness_sha256 and
  .producer.engine == "29.7.1" and .producer.compose == "5.1.4" and .producer.containerd == "2.2.6" and .producer.image_store == "containerd" and
  .consumer.engine == "29.7.1" and .consumer.compose == "5.1.4" and .consumer.containerd == "2.2.6" and .consumer.image_store == "containerd" and
  .producer_endpoint != .consumer_endpoint and
  .producer.daemon_id == .shared_daemon_id and
  .consumer.daemon_id == .shared_daemon_id and
  .producer.docker_root_dir == .shared_docker_root_dir and
  .consumer.docker_root_dir == .shared_docker_root_dir and
  (.shared_daemon_id | type == "string" and length > 0) and
  (.shared_docker_root_dir | type == "string" and startswith("/")) and
  .inventory.producer_before == .inventory.producer_after and
  .inventory.consumer_before == .inventory.consumer_after
' <<<"$duplicate_daemon_evidence" >/dev/null || fail 'duplicate-daemon negative evidence is invalid'
duplicate_daemon_evidence_sha256="$(sha256_file "$duplicate_evidence_path")"
producer_registry_metadata="$(inspect_preloaded producer "$registry_image")"
producer_postgres_metadata="$(inspect_preloaded producer "$postgres_image")"
consumer_postgres_metadata="$(inspect_preloaded consumer "$postgres_image")"
registry_image_id="$(jq -er '.Id' <<<"$producer_registry_metadata")"
producer_postgres_image_id="$(jq -er '.Id' <<<"$producer_postgres_metadata")"
consumer_postgres_image_id="$(jq -er '.Id' <<<"$consumer_postgres_metadata")"
[[ "$producer_postgres_image_id" == "$consumer_postgres_image_id" ]] ||
  fail 'producer and consumer PostgreSQL prerequisite image IDs differ'
[[ "$registry_image_id" != "$producer_postgres_image_id" ]] ||
  fail 'Registry and PostgreSQL prerequisite image IDs must differ'
prerequisites_json="$(
  jq -n \
    --arg registry_image "$registry_image" \
    --arg registry_image_id "$registry_image_id" \
    --arg postgres_image "$postgres_image" \
    --arg postgres_image_id "$producer_postgres_image_id" \
    '{registry_image:$registry_image,registry_image_id:$registry_image_id,postgres_image:$postgres_image,postgres_image_id:$postgres_image_id}'
)"
assert_resource_absent

producer_inventory_before="$(inventory producer)"
consumer_inventory_before="$(inventory consumer)"
resources_json="$(
  jq -n \
    --arg registry_container "$registry_container" \
    --arg postgres_container "$postgres_container" \
    --arg compose_project "$compose_project" \
    --arg database_network "$database_network" \
    --arg compose_backend_network "$compose_backend_network" \
    --arg database_volume "$database_volume" \
    '{registry_container:$registry_container,postgres_container:$postgres_container,compose_project:$compose_project,database_network:$database_network,compose_backend_network:$compose_backend_network,database_volume:$database_volume}'
)"

[[ "$(git -C "$root" rev-parse "$source_sha^{commit}")" == "$source_sha" ]] ||
  fail 'Issue #65 source SHA is not available in the AISoftPlatform repository'
git -C "$root" diff --quiet "$source_sha" -- docker-release codex/runtime/aisoft_release ||
  fail 'merged docker-release/v2 or release runtime bytes differ from the fixed source SHA'
[[ -z "$(git -C "$root" status --porcelain --untracked-files=all -- docker-release codex/runtime/aisoft_release)" ]] ||
  fail 'docker-release/v2 or release runtime contains tracked or untracked drift from the fixed source SHA'
source_tree="$(git -C "$root" rev-parse "$source_sha^{tree}")"
docker_release_tree="$(git -C "$root" rev-parse "$source_sha:docker-release")"
runtime_tree="$(git -C "$root" rev-parse "$source_sha:codex/runtime/aisoft_release")"
harness_sha="$(sha256_file "$root/codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh")"
driver_sha="$(sha256_file "$driver_source")"
wrapper_sha="$(sha256_file "$wrapper_source")"
web_source_sha="$(sha256_file "$web_source")"
migration_source_sha="$(sha256_file "$migration_source")"
approval_date="$(date +%F)"
candidate_matrix_json="$(
  jq \
    --arg source "docs/changes/65/verification-compose-514-lifecycle-260808.md" \
    --arg evidence "issue-65-compose-5.1.4-${source_sha:0:12}" \
    --arg date "$approval_date" '
    .matrix_revision = "2026.08.3" |
    .rows += [{
      row_id:"engine-29.7.1-compose-5.1.4-containerd-linux-amd64",
      engine:{minimum:"29.7.1",maximum_exclusive:"29.7.2"},
      compose:{minimum:"5.1.4",maximum_exclusive:"5.1.5"},
      os:"linux",architecture:"amd64",image_store:"containerd",status:"supported",
      evidence:{kind:"real-e2e",evidence_id:$evidence,date:$date,source:$source},
      remediation:"Expand only after the same task-owned disposable real lifecycle E2E passes and its immutable evidence is committed."
    }]
  ' "$root/docker-release/compatibility/image-stores-v1.json"
)"
candidate_matrix_sha="$(printf '%s\n' "$candidate_matrix_json" | shasum -a 256 | awk '{print $1}')"
architecture_source_path="$root/architecture/reference/newemaint/target-candidate/architecture.lock.json"
architecture_source_sha="$(sha256_file "$architecture_source_path")"

approval_plan_json="$(
  jq -cS -n \
    --arg source_sha "$source_sha" \
    --arg source_tree "$source_tree" \
    --arg docker_release_tree "$docker_release_tree" \
    --arg runtime_tree "$runtime_tree" \
    --arg harness_sha "$harness_sha" \
    --arg driver_sha "$driver_sha" \
    --arg wrapper_sha "$wrapper_sha" \
    --arg web_source_sha "$web_source_sha" \
    --arg migration_source_sha "$migration_source_sha" \
    --arg approval_date "$approval_date" \
    --argjson candidate_matrix "$candidate_matrix_json" \
    --arg candidate_matrix_sha "$candidate_matrix_sha" \
    --arg architecture_source_path "architecture/reference/newemaint/target-candidate/architecture.lock.json" \
    --arg architecture_source_sha "$architecture_source_sha" \
    --arg docker_client_path "$docker_client_path" \
    --arg docker_client_sha "$docker_client_sha" \
    --arg timeout_client_path "$timeout_client_path" \
    --arg timeout_client_sha "$timeout_client_sha" \
    --arg producer_host "$producer_host" \
    --arg consumer_host "$consumer_host" \
    --arg producer_id "$producer_id" \
    --arg consumer_id "$consumer_id" \
    --argjson producer "$producer_capability" \
    --argjson consumer "$consumer_capability" \
    --argjson prerequisites "$prerequisites_json" \
    --argjson duplicate_daemon_evidence "$duplicate_daemon_evidence" \
    --arg duplicate_daemon_evidence_path "$duplicate_evidence_path" \
    --arg duplicate_daemon_evidence_sha256 "$duplicate_daemon_evidence_sha256" \
    --argjson resources "$resources_json" \
    --argjson producer_inventory "$producer_inventory_before" \
    --argjson consumer_inventory "$consumer_inventory_before" \
    --arg registry_port "$registry_port" \
    --arg producer_build_web "$producer_build_web" \
    --arg producer_build_migrate "$producer_build_migrate" \
    --arg registry_web_tag "$registry_web_tag" \
    --arg registry_migrate_tag "$registry_migrate_tag" \
    --arg runtime_web "$runtime_web" \
    --arg runtime_migrate "$runtime_migrate" \
    --arg evidence_path "$evidence_path" \
    --arg execution_lock "$root/docs/changes/65/.issue65-${source_sha}.execution-lock" '
    {contract_version:"aisoft-issue-65-execution-plan/v1",
     source:{sha:$source_sha,tree:$source_tree,docker_release_tree:$docker_release_tree,runtime_tree:$runtime_tree,harness_sha256:$harness_sha,driver_sha256:$driver_sha,wrapper_sha256:$wrapper_sha,web_fixture_sha256:$web_source_sha,migration_fixture_sha256:$migration_source_sha,approval_date:$approval_date,candidate_matrix:{sha256:$candidate_matrix_sha,document:$candidate_matrix},architecture_input:{path:$architecture_source_path,sha256:$architecture_source_sha},docker_client:{path:$docker_client_path,sha256:$docker_client_sha},timeout_client:{path:$timeout_client_path,sha256:$timeout_client_sha,direct_seconds:30,lifecycle_seconds:120,kill_after_seconds:5,migration_foreground_in_owned_pgid:true,other_lifecycle_isolated_group:true}},
     producer:{endpoint:$producer_host,logical_id:$producer_id,capability:$producer},
     consumer:{endpoint:$consumer_host,logical_id:$consumer_id,capability:$consumer},
     prerequisites:$prerequisites,duplicate_daemon_negative:{path:$duplicate_daemon_evidence_path,sha256:$duplicate_daemon_evidence_sha256,evidence:$duplicate_daemon_evidence},registry_port:($registry_port|tonumber),resources:$resources,evidence_path:$evidence_path,execution_lock:$execution_lock,baseline_inventory:{producer:$producer_inventory,consumer:$consumer_inventory},
     mutations:{producer:{images:[$producer_build_web,$producer_build_migrate,$registry_web_tag,$registry_migrate_tag,$runtime_web,$runtime_migrate],containers:[$resources.registry_container,($resources.registry_container|sub("-registry$";"-migration-seed"))],registry_push_pull:true,archive_save:true},consumer:{registry_pull_probe:true,offline_load_tags:[$runtime_web,$runtime_migrate],containers:[$resources.postgres_container],compose_project:{name:$resources.compose_project,owned_label:("com.docker.compose.project="+$resources.compose_project)},networks:[$resources.database_network,$resources.compose_backend_network],volumes:[$resources.database_volume],migration_fixture:true,compose_activate:true}},
     cleanup:{prune:false,delete_only_declared_resources:true,inventory_must_equal_baseline:true,failure_bundle_suffix:".failure.<pid>.json",execution_lock_create_remove:true,retain_lock_if_process_group_not_quiesced:true}}
  '
)"
approval_plan_sha256="$(printf '%s' "$approval_plan_json" | shasum -a 256 | awk '{print $1}')"

if [[ "$mode" == "--preflight" ]]; then
  jq -n \
    --arg source_sha "$source_sha" \
    --argjson producer "$producer_capability" \
    --argjson consumer "$consumer_capability" \
    --argjson resources "$resources_json" \
    --argjson prerequisites "$prerequisites_json" \
    --argjson approval_plan "$approval_plan_json" \
    --arg approval_plan_sha256 "$approval_plan_sha256" \
    --argjson producer_inventory "$producer_inventory_before" \
    --argjson consumer_inventory "$consumer_inventory_before" \
    '{result:"PASS_READ_ONLY",mutations:0,source_sha:$source_sha,candidate_bounds:{engine:{minimum:"29.7.1",maximum_exclusive:"29.7.2"},compose:{minimum:"5.1.4",maximum_exclusive:"5.1.5"}},producer:$producer,consumer:$consumer,prerequisites:$prerequisites,resources:$resources,approval_plan:$approval_plan,approval_plan_sha256:$approval_plan_sha256,inventory:{producer:$producer_inventory,consumer:$consumer_inventory}}'
  exit 0
fi

[[ "${AISOFT_65_E2E_APPROVED_PLAN_SHA256:-}" == "$approval_plan_sha256" ]] ||
  fail 'Issue #65 execute parameters do not match the separately approved preflight plan SHA-256'
for command in awk chmod cp date go grep ln mktemp openssl python3 rm rmdir sed sleep tar timeout; do
  command -v "$command" >/dev/null 2>&1 || fail "required execute command is unavailable: $command"
done

workdir="$(mktemp -d "${TMPDIR:-/tmp}/aisoft-issue65.XXXXXX")"
release_root="$workdir/releases"
release_dir="$release_root/$source_sha"
state_root="$workdir/state"
docker_config="$workdir/docker-config"
wrapper="$workdir/docker-wrapper"
candidate_matrix="$workdir/image-stores-issue65-candidate.json"
profile_path="$workdir/target-profile.json"
env_file="$workdir/target.env"
compose_path="$release_dir/compose.json"
compose_model_path="$release_dir/compose.model.json"
archive_path="$release_dir/images.tar"
inventory_path="$release_dir/images.inventory.json"
architecture_path="$release_dir/architecture.lock.json"
phase_log="$docker_config/issue65-docker-argv.log"
orchestrator_log="$workdir/orchestrator-docker-argv.log"
web_rootfs="$workdir/web-rootfs"
web_rootfs_tar="$workdir/web-rootfs.tar"
input_snapshot_root="$workdir/input-snapshot"
snapshot_driver="$input_snapshot_root/codex/tests/integration/docker-release-v2-lifecycle-driver.py"
snapshot_runtime_root="$input_snapshot_root/codex/runtime"
snapshot_wrapper="$input_snapshot_root/docker-wrapper.sh"
snapshot_web_source="$input_snapshot_root/server.go"
snapshot_migration_source="$input_snapshot_root/migrate.sh"
snapshot_architecture="$input_snapshot_root/architecture.lock.json"
resources_created=0
cleanup_verified=0
cleanup_attempted=0
background_pid=""
failure_producer_created=null
failure_consumer_created=null
failure_snapshot_status=NOT_CAPTURED
evidence_temp=""
execution_lock="$root/docs/changes/65/.issue65-${source_sha}.execution-lock"
lock_owned=0

mkdir -p "$release_dir" "$state_root" "$docker_config" "$web_rootfs" \
  "$(dirname -- "$snapshot_driver")" "$snapshot_runtime_root" "$input_snapshot_root"
chmod 0700 "$workdir" "$state_root" "$docker_config"
cp "$driver_source" "$snapshot_driver"
cp "$wrapper_source" "$snapshot_wrapper"
cp "$web_source" "$snapshot_web_source"
cp "$migration_source" "$snapshot_migration_source"
cp "$architecture_source_path" "$snapshot_architecture"
git -C "$root" archive "$source_sha" codex/runtime/aisoft_release | tar -x -C "$input_snapshot_root"
cp "$snapshot_wrapper" "$wrapper"
chmod 0755 "$wrapper"
driver="$snapshot_driver"
real_docker="$docker_client_path"
printf '%s\n' "$real_docker" >"$docker_config/issue65-real-docker-path"
printf '%s\n' "$timeout_client_path" >"$docker_config/issue65-timeout-path"
printf '%s\n' isolated >"$docker_config/issue65-timeout-mode"
printf '%s\n' normal >"$docker_config/issue65-docker-mode"
chmod 0600 "$docker_config/issue65-real-docker-path" "$docker_config/issue65-timeout-path" \
  "$docker_config/issue65-timeout-mode" "$docker_config/issue65-docker-mode"
: >"$phase_log"
: >"$orchestrator_log"
chmod 0600 "$phase_log" "$orchestrator_log"

producer_created_refs=()
consumer_created_refs=()
producer_created_ids=()
consumer_created_ids=()

record_created_image_id() {
  local side="$1"
  local image_id="$2"
  local baseline_images
  if [[ "$side" == "producer" ]]; then
    baseline_images="$(jq -er '.images' <<<"$producer_inventory_before")"
    [[ "$baseline_images" == *"$image_id"* ]] || producer_created_ids+=("$image_id")
  else
    baseline_images="$(jq -er '.images' <<<"$consumer_inventory_before")"
    [[ "$baseline_images" == *"$image_id"* ]] || consumer_created_ids+=("$image_id")
  fi
}

record_created_repo_digest() {
  local side="$1"
  local reference="$2"
  local baseline_repo_digests
  if [[ "$side" == "producer" ]]; then
    baseline_repo_digests="$(jq -er '.repo_digests' <<<"$producer_inventory_before")"
    grep -Fqx -- "$reference" <<<"$baseline_repo_digests" || producer_created_refs+=("$reference")
  else
    baseline_repo_digests="$(jq -er '.repo_digests' <<<"$consumer_inventory_before")"
    grep -Fqx -- "$reference" <<<"$baseline_repo_digests" || consumer_created_refs+=("$reference")
  fi
}

remove_image_exact() {
  local side="$1"
  local reference="$2"
  if [[ "$side" == "producer" ]]; then
    docker_producer image inspect "$reference" >/dev/null 2>&1 &&
      docker_producer image rm "$reference" >/dev/null 2>&1 || true
  else
    docker_consumer image inspect "$reference" >/dev/null 2>&1 &&
      docker_consumer image rm "$reference" >/dev/null 2>&1 || true
  fi
}

cleanup_resources() {
  local cleanup_status=0 reference digest_reference
  cleanup_attempted=1
  if [[ -f "$compose_path" && -f "$env_file" ]]; then
    docker_consumer compose --project-name "$compose_project" --file "$compose_path" \
      --env-file "$env_file" down --volumes --remove-orphans >/dev/null 2>&1 || cleanup_status=1
  fi
  docker_consumer container inspect "$postgres_container" >/dev/null 2>&1 &&
    docker_consumer container rm --force --volumes "$postgres_container" >/dev/null 2>&1 || true
  docker_producer container inspect "$registry_container" >/dev/null 2>&1 &&
    docker_producer container rm --force --volumes "$registry_container" >/dev/null 2>&1 || true
  docker_producer container inspect "$migration_seed_container" >/dev/null 2>&1 &&
    docker_producer container rm --force --volumes "$migration_seed_container" >/dev/null 2>&1 || true
  docker_consumer network inspect "$database_network" >/dev/null 2>&1 &&
    docker_consumer network rm "$database_network" >/dev/null 2>&1 || true
  docker_consumer network inspect "$compose_backend_network" >/dev/null 2>&1 &&
    docker_consumer network rm "$compose_backend_network" >/dev/null 2>&1 || true
  docker_consumer volume inspect "$database_volume" >/dev/null 2>&1 &&
    docker_consumer volume rm "$database_volume" >/dev/null 2>&1 || true
  for reference in "$registry_web_tag" "$registry_migrate_tag"; do
    while IFS= read -r digest_reference; do
      [[ -n "$digest_reference" ]] && record_created_repo_digest producer "$digest_reference"
    done < <(
      docker_producer image inspect --format '{{json .RepoDigests}}' "$reference" 2>/dev/null |
        jq -r '.[]? | select(startswith("127.0.0.1:"))' 2>/dev/null || true
    )
  done
  for reference in "${consumer_created_refs[@]}" "${consumer_created_ids[@]}"; do
    [[ -n "$reference" ]] && remove_image_exact consumer "$reference"
  done
  for reference in "${producer_created_refs[@]}" "${producer_created_ids[@]}"; do
    [[ -n "$reference" ]] && remove_image_exact producer "$reference"
  done
  if docker_producer container inspect "$registry_container" >/dev/null 2>&1 ||
    docker_producer container inspect "$migration_seed_container" >/dev/null 2>&1 ||
    docker_consumer container inspect "$postgres_container" >/dev/null 2>&1 ||
    docker_consumer network inspect "$database_network" >/dev/null 2>&1 ||
    docker_consumer network inspect "$compose_backend_network" >/dev/null 2>&1 ||
    docker_consumer volume inspect "$database_volume" >/dev/null 2>&1 ||
    [[ -n "$(docker_consumer container ls --all --quiet --filter "label=com.docker.compose.project=$compose_project")" ]]; then
    cleanup_status=1
  fi
  producer_inventory_after="$(inventory producer)"
  consumer_inventory_after="$(inventory consumer)"
  [[ "$producer_inventory_after" == "$producer_inventory_before" ]] || cleanup_status=1
  [[ "$consumer_inventory_after" == "$consumer_inventory_before" ]] || cleanup_status=1
  if [[ "$cleanup_status" == "0" ]]; then
    cleanup_verified=1
  fi
  return "$cleanup_status"
}

write_failure_bundle() {
  local failure_result="$1"
  local cleanup_result="$2"
  local bundle_path bundle_temp lifecycle_argv orchestrator_argv state_json
  local producer_after_json consumer_after_json
  bundle_path="${evidence_path}.failure.$$.json"
  bundle_temp="${bundle_path}.tmp"
  [[ ! -e "$bundle_path" && ! -L "$bundle_path" && ! -e "$bundle_temp" && ! -L "$bundle_temp" ]] ||
    return 1
  lifecycle_argv="$(jq -s '.' "$phase_log" 2>/dev/null || printf '%s' '[]')"
  orchestrator_argv="$(jq -s '.' "$orchestrator_log" 2>/dev/null || printf '%s' '[]')"
  state_json='null'
  if [[ -f "$state_root/state.json" && ! -L "$state_root/state.json" ]]; then
    state_json="$(jq -c '.' "$state_root/state.json" 2>/dev/null || printf '%s' 'null')"
  fi
  producer_after_json="${producer_inventory_after:-null}"
  consumer_after_json="${consumer_inventory_after:-null}"
  if ! jq -n \
    --arg date "$(date +%F)" \
    --arg source_sha "$source_sha" \
    --arg approval_plan_sha256 "$approval_plan_sha256" \
    --arg execution_lock "$execution_lock" \
    --arg process_group_pid "${background_pid:-}" \
    --arg failure_snapshot_status "$failure_snapshot_status" \
    --argjson resources "$resources_json" \
    --argjson producer_capability "$producer_capability" \
    --argjson consumer_capability "$consumer_capability" \
    --argjson producer_before "$producer_inventory_before" \
    --argjson consumer_before "$consumer_inventory_before" \
    --argjson producer_created "$failure_producer_created" \
    --argjson consumer_created "$failure_consumer_created" \
    --argjson producer_after "$producer_after_json" \
    --argjson consumer_after "$consumer_after_json" \
    --argjson state "$state_json" \
    --argjson lifecycle_argv "$lifecycle_argv" \
    --argjson orchestrator_argv "$orchestrator_argv" \
    --arg failure_result "$failure_result" \
    --arg cleanup_result "$cleanup_result" '
    {contract_version:"docker-release-v2-lifecycle-e2e-failure/v1",date:$date,result:$failure_result,cleanup:$cleanup_result,
     source_sha:$source_sha,approval_plan_sha256:$approval_plan_sha256,execution_lock:$execution_lock,resources:$resources,
     producer:$producer_capability,consumer:$consumer_capability,
     process_group:(if $cleanup_result == "BLOCKED_PROCESS_GROUP" then {pid:($process_group_pid|tonumber),pgid:($process_group_pid|tonumber),quiesced:false} else null end),
     inventory:{snapshot_status:$failure_snapshot_status,producer_before:$producer_before,consumer_before:$consumer_before,producer_created:$producer_created,consumer_created:$consumer_created,producer_after:$producer_after,consumer_after:$consumer_after},
     state:$state,docker_argv:{lifecycle:$lifecycle_argv,orchestrator:$orchestrator_argv},
     remediation:"Inspect only exact declared resources; prune and broad deletion are forbidden. If cleanup is BLOCKED_PROCESS_GROUP, confirm the recorded PGID and exact resources are quiescent before manually removing the retained execution lock."}
  ' >"$bundle_temp"; then
    rm -f -- "$bundle_temp"
    return 1
  fi
  chmod 0444 "$bundle_temp"
  if ! ln "$bundle_temp" "$bundle_path"; then
    rm -f -- "$bundle_temp"
    return 1
  fi
  rm -f -- "$bundle_temp"
  printf 'FAIL: sanitized lifecycle failure bundle written: %s\n' "$bundle_path" >&2
}

terminate_background_group() {
  local pid="$1"
  local termination_failed=0
  [[ -n "$pid" ]] || return 0
  kill -TERM -- "-$pid" >/dev/null 2>&1 || true
  kill -TERM "$pid" >/dev/null 2>&1 || true
  for _ in {1..50}; do
    if ! kill -0 -- "-$pid" >/dev/null 2>&1 && ! kill -0 "$pid" >/dev/null 2>&1; then
      break
    fi
    sleep 0.1
  done
  if kill -0 -- "-$pid" >/dev/null 2>&1; then
    kill -KILL -- "-$pid" >/dev/null 2>&1 || true
  fi
  if kill -0 "$pid" >/dev/null 2>&1; then
    kill -KILL "$pid" >/dev/null 2>&1 || true
  fi
  for _ in {1..50}; do
    if ! kill -0 -- "-$pid" >/dev/null 2>&1 && ! kill -0 "$pid" >/dev/null 2>&1; then
      break
    fi
    sleep 0.1
  done
  if kill -0 -- "-$pid" >/dev/null 2>&1 || kill -0 "$pid" >/dev/null 2>&1; then
    termination_failed=1
  else
    wait "$pid" >/dev/null 2>&1 || true
  fi
  return "$termination_failed"
}

on_exit() {
  local status="$?"
  local cleanup_failed=0
  local termination_failed=0
  local cleanup_result=NOT_REQUIRED failure_result=FAIL_LIFECYCLE
  if [[ -n "$background_pid" ]] &&
    { kill -0 -- "-$background_pid" >/dev/null 2>&1 || kill -0 "$background_pid" >/dev/null 2>&1; }; then
    if terminate_background_group "$background_pid"; then
      background_pid=""
    else
      termination_failed=1
      cleanup_failed=1
      cleanup_result=BLOCKED_PROCESS_GROUP
    fi
  fi
  if [[ "$status" != "0" && "$termination_failed" == "0" ]]; then
    if [[ -n "${producer_inventory_created:-}" && -n "${consumer_inventory_created:-}" ]]; then
      failure_producer_created="$producer_inventory_created"
      failure_consumer_created="$consumer_inventory_created"
      failure_snapshot_status=CAPTURED_BEFORE_CLEANUP
    else
      failure_snapshot_status=CAPTURED_AT_FAILURE
      failure_producer_created="$(inventory producer 2>/dev/null)" || {
        failure_producer_created=null
        failure_snapshot_status=CAPTURE_PARTIAL
      }
      failure_consumer_created="$(inventory consumer 2>/dev/null)" || {
        failure_consumer_created=null
        failure_snapshot_status=CAPTURE_PARTIAL
      }
    fi
    if [[ "$resources_created" == "0" ]]; then
      producer_inventory_after="${producer_inventory_after:-$failure_producer_created}"
      consumer_inventory_after="${consumer_inventory_after:-$failure_consumer_created}"
    fi
  elif [[ "$termination_failed" == "1" ]]; then
    failure_snapshot_status=BLOCKED_PROCESS_GROUP
  fi
  if [[ "$termination_failed" == "0" && "$resources_created" == "1" && "$cleanup_verified" == "0" ]]; then
    if [[ "$cleanup_attempted" == "0" ]]; then
      if cleanup_resources; then
        cleanup_result=PASS
      else
        cleanup_failed=1
        cleanup_result=FAIL
      fi
    else
      cleanup_failed=1
      cleanup_result=FAIL
    fi
  elif [[ "$cleanup_verified" == "1" ]]; then
    cleanup_result=PASS
  fi
  if [[ "$cleanup_failed" == "1" ]]; then
    status=1
    failure_result=FAIL_CLEANUP
    printf '%s\n' 'FAIL: Issue #65 exact cleanup could not restore baseline; prune and broad deletion remain forbidden.' >&2
    jq -cn \
      --arg producer_host "$producer_host" \
      --arg consumer_host "$consumer_host" \
      --argjson resources "$resources_json" \
      '{producer_host:$producer_host,consumer_host:$consumer_host,inspect_exact_resources:$resources}' >&2 || true
  fi
  if [[ "$status" != "0" && "$lock_owned" == "1" ]]; then
    write_failure_bundle "$failure_result" "$cleanup_result" ||
      printf '%s\n' 'FAIL: sanitized lifecycle failure bundle could not be written' >&2
  fi
  if [[ -n "$evidence_temp" ]]; then
    rm -f -- "$evidence_temp"
  fi
  rm -rf -- "$workdir"
  if [[ "$lock_owned" == "1" && "$termination_failed" == "1" ]]; then
    printf 'FAIL: Issue #65 execution lock retained because process group may still mutate resources: %s\n' \
      "$execution_lock" >&2
  elif [[ "$lock_owned" == "1" ]]; then
    if ! rmdir "$execution_lock"; then
      status=1
      printf 'FAIL: Issue #65 execution lock could not be removed: %s\n' "$execution_lock" >&2
    fi
  fi
  exit "$status"
}
trap on_exit EXIT

if ! mkdir "$execution_lock"; then
  fail 'another Issue #65 execution owns the exact source lock'
fi
lock_owned=1
[[ ! -e "$evidence_path" && ! -L "$evidence_path" ]] ||
  fail 'immutable Issue #65 PASS evidence was created while waiting for the execution lock'
[[ "$(inventory producer)" == "$producer_inventory_before" && "$(inventory consumer)" == "$consumer_inventory_before" ]] ||
  fail 'Docker inventory drifted after the separately approved plan was bound'
[[ "$(sha256_file "$docker_client_path")" == "$docker_client_sha" ]] ||
  fail 'Docker client bytes drifted after the separately approved plan was bound'
[[ "$(sha256_file "$timeout_client_path")" == "$timeout_client_sha" ]] ||
  fail 'timeout client bytes drifted after the separately approved plan was bound'
[[ "$(sha256_file "$architecture_source_path")" == "$architecture_source_sha" ]] ||
  fail 'architecture lock bytes drifted after the separately approved plan was bound'
[[ "$(sha256_file "$root/codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh")" == "$harness_sha" ]] ||
  fail 'Issue #65 harness bytes drifted after the separately approved plan was bound'
[[ "$(sha256_file "$snapshot_driver")" == "$driver_sha" && \
  "$(sha256_file "$snapshot_wrapper")" == "$wrapper_sha" && \
  "$(sha256_file "$wrapper")" == "$wrapper_sha" && \
  "$(sha256_file "$snapshot_web_source")" == "$web_source_sha" && \
  "$(sha256_file "$snapshot_migration_source")" == "$migration_source_sha" && \
  "$(sha256_file "$snapshot_architecture")" == "$architecture_source_sha" ]] ||
  fail 'Issue #65 immutable input snapshot differs from the separately approved plan'
assert_resource_absent

evidence_date="$approval_date"
printf '%s\n' "$candidate_matrix_json" >"$candidate_matrix"
[[ "$(sha256_file "$candidate_matrix")" == "$candidate_matrix_sha" ]] ||
  fail 'approved candidate matrix bytes drifted before execution'
chmod 0444 "$candidate_matrix"

CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
  go build -trimpath -ldflags '-s -w -buildid=' -o "$web_rootfs/server" "$snapshot_web_source"
tar --format=ustar -C "$web_rootfs" -cf "$web_rootfs_tar" server
resources_created=1
producer_created_refs+=("$producer_build_web")
docker_producer image import --platform linux/amd64 \
  --change 'USER 65532:65532' \
  --change 'ENTRYPOINT ["/server"]' \
  --change "LABEL com.aisoft.e2e.release-id=$source_sha" \
  "$web_rootfs_tar" "$producer_build_web" >/dev/null
web_image_id="$(docker_producer image inspect --format '{{.Id}}' "$producer_build_web")"
record_created_image_id producer "$web_image_id"

docker_producer container create --name "$migration_seed_container" "$postgres_image" >/dev/null
docker_producer container cp "$snapshot_migration_source" "$migration_seed_container:/usr/local/bin/issue65-migrate"
producer_created_refs+=("$producer_build_migrate")
docker_producer container commit \
  --change 'USER 999:999' \
  --change 'ENTRYPOINT ["/usr/local/bin/issue65-migrate"]' \
  --change "LABEL com.aisoft.e2e.release-id=$source_sha" \
  "$migration_seed_container" "$producer_build_migrate" >/dev/null
docker_producer container rm "$migration_seed_container" >/dev/null
migrate_image_id="$(docker_producer image inspect --format '{{.Id}}' "$producer_build_migrate")"
[[ "$migrate_image_id" != "$web_image_id" ]] || fail 'fixture web and migration image IDs must differ'
[[ "$migrate_image_id" != "$producer_postgres_image_id" && "$web_image_id" != "$producer_postgres_image_id" ]] ||
  fail 'PostgreSQL, web and migration fixture image IDs must be pairwise distinct'
record_created_image_id producer "$migrate_image_id"

docker_producer container run --detach --name "$registry_container" \
  --publish "127.0.0.1:${registry_port}:5000" \
  --tmpfs '/var/lib/registry:rw,nosuid,nodev,noexec,size=67108864' \
  "$registry_image" >/dev/null
producer_created_refs+=("$registry_web_tag" "$registry_migrate_tag")
docker_producer image tag "$producer_build_web" "$registry_web_tag"
docker_producer image tag "$producer_build_migrate" "$registry_migrate_tag"
push_registry_image() {
  local reference="$1"
  local output="$2"
  for _ in {1..20}; do
    if docker_producer image push "$reference" >"$output" 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  fail "producer-local Registry did not accept image after 20 bounded attempts: $reference"
}
push_registry_image "$registry_web_tag" "$workdir/registry-web-push.log"
push_registry_image "$registry_migrate_tag" "$workdir/registry-migrate-push.log"

registry_web_reference="$(
  docker_producer image inspect --format '{{json .RepoDigests}}' "$registry_web_tag" |
    jq -er --arg prefix "127.0.0.1:${registry_port}/admin/aisoft-platform/web@sha256:" \
      '[.[] | select(startswith($prefix))] | if length == 1 then .[0] else error("web digest count") end'
)"
registry_migrate_reference="$(
  docker_producer image inspect --format '{{json .RepoDigests}}' "$registry_migrate_tag" |
    jq -er --arg prefix "127.0.0.1:${registry_port}/admin/aisoft-platform/migrate@sha256:" \
      '[.[] | select(startswith($prefix))] | if length == 1 then .[0] else error("migrate digest count") end'
)"
web_digest="${registry_web_reference##*@}"
migrate_digest="${registry_migrate_reference##*@}"
record_created_repo_digest producer "$registry_web_reference"
record_created_repo_digest producer "$registry_migrate_reference"
producer_created_refs+=("$runtime_web" "$runtime_migrate")
docker_producer image pull "$registry_web_reference" >/dev/null
docker_producer image pull "$registry_migrate_reference" >/dev/null
docker_producer image tag "$registry_web_reference" "$runtime_web"
docker_producer image tag "$registry_migrate_reference" "$runtime_migrate"
web_image_id="$(docker_producer image inspect --format '{{.Id}}' "$runtime_web")"
migrate_image_id="$(docker_producer image inspect --format '{{.Id}}' "$runtime_migrate")"
[[ "$web_image_id" != "$migrate_image_id" ]] || fail 'release image IDs must be unique'

docker_producer image save --output "$archive_path" "$runtime_web" "$runtime_migrate"
archive_sha="$(sha256_file "$archive_path")"
jq -n \
  --arg archive_sha "$archive_sha" \
  --arg web_reference "$registry_web_reference" \
  --arg web_digest "$web_digest" \
  --arg web_id "$web_image_id" \
  --arg web_runtime "$runtime_web" \
  --arg migrate_reference "$registry_migrate_reference" \
  --arg migrate_digest "$migrate_digest" \
  --arg migrate_id "$migrate_image_id" \
  --arg migrate_runtime "$runtime_migrate" \
  '{contract_version:"docker-release-offline-inventory/v2",archive_sha256:$archive_sha,images:[
    {service:"web",reference:$web_reference,digest:$web_digest,image_id:$web_id,transport_reference:$web_runtime,runtime_reference:$web_runtime,platform:"linux/amd64"},
    {service:"migrate",reference:$migrate_reference,digest:$migrate_digest,image_id:$migrate_id,transport_reference:$migrate_runtime,runtime_reference:$migrate_runtime,platform:"linux/amd64"}
  ]}' >"$inventory_path"
inventory_sha="$(sha256_file "$inventory_path")"

cp "$snapshot_architecture" "$architecture_path"
architecture_sha="$(sha256_file "$architecture_path")"
[[ "$architecture_sha" == "$architecture_source_sha" ]] || fail 'approved architecture lock changed during copy'
architecture_profile="$(jq -er '.profile_id' "$architecture_path")"
architecture_project="$(jq -er '.project_id' "$architecture_path")"
catalog_revision="$(jq -er '.catalog_revision' "$architecture_path")"

jq -n \
  --arg release "$source_sha" \
  --arg web "$runtime_web" \
  --arg migrate "$runtime_migrate" \
  --arg database_network "$database_network" \
  --arg compose_backend_network "$compose_backend_network" '
  {
    services:{
      web:{image:$web,user:"65532:65532",read_only:true,cap_drop:["ALL"],security_opt:["no-new-privileges:true"],tmpfs:["/tmp:size=16m,mode=1777"],deploy:{resources:{limits:{cpus:"0.25",memory:"256M"}}},logging:{driver:"json-file",options:{"max-size":"1m","max-file":"2"}},networks:{backend:null},labels:{"com.aisoft.release.id":$release,"com.aisoft.release.service":"web"},healthcheck:{test:["CMD","/server","healthcheck"],interval:"2s",timeout:"2s",retries:30}},
      migrate:{image:$migrate,user:"999:999",read_only:true,cap_drop:["ALL"],security_opt:["no-new-privileges:true"],tmpfs:["/tmp:size=16m,mode=1777"],deploy:{resources:{limits:{cpus:"0.25",memory:"256M"}}},logging:{driver:"json-file",options:{"max-size":"1m","max-file":"2"}},networks:{backend:null,database:null},labels:{"com.aisoft.release.id":$release,"com.aisoft.release.service":"migrate"},environment:{PGHOST:"${PGHOST:?required}",PGPORT:"${PGPORT:?required}",PGDATABASE:"${PGDATABASE:?required}",PGUSER:"${PGUSER:?required}",PGPASSWORD:"${PGPASSWORD:?required}",MIGRATION_MARKER:"${MIGRATION_MARKER:?required}",MIGRATION_HOLD_SECONDS:"${MIGRATION_HOLD_SECONDS:?required}"}}
    },
    networks:{backend:{internal:true,name:$compose_backend_network},database:{external:true,name:$database_network}}
  }' >"$compose_path"
compose_source_sha="$(sha256_file "$compose_path")"
docker_producer compose --project-name "$compose_project" --file "$compose_path" \
  config --format json --no-interpolate --no-env-resolution >"$compose_model_path"
compose_model_sha="$(sha256_file "$compose_model_path")"
migration_identity="sha256:$(printf '%s:%s' "$source_sha" "$(sha256_file "$snapshot_migration_source")" | shasum -a 256 | awk '{print $1}')"

jq -n \
  --arg release "$source_sha" \
  --arg compose_sha "$compose_source_sha" \
  --arg compose_model_sha "$compose_model_sha" \
  --arg architecture_sha "$architecture_sha" \
  --arg architecture_profile "$architecture_profile" \
  --arg architecture_project "$architecture_project" \
  --arg catalog_revision "$catalog_revision" \
  --arg web_reference "$registry_web_reference" \
  --arg web_digest "$web_digest" \
  --arg web_id "$web_image_id" \
  --arg web_runtime "$runtime_web" \
  --arg migrate_reference "$registry_migrate_reference" \
  --arg migrate_digest "$migrate_digest" \
  --arg migrate_id "$migrate_image_id" \
  --arg migrate_runtime "$runtime_migrate" \
  --arg migration_identity "$migration_identity" \
  --arg archive_sha "$archive_sha" \
  --arg inventory_sha "$inventory_sha" '
  {contract_version:"docker-release/v2",release_id:$release,source_repository:"admin/aisoft-platform",merge_sha:$release,platform:"linux/amd64",
   compose:{path:"compose.json",sha256:$compose_sha,model_path:"compose.model.json",model_sha256:$compose_model_sha},
   architecture:{path:"architecture.lock.json",profile_id:$architecture_profile,project_id:$architecture_project,catalog_revision:$catalog_revision,sha256:$architecture_sha},
   images:[
     {service:"web",reference:$web_reference,digest:$web_digest,image_id:$web_id,transport_reference:$web_runtime,runtime_reference:$web_runtime},
     {service:"migrate",reference:$migrate_reference,digest:$migrate_digest,image_id:$migrate_id,transport_reference:$migrate_runtime,runtime_reference:$migrate_runtime}
   ],runtime_services:["web"],migration:{service:"migrate",identity:$migration_identity,destructive:false,database_restore:"manual-only"},
   offline_bundle:{contract_version:"docker-release-offline-bundle/v2",archive_path:"images.tar",archive_sha256:$archive_sha,inventory_path:"images.inventory.json",inventory_sha256:$inventory_sha}}' \
  >"$release_dir/release.json"

postgres_password="$(openssl rand -hex 24)"
{
  printf 'POSTGRES_USER=issue65\n'
  printf 'POSTGRES_DB=issue65\n'
  printf 'POSTGRES_PASSWORD=%s\n' "$postgres_password"
  printf 'PGHOST=%s\n' "$postgres_container"
  printf 'PGPORT=5432\n'
  printf 'PGDATABASE=issue65\n'
  printf 'PGUSER=issue65\n'
  printf 'PGPASSWORD=%s\n' "$postgres_password"
  printf 'MIGRATION_MARKER=%s\n' "$source_sha"
  printf 'MIGRATION_HOLD_SECONDS=3\n'
} >"$env_file"
chmod 0600 "$env_file"

jq -n \
  --arg release_root "$release_root" \
  --arg state_root "$state_root" \
  --arg env_file "$env_file" \
  --arg compose_project "$compose_project" \
  --arg hostname "$consumer_id" \
  --arg architecture_profile "$architecture_profile" \
  --arg architecture_project "$architecture_project" \
  --arg catalog_revision "$catalog_revision" '
  {contract_version:"docker-release-target/v1",profile_id:"aisoft-65-compose-514",environment:"test",host_role:"appserver-test",expected_hostname:$hostname,transport:"offline-bundle",release_root:$release_root,state_root:$state_root,compose_project:$compose_project,env_file:$env_file,source_repository:"admin/aisoft-platform",architecture_profile_id:$architecture_profile,architecture_project_id:$architecture_project,catalog_revision:$catalog_revision,wait_timeout_seconds:90}' \
  >"$profile_path"
chmod 0600 "$profile_path"

export DOCKER_HOST="$consumer_host"

run_driver() {
  local action="$1"
  shift
  if [[ "$action" == "verify-artifact" ]]; then
    PYTHONDONTWRITEBYTECODE=1 python3 -I -S -B "$driver" \
      "$action" "$@" --release-id "$source_sha" --release-root "$release_root" \
      --compatibility-matrix "$candidate_matrix" --docker "$wrapper" --hostname "$consumer_id"
  else
    PYTHONDONTWRITEBYTECODE=1 python3 -I -S -B "$driver" \
      "$action" "$@" --release-id "$source_sha" --profile "$profile_path" \
      --compatibility-matrix "$candidate_matrix" --docker "$wrapper" --hostname "$consumer_id"
  fi
}

run_migrate_background() {
  local ready_file="$1"
  PYTHONDONTWRITEBYTECODE=1 exec python3 -I -S -B "$driver" \
    migrate --new-process-group --process-group-ready-file "$ready_file" \
    --release-id "$source_sha" --profile "$profile_path" \
    --compatibility-matrix "$candidate_matrix" --docker "$wrapper" --hostname "$consumer_id"
}

capture_phase() {
  local action="$1"
  local output_path="$2"
  local log_path="$3"
  local start_line
  start_line="$(wc -l <"$phase_log" | tr -d ' ')"
  run_driver "$action" >"$output_path"
  sed -n "$((start_line + 1)),\$p" "$phase_log" >"$log_path"
  jq -e '.ok == true' "$output_path" >/dev/null
}

assert_phase_lacks() {
  local log_path="$1"
  shift
  local pattern
  for pattern in "$@"; do
    if rg -n "$pattern" "$log_path"; then
      fail "phase log contains forbidden mutation pattern: $pattern"
    fi
  done
}

mutation_count() {
  jq -s '[.[] | select(
    (.[0] == "image" and (.[1] as $action | ["pull","load","tag","rm","import","push"] | index($action))) or
    (.[0] == "container" and (.[1] as $action | ["create","run","rm","commit","cp"] | index($action))) or
    (.[0] == "network" and (.[1] as $action | ["create","rm"] | index($action))) or
    (.[0] == "volume" and (.[1] as $action | ["create","rm"] | index($action))) or
    (.[0] == "compose" and ((index("run") != null) or (index("up") != null) or (index("down") != null)))
  )] | length' "$1"
}

artifact_result="$workdir/verify-artifact.json"
capture_phase verify-artifact "$artifact_result" "$workdir/verify-artifact.log"
[[ ! -s "$workdir/verify-artifact.log" ]] || fail 'verify-artifact must make zero Docker calls'

tamper_producer_before="$(inventory producer)"
tamper_consumer_before="$(inventory consumer)"
tampered_root="$workdir/tampered-root"
mkdir -p "$tampered_root"
cp -R "$release_dir" "$tampered_root/$source_sha"
printf '\n' >>"$tampered_root/$source_sha/compose.model.json"
tamper_log_lines="$(wc -l <"$phase_log" | tr -d ' ')"
if PYTHONDONTWRITEBYTECODE=1 python3 -I -S -B "$driver" \
  verify-artifact --release-id "$source_sha" --release-root "$tampered_root" \
  --compatibility-matrix "$candidate_matrix" --docker "$wrapper" --hostname "$consumer_id" \
  >"$workdir/tamper.output" 2>"$workdir/tamper.error"; then
  fail 'tampered artifact unexpectedly passed'
fi
[[ "$(wc -l <"$phase_log" | tr -d ' ')" == "$tamper_log_lines" ]] ||
  fail 'tampered artifact made a Docker call'
jq -e '.ok == false and .error_code == "INVALID_CONTRACT"' "$workdir/tamper.error" >/dev/null
tamper_producer_after="$(inventory producer)"
tamper_consumer_after="$(inventory consumer)"
[[ "$tamper_producer_before" == "$tamper_producer_after" && "$tamper_consumer_before" == "$tamper_consumer_after" ]] ||
  fail 'tampered artifact negative changed Docker inventory'

wrong_compose_producer_before="$(inventory producer)"
wrong_compose_consumer_before="$(inventory consumer)"
printf '%s\n' wrong-compose >"$docker_config/issue65-docker-mode"
wrong_compose_start="$(wc -l <"$phase_log" | tr -d ' ')"
if run_driver verify-target >"$workdir/wrong-compose.output" 2>"$workdir/wrong-compose.error"; then
  fail 'wrong Compose capability unexpectedly passed verify-target'
fi
sed -n "$((wrong_compose_start + 1)),\$p" "$phase_log" >"$workdir/wrong-compose.log"
assert_phase_lacks "$workdir/wrong-compose.log" '"image","(pull|load|tag)"' '"compose".*"(run|up)"'
jq -e '.ok == false and .error_code == "DEPLOYMENT_FAILED"' "$workdir/wrong-compose.error" >/dev/null
wrong_compose_mutations="$(mutation_count "$workdir/wrong-compose.log")"
[[ "$wrong_compose_mutations" == "0" ]] || fail 'wrong Compose negative performed a Docker mutation'
wrong_compose_producer_after="$(inventory producer)"
wrong_compose_consumer_after="$(inventory consumer)"
[[ "$wrong_compose_producer_before" == "$wrong_compose_producer_after" && "$wrong_compose_consumer_before" == "$wrong_compose_consumer_after" ]] ||
  fail 'wrong Compose negative changed Docker inventory'

wrong_store_producer_before="$(inventory producer)"
wrong_store_consumer_before="$(inventory consumer)"
printf '%s\n' wrong-store >"$docker_config/issue65-docker-mode"
wrong_store_start="$(wc -l <"$phase_log" | tr -d ' ')"
if run_driver verify-target >"$workdir/wrong-store.output" 2>"$workdir/wrong-store.error"; then
  fail 'wrong image store unexpectedly passed verify-target'
fi
sed -n "$((wrong_store_start + 1)),\$p" "$phase_log" >"$workdir/wrong-store.log"
assert_phase_lacks "$workdir/wrong-store.log" '"image","(pull|load|tag)"' '"compose".*"(run|up)"'
jq -e '.ok == false and .error_code == "DEPLOYMENT_FAILED"' "$workdir/wrong-store.error" >/dev/null
wrong_store_mutations="$(mutation_count "$workdir/wrong-store.log")"
[[ "$wrong_store_mutations" == "0" ]] || fail 'wrong image-store negative performed a Docker mutation'
wrong_store_producer_after="$(inventory producer)"
wrong_store_consumer_after="$(inventory consumer)"
[[ "$wrong_store_producer_before" == "$wrong_store_producer_after" && "$wrong_store_consumer_before" == "$wrong_store_consumer_after" ]] ||
  fail 'wrong image-store negative changed Docker inventory'
printf '%s\n' normal >"$docker_config/issue65-docker-mode"

missing_receipt_producer_before="$(inventory producer)"
missing_receipt_consumer_before="$(inventory consumer)"
missing_receipt_start="$(wc -l <"$phase_log" | tr -d ' ')"
if run_driver migrate >"$workdir/missing-receipt.output" 2>"$workdir/missing-receipt.error"; then
  fail 'migrate without a staging receipt unexpectedly passed'
fi
sed -n "$((missing_receipt_start + 1)),\$p" "$phase_log" >"$workdir/missing-receipt.log"
assert_phase_lacks "$workdir/missing-receipt.log" '"image","(pull|load|tag)"' '"compose".*"(run|up)"'
jq -e '.ok == false and .error_code == "DEPLOYMENT_FAILED"' "$workdir/missing-receipt.error" >/dev/null
missing_receipt_mutations="$(mutation_count "$workdir/missing-receipt.log")"
[[ "$missing_receipt_mutations" == "0" ]] || fail 'missing staging receipt negative performed a Docker mutation'
missing_receipt_producer_after="$(inventory producer)"
missing_receipt_consumer_after="$(inventory consumer)"
[[ "$missing_receipt_producer_before" == "$missing_receipt_producer_after" && "$missing_receipt_consumer_before" == "$missing_receipt_consumer_after" ]] ||
  fail 'missing staging receipt negative changed Docker inventory'

negative_json="$(
  jq -n \
    --argjson duplicate_daemon "$duplicate_daemon_evidence" \
    --argjson artifact_error "$(<"$workdir/tamper.error")" \
    --argjson wrong_compose_error "$(<"$workdir/wrong-compose.error")" \
    --argjson wrong_store_error "$(<"$workdir/wrong-store.error")" \
    --argjson missing_receipt_error "$(<"$workdir/missing-receipt.error")" \
    --argjson wrong_compose_mutations "$wrong_compose_mutations" \
    --argjson wrong_store_mutations "$wrong_store_mutations" \
    --argjson missing_receipt_mutations "$missing_receipt_mutations" \
    --argjson tamper_producer_before "$tamper_producer_before" \
    --argjson tamper_consumer_before "$tamper_consumer_before" \
    --argjson tamper_producer_after "$tamper_producer_after" \
    --argjson tamper_consumer_after "$tamper_consumer_after" \
    --argjson wrong_compose_producer_before "$wrong_compose_producer_before" \
    --argjson wrong_compose_consumer_before "$wrong_compose_consumer_before" \
    --argjson wrong_compose_producer_after "$wrong_compose_producer_after" \
    --argjson wrong_compose_consumer_after "$wrong_compose_consumer_after" \
    --argjson wrong_store_producer_before "$wrong_store_producer_before" \
    --argjson wrong_store_consumer_before "$wrong_store_consumer_before" \
    --argjson wrong_store_producer_after "$wrong_store_producer_after" \
    --argjson wrong_store_consumer_after "$wrong_store_consumer_after" \
    --argjson missing_receipt_producer_before "$missing_receipt_producer_before" \
    --argjson missing_receipt_consumer_before "$missing_receipt_consumer_before" \
    --argjson missing_receipt_producer_after "$missing_receipt_producer_after" \
    --argjson missing_receipt_consumer_after "$missing_receipt_consumer_after" '
    {duplicate_daemon:$duplicate_daemon,
     artifact_tamper:{result:"REJECTED",docker_calls:0,error:$artifact_error,inventory:{producer_before:$tamper_producer_before,consumer_before:$tamper_consumer_before,producer_after:$tamper_producer_after,consumer_after:$tamper_consumer_after}},
     wrong_compose:{result:"REJECTED",mutation_count:$wrong_compose_mutations,error:$wrong_compose_error,inventory:{producer_before:$wrong_compose_producer_before,consumer_before:$wrong_compose_consumer_before,producer_after:$wrong_compose_producer_after,consumer_after:$wrong_compose_consumer_after}},
     wrong_store:{result:"REJECTED",mutation_count:$wrong_store_mutations,error:$wrong_store_error,inventory:{producer_before:$wrong_store_producer_before,consumer_before:$wrong_store_consumer_before,producer_after:$wrong_store_producer_after,consumer_after:$wrong_store_consumer_after}},
     missing_staging_receipt:{result:"REJECTED",mutation_count:$missing_receipt_mutations,error:$missing_receipt_error,inventory:{producer_before:$missing_receipt_producer_before,consumer_before:$missing_receipt_consumer_before,producer_after:$missing_receipt_producer_after,consumer_after:$missing_receipt_consumer_after}}}
  '
)"

target_result="$workdir/verify-target.json"
capture_phase verify-target "$target_result" "$workdir/verify-target.log"
assert_phase_lacks "$workdir/verify-target.log" '"image","(pull|load|tag)"' '"compose".*"(run|up)"'

if docker_consumer image inspect "$registry_web_reference" >/dev/null 2>&1; then
  fail 'consumer already contains the Registry digest reference used by the rejection probe'
fi
log_orchestrator_argv consumer image pull "$registry_web_reference"
if "$timeout_client_path" -k 5 20 "$docker_client_path" --host "$consumer_host" image pull "$registry_web_reference" \
  >"$workdir/consumer-registry-pull.output" 2>"$workdir/consumer-registry-pull.error"; then
  consumer_created_refs+=("$registry_web_reference")
  fail 'consumer unexpectedly reached the producer-local Registry'
fi
if docker_consumer image inspect "$registry_web_reference" >/dev/null 2>&1; then
  consumer_created_refs+=("$registry_web_reference")
  fail 'failed consumer Registry probe left a new digest reference'
fi

stage_result="$workdir/stage.json"
consumer_created_refs+=("$runtime_web" "$runtime_migrate")
record_created_image_id consumer "$web_image_id"
record_created_image_id consumer "$migrate_image_id"
capture_phase stage "$stage_result" "$workdir/stage.log"
assert_phase_lacks "$workdir/stage.log" '"compose".*"(run|up)"'
jq -e '.action == "staged"' "$stage_result" >/dev/null

docker_consumer network create --internal "$database_network" >/dev/null
docker_consumer volume create "$database_volume" >/dev/null
docker_consumer container run --detach --name "$postgres_container" \
  --network "$database_network" \
  --env-file "$env_file" \
  --mount "type=volume,source=${database_volume},target=/var/lib/postgresql/data" \
  --health-cmd 'pg_isready --username issue65 --dbname issue65' \
  --health-interval 2s --health-timeout 2s --health-retries 30 \
  "$postgres_image" >/dev/null
for _ in {1..60}; do
  postgres_health="$(docker_consumer container inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$postgres_container")"
  [[ "$postgres_health" == "healthy" ]] && break
  [[ "$postgres_health" != "unhealthy" ]] || fail 'disposable PostgreSQL fixture became unhealthy'
  sleep 1
done
[[ "${postgres_health:-}" == "healthy" ]] || fail 'disposable PostgreSQL fixture did not become healthy'

migrate_result="$workdir/migrate.json"
migration_started_state="$workdir/migration-started-state.json"
migration_process_ready="$workdir/migration-process-group.json"
migrate_start_line="$(wc -l <"$phase_log" | tr -d ' ')"
printf '%s\n' foreground >"$docker_config/issue65-timeout-mode"
run_migrate_background "$migration_process_ready" >"$migrate_result" &
migrate_pid="$!"
background_pid="$migrate_pid"
for _ in {1..50}; do
  if [[ -f "$migration_process_ready" ]] &&
    jq -e --argjson pid "$migrate_pid" '.pid == $pid and .pgid == $pid' \
      "$migration_process_ready" >/dev/null 2>&1; then
    break
  fi
  kill -0 "$migrate_pid" >/dev/null 2>&1 || break
  sleep 0.1
done
if [[ ! -f "$migration_process_ready" ]] ||
  ! jq -e --argjson pid "$migrate_pid" '.pid == $pid and .pgid == $pid' "$migration_process_ready" >/dev/null 2>&1; then
  if terminate_background_group "$migrate_pid"; then
    background_pid=""
  fi
  fail 'migration driver did not establish the exact owned process group'
fi
for _ in {1..50}; do
  if [[ -f "$state_root/state.json" ]] && jq -e --arg migration "$migration_identity" \
    '.migrations[$migration].status == "started" and .last_result == "migration-started"' \
    "$state_root/state.json" >/dev/null 2>&1; then
    cp "$state_root/state.json" "$migration_started_state"
    break
  fi
  sleep 0.1
done
if [[ ! -f "$migration_started_state" ]]; then
  if terminate_background_group "$migrate_pid"; then
    background_pid=""
  fi
  fail 'transient migration started state was not observed'
fi
for _ in {1..600}; do
  if ! kill -0 -- "-$migrate_pid" >/dev/null 2>&1 && ! kill -0 "$migrate_pid" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done
if kill -0 -- "-$migrate_pid" >/dev/null 2>&1 || kill -0 "$migrate_pid" >/dev/null 2>&1; then
  if terminate_background_group "$migrate_pid"; then
    background_pid=""
  fi
  fail 'disposable PostgreSQL migration exceeded the 120 second bound'
fi
if ! wait "$migrate_pid"; then
  background_pid=""
  fail 'disposable PostgreSQL migration phase failed'
fi
background_pid=""
printf '%s\n' isolated >"$docker_config/issue65-timeout-mode"
sed -n "$((migrate_start_line + 1)),\$p" "$phase_log" >"$workdir/migrate.log"
jq -e '.ok == true' "$migrate_result" >/dev/null
assert_phase_lacks "$workdir/migrate.log" '"image","(pull|load|tag)"' '"compose".*"up"'
jq -e '.action == "migration-completed"' "$migrate_result" >/dev/null
migrate_noop_result="$workdir/migrate-noop.json"
capture_phase migrate "$migrate_noop_result" "$workdir/migrate-noop.log"
assert_phase_lacks "$workdir/migrate-noop.log" '"image","(pull|load|tag)"' '"compose".*"(run|up)"'
jq -e '.action == "migration-noop"' "$migrate_noop_result" >/dev/null

database_marker_count="$(
  docker_consumer container exec "$postgres_container" \
    psql --username issue65 --dbname issue65 --tuples-only --no-align \
    --command "SELECT count(*) FROM issue65_fixture.migration_receipt WHERE marker = '${source_sha}'"
)"
[[ "$database_marker_count" == "1" ]] || fail 'disposable PostgreSQL migration marker is not exact'

activate_result="$workdir/activate.json"
capture_phase activate "$activate_result" "$workdir/activate.log"
assert_phase_lacks "$workdir/activate.log" '"image","(pull|load|tag)"' '"compose".*"run"'
jq -e '.action == "activated"' "$activate_result" >/dev/null
status_result="$workdir/status.json"
capture_phase status "$status_result" "$workdir/status.log"
assert_phase_lacks "$workdir/status.log" '"image","(pull|load|tag)"' '"compose".*"(run|up)"'
jq -e '.ok == true and .action == "healthy"' "$status_result" >/dev/null
noop_result="$workdir/same-sha-noop.json"
capture_phase activate "$noop_result" "$workdir/same-sha-noop.log"
assert_phase_lacks "$workdir/same-sha-noop.log" '"image","(pull|load|tag)"' '"compose".*"(run|up)"'
jq -e '.action == "healthy-noop"' "$noop_result" >/dev/null

state_path="$state_root/state.json"
[[ -f "$state_path" ]] || state_path="$(find "$state_root" -maxdepth 1 -type f -name '*.json' -print -quit)"
[[ -n "$state_path" && -f "$state_path" ]] || fail 'docker-release-state/v2 file is missing'
jq -e --arg release "$source_sha" --arg migration "$migration_identity" '
  .contract_version == "docker-release-state/v2" and
  .current_release == $release and
  .staged_releases[$release].status == "completed" and
  .migrations[$migration].status == "completed" and
  .last_result == "healthy-noop"
' "$state_path" >/dev/null

phase_argv_json="$(
  jq -n \
    --argjson verify_artifact "$(jq -s '.' "$workdir/verify-artifact.log")" \
    --argjson verify_target "$(jq -s '.' "$workdir/verify-target.log")" \
    --argjson stage "$(jq -s '.' "$workdir/stage.log")" \
    --argjson migrate "$(jq -s '.' "$workdir/migrate.log")" \
    --argjson migrate_noop "$(jq -s '.' "$workdir/migrate-noop.log")" \
    --argjson activate "$(jq -s '.' "$workdir/activate.log")" \
    --argjson status "$(jq -s '.' "$workdir/status.log")" \
    --argjson same_sha_noop "$(jq -s '.' "$workdir/same-sha-noop.log")" \
    '{verify_artifact:$verify_artifact,verify_target:$verify_target,stage:$stage,migrate:$migrate,migrate_noop:$migrate_noop,activate:$activate,status:$status,same_sha_noop:$same_sha_noop}'
)"
phase_mutation_counts_json="$(
  jq -n \
    --argjson verify_artifact "$(mutation_count "$workdir/verify-artifact.log")" \
    --argjson verify_target "$(mutation_count "$workdir/verify-target.log")" \
    --argjson stage "$(mutation_count "$workdir/stage.log")" \
    --argjson migrate "$(mutation_count "$workdir/migrate.log")" \
    --argjson migrate_noop "$(mutation_count "$workdir/migrate-noop.log")" \
    --argjson activate "$(mutation_count "$workdir/activate.log")" \
    --argjson status "$(mutation_count "$workdir/status.log")" \
    --argjson same_sha_noop "$(mutation_count "$workdir/same-sha-noop.log")" \
    '{verify_artifact:$verify_artifact,verify_target:$verify_target,stage:$stage,migrate:$migrate,migrate_noop:$migrate_noop,activate:$activate,status:$status,same_sha_noop:$same_sha_noop}'
)"
jq -e '
  .verify_artifact == 0 and .verify_target == 0 and .stage > 0 and .migrate > 0 and
  .migrate_noop == 0 and .activate > 0 and .status == 0 and .same_sha_noop == 0
' <<<"$phase_mutation_counts_json" >/dev/null || fail 'phase mutation counts violate lifecycle isolation'

producer_inventory_created="$(inventory producer)"
consumer_inventory_created="$(inventory consumer)"
jq -e --arg registry "$registry_container" '.containers | contains($registry)' \
  <<<"$producer_inventory_created" >/dev/null || fail 'created producer inventory is missing the Registry container'
jq -e \
  --arg postgres "$postgres_container" \
  --arg compose_project "$compose_project" \
  --arg database_network "$database_network" \
  --arg compose_backend_network "$compose_backend_network" \
  --arg database_volume "$database_volume" '
  (.containers | contains($postgres) and contains($compose_project)) and
  (.networks | contains($database_network) and contains($compose_backend_network)) and
  (.volumes | contains($database_volume))
' <<<"$consumer_inventory_created" >/dev/null || fail 'created consumer inventory is missing an exact fixture resource'

if ! cleanup_resources; then
  fail 'Issue #65 fixture cleanup failed; inspect only the exact recorded identifiers'
fi
resources_created=0
[[ "$cleanup_verified" == "1" ]] || fail 'Issue #65 cleanup was not independently verified'

git -C "$root" diff --quiet "$source_sha" -- docker-release codex/runtime/aisoft_release ||
  fail 'docker-release/v2 or release runtime drifted during the real lifecycle run'
[[ -z "$(git -C "$root" status --porcelain --untracked-files=all -- docker-release codex/runtime/aisoft_release)" ]] ||
  fail 'docker-release/v2 or release runtime gained tracked or untracked drift during the real lifecycle run'
[[ "$(sha256_file "$root/codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh")" == "$harness_sha" && \
  "$(sha256_file "$driver_source")" == "$driver_sha" && \
  "$(sha256_file "$wrapper_source")" == "$wrapper_sha" && \
  "$(sha256_file "$web_source")" == "$web_source_sha" && \
  "$(sha256_file "$migration_source")" == "$migration_source_sha" && \
  "$(sha256_file "$architecture_source_path")" == "$architecture_source_sha" && \
  "$(sha256_file "$docker_client_path")" == "$docker_client_sha" && \
  "$(sha256_file "$timeout_client_path")" == "$timeout_client_sha" && \
  "$(sha256_file "$duplicate_evidence_path")" == "$duplicate_daemon_evidence_sha256" ]] ||
  fail 'a separately approved Issue #65 input changed during the real lifecycle run'
[[ "$(sha256_file "$snapshot_driver")" == "$driver_sha" && \
  "$(sha256_file "$snapshot_wrapper")" == "$wrapper_sha" && \
  "$(sha256_file "$wrapper")" == "$wrapper_sha" && \
  "$(sha256_file "$snapshot_web_source")" == "$web_source_sha" && \
  "$(sha256_file "$snapshot_migration_source")" == "$migration_source_sha" && \
  "$(sha256_file "$snapshot_architecture")" == "$architecture_source_sha" && \
  "$(sha256_file "$candidate_matrix")" == "$candidate_matrix_sha" ]] ||
  fail 'an immutable Issue #65 execution snapshot changed during the real lifecycle run'
argv_log_json="$(jq -Rs 'split("\n") | map(select(length > 0) | fromjson)' "$phase_log")"
orchestrator_argv_json="$(jq -s '.' "$orchestrator_log")"

evidence_temp="${evidence_path}.tmp.$$"
[[ ! -e "$evidence_temp" && ! -L "$evidence_temp" ]] ||
  fail 'evidence temporary path already exists'
jq -n \
  --arg evidence_id "issue-65-compose-5.1.4-${source_sha:0:12}" \
  --arg date "$evidence_date" \
  --arg source_sha "$source_sha" \
  --arg source_tree "$source_tree" \
  --arg docker_release_tree "$docker_release_tree" \
  --arg runtime_tree "$runtime_tree" \
  --arg harness_sha "$harness_sha" \
  --arg driver_sha "$driver_sha" \
  --arg wrapper_sha "$wrapper_sha" \
  --arg web_source_sha "$web_source_sha" \
  --arg migration_source_sha "$migration_source_sha" \
  --arg candidate_matrix_sha "$candidate_matrix_sha" \
  --arg archive_sha "$archive_sha" \
  --arg inventory_sha "$inventory_sha" \
  --arg compose_source_sha "$compose_source_sha" \
  --arg compose_model_sha "$compose_model_sha" \
  --arg architecture_sha "$architecture_sha" \
  --arg web_image_id "$web_image_id" \
  --arg migrate_image_id "$migrate_image_id" \
  --arg postgres_image_id "$producer_postgres_image_id" \
  --arg database_marker_count "$database_marker_count" \
  --arg approval_plan_sha256 "$approval_plan_sha256" \
  --argjson producer "$producer_capability" \
  --argjson consumer "$consumer_capability" \
  --argjson resources "$resources_json" \
  --argjson prerequisites "$prerequisites_json" \
  --argjson producer_before "$producer_inventory_before" \
  --argjson consumer_before "$consumer_inventory_before" \
  --argjson producer_created "$producer_inventory_created" \
  --argjson consumer_created "$consumer_inventory_created" \
  --argjson producer_after "$producer_inventory_after" \
  --argjson consumer_after "$consumer_inventory_after" \
  --argjson verify_artifact "$(<"$artifact_result")" \
  --argjson verify_target "$(<"$target_result")" \
  --argjson stage "$(<"$stage_result")" \
  --argjson migration_started "$(<"$migration_started_state")" \
  --argjson migrate "$(<"$migrate_result")" \
  --argjson migrate_noop "$(<"$migrate_noop_result")" \
  --argjson activate "$(<"$activate_result")" \
  --argjson status "$(<"$status_result")" \
  --argjson same_sha_noop "$(<"$noop_result")" \
  --argjson state "$(<"$state_path")" \
  --argjson argv "$argv_log_json" \
  --argjson orchestrator_argv "$orchestrator_argv_json" \
  --argjson phase_argv "$phase_argv_json" \
  --argjson phase_mutation_counts "$phase_mutation_counts_json" \
  --argjson negative "$negative_json" '
  {contract_version:"docker-release-v2-lifecycle-e2e-evidence/v1",evidence_id:$evidence_id,date:$date,result:"PASS",approval_plan_sha256:$approval_plan_sha256,
   source:{sha:$source_sha,tree:$source_tree,docker_release_tree:$docker_release_tree,runtime_tree:$runtime_tree,harness_sha256:$harness_sha,driver_sha256:$driver_sha,wrapper_sha256:$wrapper_sha,web_fixture_sha256:$web_source_sha,migration_fixture_sha256:$migration_source_sha,candidate_matrix_sha256:$candidate_matrix_sha},
   versions:{engine:"29.7.1",compose:"5.1.4",containerd:"2.2.6",os:"linux",architecture:"amd64",image_store:"containerd"},
   producer:$producer,consumer:$consumer,prerequisites:$prerequisites,resources:$resources,
   artifact:{archive_sha256:$archive_sha,inventory_sha256:$inventory_sha,compose_source_sha256:$compose_source_sha,compose_model_sha256:$compose_model_sha,architecture_sha256:$architecture_sha,postgres_image_id:$postgres_image_id,web_image_id:$web_image_id,migrate_image_id:$migrate_image_id},
   lifecycle:{verify_artifact:$verify_artifact,verify_target:$verify_target,stage:$stage,migration_started:$migration_started,migrate:$migrate,migrate_noop:$migrate_noop,activate:$activate,status:$status,same_sha_noop:$same_sha_noop,state:$state,phase_argv:$phase_argv,phase_mutation_counts:$phase_mutation_counts},
   negative:$negative,
   postgres:{kind:"DISPOSABLE_FIXTURE",migration_marker_count:($database_marker_count|tonumber),restore:"NOT_RUN"},
   docker_argv:{lifecycle:$argv,orchestrator:$orchestrator_argv},inventory:{producer_before:$producer_before,consumer_before:$consumer_before,producer_created:$producer_created,consumer_created:$consumer_created,producer_after:$producer_after,consumer_after:$consumer_after},
   transport:{registry:"PASS",offline_v2:"PASS",consumer_registry_pull:"REJECTED_AS_REQUIRED",compose_pull:"never",compose_build:"forbidden"},cleanup:"PASS",external:{newemaint:"NOT_RUN",dockerlab:"NOT_RUN",appserver:"NOT_RUN",production:"NOT_RUN",business_database:"NOT_RUN",business_secrets:"NOT_RUN",disposable_credential:"EPHEMERAL_NOT_RECORDED"}}' \
  >"$evidence_temp"

jq -e --arg approved_plan_sha256 "$approval_plan_sha256" '
  . as $evidence |
  .contract_version == "docker-release-v2-lifecycle-e2e-evidence/v1" and
  .result == "PASS" and
  .approval_plan_sha256 == $approved_plan_sha256 and
  .versions == {engine:"29.7.1",compose:"5.1.4",containerd:"2.2.6",os:"linux",architecture:"amd64",image_store:"containerd"} and
  .producer.daemon_id != .consumer.daemon_id and
  .producer.docker_root_dir != .consumer.docker_root_dir and
  .prerequisites.registry_image_id != .prerequisites.postgres_image_id and
  .prerequisites.postgres_image_id == .artifact.postgres_image_id and
  .negative.duplicate_daemon.result == "REJECTED_BEFORE_MUTATION" and
  .negative.duplicate_daemon.mutations == 0 and
  .negative.duplicate_daemon.inventory.producer_before == .negative.duplicate_daemon.inventory.producer_after and
  .negative.duplicate_daemon.inventory.consumer_before == .negative.duplicate_daemon.inventory.consumer_after and
  ([.artifact.postgres_image_id,.artifact.web_image_id,.artifact.migrate_image_id] | unique | length) == 3 and
  .negative.artifact_tamper.result == "REJECTED" and
  .negative.artifact_tamper.docker_calls == 0 and
  .negative.artifact_tamper.inventory.producer_before == .negative.artifact_tamper.inventory.producer_after and
  .negative.artifact_tamper.inventory.consumer_before == .negative.artifact_tamper.inventory.consumer_after and
  .negative.wrong_compose.result == "REJECTED" and .negative.wrong_compose.mutation_count == 0 and
  .negative.wrong_compose.inventory.producer_before == .negative.wrong_compose.inventory.producer_after and
  .negative.wrong_compose.inventory.consumer_before == .negative.wrong_compose.inventory.consumer_after and
  .negative.wrong_store.result == "REJECTED" and .negative.wrong_store.mutation_count == 0 and
  .negative.wrong_store.inventory.producer_before == .negative.wrong_store.inventory.producer_after and
  .negative.wrong_store.inventory.consumer_before == .negative.wrong_store.inventory.consumer_after and
  .negative.missing_staging_receipt.result == "REJECTED" and .negative.missing_staging_receipt.mutation_count == 0 and
  .negative.missing_staging_receipt.inventory.producer_before == .negative.missing_staging_receipt.inventory.producer_after and
  .negative.missing_staging_receipt.inventory.consumer_before == .negative.missing_staging_receipt.inventory.consumer_after and
  .lifecycle.stage.action == "staged" and
  (.lifecycle.migration_started.migrations | to_entries | map(.value.status) | index("started")) != null and
  .lifecycle.migrate.action == "migration-completed" and
  .lifecycle.migrate_noop.action == "migration-noop" and
  .lifecycle.activate.action == "activated" and
  .lifecycle.status.action == "healthy" and
  .lifecycle.same_sha_noop.action == "healthy-noop" and
  .lifecycle.phase_mutation_counts.verify_artifact == 0 and
  .lifecycle.phase_mutation_counts.verify_target == 0 and
  .lifecycle.phase_mutation_counts.stage > 0 and
  .lifecycle.phase_mutation_counts.migrate > 0 and
  .lifecycle.phase_mutation_counts.migrate_noop == 0 and
  .lifecycle.phase_mutation_counts.activate > 0 and
  .lifecycle.phase_mutation_counts.status == 0 and
  .lifecycle.phase_mutation_counts.same_sha_noop == 0 and
  (.lifecycle.phase_argv | keys | sort) == ["activate","migrate","migrate_noop","same_sha_noop","stage","status","verify_artifact","verify_target"] and
  .postgres.migration_marker_count == 1 and
  .cleanup == "PASS" and
  .inventory.producer_created != .inventory.producer_before and
  .inventory.consumer_created != .inventory.consumer_before and
  (.inventory.consumer_created.networks | contains($evidence.resources.database_network) and contains($evidence.resources.compose_backend_network)) and
  .inventory.producer_before == .inventory.producer_after and
  .inventory.consumer_before == .inventory.consumer_after
' "$evidence_temp" >/dev/null
chmod 0444 "$evidence_temp"
rm -rf -- "$workdir"
[[ ! -e "$workdir" ]] || fail 'secret-bearing Issue #65 workdir could not be removed before PASS publication'
if ! ln "$evidence_temp" "$evidence_path"; then
  fail 'immutable Issue #65 PASS evidence path was concurrently created; refusing overwrite'
fi
rm -f -- "$evidence_temp"
evidence_temp=""
if ! rmdir "$execution_lock"; then
  rm -f -- "$evidence_path"
  fail 'Issue #65 execution lock could not be removed before PASS publication'
fi
lock_owned=0

printf '%s\n' 'PASS: real disposable Docker release v2 lifecycle evidence written'
