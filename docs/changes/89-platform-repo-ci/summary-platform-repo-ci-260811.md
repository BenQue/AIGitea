---
issue: 89
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/89
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为平台仓库启用 PR CI（smoke），修复「自身无 CI 硬门」的 P0；required-context 落地按 broker 契约拆为真实运行读回后的同步变更
risk_flags:
  - ci-artifact-deployment
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-platform-repo-ci-260811.md
  spec: spec-platform-repo-ci-260811.md
  plan: plan-platform-repo-ci-260811.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/89-platform-repo-ci
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/90
created: 2026-08-11
updated: 2026-08-11
---

## 问题/需求总结

平台仓库无 `.gitea/workflows/`，`main` 无 required context（清单 `[]`、
`enable_status_check=false`）——第一硬规则在自己身上失效（审核 P0）。仓库已含 5 个
Python runtime 包（325 tests）与多个 shell 工具。

## 影响范围

新增 `.gitea/workflows/ci.yml`（`pull_request(main)` → job `verify` → `bash codex/tests/smoke.sh`，
context 与 NewEMaint/SFM 同款 `CI / verify (pull_request)`）。治理清单与分支保护**本 PR 不动**。

## 初步方案与建议

实现中发现并实证了一条重要契约：broker 的 `host.access.audit` 把治理清单当作 live 保护的
期望边界——清单先于真实保护翻转即 `PROTECTION_MISMATCH` fail-closed
（`test_host_access` 两用例复现）。因此落地顺序固定为：
1. 本 PR 合并 → 首次真实 workflow 运行（本 PR 的 PR run 即首跑）；
2. 从 commit status 读回准确 context 字符串；
3. 后续同步变更：manifest + `test_host_access` fixtures 同改，并执行 governance `apply`
   翻转保护——三者一体，不拆开。

## 风险

- runner 前置：gitea-ci 已装 ripgrep 15.1.0（回滚 `sudo apt-get remove -y ripgrep`）；
  jq/python3.14/git 原已具备。
- 首跑若红即为真实信号，在保护未翻转前不阻塞任何合并。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 为平台仓库启用 PR CI（smoke），修复「自身无 CI 硬门」的 P0；required-context 落地按 broker 契约拆为真实运行读回后的同步变更
risk_flags:
  - ci-artifact-deployment
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 修改 CI 属强制 complex。

### 缺失的 acceptance criteria 或决策

- 后续同步变更（manifest+fixtures+apply）需要在首跑 context 读回后另立 Issue。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| AC-1 workflow 结构 | PASS | `pull_request(main)`、job `verify`、checkout fetch-depth 0、运行 smoke |
| AC-2 清单不动的契约依据 | PASS | 清单先改时 `test_host_access` 两用例 PROTECTION_MISMATCH 复现后还原 |
| AC-3 本地 smoke | PASS（叠加 #82 修复验证） | #77 先例：临时叠加 PR #83 单行修复后全套通过，随后还原 |
| AC-4 runner 前置 | PASS | VM `rg 15.1.0` 安装读回；python3=3.14.4、jq/git 在位 |
| AC-4 首次真实 workflow | FAIL | PR #90 final head `7ee2626d86457777e679f26cd9144ee7886a8d4a`，`CI / verify (pull_request)` run/job #404，5 秒失败；不是本地 smoke PASS |
| AC-5 保护不翻转 | PASS | 本分支 diff 仅 workflow + change docs |
| required context | NOT CONFIGURED | manifest、`test_host_access` fixtures 与 governance apply 三件套继续等待后续独立 Change |
