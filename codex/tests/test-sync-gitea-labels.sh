#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
SYNC="$ROOT/codex/tools/sync-gitea-labels.sh"
SENTINEL='SYNC_TOKEN_MUST_NOT_LEAK_7f2d9a'
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin"
printf '[]\n' >"$TMP/state.json"
: >"$TMP/argv.log"
: >"$TMP/calls.log"

cat >"$TMP/bin/curl" <<'MOCK_CURL'
#!/usr/bin/env bash
set -euo pipefail

method=GET
data=''
consume_config=false
args=("$@")

for arg in "${args[@]}"; do
  printf '%s\n' "$arg" >>"$MOCK_ARGV_LOG"
done

index=0
while ((index < ${#args[@]})); do
  arg="${args[$index]}"
  case "$arg" in
    --config)
      index=$((index + 1))
      [[ "${args[$index]}" == '-' ]] && consume_config=true
      ;;
    --request)
      index=$((index + 1))
      method="${args[$index]}"
      ;;
    --data)
      index=$((index + 1))
      data="${args[$index]}"
      ;;
  esac
  index=$((index + 1))
done

if [[ "$consume_config" == true ]]; then
  saw_auth=false
  while IFS= read -r config_line; do
    if [[ "$config_line" == *"$MOCK_SENTINEL"* ]]; then
      saw_auth=true
    fi
  done
  [[ "$saw_auth" == true ]]
else
  echo 'curl mock did not receive stdin config' >&2
  exit 91
fi

printf '%s\n' "$method" >>"$MOCK_CALLS_LOG"

# Every label carries a stable synthetic id so drift repair can address it.
next_id() {
  jq '[.[].id] + [0] | max + 1' "$MOCK_STATE"
}

case "$method" in
  GET)
    cat "$MOCK_STATE"
    ;;
  POST)
    jq --argjson label "$data" --argjson id "$(next_id)" \
      '. + [$label + {id: $id}]' "$MOCK_STATE" >"$MOCK_STATE.next"
    mv "$MOCK_STATE.next" "$MOCK_STATE"
    ;;
  PATCH)
    target_id="${args[${#args[@]}-1]##*/}"
    jq --argjson label "$data" --argjson id "$target_id" \
      'map(if .id == $id then $label + {id: $id} else . end)' \
      "$MOCK_STATE" >"$MOCK_STATE.next"
    mv "$MOCK_STATE.next" "$MOCK_STATE"
    ;;
  *)
    printf 'unexpected method: %s\n' "$method" >&2
    exit 90
    ;;
esac
MOCK_CURL
chmod +x "$TMP/bin/curl"

cat >"$TMP/agent.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=owner
GITEA_REPO=repo
GITEA_TOKEN=$SENTINEL
EOF

run_sync() {
  local stdout_file="$1"
  local stderr_file="$2"
  local env_file="${3:-$TMP/agent.env}"
  PATH="$TMP/bin:$PATH" \
    AGENT_ENV_FILE="$env_file" \
    MOCK_ARGV_LOG="$TMP/argv.log" \
    MOCK_CALLS_LOG="$TMP/calls.log" \
    MOCK_STATE="$TMP/state.json" \
    MOCK_SENTINEL="$SENTINEL" \
    bash -x "$SYNC" >"$stdout_file" 2>"$stderr_file"
}

CANONICAL_COUNT="$(jq '.canonical | length' "$ROOT/codex/config/gitea-labels.json")"

run_sync "$TMP/first.stdout" "$TMP/first.stderr"
[[ "$(<"$TMP/first.stdout")" == \
  "created=$CANONICAL_COUNT updated=0 unchanged=0 retired_present=0" ]]
[[ "$(jq 'length' "$TMP/state.json")" == "$CANONICAL_COUNT" ]]

first_post_count="$(grep -c '^POST$' "$TMP/calls.log")"
[[ "$first_post_count" == "$CANONICAL_COUNT" ]]

# Second run is a pure no-op: no writes of any kind (#108 AC-2).
run_sync "$TMP/second.stdout" "$TMP/second.stderr"
[[ "$(<"$TMP/second.stdout")" == \
  "created=0 updated=0 unchanged=$CANONICAL_COUNT retired_present=0" ]]
[[ "$(jq 'length' "$TMP/state.json")" == "$CANONICAL_COUNT" ]]
[[ "$(grep -c '^POST$' "$TMP/calls.log")" == "$first_post_count" ]]
[[ "$(grep -c '^GET$' "$TMP/calls.log")" == 2 ]]
if grep -Eq '^PATCH$' "$TMP/calls.log"; then
  echo 'sync patched a label that was already in sync' >&2
  exit 1
fi

# Cosmetic-only differences must not read as drift, or provision would rewrite
# the same label on every run.
jq '(.[0].color |= ("#" + (. | ascii_upcase))) |
    (.[0].description |= ("  " + . + "  "))' \
  "$TMP/state.json" >"$TMP/state.next"
mv "$TMP/state.next" "$TMP/state.json"
run_sync "$TMP/cosmetic.stdout" "$TMP/cosmetic.stderr"
[[ "$(<"$TMP/cosmetic.stdout")" == \
  "created=0 updated=0 unchanged=$CANONICAL_COUNT retired_present=0" ]]

# Real drift in color or description is repaired in place, never by delete and
# recreate.
patch_before="$(grep -c '^PATCH$' "$TMP/calls.log" || true)"
jq '.[0].color = "ffffff" | .[1].description = "drifted"' \
  "$TMP/state.json" >"$TMP/state.next"
mv "$TMP/state.next" "$TMP/state.json"
run_sync "$TMP/drift.stdout" "$TMP/drift.stderr"
[[ "$(<"$TMP/drift.stdout")" == \
  "created=0 updated=2 unchanged=$((CANONICAL_COUNT - 2)) retired_present=0" ]]
[[ "$(grep -c '^PATCH$' "$TMP/calls.log")" == "$((patch_before + 2))" ]]
[[ "$(jq 'length' "$TMP/state.json")" == "$CANONICAL_COUNT" ]]
expected_color="$(jq -r '.canonical[0].color' "$ROOT/codex/config/gitea-labels.json")"
[[ "$(jq -r '.[0].color' "$TMP/state.json")" == "$expected_color" ]]

# Repairing drift converges: the next run is a no-op again.
run_sync "$TMP/converge.stdout" "$TMP/converge.stderr"
[[ "$(<"$TMP/converge.stdout")" == \
  "created=0 updated=0 unchanged=$CANONICAL_COUNT retired_present=0" ]]

# Retired values are reported and left alone. Deletion is not implemented, so a
# retired label can never disappear without a human doing it (#108 AC-7).
retired_name="$(jq -r '.retired[0].name' "$ROOT/codex/config/gitea-labels.json")"
jq --arg name "$retired_name" \
  '. + [{name: $name, color: "cccccc", description: "legacy", id: 9001}]' \
  "$TMP/state.json" >"$TMP/state.next"
mv "$TMP/state.next" "$TMP/state.json"
run_sync "$TMP/retired.stdout" "$TMP/retired.stderr"
[[ "$(<"$TMP/retired.stdout")" == \
  "created=0 updated=0 unchanged=$CANONICAL_COUNT retired_present=1" ]]
grep -Fq "NOTICE: retired label $retired_name still exists remotely" \
  "$TMP/retired.stderr"
[[ "$(jq --arg name "$retired_name" 'any(.[]; .name == $name)' "$TMP/state.json")" \
  == 'true' ]]

if grep -Eq '^DELETE$' "$TMP/calls.log"; then
  echo 'sync attempted to delete a label' >&2
  exit 1
fi

# A malformed manifest must fail closed before any API call is made.
calls_before_manifest="$(wc -l <"$TMP/calls.log" | tr -d ' ')"
rc=0
MANIFEST_OVERRIDE="$TMP/broken-manifest.json"
printf '[]\n' >"$MANIFEST_OVERRIDE"
PATH="$TMP/bin:$PATH" \
  AGENT_ENV_FILE="$TMP/agent.env" \
  MOCK_ARGV_LOG="$TMP/argv.log" \
  MOCK_CALLS_LOG="$TMP/calls.log" \
  MOCK_STATE="$TMP/state.json" \
  MOCK_SENTINEL="$SENTINEL" \
  bash -c '
    set -euo pipefail
    source "$1"
    aisoft_label_manifest_validate "$2"
  ' _ "$ROOT/codex/agent/gitea-label-manifest.sh" "$MANIFEST_OVERRIDE" \
  >"$TMP/manifest.stdout" 2>"$TMP/manifest.stderr" || rc=$?
[[ "$rc" == 3 ]]
[[ "$(wc -l <"$TMP/calls.log" | tr -d ' ')" == "$calls_before_manifest" ]]

# Inline profile keeps working through the transition but must print the
# deprecation notice (#111).
grep -Fq 'DEPRECATED: inline GITEA_TOKEN is deprecated' "$TMP/first.stderr"

# Token-file profile (#111): GITEA_TOKEN_FILE only, no deprecation notice.
printf '%s\n' "$SENTINEL" >"$TMP/agent.token"
chmod 600 "$TMP/agent.token"
cat >"$TMP/agent-file.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=owner
GITEA_REPO=repo
GITEA_TOKEN_FILE=$TMP/agent.token
EOF
run_sync "$TMP/third.stdout" "$TMP/third.stderr" "$TMP/agent-file.env"
[[ "$(<"$TMP/third.stdout")" == \
  "created=0 updated=0 unchanged=$CANONICAL_COUNT retired_present=1" ]]
if grep -Fq 'DEPRECATED' "$TMP/third.stderr"; then
  echo 'file profile must not print the deprecation notice' >&2
  exit 1
fi

# Permissive token file fails closed before any API call.
chmod 644 "$TMP/agent.token"
calls_before="$(wc -l <"$TMP/calls.log" | tr -d ' ')"
rc=0
run_sync "$TMP/fourth.stdout" "$TMP/fourth.stderr" "$TMP/agent-file.env" ||
  rc=$?
[[ "$rc" == 20 ]]
grep -Fq 'BLOCKED_EXTERNAL: GITEA_TOKEN_FILE mode must be 400 or 600' \
  "$TMP/fourth.stderr"
[[ "$(wc -l <"$TMP/calls.log" | tr -d ' ')" == "$calls_before" ]]

# Missing both forms is a hard requirement error.
cat >"$TMP/agent-missing.env" <<EOF
GITEA_URL=http://mock.gitea.invalid
GITEA_OWNER=owner
GITEA_REPO=repo
EOF
rc=0
run_sync "$TMP/fifth.stdout" "$TMP/fifth.stderr" "$TMP/agent-missing.env" ||
  rc=$?
[[ "$rc" == 1 ]]
grep -Fq 'GITEA_TOKEN_FILE or GITEA_TOKEN is required' "$TMP/fifth.stderr"

if grep -Fq "$SENTINEL" \
  "$TMP/argv.log" \
  "$TMP/first.stdout" "$TMP/first.stderr" \
  "$TMP/second.stdout" "$TMP/second.stderr" \
  "$TMP/cosmetic.stdout" "$TMP/cosmetic.stderr" \
  "$TMP/drift.stdout" "$TMP/drift.stderr" \
  "$TMP/converge.stdout" "$TMP/converge.stderr" \
  "$TMP/retired.stdout" "$TMP/retired.stderr" \
  "$TMP/manifest.stdout" "$TMP/manifest.stderr" \
  "$TMP/third.stdout" "$TMP/third.stderr" \
  "$TMP/fourth.stdout" "$TMP/fourth.stderr" \
  "$TMP/fifth.stdout" "$TMP/fifth.stderr"; then
  echo 'sentinel token leaked through argv, stdout, or stderr' >&2
  exit 1
fi

echo 'sync-gitea-labels mock regression passed.'
