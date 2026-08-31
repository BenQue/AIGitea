---
issue: 229
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/229
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 变更新增 host-access broker 的 typed 操作面（项目扩展标签的定义与附加）、扩展 label manifest 的解析合同与 schema，并触及 contract.py 操作表、broker dispatch、runner、CLI 与 manifest 消费者等共享核心，属治理合同新增且跨模块，强制 complex
risk_flags:
  - platform-governance
  - shared-core
  - external-contract
  - cross-module
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-project-label-write-path-260831.md
  spec: spec-project-label-write-path-260831.md
  plan: plan-project-label-write-path-260831.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/229-project-label-write-path
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/230
created: 2026-08-31
updated: 2026-08-31
---

## 问题/需求总结

`codex/config/gitea-labels.json` 自 #108 起声明 `project_extensions.allowed_prefixes` = `area/`、`priority/`，
描述写着「取值由项目自定，平台不枚举」。但 typed surface 上**没有任何一条写路径**能定义或附加这样一个标签：

| 位置 | 行为 |
|---|---|
| `broker.py:1690` `_provision_labels` | 只遍历 `manifest["canonical"]`，扩展前缀下的标签永远不会被创建 |
| `broker.py:1734` `_lifecycle_labels()` | `gitea.issue.labels.set --lifecycle` 的取值集合 = canonical 中不含 `/` 的 8 个生命周期态 |
| `contract.py:230` / `broker.py:2062` | `gitea.issue.labels.classify` 的 targets 写死 `type/*` + `complexity/*` |
| `broker.py:2086` `_replace_issue_label_dimensions` | 目标标签未在仓库定义时 fail closed 报 `TARGET_MISMATCH`，并指向 `gitea.labels.provision`——而那条路对扩展前缀是死的 |

结论：**「平台不枚举取值」被实现成了「平台不提供写面」。这两件事不是一回事。**
取值可以继续由项目决定，同时仍然由平台提供一条 typed、fail-closed 的写路径。

本变更只交付平台能力，不碰任何接入仓的 Issue 数据。

## 影响范围

- `codex/config/gitea-labels.json`：label manifest 的解析合同（新增项目扩展取值段）
- `codex/config/host-access-broker.json`：typed 操作表（当前 31 项）
- `codex/runtime/aisoft_host_access/`：`contract.py` 的 `EXPECTED_OPERATIONS`、`broker.py` dispatch 与实现、`runner.py`、`cli.py`
- `codex/runtime/tests/test_host_access.py`、`codex/tests/test-host-access-broker.sh`、`codex/tests/smoke.sh`（operation 计数 guard）
- `gitea-labels.json` 的其它消费者（`aisoft_label_manifest_lifecycle` 一类的派生规则）
- 不改动 27 个 canonical 标签，也不改动 `type/` / `complexity/` / lifecycle / `triage/` 四维正交

## 初步方案与建议

在 typed surface 上补齐扩展前缀的两个半边——**定义**（仓库级）与**附加**（Issue 级），
两者都从 install-time manifest 派生允许取值，对未声明前缀与 canonical 四维 fail closed。
具体落点（写面位置、取值来源、正交性语义、既有化石处置）由映射的 `spec` 裁决。

## 风险

- **操作表最小性**：typed surface 的价值在于它不通用；任何形似「任意标签写」的实现都会侵蚀这个价值，
  必须由前缀白名单 + manifest 取值集合双重 fail closed 约束。
- **既有化石被改写**：`_provision_labels` 对 canonical 是「有则 PATCH 对齐」；扩展清单若照抄该行为，
  NewEMaint 上 8 个平台接入之前就存在的扩展标签的颜色与描述会被静默改写。
- **manifest schema 变更的下游**：`gitea-labels.json` 有多个消费者，schema 变更须逐一确认解析兼容。
- **安装快照**：新 typed 操作合并后需两台重装 broker 才对绝对路径调用方生效（06 踩坑 20）；
  PR 合并 ≠ 能力可用，本变更不宣称任何部署完成。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 变更新增 host-access broker 的 typed 操作面（项目扩展标签的定义与附加）、扩展 label manifest 的解析合同与 schema，并触及 contract.py 操作表、broker dispatch、runner、CLI 与 manifest 消费者等共享核心，属治理合同新增且跨模块，强制 complex
risk_flags:
  - platform-governance
  - shared-core
  - external-contract
  - cross-module
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: add`：`EXPECTED_OPERATIONS`（`contract.py:206-232`）新增条目、
  `host-access-broker.json` 操作表由 31 项增加，对外可调用面扩大，不是 restore/unchanged。
- 强制 complex 触发项（任一即足够，此处同时命中四条）：
  - **Agent/平台治理变更**——host-access broker 是治理写路径的唯一入口；
  - **外部契约**——typed 操作表是所有调用方（VM agent、Loop、`codex/tools/*.sh`）依赖的对外合同；
  - **共享核心**——`contract.py` / `broker.py` / `runner.py` 被全部项目共用；
  - **schema/解析合同变更**——`gitea-labels.json` 的结构被多个消费者解析。
- 不满足 small 的任一必要条件：范围非局部（跨 config / runtime / tests 三层），
  且合同效果是 add 而非 restore|unchanged。
- Issue 正文自身也裁定「治理合同 + broker typed surface + 共享核心 → 强制 complex」，与本判级一致。
- `verification` 未声明：本次验收证据（单元测试、manifest 契约测试、smoke）全部可由
  diff review 与 required CI `CI / verify (pull_request)` 复现，与 #108、#115 同型（两者均为
  summary/spec/plan 三件套，无 verification）。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文已给出可测验收标准与四个待裁决设计问题；四问的答案由映射的 `spec` 给出，
  不构成信息不足——不进入 `awaiting-triage`。
