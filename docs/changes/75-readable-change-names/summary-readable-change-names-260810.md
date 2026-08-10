---
issue: 75
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/75
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 将纯编号 Change 名称升级为 Issue 编号与稳定可读 slug 组合，并在 controller、broker、文档与 PR 合同中提供 fail-closed 一致性和 legacy 维护兼容
risk_flags:
  - authorization
  - external-contract
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-readable-change-names-260810.md
  spec: spec-readable-change-names-260810.md
  plan: plan-readable-change-names-260810.md
  verification: verification-readable-change-names-260810.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/75-readable-change-names
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/76
created: 2026-08-10
updated: 2026-08-10
---

## 问题/需求总结

当前平台把 Issue #N、`change/N`、`docs/changes/N/` 和 controller worktree 绑定为纯编号。
编号仍然适合作为审计主键，但 branch、worktree 和文档目录列表缺少主题信息，历史 Change 增多后难以
直接识别、复查和安全清理。

Issue #75 要求新 Change 使用一个不可漂移的可读名称：
`change/N-short-description`、`docs/changes/N-short-description/` 与
`issue-N-short-description` worktree label/path 共用完全相同的 `N-short-description`。PR 继续以唯一、
精确的 `Closes #N` 绑定 Issue，编号仍是唯一主键。

## 影响范围

- shared ChangeName parser、analyzer/writer、semantic document resolver/loader、controller/worktree/state。
- `host-access-broker/v1` 的 `git.fetch.change`、`git.push.change` 与 PR create/update/read validation。
- agent shell entrypoints、provider request、cleanup/deployment fallback parser、skills、templates 与 smoke tests。
- `AGENTS.md`、`codex/global-AGENTS.md`、README、Issue/Loop/运维分册及 onboarding guidance。
- existing `change/N`、`docs/changes/N/` 和历史 PR 的只读/维护兼容；不批量重命名或删除历史对象。

## 初步方案与建议

新增单一 `ChangeName` 值对象和 parser，集中产生 branch、semantic directory 与 worktree label。新 writer
必须使用 2–4 个 lowercase ASCII kebab-case words、总长不超过 32 的 slug；目录、front matter、文档
basename slug、branch、worktree 与 PR head 任一不一致即 fail closed。

legacy 兼容不能由调用方通过 `--legacy` 开关伪造。runtime 只把已经存在的 exact remote `change/N` 或已在
Git history 中存在的 `docs/changes/N/` 当作 legacy maintenance evidence；新创建路径默认拒绝纯编号。
同一 Issue 若发现多个 readable branch、多个 semantic directory、legacy/readable 并存或多个 open PR，
必须停止并请求人工处理。

Issue #75 自身是 bootstrap Change：当前 installed broker 只接受 `change/N`。候选实现通过全部 local
security/compatibility tests 后，只允许从本 worktree 运行 source candidate broker，把 exact
`change/75-readable-change-names` 非强制同名推送到 manifest-fixed AISoftPlatform remote。人工合并后才从
exact protected-main bytes 安装，并要求 second run no-op/readback；不以普通 `git push` 绕过 broker。

## 风险

- 多套正则会造成 branch/docs/worktree/PR 规则漂移；必须由一个共享 parser/formatter 提供唯一语义。
- 宽松 legacy flag 会让新 Change 继续创建纯编号名称；legacy 必须来自 remote/history evidence。
- prefix/substring 校验可能把 Issue #75 与 #750、或一个 slug 与其前缀混淆；所有检查必须 full-match。
- 同一 Issue 的多个 active slug 会破坏唯一 PR 和 cleanup；push/PR 前必须查重并 fail closed。
- 候选 broker 自举若扩大到任意 remote/refspec 会绕过治理；bootstrap 仍必须固定 project、operation、branch、
  remote、non-force/non-delete 和 human-only merge。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 将纯编号 Change 名称升级为 Issue 编号与稳定可读 slug 组合，并在 controller、broker、文档与 PR 合同中提供 fail-closed 一致性和 legacy 维护兼容
risk_flags:
  - authorization
  - external-contract
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 修改 shared controller、Git push allowlist、PR 外部合同、Agent 行为和平台治理规则，命中强制 complex。
- 需要新旧命名并存窗口、bootstrap delivery、跨模块一致性与下游安装顺序，不能作为局部文档修正处理。
- Issue 已给出可测 acceptance criteria 和明确禁止范围，剩余命名细节在 mapped spec 中收敛。

### 缺失的 acceptance criteria 或决策

无。slug 语法、保留字、不可变策略、legacy 判定、重复检测、自举、安装与人工合并边界均在 spec 中明确。
