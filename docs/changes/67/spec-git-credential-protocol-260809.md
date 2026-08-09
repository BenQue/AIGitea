---
issue: 67
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/67
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authentication
  - security
  - external-contract
  - shared-core
  - platform-governance
depends_on:
  - 61
status: approved
branch: change/67
pr_url:
created: 2026-08-09
updated: 2026-08-09
---

# Git credential protocol compatibility spec

## 目标与原因

让 fixed `git-credential-aisoft-host` 正确消费当前 Git credential helper `get` 请求中的合法有序多值
attributes，同时保持 Issue #61 建立的 exact identity、host、path 与 cross-project fail-closed 边界。

本 Change 只修复 protocol parser 和对应验证；不修改 credential store、identity route、operation
catalog、Gitea 权限或部署状态。

## Acceptance criteria

- [x] **AC-1** parser 把 `protocol`、`host`、`path`、`username` 作为唯一 scalar 处理；前三项必须存在，
  每个 scalar 最多出现一次，unknown scalar、重复 scalar、空 key、无 `=` 行或 NUL 输入均返回
  `CREDENTIAL_PROTOCOL_INVALID`。
- [x] **AC-2** parser 对 syntactically valid `key[]` 建立有序多值列表，允许同一 key 重复并保持 values
  的输入顺序；不影响 basic username/password route 的 `capability[]`、`wwwauth[]` 和 unknown
  multi-valued attributes 在解析后被忽略，不进入输出、identity 或 target 决策。
- [x] **AC-3** `protocol` 与 manifest scheme、`host` 与 exact netloc、`path` 与 exact
  `owner/repository.git`、`username` 与 exact project-agent 的校验不变；wrong host/protocol/path/
  username 与 cross-project target 均在 credential resolve/output 前 fail closed。
- [x] **AC-4** `get` success 仍只在 private helper pipe 返回 exact `username` 与 `password`；`store`/
  `erase` 保持空输出。真实 token 不进入 argv、terminal stdout/stderr、日志、Git config、Issue/PR、
  repository 或测试 fixture。
- [x] **AC-5** unit tests 覆盖 ordered multi-values、unknown arrays、重复/unknown scalar、malformed/NUL、
  host/protocol/path/identity/cross-project negatives；CLI credential-helper regression 使用与 live probe
  相同的 key 顺序和重复形状，并通过 synthetic credential 验证 success path。
- [x] **AC-6** shell helper negative tests 证明 malformed/unknown scalar 在 Keychain 读取前脱敏非零退出；
  live protocol probe 只记录字段名，精确为两个 `capability[]`、`protocol`、`host`、`path`、`username`、
  `wwwauth[]`，不记录字段值。
- [x] **AC-7** focused unit、credential-helper shell、`bash -n`、ShellCheck（若可用）、strict JSON、
  Secret scan、`git diff --check` 和完整 `bash codex/tests/smoke.sh` 全部通过；本地 PASS 与 remote CI
  分开记录。
- [ ] **AC-8** 只创建唯一 `change/67` 与唯一 `Closes #67` PR。final required CI 按 live protection
  判定；最终 merge 仅由人工执行，不修改 protection/ACL/merge 权限。
- [ ] **AC-9** 人工 merge 后只能从 exact merged protected-main bytes 重装 broker/helper，验证第二次
  install 为 no-op，再以 `aisoft-platform-agent` 完成真实 feature branch push 和 read-back；合并前这些
  live mutation 均保持 `NOT RUN`。

## 接口、数据与兼容性影响

`credential_from_protocol()` 的外部返回格式不变。内部 parser 从单一 scalar dictionary 改为两个集合：

- `scalars: key -> value`：只允许 `protocol`、`host`、`path`、`username`，严格唯一。
- `multivalued: key[] -> ordered values`：保留合法重复与输入顺序，但 v1 basic route 不消费其 values。

本 Change 不宣告支持 `authtype`/`credential` route，也不把任何 multi-valued attribute 提升为授权输入。

## 风险与回滚约束

- unknown scalar 继续 fail closed；不能以 Git “ignore unknown attributes” 为由放宽 scalar allowlist。
- multi-valued key 必须非空并精确以 `[]` 结尾；malformed key/line 不能在解析时被静默丢弃。
- 候选回滚为 revert。post-merge installer 沿用 Issue #61 的 previous runtime/helper 回切；live canary
  失败时停止，不创建额外账号/PAT、不扩 ACL、不修改 protected `main`。
- 若 bootstrap push 仍被旧 installed helper 阻塞，只允许单进程 compatibility adapter：字段值与 Secret
  不落盘、不输出、不进入 argv；verification 必须明确它是 bootstrap 路径，不是最终修复证据。

## 非目标

- 不新增或修改 Gitea account/PAT/ACL/visibility/protection/merge permission，不访问 `ci-bot` credential。
- 不修改 Issue #66、NewEmaint 或其它项目 worktree/branch/Issue/PR。
- 不操作 Docker、OrbStack lifecycle、VM/service/timer/profile、数据库、deployment、migration、restart、
  prune 或 production。
- 不自动 merge，不在人工 merge 前安装 candidate 或运行真实 write canary。

## 未决问题

无。
