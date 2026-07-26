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

# Spec

## 目标与原因

让任意已接入应用仓库中的 Codex 会话都能发现 AISoftPlatform skills，并在不索要、不复制、不打印凭据的前提下，确定性地访问和检查本地私有 Gitea。访问失败必须区分网络、身份、ACL、profile 缺失与对象不存在，禁止把匿名 `404` 当成删除或不存在证据。

新项目初始化/接入流程还必须自动、幂等确保平台统一身份 `ci-bot` 是目标软件仓库的 `write` collaborator。`write` 是精确目标而非最低下限：不得请求或保留由本工具授予的 `admin`，不得改变 `main` 分支保护，不得获得 direct/force push `main` 或自动合并能力。任何 collaborator 配置、权限回读、真实 bot 访问或 branch-protection 不变量验证失败，都必须停止并报告 `BLOCKED_EXTERNAL`。

## Acceptance criteria

- [x] AC-1：`$aisoft-platform` 和 `$gitea-platform-ops` 明确触发于私有 Gitea Issue/PR/Actions/branch protection 检查与认证排障，并要求先解析精确目标仓库。
- [x] AC-2：访问顺序固定为：显式 project profile/最小权限 API → 已配置 Git credential 的 refs 检查 → VM-local 管理员凭据的授权只读 API → 已登录浏览器只读回退；禁止匿名 API 作为 private repo 的存在性检查。
- [x] AC-3：新增 helper 只允许 GET；校验 profile/credential mode、owner/repo、expected target 和相对 resource path；token 通过 curl stdin config 传递，不进入 argv、stdout 或 stderr。
- [x] AC-4：只读排障不得自动创建 profile 或临时扩大 ACL；collaborator 变更只能由明确的项目初始化/接入流程调用，不把 token 写入 Mac、remote、文档或日志。
- [x] AC-5：项目运维文档记录 Mac/VM 两条访问路径、`404` 语义、脱敏输出要求和 helper 使用方式。
- [x] AC-6：skills-only 安装器只复制 platform skills 到目标 `$HOME/.agents/skills/`，不复制凭据、不安装 runtime/systemd、不启用 provider/timer。
- [x] AC-7：synthetic tests 覆盖 profile、VM credential fallback、target mismatch、unsafe resource、permissive mode、secret redaction 和 skills-only manifest；平台 smoke 与 skill validation 全部通过。
- [x] AC-8：候选 skill 不在 PR 合并前安装到用户全局目录；合并后由人运行 skills-only installer，再以 fresh Codex session 验证 skill discovery。
- [x] AC-9：新增 purpose-built collaborator 工具，仅接受精确目标仓库和固定 collaborator `ci-bot`，调用 Gitea 1.26.4 `PUT /repos/{owner}/{repo}/collaborators/ci-bot`，payload 固定为 `{"permission":"write"}`，不提供 `admin` 参数或通用任意用户授权入口。
- [x] AC-10：工具幂等。当前权限为 `write` 时不执行 PUT；缺失或 `read` 时最多执行一次 PUT 并回读为 `write`；重复运行不报错、不重复写、不扩大权限。若回读为 `admin` 或未知权限，停止并报告 `BLOCKED_EXTERNAL`，不得把异常状态当成功。
- [x] AC-11：配置前后由管理身份分别回读 `main` branch protection 的安全关键字段；必须保持禁止 direct push、禁止 force push、required status check/context 和人工合并约束不变。保护不存在、读取失败或关键字段变化时报告 `BLOCKED_EXTERNAL`。
- [x] AC-12：配置后以 `ci-bot` 自身 credential 回读仓库元数据和 `ci-bot` 权限；验证其可读取私有仓库且权限为 `write`，但不要求 `ci-bot` 读取仅管理身份可见的 branch-protection API，也不通过实际推送 `main` 做破坏性验证。
- [x] AC-13：缺少管理侧 credential、缺少 `ci-bot` credential、API 非 2xx、target mismatch、credential mode 过宽、权限/保护回读不一致或真实 bot 访问失败时，工具返回非零，标准错误包含稳定终态 `BLOCKED_EXTERNAL`，且不得静默跳过后续接入。
- [x] AC-14：项目初始化/接入 runbook 把 collaborator 工具设为标签、profile、Loop 或部署步骤之前的 mandatory gate；项目 profile、状态和工作树仍逐项目隔离，统一的只有 `ci-bot` 身份。
- [x] AC-15：对现有仓库只读盘点必须由显式 AISoftPlatform profile/接入清单驱动，输出 repo、当前权限、main 保护摘要和计划动作；未经本次后续人工确认不得批量 PUT，不得把所有 Gitea 仓库或 `admin/aisoft-platform` 等平台控制仓库自动纳入回补。

## 接口、数据与兼容性影响

只读 helper 接口：

```text
AGENT_ENV_FILE=/path/to/exact-profile.env gitea-readonly.sh <resource>
GITEA_URL=... GITEA_OWNER=... GITEA_REPO=... \
GITEA_CREDENTIAL_FILE=/path/to/credentials gitea-readonly.sh <resource>
```

`resource` 为 repo-relative API path；`repo` 表示仓库元数据端点。helper 输出 Gitea 原始 JSON，调用者再用 `jq` 选择必要字段。

skills-only installer：

```text
bash codex/install-skills.sh [target-home]
```

collaborator gate：

```text
GITEA_URL=... GITEA_OWNER=... GITEA_REPO=... \
GITEA_EXPECT_URL=... GITEA_EXPECT_OWNER=... GITEA_EXPECT_REPO=... \
GITEA_ADMIN_CREDENTIAL_FILE=/path/to/admin-credential \
GITEA_BOT_CREDENTIAL_FILE=/path/to/ci-bot-credential \
codex/tools/ensure-gitea-collaborator.sh
```

当前 VM 的两个 token 可来自同一个 mode 600 operator credential file；在其它环境也可使用可由同一 operator context 读取的独立文件。目标非 secret 坐标先从 exact project profile 解析，但不得跨用户复制 token。工具只允许 `GITEA_COLLABORATOR=ci-bot`（省略时也固定为 `ci-bot`）。credential 内容经 curl stdin config 传递，不能进入 argv、stdout、stderr、Git config 或提交内容。

## 风险与回滚约束

- helper fail closed：缺变量、权限过宽、目标不匹配、路径不安全或 API 非 2xx 都返回非零。
- 管理员 credential fallback 仅用于用户已授权的只读 evidence；任何 mutation 继续走专用脚本或人工浏览器确认。
- collaborator 工具 fail closed：只有显式项目初始化/接入允许 mutation；配置失败不得继续标签、profile、Loop、CI 或部署接入。
- `ci-bot write` 的回滚是由管理员把该仓库 collaborator 恢复到写前状态；工具必须输出不含 secret 的写前权限和计划动作，但本 PR 不自动执行批量回滚。
- 回滚为 revert 本 PR；已存在的 profile、credential、runtime 和 timer 不受影响。
- 不删除或轮换任何现有凭据。

## 非目标

- 不在未确认前批量给 `admin/NewEMaint` 或其它现有仓库回补权限。
- 不创建 E-Maintenance Loop profile，不启用 provider/timer。
- 不更改 `admin/aisoft-platform` 等平台控制仓库的 collaborator 权限。
- 不验证 direct push/force push `main`；使用 branch protection API 回读作为非破坏性证据。
- 不修改任何 Issue/PR 状态，不合并 PR，不部署应用。
- 不建立 Mac 侧 token 副本或新的长期 secret。

## 未决问题

- 现有接入仓库的真实回补目标清单需在只读盘点后由人确认；这不阻塞候选工具、测试和单仓库只读/无权限变更验证。
