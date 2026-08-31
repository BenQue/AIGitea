---
issue: 229
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/229
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - external-contract
  - cross-module
depends_on: []
status: approved
branch: change/229-project-label-write-path
created: 2026-08-31
updated: 2026-08-31
---

# Spec：project_extensions 的 typed 写面

## 目标与原因

`gitea-labels.json` 的 `project_extensions.allowed_prefixes`（`area/`、`priority/`）自 #108 起就声明着，
但 typed surface 上没有任何一条路能**定义**或**附加**这样一个标签。结果是一个项目要用 `priority/parked`
只剩两条路：绕开 broker（治理禁令），或者不用。

本变更补齐这条写路径。**#108 的裁决不推翻**：平台仍然不枚举 `area/*` / `priority/*` 的取值，
也不规定它们的命名规范；平台只提供一条 typed、fail-closed、对未声明前缀关闭的写面。

## 四个设计问题的裁决

### D1（Q1）写面放在哪：新增两条独立 typed 操作，**不**扩 `gitea.labels.provision`

```
gitea.labels.extension.define        (label, color, description)   project-agent, mutating
gitea.issue.labels.extension.set     (number, label)               project-agent, mutating
```

操作表由 31 项增至 **33** 项。命名沿用 #108 已确立的规则（`contract.py:207-209`）：
**带 `issue.` 段的操作是「附加」，不带的是「定义」**。

**否决「扩 `gitea.labels.provision`」的理由（代价论证，非默认取舍）：**

现有 `provision` 是一条无参数的 canonical 全量收敛（`broker.py:1690-1730`）：缺失则 POST、
metadata 一致则 no-op、metadata 漂移则 PATCH、retired 只报告。把项目扩展清单塞进这条操作，
会把**两种不同的 metadata 所有权**混进同一个操作：

| | metadata 事实源 | 期望的收敛行为 |
|---|---|---|
| canonical | 平台（`gitea-labels.json`） | 持续 PATCH 对齐 |
| extension | 项目 | 既有值不得被平台静默改写（见 D4） |

即使在内部分支成「canonical 可 PATCH、extension 只 create」，一个操作也会同时表达两套 reconciliation 语义，
receipt 里的 `created/updated/unchanged` 也随之失去单一含义。

**对「操作表最小性」的正面回答**：最小性的含义是**每条操作的能力最小且不可泛化**，不是条目数最少。
`contract.py:207-209` 与 `test_host_access.py:1566` 已经把这条原则写死过一次——
#115 明确拒绝「接受任意 label set 的操作」，要求按维度提供 typed writer。
两条操作 32 vs 33 的差额，换来的是定义/附加、canonical/extension 两条边界都保持清晰。

同理，**`gitea.issue.labels.extension.set` 不得在标签缺失时顺手创建**：
`broker.py:2096` 的「attaching is not defining」边界保留，缺定义时仍返回 `TARGET_MISMATCH`，
但报错文本改为指向新的 `gitea.labels.extension.define`（现在这条指路不再是死路）。

### D2（Q2）取值从哪读：**取值不进入任何平台 manifest**，由调用方作为 typed 参数传入

manifest 只提供**允许的前缀集合**（`project_extensions.allowed_prefixes`，已存在）；
具体取值（`parked`、`web`、…）由调用方在调用时给出，broker 校验它唯一匹配一个已声明前缀。

**与 #108 裁决的关系（正面回答，不绕过）：**

Issue 提示的两个候选（`gitea-governance.json` 项目条目加字段 / `gitea-labels.json` 加 per-project 段）
**都被否决**，理由是它们真的会推翻 #108，而不只是「看起来像」：

- 把取值列进平台仓 manifest，客观上就是「平台枚举了该项目允许哪些具体值」。
  辩称「平台只登记、不定义业务语义」是绕过而非回答——#108 的裁决字面是
  「不为 `area/*` / `priority/*` 枚举取值」（`docs/changes/108-label-provisioning/spec-label-provisioning-260814.md:91,142`），
  枚举就是枚举。
- 若坚持这条路，前置动作必须是**先显式修改 #108 的裁决**（改成「平台不定义全局语义，但登记项目声明值」），
  那是一次独立的治理裁决变更，不属于本 Issue 的授权范围。

**参数化方案与 #108 是一致的，不是妥协**：平台声明 `priority/` 这个前缀合法（治理决定，
增删前缀仍走平台 PR + 重装），项目决定 `priority/parked` 这个取值（项目决定，不需要平台介入）。
这正是 #108「只声明前缀合法，不枚举取值」的字面实现。

**这条选择还消掉了一个本不该付的代价**：若取值进 manifest，项目每新增一个 `area/*` 就要走
一次平台仓 PR 并在两台主机重装 broker（installer 会把三份 manifest 一起复制到 `/usr/local/share/aisoft/`，
`install-host-access-broker.sh:58`）。这个代价对「新增/退役一个允许前缀」这种治理级变化是合理的，
对日常新增一个项目维度取值则不合理。

**写面仍然不通用**（这是 typed surface 的全部价值，逐条守住）：

- repository / owner / base URL 全部来自 manifest，调用方给不出（`broker.py:1550`）
- HTTP method 与 endpoint 写死在实现里，不接受路径参数
- `label` 必须**唯一匹配**一个已声明前缀，否则 fail closed
- 前缀下的四个 canonical 维度（`type/`、`complexity/`、`triage/`、无命名空间的 lifecycle）
  与 retired 取值一律拒绝
- 没有 delete 操作
- Issue 附加只替换匹配前缀的那**一维**

**`schema_version` 保持 2**：本方案不新增 manifest 段，只让 broker 正确消费已存在的
`allowed_prefixes`。（若将来改走 per-project 取值段，必须升到 3——`gitea-label-manifest.sh:75`、
`broker.py:2178` 都要求版本恰为 2，`test-gitea-label-manifest.sh:94` 把版本 3 判为 invalid；
在 v2 里静默加段会让旧 broker 接受整个对象再丢弃新段，正是 #108 当初拒绝的「半迁移仍给出可信答案」。）

### D3（Q3）正交性：`area/` 与 `priority/` 是**两个各自独立、各自单值**的维度

```
area/*      0..1
priority/*  0..1
```

写 `area/x` 时 `in_dimension = name.startswith("area/")`、`targets = ("area/x",)`；
写 `priority/y` 时独立地用 `priority/`。**绝不把两个前缀合并成一个 `project_extensions` 族**——
否则设置 `area/x` 会把已有的 `priority/y` 一并移除（`_replace_issue_label_dimensions` 的语义是整维替换）。

理由：

- #108 本就把 `area/` 与 `priority/` 视为两个彼此正交的项目维度
  （`docs/changes/108-label-provisioning/spec-label-provisioning-260814.md:30`）。
- 现有四维全部单值/互斥；`triage/` 实际分成 category 与 state 两个子维度，每个也恰好一个
  （`03-Issue-Spec-Plan与单闸门开发流程.md:164,188`）。扩展维度照抄这条，理由是
  「一个 Issue 属于多个功能域」是一个**产品需求**，不是本 Issue 的既定事实；
  今天把它做成单值，将来要升级为 set-valued 需要一次显式的治理 Issue，
  而不是让今天的操作偶然接受多个 target。
- `_replace_issue_label_dimensions` 允许 `targets` 是多元组（`broker.py:2091`），
  所以「单值」必须由新操作**固定传 singleton tuple** 来保证，不能依赖 helper 隐含成立。
- helper 会完整保留 `in_dimension` 之外的全部标签（`broker.py:2139`），
  所以只有「用单个匹配前缀定义 dimension」才能同时保住另一个扩展维度与 canonical 四维。

**补一个当前不存在的结构门**：已声明的扩展前缀之间必须互不包含、互不相等。
现有 validator 只检查扩展前缀与 `type/` / `complexity/` / `triage/` 的重叠
（`gitea-label-manifest.sh:120,139`），没有检查扩展前缀彼此重叠——
而 D3 的「唯一匹配」依赖这个不变量。

### D4（Q4）既有化石：**采纳，不接管**（adopt, not manage）

NewEMaint 上那 8 个平台接入之前就存在的扩展标签：

- 继续被 readback 认定为合法扩展标签并输出 `INFO`（`aisoft-project-check.sh:443,470`，行为不变）
- 可以直接被新的附加操作使用
- **`define` 遇到同名既有标签时不 PATCH**，返回 `existing-preserved` 并附上实际 metadata
- 不升级为 canonical、不删除、不要求一次性迁移

`define` 的行为表：

| 远端状态 | 行为 |
|---|---|
| 不存在，前缀已声明 | POST 创建，使用本次传入的 `label/color/description` |
| 已存在，前缀已声明 | **不 PATCH**，返回 `existing-preserved` + 实际 metadata |
| 前缀未声明（如 `team/x`） | `REQUEST_DENIED`，零 mutation |
| 名字落在 canonical 四维内 | `REQUEST_DENIED`，必须走既有 canonical writer |
| retired 取值 | `REQUEST_DENIED` |
| delete | 操作不存在 |

**明确不照抄 canonical 的 PATCH 行为**（`broker.py:1706-1716`），理由是所有权不同：
canonical 的 metadata 有平台唯一事实源，PATCH 是收敛到那个事实源；extension 的 metadata 没有平台事实源，
PATCH 等于把「某一次 define 请求随手带的 color/description」当成永久权威，
并且会静默改写 Issue 正文实测到的那 8 个化石的颜色与描述。**那不是想要的。**

「纳管」在这里的准确含义是**「可经 typed surface 合法定义与附加」**，不是「平台接管其 metadata」。

## Acceptance criteria

- [ ] **AC-1** 存在一条 typed 路径能在接入仓库中**定义**一个 `priority/<value>` 标签
      （`gitea.labels.extension.define`），并**附加**到指定 Issue（`gitea.issue.labels.extension.set`）；两步都有测试覆盖。
- [ ] **AC-2** 负向 fail-closed：未声明前缀（`team/x`）被拒；canonical 四个维度
      （`type/`、`complexity/`、`triage/`、无命名空间的 lifecycle）**不能**经这两条新路写入；retired 取值被拒；
      空 suffix、歧义匹配、非法颜色被拒。每种各有用例，且断言零 mutation。
- [ ] **AC-3** 附加操作**不动**该 Issue 上的其它任何维度：`type/*`、`complexity/*`、lifecycle、`triage/*`
      以及**另一个扩展维度**在操作前后逐一不变（与 #115 的 AC 同型，照抄该断言形状）。
- [ ] **AC-4** 单维单值：`area/old + area/new → set area/new` 收敛为只剩 `area/new`（一次 PUT）；
      `area/new → set area/new` 是 no-op（零 PUT）；`area/old + priority/high → set area/new`
      结果为 `area/new + priority/high`。
- [ ] **AC-5** `define` 对既有标签**不 PATCH**：NewEMaint 形态的化石 fixture 在 define 后
      color 与 description 逐字不变，receipt 为 `existing-preserved`。
- [ ] **AC-6** `gitea.labels.provision`、`gitea.issue.labels.set`、`gitea.issue.labels.classify`
      三者的既有行为**逐字不变**，回归全绿（包括 canonical 的 PATCH 收敛行为）。
- [ ] **AC-7** 已声明扩展前缀之间互不包含、互不相等，由 manifest validator 强制；违反的 manifest 被判 invalid。
- [ ] **AC-8** 操作表由 31 增至 33，且全部计数/集合 guard 同步：
      `test-host-access-broker.sh:16` 的 `.operation_count`、`:21` 的 `[.operations[].name] | length`、
      `contract.py` 的 `EXPECTED_OPERATIONS` 集合相等断言；installer 的动态计数与 provenance 输出一致。
- [ ] **AC-9** `bash codex/tests/smoke.sh` 全绿。
- [ ] **AC-10** `codex/runtime/tests/test_host_access.py` 全绿；
      `test_cli_exposes_only_typed_issue_and_pull_fields` 的三处 `assert_called_once_with` 同步更新后仍逐字钉死 kwargs。
- [ ] **AC-11** 四问在本 spec 中各有明确裁决，第 2 问正面回答了与 #108 裁决的关系（D2）。
- [ ] **AC-12** 判级投影在合并前用 `apply-classification-labels.sh --verify 229` 读回 `projected`。

## 接口、数据与兼容性影响

**新增对外合同**（两条 typed 操作 + 三个 typed CLI 参数 `--label` / `--color` / `--description`）。
新增是纯 additive：既有 31 条操作的 route、mutating 标志与参数集合逐字不变。

`gitea-labels.json` 的 `schema_version` **不变（2）**，不新增字段；只有 validator 增加一条
「扩展前缀彼此不重叠」的断言——这条对现有的 `area/` + `priority/` 是满足的，不构成破坏性变更。

**安装快照**：新操作对直接调用 `/usr/local/libexec/aisoft/host-access-broker` 的调用方
（VM agent、Loop、手敲绝对路径的人）需要两台重装 broker 才可用；
`codex/tools/*.sh` 经同目录 wrapper 使用仓库内 manifest，在 checkout 里当场可用。
**本变更不执行重装，也不宣称任何部署完成。**

## 风险与回滚约束

- **回滚**：纯 additive，`git revert` 单个 merge commit 即可完全撤销源码侧；
  已由新操作在远端创建的扩展标签不会被 revert 删除（typed surface 无 delete，这是既定合同），
  它们退化为「化石」，与 NewEMaint 现状同型，不影响任何既有维度。
- **最大风险是写面泛化**：任何让调用方影响 repository / URL / method / 标签维度归属的实现都必须拒绝。
  由 AC-2 与操作表断言共同守。
- **第二风险是化石被改写**：由 AC-5 守。
- **operation 计数 guard 静默失败**：`smoke.sh:204` 在 `set -e` 下直接跑
  `test-host-access-broker.sh`，后者两处 `jq -e` 把 stdout 重定向到 `/dev/null`，
  计数不匹配时表现为**零输出、exit 1**。已定位到确切行号（AC-8），实现时一次改齐。
  （**订正 Issue 正文**：硬编码字面量只有**两处**，都在 `test-host-access-broker.sh`；
  第三层是 installer 的动态计数，不含字面量；`contract.py` 的集合相等是第四层隐式 guard。）

## 非目标

- 不枚举 `area/*` / `priority/*` 的具体取值或语义（#108 裁决不推翻）
- 不改动 27 个 canonical 标签与四维正交
- 不新增通用的「任意标签写」操作
- 不新增任何 delete 操作
- 不新增 `allowed_prefixes` 的取值（`area/`、`priority/` 保持两项）
- 不碰 LocalWMS 仓；应用侧打标签是本 Issue 合并后的独立 Issue
- 不执行 broker 重装，不宣称任何部署或生产就绪

## 未决问题

无。四个设计问题均已在 D1–D4 裁决。
