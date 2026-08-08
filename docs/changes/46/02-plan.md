---
issue: 46
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/46
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
  - compatibility
  - artifact
  - platform-governance
depends_on:
  - 27
status: approved
branch: change/46
pr_url: ''
created: 2026-08-08
updated: 2026-08-08
---

# Implementation plan

1. 在 exact origin/main 运行旧 jq assertion，保存 exit 1 与 matrix/runtime contract 只读证据。
2. 只修改 `codex/tests/smoke.sh`：检查两个 exact row IDs，并分别绑定 containerd supported real-E2E
   evidence 与 classic rejected null-evidence。
3. 继续运行 full smoke，定位 Issue #35 同 commit 加入但从未满足的 exact `retire-shared-bot` 静态门禁；
   在 `gitea-platform-ops` 既有逐仓库 retirement gate 中补上 purpose-built subcommand 名称。
4. 补齐本 Change summary/spec/plan/verification，不修改 Issue #27 evidence 或 compatibility matrix。
5. 运行新 jq assertion、full smoke、`bash -n`、ShellCheck、`git diff --check` 和 changed-file review。
6. push `change/46`，创建 `Closes #46` PR；核对 final head/statuses/Actions 后停在人工 merge gate。
7. 人工合并后刷新 `origin/main`，让 Issue #45 从新 main 重跑完整 smoke；本 Change 不执行部署。

## 涉及文件

- `codex/tests/smoke.sh`
- `codex/skills/gitea-platform-ops/SKILL.md`
- `docs/changes/46/{00-summary,01-spec,02-plan,03-verification}.md`
