---
issue: 243
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/243
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags: []
depends_on:
  - 222
status: contract-drafting
branch: change/243-issue-entry-label-sweep
created: 2026-09-05
updated: 2026-09-05
---

# Spec · 衍生 Issue 立案即带流程入口标签，调度会话定期清扫开放 Issue

## 目标与原因

立案必须落进流程入口，开放 Issue 必须有确定性的清扫节奏。今天两者都缺：broker 的
`gitea.issue.create` 不写任何标签，`issue-session-flow` 也没有任何一节告诉调度会话怎么
清扫开放 Issue。

## 治理文件修改授权

本 spec 明确授权本次变更修改下列治理文件，且仅限本 spec 描述的内容：

- `skill-for-claude/issue-session-flow/SKILL.md` 与 `codex/skills/issue-session-flow/SKILL.md`：
  新增「开放 Issue 清扫」一节。
- `skill-for-claude/aisoft-platform/SKILL.md`：会话标准动作第 1 步补上入口标签参数。
- `03-Issue-Spec-Plan与单闸门开发流程.md`：新增衍生 Issue 的正文要求与默认认领方。
- `docs/agents/issue-tracker.md` 与其逐字节副本 `templates/docs/agents/issue-tracker.md`：
  同一条约定的英文表述。
- `codex/tests/smoke.sh`：只新增钉住上述内容的守卫，不改动任何既有闸门的语义。

不授权修改 `AGENTS.md`、controller、`.gitea/workflows/ci.yml` 或任何部署脚本。治理文件必须由独立的受控步骤单独提交并
停止，不得与 runtime 改动混在同一个 commit 里；实施 runtime 之前重新读取改动后的治理文件。

## 范围 1：立案即入口

`gitea.issue.create` 新增一个必填 typed 参数 `entry_label`（CLI 上是 `--entry-label`）。
操作在创建 Issue 的同一个 POST 里把入口标签随 `labels` 写入。

裁定与理由：

- **实现位置在 broker，不在 `aisoft_loop` 包装层。** 根因是 broker 操作本身不写标签；包装层
  的修复可以被绕过，而每个会话直接调的正是 broker。
- **必填而不是带默认值的可选参数。** broker 的参数闸门是精确集合相等，合同里没有可选参数；
  引入它要改动 manifest 中全部操作的 schema。且本 Issue 的根因就是一个看不见的默认值，
  再加一个藏在 broker 里的默认值，调用点仍然看不出这条 Issue 走的是哪个入口。
- **一次 POST，不是创建后补一次 PUT。** 没有「已创建但还没有标签」的中间态。
- **取值限定为两个流程入口**：`needs-analysis`（`03` §4 的生命周期入口，触发 analyzer）与
  `triage/needs-triage`（Matt triage 入口）。这两个名字来自 `03` 的流程定义，不是某个标签
  维度的枚举，所以在 broker 里写成显式集合而不是从 manifest 推导；同时仍然要求该名字出现在
  安装期 label manifest 的 canonical 列表里，退役或未声明的名字在发出任何请求之前失败。
- **不放宽任何 identity route。** 身份路由仍是 `project-agent`，`mutating` 仍是 `true`，
  操作总数不变，不新增操作，不给 `coder` 新增写权限。写标签用的就是创建 Issue 的那把凭据。

失败语义：

| 情形 | 结果 |
|---|---|
| 缺少 `--entry-label` 或多传参数 | `ARGUMENT_MISMATCH`，在解析凭据之前 |
| 取值不是两个流程入口之一 | `ARGUMENT_MISMATCH`，在发出请求之前 |
| 取值未在安装期 label manifest 中声明 | `ARGUMENT_MISMATCH`，在发出请求之前 |
| 取值在仓库里没有定义 | `TARGET_MISMATCH`，并点名 `gitea.labels.provision` |

## 范围 2：调度会话清扫

`issue-session-flow` 增加「开放 Issue 清扫」一节，两份 skill 各按自己的语言写，内容合同一致：

- **触发**：一批 Issue 派单完成时，以及调度会话每次被唤醒时。
- **枚举**：`gitea.issue.list` 落地前（#222），用逐号 `gitea.issue.read` 从已知最大编号向下读，
  并在文档里注明这是临时手段。
- **逐条判定表**，固定列：编号、标题、归属仓、重复于、判定、下一步。
- **需裁决项汇总**，固定格式：一行一条，写清可选项与不裁决的后果。
- 清扫只判定与派单，不实现任何 Issue。

本节不得出现任何具体项目名或交付形态实现名（smoke 的治理守卫）。

## 范围 3：衍生 Issue 的正文要求与默认认领方

`03` 与 `docs/agents/issue-tracker.md` 写明：衍生 Issue 的作者会话必须在正文写清来源会话、
目标项目、可测验收标准与已知依赖；调度会话是衍生 Issue 的默认认领方。

## Acceptance criteria

- [ ] AC-1 经 broker `gitea.issue.create` 新建的 Issue，`gitea.issue.labels.read` 读回含入口标签。
- [ ] AC-2 `host.access.audit` 显示执行该写入的身份仍是 project agent，scope 与 manifest 一致，
      未出现任何新的 identity route。
- [ ] AC-3 缺参数、非入口取值、未声明取值分别以 `ARGUMENT_MISMATCH` 在请求之前失败；
      仓库未定义该标签时以 `TARGET_MISMATCH` 失败并点名定义操作。
- [ ] AC-4 `06` 踩坑 20 的同步点全部更新，`operation_count` 仍为 33，
      `gitea.issue.create` 的 `arguments` 在 manifest 与合同两侧一致为三项。
- [ ] AC-5 两份 `issue-session-flow` 都有「开放 Issue 清扫」节，含逐条判定表与需裁决汇总格式，
      并注明枚举依赖 #222、当前用逐号读取。
- [ ] AC-6 `03` 与 `docs/agents/issue-tracker.md` 写明衍生 Issue 的正文要求与默认认领方。
- [ ] AC-7 `bash codex/tests/smoke.sh` 全绿。

## 接口、数据与兼容性影响

- 外部契约变化：`gitea.issue.create` 的参数从两项变三项。这是**破坏性**的调用方变化——旧调用
  在新 broker 上以 `ARGUMENT_MISMATCH` 失败，新调用在旧 broker 上以同样的方式失败。两种失败
  都是 fail closed，不会静默创建无标签 Issue。
- 生效需要在 Mac 与 gitea-ci VM 两台重装 broker；只装一台会出现假的权限问题形态。
- 无数据迁移，无 schema 变更，无部署影响。

## 风险与回滚约束

- 回滚方式：revert 本次 PR 的 merge commit，并在两台重装 broker。参数合同回到两项，历史 Issue
  上已写入的入口标签保留，不需要数据回滚。
- 已存在的开放 Issue 不在本次自动补标签范围内；补写用既有 `gitea.issue.labels.set`，由清扫按
  逐条判定执行。

## 非目标

- 不新增枚举开放 Issue 的 typed 操作，也不新增关闭 Issue 的操作，两者都属于 #222。
- 不新增写 `triage/` 维度的 typed 操作；入口标签是创建时的一次性写入，不是 triage 状态机。
- 不批量给既有的开放 Issue 补标签，也不关闭已发现的重复项。
- 不引入定时任务或自动化认领；清扫由调度会话执行。

## 未决问题

无。
