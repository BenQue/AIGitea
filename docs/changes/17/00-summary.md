---
issue: 17
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/17
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正私有 Gitea 访问与技能发现合同，涉及凭据边界、Agent 行为和安装流程
risk_flags:
  - platform-governance
  - authentication-authorization
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
depends_on: []
status: implemented
branch: change/17
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/18
created: 2026-07-26
updated: 2026-07-26
---

## 问题/需求总结

应用仓库中的 Codex 会话当前不一定能发现 AISoftPlatform skills，并可能先匿名访问私有 Gitea API。匿名访问私有仓库返回 `404` 或 Git 的 `Repository not found`，但这只说明当前身份没有可见性，不能证明仓库、Issue 或 PR 不存在。E-Maintenance 实证还表明：`coder` 只有 `hsdb.env`、`newrsdesign.env`，其既有 `ci-bot` credential 无权读取 `admin/NewEMaint`；而 VM 内受保护的管理员凭据可完成脱敏只读查询。

本次追加要求把访问修复从“只读 fallback”推进为新项目接入合同：所有通过 AISoftPlatform skill 初始化、接入或部署的本地 Gitea 软件仓库，都必须幂等确保统一身份 `ci-bot` 是仓库协作者，权限精确为 `write`。该权限允许读取私有仓库、处理 Issue/评论/标签、推送受控变更分支和创建 PR，但不能获得 `admin`，也不能绕过受保护 `main`、required status check 或人工最终合并门禁。

## 影响范围

- 更新 `$aisoft-platform` 和 `$gitea-platform-ops` 的触发条件与私有 Gitea 访问阶梯。
- 新增只读 Gitea API helper，只允许 GET，不复制或打印凭据。
- 新增 skills-only 安装器，让应用仓库会话可以发现平台技能，同时不安装 runtime、systemd、profile 或凭据。
- 新增专用的 `ci-bot` collaborator 配置与验证工具，并纳入项目初始化/接入 runbook。
- 配置前后回读 `ci-bot` 仓库权限和 `main` 分支保护；配置后还要以 `ci-bot` 身份完成真实仓库读取与受保护分支可见性验证。
- 先只读盘点明确由 AISoftPlatform 接入的软件仓库，生成人工确认的回补清单；不扫描后直接修改全部 Gitea 仓库，也不自动纳入平台控制仓库。
- 更新运维文档与 smoke tests。

## 初步方案与建议

先从显式项目 profile 或目标仓库 remote 确认 Gitea URL、owner 和 repo。Git refs 优先复用 Mac Git credential helper；Issue/PR/Actions 等 API evidence 优先使用目标项目的 mode 600 profile。若目标私有仓库没有 project profile 或 bot 权限，只在已授权的只读检查中，通过 `gitea-ci` VM 本地管理员凭据文件调用只读 helper，并只输出必要、脱敏的 JSON。浏览器已登录会话是 API helper 不可用时的只读回退。

项目接入使用 Gitea 1.26.4 Swagger 定义的 `PUT /repos/{owner}/{repo}/collaborators/{collaborator}`，始终提交 `{"permission":"write"}`；随后用 `GET .../collaborators/ci-bot/permission` 回读精确权限。重复运行对已是 `write` 的仓库不写入，对 `admin` 或其它超出合同的状态不得静默保留或扩大；任何配置或验证失败都返回非零并报告 `BLOCKED_EXTERNAL`。工具还要在写前和写后回读 `main` branch protection，确保禁止 direct/force push、required status contexts 和人工合并约束没有变化。

## 风险

- `ci-bot write` 会扩大仓库可见性和 feature-branch 写入面，只允许作为明确项目初始化/接入合同执行，不得作为临时只读排障捷径。
- 误把 `admin`、平台控制仓库或未接入仓库纳入批量回补会扩大 blast radius。
- 只检查 collaborator API 而不回读 branch protection，可能让“不能写 main”的关键约束缺少证据。
- 把 token 放入命令参数、日志、Mac 文件或 Git remote 会泄露凭据。
- 未核对目标 profile 就 source `~/.agent.env` 可能读取错误仓库。
- 把未合并 skill candidate 安装到全局目录会绕过最终 PR 交付闸门。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正私有 Gitea 访问与技能发现合同，涉及凭据边界、Agent 行为和安装流程
risk_flags:
  - platform-governance
  - authentication-authorization
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
```

### 判级证据

- 修改 Codex skill 的访问决策、凭据使用边界和安装方式，命中 Agent/platform governance 强制 complex。
- 真实失败包含匿名 private-repo `404`、缺失 project profile 和 bot ACL，不是单一文档措辞问题。
- 需要新增安全脚本与 synthetic tests，确保 token 不进入 argv/stdout/stderr。

### 缺失的 acceptance criteria 或决策

- 候选配置逻辑、单仓库 synthetic/live 验证和只读回补盘点可以继续。
- 对现有仓库执行真实批量 collaborator 回补仍缺人工确认；实现必须先输出“明确接入仓库、当前权限、计划动作、main 保护摘要”，停在确认点。
