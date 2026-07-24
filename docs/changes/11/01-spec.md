---
issue: 11
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/11
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core-component
  - external-contract
depends_on: []
status: contract-ready
branch: change/11
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Spec

## 目标与原因

为并行 Issue 增加一个最小、可审计的依赖合同，使依赖在最终 PR 和 controller 终态中可见。Gitea Actions 的 pull request ref 是 head 分支而非 merge preview，因此编译可见和编译不可见的跨 Issue 依赖都不能只依赖现有 CI；平台需要在 Gate C 前提供独立信号，但不得引入锁、自动合并或新的人工审批闸门。

## Acceptance criteria

- [ ] AC-1：change 模板支持可选 `depends_on` 正整数列表；旧文档缺少该字段时按空列表处理。
- [ ] AC-2：合同加载器拒绝自依赖、重复编号、非整数、零和负数，并返回明确、脱敏的 `ContractError`。
- [ ] AC-3：最终 PR 正文对每个依赖生成可见清单；无依赖时明确显示 `None`。
- [ ] AC-4：本地验证与 PR CI 通过后，只要任一依赖 Issue 未同时满足 `state=closed` 和 `deployed` 标签，controller 就保存 `awaiting_dependencies`、返回 `CONTINUE`，且不得再次调用 provider 或创建第二个 PR。
- [ ] AC-5：依赖全部满足后，下一次 controller 运行重新确认 PR CI，并进入既有 `READY_FOR_REVIEW`；最终合并仍只能由人执行。
- [ ] AC-6：现有无依赖 small/complex、CI pending/failure、自修复和 provider parity 回归保持通过。

## 接口、数据与兼容性影响

- 新增 front matter 字段：

  ```yaml
  depends_on:
    - 50
    - 53
  ```

- `Contract` 新增不可变 `dependencies: tuple[int, ...]`。
- summary 是 controller 的依赖事实源；spec/plan 镜像同一列表供人审阅。缺失 `depends_on` 等价于 `[]`，保持旧仓库兼容。
- 依赖完成的唯一机械判据为：目标 Issue `state` 为 `closed`，且其标签集合包含 `deployed`。
- controller 不修改依赖 Issue，不创建锁，不替人合并，也不改变受保护 `main` 的 required context。

## 风险与回滚约束

- 回滚为 revert 本变更；旧 summary 因缺省为空仍可被旧/新 controller 读取。
- Gitea API 暂时不可达时属于外部阻塞，不得把依赖误判为已完成。
- `deployed` 标签漂移会保持等待，需人核对真实部署证据后按既有流程修正标签。
- PR CI 仍测试 head；依赖护栏补充而不替代 branch protection、review 或部署验证。

## 非目标

- 不实现跨 Issue 锁、自动排序、自动 rebase 或自动 merge。
- 不修改 Gitea `main` 分支保护和 required CI context。
- 不把仓库外 master plan 变成新的平台数据库。
- 普通 implementation worker 永远不得编辑本运行 governing `AGENTS.md`。

## 未决问题

无。
