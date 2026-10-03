#!/usr/bin/env bash
# Isolated operator process + real filesystem; external Gitea is a synthetic fixture.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
REAL_PYTHON="$(command -v python3)"
mkdir -p "$TMP/bin"
export ROTATION_FIXTURE_ROOT="$ROOT" ROTATION_FIXTURE_PYTHON="$REAL_PYTHON"
cat >"$TMP/bin/python3" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
[[ "$1" == -I && "$2" == -c && "$3" == *credential_rotation* ]]
shift 3
exec "$ROTATION_FIXTURE_PYTHON" "$ROTATION_FIXTURE_ROOT/codex/runtime/tests/rotation_cli_fixture.py" "$@"
MOCK
chmod +x "$TMP/bin/python3"
SOURCE=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

initialize() {
  export ROTATION_FIXTURE_STORE="$TMP/$1/credentials"
  "$REAL_PYTHON" - <<'PY'
import os
from pathlib import Path
root=Path(os.environ['ROTATION_FIXTURE_STORE'])
parent=root/'projects/newemaint'
parent.mkdir(parents=True)
for p in (root,root/'projects',parent): p.chmod(0o700)
files={
'routine-merge-agent.token':'old-secret-canary\n',
'newemaint-routine-merger.account-created-by-issue-213':'issue=213\nusername=newemaint-routine-merger\n',
'newemaint-routine-merger.must-change-password-unset-by-issue-213':'issue=213\nusername=newemaint-routine-merger\npolicy=must-change-password-unset\n',
'routine-merge-agent.token-created-by-issue-213':'issue=213\nusername=newemaint-routine-merger\ntoken_kind=routine-merge-agent\n'}
for name,data in files.items():
 p=parent/name; p.write_text(data); p.chmod(0o600)
PY
}

run_operator() {
  PATH="$TMP/bin:$PATH" bash "$ROOT/codex/tools/rotate-gitea-service-account.sh" \
    --project newemaint --issue 316 --sha "$SOURCE" --token-kind routine-merge-agent \
    >"$TMP/stdout" 2>"$TMP/stderr"
}

assert_no_secret_output() {
  if rg -q 'old-secret-canary|candidate-secret-canary|1111111111111111111111111111111111111111111111111111111111111111' "$TMP/stdout" "$TMP/stderr"; then
    printf '%s\n' 'FAIL: synthetic Secret escaped public operator output' >&2
    exit 1
  fi
}

initialize success
run_operator
assert_no_secret_output
"$REAL_PYTHON" - "$ROTATION_FIXTURE_STORE" <<'PY'
from pathlib import Path
import sys
transaction=Path(sys.argv[1])/'projects/newemaint/.rotation-routine-merge-agent'
for name in ('journal.json', 'provenance.json'):
 raw=(transaction/name).read_text()
 assert '1'*64 not in raw and 'operator_capability' not in raw
PY
"$REAL_PYTHON" -c 'import json,sys; assert json.load(open(sys.argv[1]))["result"]=="rotated"' "$TMP/stdout"
run_operator
assert_no_secret_output
"$REAL_PYTHON" -c 'import json,sys; assert json.load(open(sys.argv[1]))["result"]=="no-op"; d=json.load(open(sys.argv[2])); assert (d["created"],d["deleted"])==(1,1)' "$TMP/stdout" "$ROTATION_FIXTURE_STORE/fake-gitea.json"

for scenario in revoke write; do
  initialize "$scenario"
  export ROTATION_FIXTURE_FAILURE="$scenario"
  if run_operator; then
    printf '%s\n' 'FAIL: fault unexpectedly reported success' >&2
    exit 1
  fi
  assert_no_secret_output
  [[ ! -e "$ROTATION_FIXTURE_STORE/projects/newemaint/routine-merge-agent.token" ]]
  unset ROTATION_FIXTURE_FAILURE
  run_operator
  assert_no_secret_output
  "$REAL_PYTHON" -c 'import json,sys; d=json.load(open(sys.argv[1])); assert (d["created"],d["deleted"])==(1,1)' "$ROTATION_FIXTURE_STORE/fake-gitea.json"
done
initialize scope
export ROTATION_FIXTURE_FAILURE=scope
if run_operator; then exit 1; fi
assert_no_secret_output
[[ ! -e "$ROTATION_FIXTURE_STORE/projects/newemaint/routine-merge-agent.token" ]]
"$REAL_PYTHON" -c 'import json,sys; d=json.load(open(sys.argv[1])); assert (d["created"],d["deleted"])==(1,1); assert list(d["tokens"])==["old-secret-canary"]' "$ROTATION_FIXTURE_STORE/fake-gitea.json"
unset ROTATION_FIXTURE_FAILURE
printf '%s\n' 'PASS: isolated shell rotation/no-op/revoke-failure/scope-mismatch/write-failure/Secret-output checks'
