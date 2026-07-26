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

## Acceptance criteria

- [ ] AC-1：`$aisoft-platform` 和 `$gitea-platform-ops` 明确触发于私有 Gitea Issue/PR/Actions/branch protection 检查与认证排障，并要求先解析精确目标仓库。
- [ ] AC-2：访问顺序固定为：显式 project profile/最小权限 API → 已配置 Git credential 的 refs 检查 → VM-local 管理员凭据的授权只读 API → 已登录浏览器只读回退；禁止匿名 API 作为 private repo 的存在性检查。
- [ ] AC-3：新增 helper 只允许 GET；校验 profile/credential mode、owner/repo、expected target 和相对 resource path；token 通过 curl stdin config 传递，不进入 argv、stdout 或 stderr。
- [ ] AC-4：project profile 缺失或 bot ACL 不足时不自动创建 profile、不授予协作者权限、不把 token 写入 Mac、remote、文档或日志。
- [ ] AC-5：项目运维文档记录 Mac/VM 两条访问路径、`404` 语义、脱敏输出要求和 helper 使用方式。
- [ ] AC-6：skills-only 安装器只复制 platform skills 到目标 `$HOME/.agents/skills/`，不复制凭据、不安装 runtime/systemd、不启用 provider/timer。
- [ ] AC-7：synthetic tests 覆盖 profile、VM credential fallback、target mismatch、unsafe resource、permissive mode、secret redaction 和 skills-only manifest；平台 smoke 与 skill validation 全部通过。
- [ ] AC-8：候选 skill 不在 PR 合并前安装到用户全局目录；合并后由人运行 skills-only installer，再以 fresh Codex session 验证 skill discovery。

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

## 风险与回滚约束

- helper fail closed：缺变量、权限过宽、目标不匹配、路径不安全或 API 非 2xx 都返回非零。
- 管理员 credential fallback 仅用于用户已授权的只读 evidence；任何 mutation 继续走专用脚本或人工浏览器确认。
- 回滚为 revert 本 PR；已存在的 profile、credential、runtime 和 timer 不受影响。
- 不删除或轮换任何现有凭据。

## 非目标

- 不给 `ci-bot` 增加 `admin/NewEMaint` 权限。
- 不创建 E-Maintenance Loop profile，不启用 provider/timer。
- 不修改任何 Issue/PR 状态，不合并 PR，不部署应用。
- 不建立 Mac 侧 token 副本或新的长期 secret。

## 未决问题

无。
