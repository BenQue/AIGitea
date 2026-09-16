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
test -x "$AGENT_DIR/project-poll.sh"
test -x "$AGENT_DIR/analyze-codex.sh"
test -x "$AGENT_DIR/analyze-claude.sh"
test -x "$AGENT_DIR/claude-provider.sh"
test -x "$AGENT_DIR/claude-analyzer.sh"
test -x "$AGENT_DIR/loop-controller.sh"
test -x "$AGENT_DIR/gitea-readonly.sh"
test -x "$AGENT_DIR/ensure-gitea-collaborator.sh"
test -f "$TARGET_HOME/.local/lib/aisoft-loop/aisoft_loop/controller.py"
test -f "$TARGET_HOME/.local/lib/aisoft-loop/aisoft_host_access/broker.py"
test -f "$TARGET_HOME/.local/lib/aisoft-loop/aisoft_gitea_governance/contract.py"
test -f "$TARGET_HOME/.local/lib/aisoft-loop/aisoft_change_name.py"
test -f "$TARGET_HOME/.local/lib/aisoft-loop/aisoft_worktree_owner.py"
test -f "$TARGET_HOME/.local/share/aisoft/host-access-broker.json"
test -f "$TARGET_HOME/.local/share/aisoft/gitea-governance.json"
test -f "$TARGET_HOME/.agents/skills/gitea-development-loop/SKILL.md"
test -L "$TARGET_HOME/.agents/skills/triage"
test -L "$TARGET_HOME/.agents/skills/implement"
test "$(readlink "$TARGET_HOME/.agents/vendor/mattpocock/current")" = 'releases/v1.2.2'
test ! -e "$TARGET_HOME/.agents/vendor/mattpocock/previous"
test -f "$TARGET_HOME/.agents/vendor/mattpocock/current/manifest.json"
test "$(jq '.skill_count' "$TARGET_HOME/.agents/vendor/mattpocock/current/manifest.json")" = 35
test -f "$TARGET_HOME/.agents/skills/triage/SKILL.md"
test -f "$TARGET_HOME/.config/systemd/user/aisoft-agent@.service"
test -f "$TARGET_HOME/.config/systemd/user/aisoft-agent@.timer"
test -d "$TARGET_HOME/.config/aisoft/projects"
if find "$TARGET_HOME/.config/aisoft/projects" -type f | grep -q .; then
  echo 'installer must not create a project profile or credential file' >&2
  exit 1
fi
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
TOKEN_FILE="$TEMP_ROOT/agent.token"
printf '%s\n' 'sentinel-runtime-token' >"$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"
cat >"$ENV_FILE" <<EOF
AISOFT_PROJECT_ID=aisoft-platform
GITEA_URL=http://gitea.test:3000
GITEA_OWNER=owner
GITEA_REPO=repo
GITEA_IDENTITY=aisoft-platform-agent
GITEA_TOKEN_FILE=$TOKEN_FILE
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

ENV_WITH_DEFAULT_REPO="$TEMP_ROOT/agent-default-repo.env"
grep -v '^AGENT_REPO_DIR=' "$ENV_FILE" >"$ENV_WITH_DEFAULT_REPO"
chmod 600 "$ENV_WITH_DEFAULT_REPO"
HOME="$TARGET_HOME" AGENT_ENV_FILE="$ENV_WITH_DEFAULT_REPO" bash -c \
  'source "$1"; load_agent_env; test "$AGENT_REPO_DIR" = "$HOME/work/$GITEA_REPO"' \
  _ "$ROOT/codex/agent/common.sh"

printf '%s\n%s\n' 'sentinel-runtime-token' 'second-token' >"$TOKEN_FILE"
if HOME="$TARGET_HOME" AGENT_ENV_FILE="$ENV_FILE" bash -c \
  'source "$1"; load_agent_env' _ "$ROOT/codex/agent/common.sh" >/dev/null 2>&1; then
  echo 'multi-line project token must be rejected' >&2
  exit 1
fi
printf '%s\n' 'sentinel-runtime-token' >"$TOKEN_FILE"

if AGENT_ENV_FILE="$ENV_FILE" ANALYSIS_PROVIDER=none IMPLEMENT_PROVIDER=gpt \
  AISOFT_LOOP_STATE_DIR="$TEMP_ROOT/state-invalid" \
  "$ROOT/codex/agent/provider-poll.sh" >/dev/null 2>&1; then
  echo 'an unsupported implementation provider must be rejected' >&2
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

for provider in claude codex; do
  MOCK_ARGV_LOG="$TEMP_ROOT/python-argv-$provider" \
  AGENT_ENV_FILE="$ENV_FILE" ANALYSIS_PROVIDER="$provider" IMPLEMENT_PROVIDER="$provider" \
  AISOFT_LOOP_STATE_DIR="$TEMP_ROOT/state-$provider" \
  PATH="$MOCK_BIN:$PATH" \
    "$ROOT/codex/agent/provider-poll.sh"
  if grep -Fq sentinel-runtime-token "$TEMP_ROOT/python-argv-$provider"; then
    echo "$provider poll leaked the agent token into child argv" >&2
    exit 1
  fi
done

WORKTREE_MOCK_BIN="$TEMP_ROOT/worktree-bin"
mkdir -p "$WORKTREE_MOCK_BIN" "$TEMP_ROOT/repo"
cat >"$WORKTREE_MOCK_BIN/git" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *' fetch -q origin main' ]]; then
  exit 0
fi
if [[ "$*" == *' ls-remote --heads origin refs/heads/change/8 refs/heads/change/8-*' ]]; then
  printf '%s\t%s\n' 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeef' 'refs/heads/change/8'
  exit 0
fi
if [[ "$*" == *' fetch -q origin change/8' ]]; then
  exit 0
fi
if [[ "$*" == *' show-ref --verify --quiet refs/heads/change/8' ]]; then
  exit 1
fi
if [[ "$*" == *' worktree add -b change/8 '* ]]; then
  printf '%s\n' "branch 'change/8' set up to track 'origin/change/8'."
  printf '%s\n' 'HEAD is now at deadbee synthetic'
  exit 0
fi
if [[ "$*" == *' branch --show-current' ]]; then
  printf '%s\n' 'change/8'
  exit 0
fi
printf 'unexpected git argv: %s\n' "$*" >&2
exit 2
EOF
chmod 755 "$WORKTREE_MOCK_BIN/git"
worktree_output="$(
  HOME="$TARGET_HOME" \
  AGENT_ENV_FILE="$ENV_FILE" \
  AISOFT_LOOP_STATE_DIR="$TEMP_ROOT/worktree-state" \
  PYTHONPATH="$ROOT/codex/runtime" \
  PATH="$WORKTREE_MOCK_BIN:$PATH" \
  bash -c 'source "$1"; load_agent_env; prepare_change_worktree 8 false' \
    _ "$ROOT/codex/agent/common.sh"
)"
test "$worktree_output" = "$TEMP_ROOT/worktree-state/worktrees/issue-8"

test "$(PYTHONPATH="$ROOT/codex/runtime" python3 -m aisoft_loop.cli \
  change-name 75 readable-change-names)" = 'change/75-readable-change-names'
if PYTHONPATH="$ROOT/codex/runtime" python3 -m aisoft_loop.cli \
  change-name 75 legacy-fix >/dev/null 2>&1; then
  echo 'reserved readable change slug must be rejected' >&2
  exit 1
fi

PROFILE_HOME="$TEMP_ROOT/profile-home"
PROFILE_AGENT="$PROFILE_HOME/agent"
PROFILE_CONFIG="$PROFILE_HOME/.config/aisoft/projects"
PROFILE_CREDENTIALS="$PROFILE_HOME/.config/aisoft/credentials"
PROFILE_BIN="$PROFILE_HOME/bin"
PROFILE_SHARE="$PROFILE_HOME/.local/share/aisoft"
mkdir -p "$PROFILE_AGENT" "$PROFILE_CONFIG" "$PROFILE_CREDENTIALS" "$PROFILE_BIN" "$PROFILE_SHARE"
cp "$ROOT/codex/config/host-access-broker.json" "$PROFILE_SHARE/host-access-broker.json"
cp "$ROOT/codex/config/gitea-governance.json" "$PROFILE_SHARE/gitea-governance.json"
cp "$ROOT/codex/agent/project-poll.sh" "$PROFILE_AGENT/project-poll.sh"
cp "$ROOT/codex/agent/common.sh" "$PROFILE_AGENT/common.sh"
cat >"$PROFILE_AGENT/provider-poll.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'env=%s\nstate=%s\nworktrees=%s\n' \
  "$AGENT_ENV_FILE" "$AISOFT_LOOP_STATE_DIR" "$LOOP_WORKTREE_ROOT"
EOF
chmod 755 "$PROFILE_AGENT/provider-poll.sh"
cat >"$PROFILE_BIN/python3" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *'profile-consume-check'* ]]; then
  exit 0
fi
exec /usr/bin/python3 "$@"
EOF
chmod 755 "$PROFILE_BIN/python3"
printf '%s\n' 'not-a-real-token' >"$PROFILE_CREDENTIALS/emaintenance.token"
chmod 600 "$PROFILE_CREDENTIALS/emaintenance.token"
cat >"$PROFILE_CONFIG/emaintenance.env" <<EOF
AISOFT_PROJECT_ID=newemaint
GITEA_URL=http://gitea-ci.orb.local:3000
GITEA_OWNER=admin
GITEA_REPO=NewEMaint
GITEA_IDENTITY=newemaint-agent
GITEA_TOKEN_FILE=$PROFILE_CREDENTIALS/emaintenance.token
AGENT_REPO_DIR=$PROFILE_HOME/work/NewEMaint
ANALYSIS_PROVIDER=none
IMPLEMENT_PROVIDER=none
EOF
chmod 600 "$PROFILE_CONFIG/emaintenance.env"
profile_output="$(HOME="$PROFILE_HOME" PATH="$PROFILE_BIN:$PATH" \
  "$PROFILE_AGENT/project-poll.sh" emaintenance)"
grep -Fxq "env=$PROFILE_CONFIG/emaintenance.env" <<<"$profile_output"
grep -Fxq "state=$PROFILE_HOME/.local/state/aisoft-loop/projects/emaintenance" <<<"$profile_output"
grep -Fxq "worktrees=$PROFILE_HOME/.local/state/aisoft-loop/projects/emaintenance/worktrees" <<<"$profile_output"
if HOME="$PROFILE_HOME" PATH="$PROFILE_BIN:$PATH" \
  "$PROFILE_AGENT/project-poll.sh" '../invalid' >/dev/null 2>&1; then
  echo 'project profile traversal must be rejected' >&2
  exit 1
fi
chmod 644 "$PROFILE_CONFIG/emaintenance.env"
if HOME="$PROFILE_HOME" PATH="$PROFILE_BIN:$PATH" \
  "$PROFILE_AGENT/project-poll.sh" emaintenance >/dev/null 2>&1; then
  echo 'group/world-readable project profile must be rejected' >&2
  exit 1
fi
chmod 600 "$PROFILE_CONFIG/emaintenance.env"

cat >"$PROFILE_BIN/python3" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"status":"BLOCKED_EXTERNAL","code":"HTTP_404"}' >&2
exit 20
EOF
chmod 755 "$PROFILE_BIN/python3"
set +e
profile_failure_output="$(HOME="$PROFILE_HOME" PATH="$PROFILE_BIN:$PATH" \
  "$PROFILE_AGENT/project-poll.sh" emaintenance 2>&1)"
profile_failure_status=$?
set -e
test "$profile_failure_status" = 20
grep -Fq 'BLOCKED_EXTERNAL' <<<"$profile_failure_output"

POLL_FAIL_BIN="$TEMP_ROOT/poll-fail-bin"
mkdir -p "$POLL_FAIL_BIN"
cat >"$POLL_FAIL_BIN/python3" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *'list-issues'* ]]; then
  printf '%s\n' 'Gitea HTTP 404' >&2
  exit 2
fi
exec /usr/bin/python3 "$@"
EOF
chmod 755 "$POLL_FAIL_BIN/python3"
set +e
poll_failure_output="$(AGENT_ENV_FILE="$ENV_FILE" ANALYSIS_PROVIDER=codex IMPLEMENT_PROVIDER=none \
  AISOFT_LOOP_STATE_DIR="$TEMP_ROOT/state-http-failure" PATH="$POLL_FAIL_BIN:$PATH" \
  "$ROOT/codex/agent/provider-poll.sh" 2>&1)"
poll_failure_status=$?
set -e
test "$poll_failure_status" = 20
grep -Fq 'Gitea HTTP 404' <<<"$poll_failure_output"
grep -Fq 'BLOCKED_EXTERNAL: failed to list needs-analysis Issues' <<<"$poll_failure_output"

echo 'Codex agent runtime mock regression passed.'
