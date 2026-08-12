---
issue: 96
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/96
change_type: bugfix
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 host-role 测试对 Bash errexit 继承语义的版本依赖，恢复 Mac 与 CI VM 一致的 fail-closed 验证结果
risk_flags:
  - ci-change
  - security
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-host-role-test-errexit-260812.md
  spec: spec-host-role-test-errexit-260812.md
  plan: plan-host-role-test-errexit-260812.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/96-host-role-test-errexit
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

## 问题/需求总结

平台 PR CI 首跑在 VM Bash 5.3 上失败，而 Mac Bash 3.2 通过。trace 证明 guard 对 fixture 正确
返回 20 deny；失败来自测试把“guard 非零后不得执行 mutation”交给 `set -e` 在子 shell 中隐式
中断。外层 `set +e` 在 Bash 5 会改变该继承行为，mutation marker 被写出并把最终状态覆盖为 0。

## 影响范围

- `codex/tests/test-host-role-guard.sh`：显式捕获 guard rc，仅 rc=0 才写 mutation marker。
- `codex/tests/test-install-host-role.sh`：同批消除静默断言，所有失败给出明确 `FAIL:`。
- 本 Change 的 summary/spec/plan。

## 初步方案与建议

不改 production guard。所有测试断言都通过 `fail()` 报告语义；allow/deny/invalid/identity/mode 与
mutation gate 均显式捕获 rc，不依赖不同 Bash 版本对 `errexit` 的继承规则。

## 风险

测试涉及安全闸门但不改变 guard runtime。风险是误改测试而掩盖真实 deny；通过固定 rc、decision
文本、marker 未写三重断言，并在 Bash 3.2/5.3 双端真实运行控制。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 修复 host-role 测试对 Bash errexit 继承语义的版本依赖，恢复 Mac 与 CI VM 一致的 fail-closed 验证结果
risk_flags:
  - ci-change
  - security
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 变更 CI 硬门并验证 host-role 安全边界，命中强制 complex。
- 用户已批准根因与实现方向，不存在未决决策。

### 缺失的 acceptance criteria 或决策

无。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| Mac Bash 3.2 `bash -n` + targeted tests | PASS | guard/installer success 输出各一次 |
| ShellCheck | PASS | 两个修改脚本 0 findings |
| gitea-ci Bash 5.3 targeted tests | PASS | guard/installer success 输出各一次 |
| `bash codex/tests/smoke.sh` | PASS | 325 tests OK；static smoke passed |
| production guard/schema/catalog/profile | NOT CHANGED | diff 不含相关 runtime/config/live 文件 |
| PR final-head CI | PENDING | push/PR 后读取 `CI / verify (pull_request)` |
| required-context 三件套 | NOT RUN | 明确留后续独立 Issue |
