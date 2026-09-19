---
issue: 312
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/312
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - ci-integration
depends_on: []
status: contract-drafting
branch: change/312-governance-context-sync
created: 2026-09-19
updated: 2026-09-19
---

# Spec：NewEMaint required context 同步与 routine pilot 多 context 声明

## 目标与原因

让平台治理合同重新等于 NewEMaint 真实的、经负责人授权的 `main` 分支保护，从而解除
`host.access.audit --project newemaint` 的 `PROTECTION_MISMATCH`，并让 routine merger 的最终 head
硬门在两个 required context 上都成立。

同时解除 `routine_live_pilot` 对 required context **数量**的硬性上限。该上限是 #213 引入的，当时
每个仓只有一条 context；它现在把「给一个 routine pilot 仓增加 required CI」变成了一次全平台
broker 停摆，而不是一次声明更新。

## Acceptance criteria

- [ ] AC-1 `host-access-broker --project newemaint --operation host.access.audit` 返回非 BLOCKED，
      且 `gitea.protection.read` 读回的 `status_check_contexts` 与 manifest 中 NewEMaint 的
      `status_check_contexts` 排序后逐字相同。
- [ ] AC-2 `bash codex/tests/smoke.sh` 全绿；`codex/runtime/tests` 中覆盖 governance 合同的测试全绿，
      且新增用例分别钉住「pilot 接受多 context」与「`required_contexts` 与 `status_check_contexts`
      不一致时拒绝加载」。
- [ ] AC-3 `06-运维手册与踩坑集.md` 写明 required context 的增删顺序（先改 manifest 并安装，再改
      Gitea 分支保护），并记录本例日期 2026-09-19 与它造成的实际后果。
- [ ] AC-4 verification 文档写入 `newemaint`、`localwms`、`sfm-digital-board`、`aisoft-platform`
      四个项目改动前后的 audit 状态表；`aisoft-loop check-change-documents` PASS；
      `codex/tools/apply-classification-labels.sh --verify 312` 两个维度读回 `projected`。

## 接口、数据与兼容性影响

**manifest schema（破坏性，单文件受控）**：`routine_live_pilot` 的键集合从

```text
… , "required_context", …        # 字符串
```

改为

```text
… , "required_contexts", …       # 字符串列表
```

`_exact_keys` 是精确集合，没有可选键，因此这是一次一次性的 schema 迁移。全仓只有一个 pilot
（`contract.py` 强制 NewEMaint 唯一），并且 `required_context` 没有任何 manifest 之外的读者
（`rollback-gitea-routine-pilot.sh` 与 `bootstrap-gitea-service-account.sh` 只读 `project_id`、
`rollout_issue`、`canary_issue`），所以改名不留下第二个调用方。

**校验规则**：`len(status_check_contexts) == 1` 去掉；新增
`tuple(required_contexts) == tuple(status_check_contexts)`，有序精确相等。有序而不是集合相等，是
为了让 manifest 里两处声明可以逐字比对，与 pilot 块其它字段（全 SHA、SHA-256 digest、计数恒等 1）
的严格度一致。

**运行时兼容性**：已安装的 broker runtime 与已安装的 manifest 是一对。合并后必须两台重装
（Mac 与 gitea-ci VM）；只装一边会让那一边加载合同失败。

**不变的东西**：`non_target_repositories_sha256` 只覆盖非 NewEMaint 条目，本次不受影响；
routine merge 的第 6、7 步代码不改；分支保护本身不由本 PR 改动。

## 风险与回滚约束

- 治理合同加载失败会让**全部**项目的 broker 操作 fail closed。manifest 与 `contract.py` 必须在同一
  commit 内改完，安装后立刻对四个项目重跑 audit 作为回归。
- 合并前安装的是未合并的合同。回滚路径：从 `origin/main` 重新运行
  `codex/install-host-access-broker.sh`，installer 幂等，重装后 audit 应回到
  `PROTECTION_MISMATCH`——这正是「装回旧合同」的可观测证据。
- 本 PR 不触碰 Gitea 分支保护，也不执行任何 merge 或部署。

## 非目标

- 不改 routine merge 的硬门逻辑（核对结论：它已经要求全部 context 成功）。
- 不改 NewEMaint 的 `routine_auto_merge_enabled`、merger 身份或 canary 限制。
- 不动 `block_on_outdated_branch`（#299 已裁决）、不动 `required_context_migration`（那是
  0 → 1 条 context 的窄迁移，与本次 1 → 2 条无关）。
- 不改任何项目的 Gitea 分支保护；不为其它项目做 onboarding 或对齐。

## 未决问题

- 无。
