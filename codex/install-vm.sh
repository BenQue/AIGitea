#!/usr/bin/env bash
# Install tracked runtime and skills without credentials, provider enablement, or service mutation.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_HOME="${1:-$HOME}"
AGENT_DIR="${2:-$TARGET_HOME/agent}"
RUNTIME_DIR="$TARGET_HOME/.local/lib/aisoft-loop"

install -d -m 700 \
  "$TARGET_HOME/.codex" \
  "$TARGET_HOME/.config/aisoft/projects" \
  "$TARGET_HOME/.config/systemd/user" \
  "$TARGET_HOME/.local/lib" \
  "$RUNTIME_DIR" \
  "$RUNTIME_DIR/aisoft_loop" \
  "$AGENT_DIR"

bash "$ROOT/codex/install-skills.sh" "$TARGET_HOME"

for unit in "$ROOT"/codex/systemd/aisoft-agent@.*; do
  [[ -f "$unit" ]] || continue
  install -m 644 "$unit" "$TARGET_HOME/.config/systemd/user/$(basename "$unit")"
done

for source_file in "$ROOT"/codex/runtime/aisoft_loop/*.py; do
  install -m 644 "$source_file" "$RUNTIME_DIR/aisoft_loop/$(basename "$source_file")"
done
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
echo "Disabled project service templates installed in $TARGET_HOME/.config/systemd/user"
echo 'No project profile, credentials, timer enablement, provider enablement, merge, or deployment action was performed.'
