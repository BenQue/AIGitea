---
issue: 101
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/101
change_type: bugfix
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 sync runtime 对 GNU/BSD stat 选项失败语义的错误依赖，恢复私有文件 mode gate 在 Mac 与 Linux 的一致性
risk_flags:
  - security
  - credential-boundary
  - sync-runtime
  - ci-change
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-sync-stat-portability-260812.md
  spec: spec-sync-stat-portability-260812.md
  plan: plan-sync-stat-portability-260812.md
confidence: high
override_reason: 用户 2026-08-12 明确要求按 complex 推进
depends_on: []
status: approved
branch: change/101-sync-stat-portability
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

## 问题/需求总结

PR #100 的真实 Gitea Actions 证明 host-role tests 已通过，随后 `sync/tests/test-inbound-sync.sh`
在 gitea-ci 失败。根因是 sync runtime 先调用 BSD `stat -f '%Lp'`：GNU `stat` 对该调用返回
rc=0 和文件系统描述，导致 GNU `stat -c '%a'` fallback 永远不执行，合法 mode `600` 被误判。

## 影响范围

- `sync/inbound-sync.sh` 的 profile/token private-mode gate。
- `sync/git-credential-token-file.sh` 的 credential file mode gate。
- `sync/tests/test-inbound-sync.sh` 与 `sync/tests/test-install.sh` 的 GNU/BSD portability fixtures。
- 本 Change 的 mapped summary/spec/plan。

## 初步方案与建议

先尝试 GNU `stat -c '%a'` 并验证输出是 octal mode；失败或输出不合规时，再尝试 BSD
`stat -f '%Lp'` 并做相同验证。两个 runtime 保持只接受 `400/600`，tests 同时覆盖合法私有 mode、
`644` fail-closed，以及 GNU `-f` 偶然成功但输出非 mode 的回归形态。

## 风险

该逻辑位于 credential/profile 安全边界且影响 CI，按强制规则为 complex。实现不得放宽 mode、打印
token、安装 runtime、启用 timer 或执行真实 GitHub/Gitea 同步。回滚为人工 revert 本 PR。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 sync runtime 对 GNU/BSD stat 选项失败语义的错误依赖，恢复私有文件 mode gate 在 Mac 与 Linux 的一致性
risk_flags:
  - security
  - credential-boundary
  - sync-runtime
  - ci-change
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: 用户 2026-08-12 明确要求按 complex 推进
```

### 判级证据

- 修改 credential/profile mode gate，命中 security、shared runtime 与 CI 强制 complex。
- 用户已明确批准 runtime 修改、双端验证、typed push 和唯一 PR，并明确禁止部署与 live sync。
- #96 的 test-only 边界已通过独立 Issue #101 完成升级，没有把 runtime 修复倒灌回 #96。

### 缺失的 acceptance criteria 或决策

无。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| mapped contract | PASS | resolver 在实现前返回 summary/spec/plan exact mapping |
| targeted Mac BSD stat | PASS | fake-GNU 回归 + `AISOFT_TEST_USE_REAL_STAT=1` 真实 BSD；inbound/install 均通过 |
| targeted VM GNU stat | PASS | Bash 5.3.9、uutils GNU-compatible stat 0.8.0；fake-GNU + 真实 GNU；inbound/install 均通过 |
| `bash -n` / ShellCheck | PASS / VM NOT AVAILABLE | Mac 4 文件 syntax + ShellCheck 0 findings；VM syntax PASS，未安装 ShellCheck |
| `bash codex/tests/smoke.sh` | PASS | Mac 与 gitea-ci VM 均通过；VM 325 tests + static smoke PASS |
| Standards / Spec review | PASS / PASS | 两轴均 0 finding；未发现 documented-standard、scope 或实现偏差 |
| PR final-head CI | PENDING | typed push/PR 后回读 |
| install/timer/real sync/deploy/labels/required-context | NOT RUN | 明确不授权 |
