---
issue: 108
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/108
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - cross-module
  - credential-handling
depends_on: []
status: contract-drafting
branch: change/108-label-provisioning
pr_url:
created: 2026-08-14
updated: 2026-08-14
---

# Spec：标签 provision 成为平台能力，canonical taxonomy 增加项目维度扩展点

## 目标与原因

把「新项目该有哪些标签」从**散文描述 + 人工执行**变成**声明式 manifest + 确定性幂等命令**，
并让 canonical taxonomy 能合法表达项目本地维度，使 agent 不再需要私自造标签。

现状的根因不是「项目乱建标签」，而是 **canonical taxonomy 缺少真实项目需要的维度，且
provision 不是平台能力**。NewEMaint 的 12 个非 manifest 标签覆盖 37 个 Issue 引用，其中
`area/*` 与 `priority/*` 与治理四维正交、不冲突，是合理的项目扩展；只有 3 个 `type/*` 与
1 个退役取值需要收敛。

### 与相邻 Issue 的边界（已决）

| Issue | 归属 | 与本 Issue 的关系 |
|---|---|---|
| #106 | `aisoft-project-check` 检测能力 | 已交付。本 Issue 改其 `labels-readback` 的判定依据，从「兜底 INFO」改为「按声明校验」 |
| #111 | 5 个工具的 `GITEA_TOKEN_FILE` 解析 | **已合并（PR #114）**。本 Issue 直接受益，不重复实现 token 解析 |
| #115 | `gitea.issue.labels.*`（Issue 级标签挂载）+ `completed` 终态 | **不阻塞本 Issue**。#115 面向 `/repos/{o}/{r}/issues/{index}/labels`，本 Issue 面向 `/repos/{o}/{r}/labels`，是两个不同的 Gitea API 面 |

本 Issue 新增的 `gitea.labels.read` 与 `gitea.labels.provision` 与 #115 计划新增的
`gitea.issue.labels.read` / `gitea.issue.labels.set` 命名上刻意区分：**无 `issue.` 段的是
仓库级标签定义，有 `issue.` 段的是某个 Issue 的标签挂载。**

## Acceptance criteria

- [ ] **AC-1**：`codex/config/gitea-labels.json` 采用带 `schema_version` 的对象结构，声明
      `canonical`、`project_extensions.allowed_prefixes`、`retired` 三个字段；旧的裸数组
      结构被 fail-closed 拒绝并给出明确错误，不静默兼容。
- [ ] **AC-2**：`sync-gitea-labels.sh` 对齐 manifest —— 缺失则创建，`color`/`description`
      漂移则更新，`retired` 项不创建。连续执行两次，第二次输出 `created=0 updated=0`
      且退出码 0（幂等 no-op）。
- [ ] **AC-3**：新增 broker typed 操作 `gitea.labels.read`（project-agent、只读）与
      `gitea.labels.provision`（project-agent、mutation）。二者均无删除能力；请求删除类
      操作返回 `REQUEST_DENIED`。
- [ ] **AC-4**：`aisoft-project-check.sh` 的 `labels-readback` 按声明判定：符合
      `allowed_prefixes` 的标签为 PASS；不在 canonical 且不符合任何声明前缀的报 GAP
      （覆盖拼写错误场景，如 `aera/web`）。
- [ ] **AC-5**：受管命名空间冲突（`type/*`、`complexity/*`、`triage/*` 中的非 canonical 值）
      与 `retired` 取值仍在用时，GAP 输出**附所属 Issue 编号清单**，而非仅标签名。
- [ ] **AC-6**：`onboarding-runbook.md` §5 的四条散文替换为一条确定性命令，与
      `host.access.audit` / `mac.git.bind` / `host.onboarding.check` 同级列出，并注明可重复
      执行。
- [ ] **AC-7**：退役取值有明确迁移路径且不通过静默删除实现——工具只报告 `retired` 在用
      及其 Issue 清单，删除标签本身不在任何 typed 操作内。
- [ ] **AC-8**：`bash codex/tests/smoke.sh` 全绿。

## 接口、数据与兼容性影响

### manifest 结构（破坏性变更，同批次迁移消费者）

```json
{
  "schema_version": 2,
  "canonical": [ { "name": "...", "color": "...", "description": "..." } ],
  "project_extensions": {
    "allowed_prefixes": [
      { "prefix": "area/", "description": "项目功能域，取值由项目自定" },
      { "prefix": "priority/", "description": "项目优先级，取值由项目自定" }
    ]
  },
  "retired": [
    { "name": "complexity/standard", "superseded_by": "complexity/complex",
      "retired_in": "1cbe714", "note": "..." }
  ]
}
```

约束：

- `allowed_prefixes[].prefix` 必须以 `/` 结尾，且**不得与受管命名空间前缀重叠**
  （`type/`、`complexity/`、`triage/`）。违反则 manifest 校验 fail closed。
- `retired[].name` 不得同时出现在 `canonical` 中。
- 扩展前缀只声明**前缀合法**，不枚举取值——项目自主决定 `area/web` 还是 `area/billing`。
  这是刻意的：平台管治理维度，项目管业务维度。

### 既有消费者迁移

| 消费者 | 现在 | 之后 |
|---|---|---|
| `sync-gitea-labels.sh:88` | `jq -c '.[]' "$MANIFEST"` | `jq -c '.canonical[]'` + 结构校验 |
| `aisoft-project-check.sh:269,281` | `$expected` 直取数组、`[$canonical[0][].name]` | 走 `.canonical`，并读 `.project_extensions` 与 `.retired` |

两者与 manifest 必须在同一 PR 内交付。旧结构被显式拒绝而非兼容，理由是半迁移状态下
`labels-readback` 会静默给出错误结论，比直接失败更危险。

### broker typed 操作

```
"gitea.labels.read":      ("project-agent", False, ())
"gitea.labels.provision": ("project-agent", True,  ())
```

- `gitea.labels.read` → `GET /repos/{owner}/{repo}/labels?limit=100&page=N`（分页有安全上限）。
- `gitea.labels.provision` → 读回现状后，对差异项 `POST /labels` 或 `PATCH /labels/{id}`。
  返回机器可读摘要 `{created, updated, unchanged, skipped_retired, status}`。
- **不新增任何 `DELETE` 路径**。标签删除保持不可达，这是 AC-7 的机制保证而非约定。
- 身份路由为 project-agent：已由 `host.access.audit` 确认其 token scope 含 `write:issue`，
  Gitea label 端点属该 scope。

### 向后兼容性

- 不改变任何**标签的语义**，不重命名、不删除任何在用标签。
- 不改写历史 change 文档中的 `effective_complexity: standard`——历史是审计证据。
- 各项目仓库的实际标签集合在本 Issue 内**零变更**；provision 是能力交付，执行是各项目
  自己的 Issue（如 NewEMaint #69）。

## 风险与回滚约束

| 风险 | 缓解 |
|---|---|
| manifest 结构变更打断两个消费者 | 同 PR 交付 + 新增结构校验测试 + `smoke.sh` 接入 |
| provision 因空白/大小写差异反复"修复"伪漂移 | 比较前对 `color`（小写、去 `#`）与 `description`（去首尾空白）确定性归一化，并加幂等回归测试 |
| 扩展前缀声明被滥用为绕过受管命名空间 | manifest 校验拒绝与 `type/`/`complexity/`/`triage/` 重叠的前缀 |
| 新 typed 操作扩大 broker 攻击面 | 无参数、无删除、fail closed；沿用既有分页上限与响应格式校验模式 |

回滚：单 PR revert 即可。无数据迁移、无制品、无部署，回滚后 manifest 回到裸数组、两个
消费者回到旧解析，各项目实际标签不受影响。

## 非目标

- 不执行任何项目的标签收敛动作（NewEMaint #69 等待本 Issue 交付后自行决定）。
- 不实现 Issue 级标签挂载与 `completed` 终态推进（#115）。
- 不实现标签删除能力（刻意排除）。
- 不改动判级规则、单闸门合同、CI workflow、部署链路。
- 不为 `area/*` / `priority/*` 枚举取值或规定命名规范。

## 未决问题

> 进入 `approved` 前必须清空所有会改变实现方向的未决问题。

### UQ-1（需人决策）：`type/security`、`type/reliability`、`type/data` 的归宿

`type/*` 是受管命名空间，AI 判级依赖它是**封闭集合**。两个方向互斥：

**方案 A（建议）——纳入 canonical，扩为 10 个 type。**

- 依据：`type/security` 实测 8 次，高于 canonical 的 `type/docs`(1) 与 `type/feature`(1)。
  它反映的是真实且高频的变更类型，不是噪音。
- `type/reliability`(2) 与 `type/data`(1) 同属 canonical 7 类未覆盖的语义：前者是可用性/
  韧性修复，后者是数据与 schema 变更，二者都不能干净归入现有 7 类。
- 代价：判级规则需为 3 个新 type 补充判定证据描述；11 个 Issue 的现有标签**原地合法化**，
  零迁移动作。

**方案 B——迁移到扩展维度（如 `concern/security`）。**

- 依据：保持 canonical `type/*` 稳定在 7 个。
- 代价：11 个 Issue 需逐个改引用后才能处理标签，且需先有 #115 的 Issue 级标签写入能力
  才能自动化——**这会让本 Issue 重新阻塞于 #115**。

**倾向方案 A**：它零迁移、不引入新阻塞，且符合「taxonomy 缺维度就补维度」的本 Issue 主旨。
方案 B 是在把一个已被证实有用的维度赶出受管空间。

### UQ-2（已解，记录留痕）

`area/*` 与 `priority/*` 是否成为合法扩展前缀 —— **是**。实测 37 个 Issue 引用、与治理
四维正交、无命名空间冲突。这是本 Issue `project_extensions` 声明的首批取值。
