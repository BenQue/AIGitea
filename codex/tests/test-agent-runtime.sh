#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEMP_ROOT"' EXIT

TARGET_HOME="$TEMP_ROOT/home"
AGENT_DIR="$TARGET_HOME/agent"
mkdir -p "$TARGET_HOME"

"$ROOT/codex/install-vm.sh" "$TARGET_HOME" "$AGENT_DIR" >/dev/null
first_manifest="$TEMP_ROOT/first-manifest"
find "$TARGET_HOME" -type f -print0 | sort -z | xargs -0 shasum -a 256 >"$first_manifest"
"$ROOT/codex/install-vm.sh" "$TARGET_HOME" "$AGENT_DIR" >/dev/null
second_manifest="$TEMP_ROOT/second-manifest"
find "$TARGET_HOME" -type f -print0 | sort -z | xargs -0 shasum -a 256 >"$second_manifest"
diff -u "$first_manifest" "$second_manifest"

test -x "$AGENT_DIR/provider-poll.sh"
test -x "$AGENT_DIR/analyze-codex.sh"
test -x "$AGENT_DIR/loop-controller.sh"
test -f "$TARGET_HOME/.local/lib/aisoft-loop/aisoft_loop/controller.py"
test -f "$TARGET_HOME/.agents/skills/gitea-development-loop/SKILL.md"
if mode="$(stat -f '%Lp' "$TARGET_HOME/.codex/AGENTS.md" 2>/dev/null)"; then
  :
else
  mode="$(stat -c '%a' "$TARGET_HOME/.codex/AGENTS.md")"
fi
test "$mode" = 600
test ! -e "$TARGET_HOME/.agent.env"
if find "$TARGET_HOME/.local/lib/aisoft-loop" -name '__pycache__' -o -name '*.pyc' | grep -q .; then
  echo 'installer copied Python cache artifacts' >&2
  exit 1
fi

ENV_FILE="$TEMP_ROOT/agent.env"
cat >"$ENV_FILE" <<EOF
GITEA_URL=http://gitea.test:3000
GITEA_OWNER=owner
GITEA_REPO=repo
GITEA_TOKEN=sentinel-runtime-token
AGENT_REPO_DIR=$TEMP_ROOT/repo
EOF
chmod 600 "$ENV_FILE"

xtrace_output="$TEMP_ROOT/xtrace-output"
AGENT_ENV_FILE="$ENV_FILE" bash -x -c \
  'source "$1"; load_agent_env; echo loaded' _ "$ROOT/codex/agent/common.sh" \
  >"$xtrace_output" 2>&1
grep -Fq loaded "$xtrace_output"
if grep -Fq sentinel-runtime-token "$xtrace_output"; then
  echo 'agent token leaked through xtrace' >&2
  exit 1
fi

AGENT_ENV_FILE="$ENV_FILE" ANALYSIS_PROVIDER=none IMPLEMENT_PROVIDER=none \
  AISOFT_LOOP_STATE_DIR="$TEMP_ROOT/state-none" \
  "$ROOT/codex/agent/provider-poll.sh"

if AGENT_ENV_FILE="$ENV_FILE" ANALYSIS_PROVIDER=none IMPLEMENT_PROVIDER=claude \
  AISOFT_LOOP_STATE_DIR="$TEMP_ROOT/state-claude" \
  "$ROOT/codex/agent/provider-poll.sh" >/dev/null 2>&1; then
  echo 'Claude implementation must remain disabled before parity' >&2
  exit 1
fi

MOCK_BIN="$TEMP_ROOT/bin"
mkdir -p "$MOCK_BIN"
cat >"$MOCK_BIN/python3" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" >>"$MOCK_ARGV_LOG"
exit 0
EOF
chmod 755 "$MOCK_BIN/python3"
MOCK_ARGV_LOG="$TEMP_ROOT/python-argv" \
AGENT_ENV_FILE="$ENV_FILE" ANALYSIS_PROVIDER=codex IMPLEMENT_PROVIDER=none \
AISOFT_LOOP_STATE_DIR="$TEMP_ROOT/state-codex" \
PATH="$MOCK_BIN:$PATH" \
  "$ROOT/codex/agent/provider-poll.sh"
test -f "$TEMP_ROOT/python-argv"
if grep -Fq sentinel-runtime-token "$TEMP_ROOT/python-argv"; then
  echo 'agent token appeared in child argv' >&2
  exit 1
fi

echo 'Codex agent runtime mock regression passed.'
