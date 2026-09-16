#!/usr/bin/env bash
# Install tracked runtime and skills without credentials, provider enablement, or service mutation.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_HOME="${1:-$HOME}"
AGENT_DIR="${2:-$TARGET_HOME/agent}"
RUNTIME_DIR="$TARGET_HOME/.local/lib/aisoft-loop"
SHARE_DIR="$TARGET_HOME/.local/share/aisoft"

# Source provenance and staleness gate (#162, #171). Must stay before the first
# filesystem write below; `install -d` counts as a write.
# shellcheck disable=SC1091
source "$ROOT/codex/lib/install-source-guard.sh"

aisoft_install_source_guard install-vm "$ROOT" \
  'runtime modules' "$(
    aisoft_install_source_file_count \
      "$ROOT"/codex/runtime/aisoft_loop/*.py \
      "$ROOT"/codex/runtime/aisoft_host_access/*.py \
      "$ROOT"/codex/runtime/aisoft_gitea_governance/*.py \
      "$ROOT/codex/runtime/aisoft_change_name.py" \
      "$ROOT/codex/runtime/aisoft_worktree_owner.py"
  )" \
  operations "$(
    aisoft_install_source_json_count "$ROOT/codex/config/host-access-broker.json" operations
  )"

install -d -m 700 \
  "$TARGET_HOME/.codex" \
  "$TARGET_HOME/.config/aisoft/projects" \
  "$TARGET_HOME/.config/systemd/user" \
  "$TARGET_HOME/.local/lib" \
  "$TARGET_HOME/.local/share" \
  "$SHARE_DIR" \
  "$RUNTIME_DIR" \
  "$RUNTIME_DIR/aisoft_loop" \
  "$RUNTIME_DIR/aisoft_host_access" \
  "$RUNTIME_DIR/aisoft_gitea_governance" \
  "$AGENT_DIR"

bash "$ROOT/codex/install-skills.sh" "$TARGET_HOME"

for unit in "$ROOT"/codex/systemd/aisoft-agent@.*; do
  [[ -f "$unit" ]] || continue
  install -m 644 "$unit" "$TARGET_HOME/.config/systemd/user/$(basename "$unit")"
done

for source_file in "$ROOT"/codex/runtime/aisoft_loop/*.py; do
  install -m 644 "$source_file" "$RUNTIME_DIR/aisoft_loop/$(basename "$source_file")"
done
for source_file in "$ROOT"/codex/runtime/aisoft_host_access/*.py; do
  install -m 644 "$source_file" "$RUNTIME_DIR/aisoft_host_access/$(basename "$source_file")"
done
for source_file in "$ROOT"/codex/runtime/aisoft_gitea_governance/*.py; do
  install -m 644 "$source_file" "$RUNTIME_DIR/aisoft_gitea_governance/$(basename "$source_file")"
done
install -m 644 "$ROOT/codex/runtime/aisoft_change_name.py" \
  "$RUNTIME_DIR/aisoft_change_name.py"
install -m 644 "$ROOT/codex/runtime/aisoft_worktree_owner.py" \
  "$RUNTIME_DIR/aisoft_worktree_owner.py"
install -m 644 "$ROOT/codex/config/host-access-broker.json" \
  "$SHARE_DIR/host-access-broker.json"
install -m 644 "$ROOT/codex/config/gitea-governance.json" \
  "$SHARE_DIR/gitea-governance.json"
find "$RUNTIME_DIR" -type d -exec chmod 755 {} +
find "$RUNTIME_DIR" -type f -exec chmod 644 {} +

for script in "$ROOT"/codex/agent/*.sh; do
  install -m 755 "$script" "$AGENT_DIR/$(basename "$script")"
done
install -m 755 "$ROOT/codex/tools/gitea-readonly.sh" \
  "$AGENT_DIR/gitea-readonly.sh"
install -m 755 "$ROOT/codex/tools/ensure-gitea-collaborator.sh" \
  "$AGENT_DIR/ensure-gitea-collaborator.sh"
if [[ -f "$ROOT/codex/config.toml" && ! -e "$TARGET_HOME/.codex/config.toml" ]]; then
  install -m 600 "$ROOT/codex/config.toml" "$TARGET_HOME/.codex/config.toml"
fi
if [[ ! -e "$TARGET_HOME/.codex/AGENTS.md" ]]; then
  install -m 600 "$ROOT/codex/global-AGENTS.md" "$TARGET_HOME/.codex/AGENTS.md"
fi

echo "Codex skills installed in $TARGET_HOME/.agents/skills"
echo "Loop runtime installed in $RUNTIME_DIR"
echo "Agent scripts installed in $AGENT_DIR"
echo "Host access/profile contracts installed in $SHARE_DIR"
echo "Disabled project service templates installed in $TARGET_HOME/.config/systemd/user"
echo 'No project profile, credentials, timer enablement, provider enablement, merge, or deployment action was performed.'
