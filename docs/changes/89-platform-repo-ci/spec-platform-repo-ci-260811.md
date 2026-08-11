---
issue: 89
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/89
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - ci-artifact-deployment
depends_on: []
status: contract-drafting
branch: change/89-platform-repo-ci
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Spec

## 目标与原因

平台仓库自身无 PR CI、`main` 保护无 required context（治理清单显式 `[]`），与第一硬规则
在自己身上矛盾。仓库已含 5 个 Python runtime 包（325 tests）与多个 shell 工具，需要与
NewEMaint/SFM 同款的 `CI / verify (pull_request)` 硬门。

## Acceptance criteria

- [ ] AC-1 `.gitea/workflows/ci.yml`：`pull_request(main)` 触发、job `verify`、steps 含
      `actions/checkout@v4`（fetch-depth 0，smoke 需要 git history）与 `bash codex/tests/smoke.sh`。
- [ ] AC-2 治理清单在本 PR **保持不变**：实现中发现 broker 把 manifest 当作 live 保护的期望
      边界（`host.access.audit` 对比二者，PROTECTION_MISMATCH 即 fail-closed，
      `test_host_access` 两用例实证）。契约含义：manifest 翻转必须与真实保护翻转同步。
      因此 required context 的落地是后续独立变更：真实 workflow 运行读回 context 字符串后，
      同一变更内更新 manifest + `test_host_access` fixtures，并执行 governance `apply`。
- [ ] AC-3 本地 `bash codex/tests/smoke.sh` 全绿。
- [ ] AC-4 runner 前置就绪：gitea-ci 具备 rg/jq/python3；本 PR 自身产生首次真实 workflow 运行。
- [ ] AC-5 分支保护不在本 PR 内翻转——合并并读回真实 context 字符串后，由人工/授权治理步骤
      以 governance `apply` 落 protection（防 context 配错锁死合并）。

## 接口/数据/兼容影响

新增 workflow 只在 PR 事件运行 smoke（只读测试 + 临时目录），不持有部署凭据、不触碰
runtime/制品。治理清单变更只影响后续 governance apply 的期望值。

## 治理授权

本 spec 明确授权：新增 `.gitea/workflows/ci.yml`。已执行的运维前置（VM 安装 ripgrep
15.1.0，回滚 `sudo apt-get remove -y ripgrep`）记录于 verification。不授权修改治理清单、
不授权翻转分支保护（二者绑定为后续同步变更）。

## 非目标

- 不为其它仓库改动清单；不修改 smoke 内容；不在本 PR 内执行 governance apply。
