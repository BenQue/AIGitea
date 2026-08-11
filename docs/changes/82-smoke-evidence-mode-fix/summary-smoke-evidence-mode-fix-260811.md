---
issue: 82
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/82
change_type: bugfix
requested_complexity: small
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 移除 git 无法保持的 mode==444 断言，恢复 smoke 在全新检出上可通过的既有预期；字节不可变仍由精确 sha256 保证
risk_flags: []
required_docs:
  - summary
documents:
  summary: summary-smoke-evidence-mode-fix-260811.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/82-smoke-evidence-mode-fix
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/83
created: 2026-08-11
updated: 2026-08-11
---

## 问题/需求总结

`codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh` 的 Issue #65 evidence 预检要求
`docs/changes/65/issue-65-compose-5.1.4-*.json` 的文件 mode 精确等于 `444`。git 只保留可执行位，
任何全新 clone/worktree 检出该文件都是 `644`，因此 `bash codex/tests/smoke.sh` 在干净环境恒定
FAIL（`Issue #65 final evidence bytes or mode are invalid`）。Issue #77 验收表已记录同一现象并以
临时 `chmod 444` 复跑规避；2026-08-11 在 `main@0b6d451` 全新 worktree 复现。

## 影响范围

单文件 `codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh` 的一处断言；不改动
evidence 文件字节、不改动其余检查（regular file、非 symlink、sha256、JSON 合同校验全部保留）。

## 初步方案与建议

删除 mode==444 条件并加注释说明原因；失败消息相应改为 `bytes are invalid`。字节不可变性
由 pinned sha256 `b58bb7…eb89` 完整保证，mode 断言在 git 往返后不可满足、不提供额外保护。

## 风险

极低。唯一语义变化：不再要求本地文件系统上的只读位——该属性本来就无法通过 git 交付。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: small
assessed_complexity: small
effective_complexity: small
contract_effect: restore
reason: 移除 git 无法保持的 mode==444 断言，恢复 smoke 在全新检出上可通过的既有预期；字节不可变仍由精确 sha256 保证
risk_flags: []
required_docs:
  - summary
confidence: high
override_reason: ''
```

### 判级证据

- 只修测试脚本自身错误期望，恢复「smoke 在 fresh checkout 通过」的既有平台预期
  （AGENTS.md：修改 shell 脚本后运行 smoke——前提是它可以通过）。
- 不触碰 CI workflow、部署、治理文件；单断言可 revert。

### 缺失的 acceptance criteria 或决策

无。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| 全新 worktree `bash codex/tests/smoke.sh` | PASS | `Ran 325 tests … OK` + `Codex platform static smoke checks passed.`，exit 0（2026-08-11，`change/82` worktree） |
| evidence 字节未变 | PASS | `shasum -a 256` = `b58bb7b57d53a104f922e66c7dc1342bc1b5b133038f60fa8f2ace8d8dbdeb89` |
| `bash -n` | PASS | 无输出 |
| ShellCheck | NOT RUN | 本机未安装 shellcheck（AGENTS.md 允许「若环境可用」） |
| 远端 CI / 人工合并 | NOT RUN | 平台仓库当前无 required CI context；等待人工合并 |
