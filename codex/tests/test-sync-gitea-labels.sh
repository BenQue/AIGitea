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
case "$method" in
  GET)
    cat "$MOCK_STATE"
    ;;
  POST)
    jq --argjson label "$data" '. + [$label]' "$MOCK_STATE" >"$MOCK_STATE.next"
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
  PATH="$TMP/bin:$PATH" \
    AGENT_ENV_FILE="$TMP/agent.env" \
    MOCK_ARGV_LOG="$TMP/argv.log" \
    MOCK_CALLS_LOG="$TMP/calls.log" \
    MOCK_STATE="$TMP/state.json" \
    MOCK_SENTINEL="$SENTINEL" \
    bash -x "$SYNC" >"$stdout_file" 2>"$stderr_file"
}

run_sync "$TMP/first.stdout" "$TMP/first.stderr"
[[ "$(<"$TMP/first.stdout")" == 'created=16 existing=16' ]]
[[ "$(jq 'length' "$TMP/state.json")" == 16 ]]

first_post_count="$(grep -c '^POST$' "$TMP/calls.log")"
[[ "$first_post_count" == 16 ]]

run_sync "$TMP/second.stdout" "$TMP/second.stderr"
[[ "$(<"$TMP/second.stdout")" == 'created=0 existing=16' ]]
[[ "$(jq 'length' "$TMP/state.json")" == 16 ]]
[[ "$(grep -c '^POST$' "$TMP/calls.log")" == "$first_post_count" ]]
[[ "$(grep -c '^GET$' "$TMP/calls.log")" == 2 ]]
if grep -Eq '^(PATCH|DELETE)$' "$TMP/calls.log"; then
  echo 'sync attempted a destructive label method' >&2
  exit 1
fi

if grep -Fq "$SENTINEL" \
  "$TMP/argv.log" \
  "$TMP/first.stdout" "$TMP/first.stderr" \
  "$TMP/second.stdout" "$TMP/second.stderr"; then
  echo 'sentinel token leaked through argv, stdout, or stderr' >&2
  exit 1
fi

echo 'sync-gitea-labels mock regression passed.'
