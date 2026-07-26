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
7. 从本机 Gitea 1.26.4 Swagger 固化 collaborator PUT、permission GET 和 branch protection GET 合同。
8. 实现 `ensure-gitea-collaborator.sh`：固定 `ci-bot` + `write`、管理身份写前/写后权限与保护快照、必要时单次 PUT、bot 身份仓库/权限真实回读、失败输出 `BLOCKED_EXTERNAL`。
9. 把 collaborator gate 纳入项目初始化/接入 runbook；在 collaborator gate 成功前，不继续标签、profile、Loop、CI 或部署接入。
10. 增加安全与幂等 synthetic tests：missing→write、read→write、write no-op、重复执行、admin/unknown fail closed、branch protection 缺失/变化、API/credential/target 失败、bot 真实访问和 secret redaction。
11. 从显式 profile/接入证据只读列出已有 AISoftPlatform 软件仓库、当前 `ci-bot` 权限、`main` 保护摘要和计划动作；未经人工确认不批量 PUT，不纳入平台控制仓库。
12. 完成 smoke、ShellCheck、六个 skill validation 和不泄密的 live integration；提交并推送到既有 `change/17` / PR #18，更新 Issue/PR 证据；不合并、不安装未合并 candidate。

## 涉及文件

- `skill-for-codex/SKILL.md`
- `skill-for-codex/references/private-gitea-access.md`
- `codex/skills/gitea-platform-ops/SKILL.md`
- `codex/tools/gitea-readonly.sh`
- `codex/tools/ensure-gitea-collaborator.sh`
- `codex/install-skills.sh`
- `codex/install-vm.sh`
- `codex/tests/test-gitea-readonly.sh`
- `codex/tests/test-ensure-gitea-collaborator.sh`
- `codex/tests/test-install-skills.sh`
- `codex/tests/smoke.sh`
- `skill-for-codex/references/onboarding-runbook.md`
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
| AC-9, AC-10 | `bash codex/tests/test-ensure-gitea-collaborator.sh`：permission 状态机和 PUT 次数断言 |
| AC-11 | 同一测试断言 branch protection 写前/写后摘要一致、缺失/变化 fail closed |
| AC-12 | mock 管理 token 与 bot token 分离；live 测试只读验证 bot repo/permission；branch protection 由管理身份回读 |
| AC-13 | `bash -x` redaction、credential mode/target/API failure cases，统一 `BLOCKED_EXTERNAL` |
| AC-14 | `rg` 检查 onboarding runbook 和 platform skill mandatory gate |
| AC-15 | 只读 inventory 输出与人工确认记录；确认前 API mutation count 必须为 0 |

## 部署与回滚

无应用部署。PR 合并前不安装 candidate。合并后的 skills-only 安装由人执行；若 fresh session 验证失败，恢复上一提交的 skills 目录或 revert PR。现有 runtime、profile、credentials、systemd unit 和 timer 均不改变。

单仓库 collaborator 变更的外部回滚是由管理员恢复写前 permission 或移除新增 collaborator，再回读 `main` protection；工具与证据不得保存 token。现有仓库的批量回补属于本计划的人工停止点，只有收到明确仓库清单确认后才执行。

## 实施与验证证据

- 本机 Gitea `1.26.4` Swagger 已核对 collaborator PUT、permission GET 和 branch-protection GET；`ci-bot write` 对 branch-protection GET 的真实响应为 `403`，因此保护由管理身份写前/写后回读，bot 只验证 repository/permission，避免为了验证而升级为 `admin`。
- `bash codex/tests/smoke.sh` 通过：103 项 Python runtime tests、全部 shell synthetic regressions 和 static checks。
- PR 差异内全部 shell scripts 已通过 `bash -n` 与 ShellCheck；六个 AISoftPlatform skills 均通过 `quick_validate.py`。
- `admin/HSDB` 真实 gate：`permission=write action=unchanged main_protection=verified bot_access=verified`，没有 collaborator PUT。
- 显式 profile inventory 仅包含 `admin/HSDB` 与 `admin/rsdesign-new`。两者 `ci-bot` 均已是 `write`，计划 collaborator action 都为 `none`。
- `admin/rsdesign-new` 的 direct/force push 与 required CI 已保护，但 `enable_merge_whitelist=false`，候选 gate 只读结果为 `main_protection=blocked onboarding_gate=blocked`。本变更未修改其分支保护；需单独人工决定是否修复。
- `admin/NewEMaint` 无显式 project profile，`admin/aisoft-platform` 是平台控制仓库，均未纳入回补。没有批量 ACL mutation，没有安装未合并全局 skill，也没有合并 PR。
