---
issue: 97
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/97
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 将 guard 的 permission/read failure 与 malformed JSON 分开分类，并固定 live probe 的授权调用身份
risk_flags:
  - security
  - operations
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-guard-error-classification-260812.md
  spec: spec-guard-error-classification-260812.md
  plan: plan-guard-error-classification-260812.md
confidence: high
override_reason: ''
depends_on:
  - 96
  - 101
status: ready-for-review
branch: change/97-guard-error-classification
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

## 问题/需求总结

#97 原先把普通 VM 用户得到的 `invalid-json` 误判成 live guard/schema 回归。只读实证证明
installed bytes 与 `main@10c9065` 一致；profile 为 `root:gitea-runner 640`；以 `gitea-runner`
执行 build=0、application start=20。真实问题是 guard 混淆不可读与 malformed JSON，且 06 §1
没有固定调用身份。

## 影响范围

- `codex/tools/verify-host-role.sh` 的输入可读性与 JSON syntax 错误分类。
- `codex/tests/test-host-role-guard.sh` 的 profile/schema/catalog 正反 fixtures。
- `06-运维手册与踩坑集.md` 的 live probe identity。
- 本 Change 的 summary/spec/plan。

本分支 stack 在 #96 test-control-flow 修复之上，避免复制旧的 Bash 版本依赖；#101 是当前远端
smoke 的独立 sync runtime blocker。两者均需先人工合并，#97 不复制其实现。

## 初步方案与建议

保持 secure path owner/mode 检查在前，再逐一检查 profile/schema/catalog 是否可读，最后分别用
`jq -e 'true'` 要求至少一个完整 JSON value。不可读使用 `<kind>-permission-denied`，malformed/empty
使用 `<kind>-invalid-json`；全部 rc=30
且不输出输入内容。06 §1 固定 `-u gitea-runner`。

## 风险

修改 fail-closed guard，强制 complex。行为只细分诊断 reason，不放宽 owner/mode/capability/identity
判定。回滚为人工 revert；本 PR 不安装 live guard、不改 profile/group/service。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 将 guard 的 permission/read failure 与 malformed JSON 分开分类，并固定 live probe 的授权调用身份
risk_flags:
  - security
  - operations
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 修改安全 guard 与运维调用合同，命中强制 complex。
- 用户已批准 #97 改题、错误分类与身份固定方向。

### 缺失的 acceptance criteria 或决策

无。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| profile/schema/catalog permission 分类 | PASS | 三类不可读 fixture 均 rc=30 + `<kind>-permission-denied` |
| profile/schema/catalog malformed 分类 | PASS | 截断、empty、whitespace fixtures 均 rc=30 + `<kind>-invalid-json`，marker 未泄漏 |
| 既有 allow/deny/identity/owner-mode | PASS | targeted guard + full smoke 保持既有断言 |
| Mac Bash 3.2 + ShellCheck | PASS | `bash -n` 与 ShellCheck 0 findings；targeted guard/installer PASS |
| VM Bash 5.3 targeted | PASS | gitea-ci VM Bash 5.3.9；mounted branch guard/installer PASS |
| `bash codex/tests/smoke.sh` | PASS | 325 tests OK；static smoke passed |
| live guard/profile/group/install/service | NOT CHANGED | 本 Change 不授权 |
| PR final-head CI | BLOCKED BY #101 | sync runtime 独立 blocker；不作 fake stat 绕过 |
| 合并/部署/标签/required-context | NOT RUN | 明确不授权 |
