---
issue: 17
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/17
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - authentication-authorization
depends_on: []
status: implemented
branch: change/17
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/18
created: 2026-07-26
updated: 2026-07-26
---

# Implementation plan

## 任务分解

1. 用 E-Maintenance 私有仓库复现匿名 API、`coder/ci-bot` ACL 和 VM-local admin read-only 三条路径，记录脱敏 evidence。
2. 更新 composite/platform-ops skills 的触发描述、目标解析、访问阶梯、`404` 语义和权限不扩张边界。
3. 实现只读 Gitea helper，复用 exact project profile 或 VM-local credential file，严格限制 GET、目标和 resource path。
4. 实现 skills-only installer，并让 VM installer 复用它，消除两套复制逻辑。
5. 更新 06 运维文档与 README 导航。
6. 增加 helper/installer synthetic tests、smoke assertions 和 skill validation。
7. 提交并推送 `change/17`，创建 `Closes #17` 的最终 PR；不合并、不安装未合并 candidate。

## 涉及文件

- `skill-for-codex/SKILL.md`
- `skill-for-codex/references/private-gitea-access.md`
- `codex/skills/gitea-platform-ops/SKILL.md`
- `codex/tools/gitea-readonly.sh`
- `codex/install-skills.sh`
- `codex/install-vm.sh`
- `codex/tests/test-gitea-readonly.sh`
- `codex/tests/test-install-skills.sh`
- `codex/tests/smoke.sh`
- `06-运维手册与踩坑集.md`
- `README.md`
- `docs/changes/17/`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1, AC-2, AC-4 | `rg` 检查两个 SKILL.md 与 private access reference |
| AC-3 | `bash codex/tests/test-gitea-readonly.sh` + ShellCheck |
| AC-5 | `rg` 检查 06 的 authenticated access ladder |
| AC-6 | `bash codex/tests/test-install-skills.sh` |
| AC-7 | `bash codex/tests/smoke.sh` + `quick_validate.py` |
| AC-8 | `git diff`/PR review；全局 skill 目录在合并前不变 |

## 部署与回滚

无应用部署。PR 合并前不安装 candidate。合并后的 skills-only 安装由人执行；若 fresh session 验证失败，恢复上一提交的 skills 目录或 revert PR。现有 runtime、profile、credentials、systemd unit 和 timer 均不改变。
