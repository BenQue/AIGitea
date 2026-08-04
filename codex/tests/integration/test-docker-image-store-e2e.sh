#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
fixture_root="$root/codex/tests/fixtures/docker-image-store-e2e"
mode="${1:---not-run}"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
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

not_run() {
  printf '%s\n' 'NOT RUN: Docker image-store E2E requires separate disposable-environment authorization.'
  printf '%s\n' 'Use --preflight for authorized read-only probes or --execute for the exact approved fixture.'
}

case "$mode" in
  --not-run)
    not_run
    exit 0
    ;;
  --preflight|--execute) ;;
  *) fail 'usage: test-docker-image-store-e2e.sh [--not-run|--preflight|--execute]' ;;
esac

if [[ "$mode" == "--preflight" ]]; then
  [[ "${AISOFT_E2E_READONLY_AUTHORIZED:-}" == "issue-27-disposable-preflight-approved" ]] ||
    fail 'read-only preflight authorization marker is missing'
else
  [[ "${AISOFT_E2E_EXECUTE_AUTHORIZED:-}" == "issue-27-disposable-e2e-approved" ]] ||
    fail 'execute authorization marker is missing'
fi

for command in docker jq grep; do
  command -v "$command" >/dev/null 2>&1 || fail "required command is unavailable: $command"
done
if [[ "$mode" == "--execute" ]]; then
  for command in awk chmod cp date go mktemp rm shasum sort timeout; do
    command -v "$command" >/dev/null 2>&1 || fail "required execute command is unavailable: $command"
  done
fi

producer_host="${AISOFT_E2E_PRODUCER_DOCKER_HOST:-}"
consumer_host="${AISOFT_E2E_CONSUMER_DOCKER_HOST:-}"
producer_id="${AISOFT_E2E_PRODUCER_ID:-}"
consumer_id="${AISOFT_E2E_CONSUMER_ID:-}"
release_id="${AISOFT_E2E_RELEASE_ID:-}"
expected_store="${AISOFT_E2E_EXPECTED_STORE:-containerd}"
registry_image="${AISOFT_E2E_REGISTRY_IMAGE:-}"
registry_port="${AISOFT_E2E_REGISTRY_PORT:-}"
evidence_path="${AISOFT_E2E_EVIDENCE_PATH:-}"

[[ -n "$producer_host" && -n "$consumer_host" ]] || fail 'two Docker hosts are required'
[[ "$producer_host" != "$consumer_host" ]] || fail 'producer and consumer Docker hosts must differ'
validate_docker_host producer "$producer_host"
validate_docker_host consumer "$consumer_host"
[[ "$producer_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]] ||
  fail 'AISOFT_E2E_PRODUCER_ID is invalid'
[[ "$consumer_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]] ||
  fail 'AISOFT_E2E_CONSUMER_ID is invalid'
[[ "$producer_id" != "$consumer_id" ]] || fail 'producer and consumer IDs must differ'
[[ "$release_id" =~ ^[0-9a-f]{40}$ ]] || fail 'AISOFT_E2E_RELEASE_ID must be a full Git SHA'
[[ "$expected_store" == "containerd" || "$expected_store" == "classic" ]] ||
  fail 'AISOFT_E2E_EXPECTED_STORE must be containerd or classic'
[[ "$registry_image" =~ ^[a-z0-9][a-z0-9./:_-]*@sha256:[0-9a-f]{64}$ ]] ||
  fail 'AISOFT_E2E_REGISTRY_IMAGE must be digest-pinned'
[[ "$registry_port" =~ ^[0-9]+$ ]] || fail 'AISOFT_E2E_REGISTRY_PORT must be numeric'
((registry_port >= 1024 && registry_port <= 65535)) || fail 'Registry port is out of range'
if [[ "$mode" == "--execute" ]]; then
  [[ "$evidence_path" == /* && "$evidence_path" != *".."* ]] ||
    fail 'AISOFT_E2E_EVIDENCE_PATH must be an absolute normalized path'
  [[ -d "$(dirname -- "$evidence_path")" ]] || fail 'evidence parent directory does not exist'
  [[ ! -e "$evidence_path" ]] || fail 'evidence path already exists; immutable evidence is not overwritten'
fi

docker_producer() {
  docker --host "$producer_host" "$@"
}

docker_consumer() {
  docker --host "$consumer_host" "$@"
}

detect_capability() {
  local side="$1"
  local server driver driver_status compose_version store marker_count driver_type_count
  local daemon_id docker_root_dir compose_minor
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
  jq -e '
    type == "object" and
    (.Version | type == "string") and
    .Os == "linux" and .Arch == "amd64"
  ' <<<"$server" >/dev/null || fail "$side Docker server metadata is invalid"
  jq -e '(. == null) or (type == "array")' <<<"$driver_status" >/dev/null ||
    fail "$side Docker DriverStatus is invalid"
  marker_count="$(jq '[.[]? | select(.[0] == "driver-type" and .[1] == "io.containerd.snapshotter.v1")] | length' <<<"$driver_status")"
  driver_type_count="$(jq '[.[]? | select(.[0] == "driver-type")] | length' <<<"$driver_status")"
  if [[ "$marker_count" == "1" && "$driver_type_count" == "1" && "$driver" == "overlayfs" ]]; then
    store="containerd"
  elif [[ "$driver_type_count" == "0" && "$driver" == "overlay2" ]]; then
    store="classic"
  else
    fail "$side Docker image store is unknown, ambiguous, or conflicting"
  fi
  [[ "$store" == "$expected_store" ]] || fail "$side Docker image store does not match the authorized mode"
  jq -e -r '.Version' <<<"$server" | grep -Eq '^29\.[0-9]+\.[0-9]+$' ||
    fail "$side Docker Engine must be exact major 29"
  if [[ "$compose_version" =~ ^2\.([0-9]+)\.[0-9]+$ ]]; then
    compose_minor="$((10#${BASH_REMATCH[1]}))"
  else
    fail "$side Docker Compose must report exact v2 major.minor.patch"
  fi
  ((compose_minor >= 27)) ||
    fail "$side Docker Compose is below the committed compatibility range"
  [[ -n "$daemon_id" && ${#daemon_id} -le 256 && "$daemon_id" != *$'\n'* ]] ||
    fail "$side Docker daemon ID is invalid"
  [[ "$docker_root_dir" == /* && ${#docker_root_dir} -le 4096 && "$docker_root_dir" != *$'\n'* ]] ||
    fail "$side Docker data root is invalid"
  jq -n \
    --arg engine "$(jq -r '.Version' <<<"$server")" \
    --arg compose "$compose_version" \
    --arg store "$store" \
    --arg daemon_id "$daemon_id" \
    --arg docker_root_dir "$docker_root_dir" \
    '{engine:$engine,compose:$compose,os:"linux",architecture:"amd64",image_store:$store,daemon_id:$daemon_id,docker_root_dir:$docker_root_dir}'
}

transport_reference="aisoft.local/admin/issue27/web:$release_id"
fixture_prefix="aisoft-issue27-${release_id:0:12}"
registry_container="$fixture_prefix-registry"
compose_project="$fixture_prefix-consumer"
registry_tag="127.0.0.1:${registry_port}/aisoft/issue27:${release_id}"

producer_capability="$(detect_capability producer)"
consumer_capability="$(detect_capability consumer)"
producer_daemon_id="$(jq -er '.daemon_id' <<<"$producer_capability")"
consumer_daemon_id="$(jq -er '.daemon_id' <<<"$consumer_capability")"
[[ "$producer_daemon_id" != "$consumer_daemon_id" ]] ||
  fail 'producer and consumer endpoints resolve to the same Docker daemon'
registry_fixture_metadata="$(
  docker_producer image inspect --format '{{json .}}' "$registry_image" 2>/dev/null
)" || fail 'digest-pinned Registry fixture image is not preloaded on producer'
jq -e '
  type == "object" and
  (.Id | type == "string" and test("^sha256:[0-9a-f]{64}$")) and
  .Os == "linux" and .Architecture == "amd64"
' <<<"$registry_fixture_metadata" >/dev/null ||
  fail 'Registry fixture image metadata is invalid'
if docker_producer container inspect "$registry_container" >/dev/null 2>&1; then
  fail 'fixture Registry container already exists'
fi
if docker_producer image inspect "$transport_reference" >/dev/null 2>&1; then
  fail 'fixture transport tag already exists on producer'
fi
if docker_consumer image inspect "$transport_reference" >/dev/null 2>&1; then
  fail 'fixture transport tag already exists on consumer'
fi
if [[ -n "$(docker_consumer ps -aq --filter "label=com.docker.compose.project=$compose_project")" ]]; then
  fail 'fixture Compose project already exists on consumer'
fi

if [[ "$mode" == "--preflight" ]]; then
  jq -n \
    --arg producer_id "$producer_id" \
    --arg consumer_id "$consumer_id" \
    --argjson producer "$producer_capability" \
    --argjson consumer "$consumer_capability" \
    '{result:"PASS_READ_ONLY",producer_id:$producer_id,consumer_id:$consumer_id,producer:$producer,consumer:$consumer,mutations:0}'
  exit 0
fi

producer_volumes_before="$(docker_producer volume ls --quiet | LC_ALL=C sort)"
consumer_volumes_before="$(docker_consumer volume ls --quiet | LC_ALL=C sort)"
producer_images_before="$(docker_producer image ls --all --no-trunc --quiet | LC_ALL=C sort -u)"
consumer_images_before="$(docker_consumer image ls --all --no-trunc --quiet | LC_ALL=C sort -u)"

workdir="$(mktemp -d "${TMPDIR:-/tmp}/aisoft-issue27.XXXXXX")"
compose_path="$workdir/compose.json"
archive_path="$workdir/images.tar"
inventory_path="$workdir/images.inventory.json"
release_path="$workdir/release.json"
architecture_path="$workdir/architecture.lock.json"
resources_created=0
image_id=""

cleanup_resources() {
  local cleanup_status=0 current_image
  if ! docker_consumer compose --project-name "$compose_project" --file "$compose_path" down --volumes --remove-orphans >/dev/null 2>&1; then
    cleanup_status=1
  fi
  if ! docker_consumer image rm "$transport_reference" >/dev/null 2>&1; then
    cleanup_status=1
  fi
  if [[ -n "$image_id" ]] && docker_consumer image inspect "$image_id" >/dev/null 2>&1; then
    if ! docker_consumer image rm "$image_id" >/dev/null 2>&1; then
      cleanup_status=1
    fi
  fi
  if ! docker_producer container rm --force --volumes "$registry_container" >/dev/null 2>&1; then
    cleanup_status=1
  fi
  if ! docker_producer image rm "$transport_reference" "$registry_tag" >/dev/null 2>&1; then
    cleanup_status=1
  fi
  if [[ -n "$image_id" ]] && docker_producer image inspect "$image_id" >/dev/null 2>&1; then
    if ! docker_producer image rm "$image_id" >/dev/null 2>&1; then
      cleanup_status=1
    fi
  fi
  for current_image in $(docker_producer image ls --all --no-trunc --quiet | LC_ALL=C sort -u); do
    if ! grep -Fqx "$current_image" <<<"$producer_images_before" &&
      docker_producer image inspect "$current_image" >/dev/null 2>&1; then
      if ! docker_producer image rm "$current_image" >/dev/null 2>&1; then
        cleanup_status=1
      fi
    fi
  done
  for current_image in $(docker_consumer image ls --all --no-trunc --quiet | LC_ALL=C sort -u); do
    if ! grep -Fqx "$current_image" <<<"$consumer_images_before" &&
      docker_consumer image inspect "$current_image" >/dev/null 2>&1; then
      if ! docker_consumer image rm "$current_image" >/dev/null 2>&1; then
        cleanup_status=1
      fi
    fi
  done
  if [[ -n "$(docker_consumer ps -aq --filter "label=com.docker.compose.project=$compose_project")" ]]; then
    cleanup_status=1
  fi
  if [[ -n "$(docker_consumer network ls -q --filter "label=com.docker.compose.project=$compose_project")" ]]; then
    cleanup_status=1
  fi
  if docker_consumer image inspect "$transport_reference" >/dev/null 2>&1; then
    cleanup_status=1
  fi
  if docker_producer container inspect "$registry_container" >/dev/null 2>&1; then
    cleanup_status=1
  fi
  if docker_producer image inspect "$transport_reference" >/dev/null 2>&1 ||
    docker_producer image inspect "$registry_tag" >/dev/null 2>&1; then
    cleanup_status=1
  fi
  if [[ -n "$image_id" ]] &&
    { docker_consumer image inspect "$image_id" >/dev/null 2>&1 ||
      docker_producer image inspect "$image_id" >/dev/null 2>&1; }; then
    cleanup_status=1
  fi
  if [[ "$(docker_producer volume ls --quiet | LC_ALL=C sort)" != "$producer_volumes_before" ]] ||
    [[ "$(docker_consumer volume ls --quiet | LC_ALL=C sort)" != "$consumer_volumes_before" ]]; then
    cleanup_status=1
  fi
  if [[ "$(docker_producer image ls --all --no-trunc --quiet | LC_ALL=C sort -u)" != "$producer_images_before" ]] ||
    [[ "$(docker_consumer image ls --all --no-trunc --quiet | LC_ALL=C sort -u)" != "$consumer_images_before" ]]; then
    cleanup_status=1
  fi
  return "$cleanup_status"
}

on_exit() {
  local status="$?"
  if [[ "$resources_created" == "1" ]]; then
    cleanup_resources || true
  fi
  rm -rf -- "$workdir"
  exit "$status"
}
trap on_exit EXIT

CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
  go build -trimpath -ldflags '-s -w -buildid=' -o "$workdir/server" \
  "$fixture_root/server.go"

resources_created=1
docker_producer image build \
  --platform linux/amd64 \
  --pull=false \
  --network none \
  --build-arg "RELEASE_ID=$release_id" \
  --tag "$registry_tag" \
  --file "$fixture_root/Dockerfile" \
  "$workdir" >/dev/null

image_id="$(docker_producer image inspect --format '{{.Id}}' "$registry_tag")"
[[ "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]] || fail 'producer image ID is invalid'

docker_producer container run \
  --detach \
  --name "$registry_container" \
  --publish "127.0.0.1:${registry_port}:5000" \
  --tmpfs "/var/lib/registry:rw,nosuid,nodev,noexec,size=67108864" \
  "$registry_image" >/dev/null
docker_producer image push "$registry_tag" >/dev/null

registry_reference="$(
  docker_producer image inspect --format '{{json .RepoDigests}}' "$registry_tag" |
    jq -er --arg prefix "127.0.0.1:${registry_port}/aisoft/issue27@sha256:" \
      '[.[] | select(startswith($prefix))] | if length == 1 then .[0] else error("digest count") end'
)"
[[ "$registry_reference" =~ @sha256:[0-9a-f]{64}$ ]] || fail 'Registry digest reference is invalid'
registry_digest="${registry_reference##*@}"

docker_producer image pull "$registry_reference" >/dev/null
pulled_id="$(docker_producer image inspect --format '{{.Id}}' "$registry_reference")"
[[ "$pulled_id" == "$image_id" ]] || fail 'Registry digest pull changed image ID'
docker_producer image tag "$registry_reference" "$transport_reference"
tagged_id="$(docker_producer image inspect --format '{{.Id}}' "$transport_reference")"
[[ "$tagged_id" == "$image_id" ]] || fail 'transport tag does not resolve to the exact image ID'

docker_producer image save --output "$archive_path" "$transport_reference"
archive_sha="$(shasum -a 256 "$archive_path" | awk '{print $1}')"

jq -n \
  --arg service web \
  --arg reference "$registry_reference" \
  --arg digest "$registry_digest" \
  --arg image_id "$image_id" \
  --arg transport "$transport_reference" \
  --arg archive_sha "$archive_sha" \
  '{contract_version:"docker-release-offline-inventory/v2",archive_sha256:$archive_sha,images:[{service:$service,reference:$reference,digest:$digest,image_id:$image_id,transport_reference:$transport,runtime_reference:$transport,platform:"linux/amd64"}]}' \
  >"$inventory_path"
inventory_sha="$(shasum -a 256 "$inventory_path" | awk '{print $1}')"

cp "$root/architecture/reference/newemaint/architecture.lock.json" "$architecture_path"
architecture_sha="$(shasum -a 256 "$architecture_path" | awk '{print $1}')"

jq -n \
  --arg image "$transport_reference" \
  --arg release "$release_id" \
  '{services:{web:{image:$image,pull_policy:"never",user:"65532:65532",read_only:true,cap_drop:["ALL"],security_opt:["no-new-privileges:true"],tmpfs:["/tmp:size=16m,mode=1777"],deploy:{resources:{limits:{cpus:"0.25",memory:"268435456"}}},logging:{driver:"json-file",options:{"max-size":"1m","max-file":"2"}},networks:{backend:null},labels:{"com.aisoft.release.id":$release,"com.aisoft.release.service":"web"},healthcheck:{test:["CMD","/server","healthcheck"],interval:"2s",timeout:"2s",retries:15}}},networks:{edge:{internal:false},backend:{internal:true}}}' \
  >"$compose_path"
compose_sha="$(shasum -a 256 "$compose_path" | awk '{print $1}')"

jq -n \
  --arg release "$release_id" \
  --arg compose_sha "$compose_sha" \
  --arg architecture_sha "$architecture_sha" \
  --arg reference "$registry_reference" \
  --arg digest "$registry_digest" \
  --arg image_id "$image_id" \
  --arg transport "$transport_reference" \
  --arg archive_sha "$archive_sha" \
  --arg inventory_sha "$inventory_sha" \
  '{contract_version:"docker-release/v1",release_id:$release,source_repository:"admin/issue27",merge_sha:$release,platform:"linux/amd64",compose:{path:"compose.json",sha256:$compose_sha},architecture:{path:"architecture.lock.json",profile_id:"linux-node-postgres-v1",catalog_revision:"2026.08.0",sha256:$architecture_sha},images:[{service:"web",reference:$reference,digest:$digest,image_id:$image_id,transport_reference:$transport,runtime_reference:$transport}],runtime_services:["web"],migration:null,offline_bundle:{contract_version:"docker-release-offline-bundle/v2",archive_path:"images.tar",archive_sha256:$archive_sha,inventory_path:"images.inventory.json",inventory_sha256:$inventory_sha}}' \
  >"$release_path"

if timeout 20 docker_consumer image pull "$registry_reference" >/dev/null 2>&1; then
  docker_consumer image rm "$registry_reference" >/dev/null 2>&1 || true
  fail 'offline consumer unexpectedly reached the producer Registry'
fi

docker_consumer image load --input "$archive_path" >/dev/null
consumer_id_after_load="$(docker_consumer image inspect --format '{{.Id}}' "$transport_reference")"
consumer_platform="$(docker_consumer image inspect --format '{{.Os}}/{{.Architecture}}' "$transport_reference")"
consumer_repo_digests="$(docker_consumer image inspect --format '{{json .RepoDigests}}' "$transport_reference")"
[[ "$consumer_id_after_load" == "$image_id" ]] || fail 'consumer image ID differs after load'
[[ "$consumer_platform" == "linux/amd64" ]] || fail 'consumer image platform differs after load'

docker_consumer compose \
  --project-name "$compose_project" \
  --file "$compose_path" \
  config --format json --no-interpolate --no-env-resolution >/dev/null
if ! docker_consumer compose \
  --project-name "$compose_project" \
  --file "$compose_path" \
  up --detach --wait --wait-timeout 60 --pull never --no-build >/dev/null; then
  failed_container_id="$(
    docker_consumer compose --project-name "$compose_project" --file "$compose_path" \
      ps --all --quiet web 2>/dev/null || true
  )"
  if [[ "$failed_container_id" =~ ^[0-9a-f]{12,64}$ ]]; then
    docker_consumer container inspect \
      --format 'consumer state: exit={{.State.ExitCode}} oom={{.State.OOMKilled}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
      "$failed_container_id" >&2 || true
  fi
  fail 'consumer Compose up or health wait failed'
fi

container_id="$(docker_consumer compose --project-name "$compose_project" --file "$compose_path" ps --quiet web)"
[[ "$container_id" =~ ^[0-9a-f]{12,64}$ ]] || fail 'consumer Compose container ID is invalid'
container_inspect="$(docker_consumer container inspect --format '{{json .}}' "$container_id")"
jq -e \
  --arg runtime "$transport_reference" \
  --arg image_id "$image_id" \
  --arg release "$release_id" \
  '.Config.Image == $runtime and .Image == $image_id and .Config.Labels["com.aisoft.release.id"] == $release and .Config.Labels["com.aisoft.release.service"] == "web" and .State.Running == true and .State.Health.Status == "healthy"' \
  <<<"$container_inspect" >/dev/null || fail 'post-start container identity or health mismatch'

if ! cleanup_resources; then
  fail 'fixture cleanup failed; inspect only the exact recorded fixture identifiers'
fi
resources_created=0

jq -n \
  --arg evidence_id "issue-27-${expected_store}-${release_id:0:12}" \
  --arg date "$(date -u +%F)" \
  --arg release "$release_id" \
  --arg producer_id "$producer_id" \
  --arg consumer_id "$consumer_id" \
  --arg expected_store "$expected_store" \
  --argjson producer "$producer_capability" \
  --argjson consumer "$consumer_capability" \
  --arg registry_reference "$registry_reference" \
  --arg image_id "$image_id" \
  --arg runtime_reference "$transport_reference" \
  --arg archive_sha "$archive_sha" \
  --arg inventory_sha "$inventory_sha" \
  --arg compose_sha "$compose_sha" \
  --arg architecture_sha "$architecture_sha" \
  --argjson consumer_repo_digests "$consumer_repo_digests" \
  '{contract_version:"docker-image-store-e2e-evidence/v1",evidence_id:$evidence_id,date:$date,result:"PASS",release_id:$release,producer_id:$producer_id,consumer_id:$consumer_id,expected_store:$expected_store,producer:$producer,consumer:$consumer,registry_reference:$registry_reference,image_id:$image_id,runtime_reference:$runtime_reference,archive_sha256:$archive_sha,inventory_sha256:$inventory_sha,compose_sha256:$compose_sha,architecture_sha256:$architecture_sha,consumer_repo_digests:$consumer_repo_digests,offline_registry_pull:"REJECTED_AS_REQUIRED",compose_pull:"never",compose_build:"forbidden",cleanup:"PASS"}' \
  >"$evidence_path"
chmod 0444 "$evidence_path"

printf '%s\n' "PASS: real disposable Docker $expected_store E2E evidence written"
trap - EXIT
rm -rf -- "$workdir"
