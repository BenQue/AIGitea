---
issue: 192
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/192
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on: []
status: contract-drafting
branch: change/192-selective-deploy-lifecycle
created: 2026-08-24
updated: 2026-08-24
---

# Spec · 「跳过等待部署」必须等到一个有保证的终点

## 目标与原因

### 裁决

**「跳过并等待 `deployed`」只有在等待有保证的终点时才是正确的处置。** `deployment_lifecycle`
今天回答的是「这个仓库有没有那条链路」，而正确的问题是「**这条链路会不会覆盖到本次 merge**」。
两者在「合并即部署」的仓库上重合，在「按需部署」的仓库上分叉——分叉处就是本 Issue 的缺口。

因此把 `deployment_lifecycle` 拆成三档，并把**缺省**换成不会让 Issue 卡住的那一档：

| 取值 | 声明的事实 | `required_docs` 含 `verification` 时的终态 |
|---|---|---|
| `application-deploy` | 链路存在，且**每一次 merge 都会被它部署** | 跳过，`reason: requires-deployment` |
| `application-deploy-selective` | 链路存在，但只覆盖一部分 merge（**缺省**） | `completed`，`reason: deployment-not-guaranteed` |
| `none` | 没有链路，`deployed` 不可达 | `completed`，`reason: no-deployment-chain` |

`required_docs` 不含 `verification` 时三档一律 `completed`，与今天相同。

两个条件仍然全部取自仓库证据——一个是 summary front matter 的 `required_docs`，一个是
governance manifest 的仓库声明——工具**没有新增任何接受人工终态判断的入口**，#163 的约束不变。

### 为什么缺省必须换

#163 选 `application-deploy` 作缺省的理由写在 `codex/runtime/tests/test_deployment_lifecycle.py`
里：「反过来会让任何未声明的应用仓库在部署之前就被写成 completed——比本 Issue 修的漏写严重
得多」。这个比较在两处不成立：

1. **早写的 `completed` 会被部署链路自己覆盖掉。** `mark-deployed-issues.sh` 从 Issue 上剥掉
   整个生命周期维度再写 `deployed`（该文件构造 `ids` 的 jq 表达式），所以「先 `completed`、
   后来真部署了」这条路径的终点仍然是 `deployed`，误差只到下一次部署为止。
2. **早写的 `completed` 也不可能盖掉一次真实部署。** broker 的 `_set_issue_lifecycle` 对
   `lifecycle == "completed" and "deployed" in attached` 直接 `REQUEST_DENIED`
   （`codex/runtime/aisoft_host_access/broker.py`）。

而漏写方向没有任何组件会回头补——`03` §11 自己写着「没有任何组件处在能观察到合并的位置上」。
一个可自愈的错、一个不可自愈的错，缺省必须取可自愈的那一档。

### 为什么不选另外两条路（Issue 正文的方向 1 与方向 3）

- **方向 1「区分声明了 `verification` 且这次确实部署了」**：需要一个「本次变更部不部署」的
  机读来源，而现有仓库证据里没有。两个候选都被实测否掉，证据见映射的 verification：
  verification 文档的 `## 部署验收` 小节（`03` §3 规定不部署时整节删除）在 5 个仓库的**全部**
  历史 verification 文档里一次都没出现过，真部署的变更（LocalWMS #7）用的是自己的标题编号；
  `risk_flags` 不是封闭词表，`deployment` / `deployment_work` / `implicit-main-push-deploy`
  并存，无法作为判据。硬造一个新 front matter 键则只有终态工具一个消费者，那正是「人工传入的
  终态判断」换个写法。
- **方向 3「第二行是对的，那些变更应当声明 `verification` 并接受等待」**：LocalWMS 上已经实测
  否掉——15 个声明了 `verification` 的已合并 Issue 里 5 个至今没有任何标签，另外 10 个的
  `completed` 是绕过这条判定写上去的。等待没有终点时，人不会等，只会绕过去。

### 非选项：给生命周期加第九个「已合并待部署」标签

四维正交的 24 个标签由 canonical label manifest 定义，`sync-gitea-labels.sh`、broker 的
`_lifecycle_labels()` 与全部投影工具都从它派生。加一个状态是另一条独立的合同变更，需要自己的
验收标准，不在本 Issue 范围内。

## Acceptance criteria

- [ ] AC-1 `DEPLOYMENT_LIFECYCLES` 含三个取值，`DEFAULT_DEPLOYMENT_LIFECYCLE`
      为 `application-deploy-selective`；非法取值仍然 fail closed。
- [ ] AC-2 `mark-completed-issues.sh` 对声明了 `verification` 的 Issue：`application-deploy`
      判 `skip` / `requires-deployment`；`application-deploy-selective`（含未声明）判
      `set-completed` / `deployment-not-guaranteed`；`none` 判 `set-completed` /
      `no-deployment-chain`。
- [ ] AC-3 manifest 里出现工具不认识的 `deployment_lifecycle` 取值时，工具报错退出而不是落进
      任何一档。
- [ ] AC-4 `required_docs` 不含 `verification` 的 Issue 在三档下的判定与本次改动前逐字节相同。
- [ ] AC-5 `aisoft-platform` 仍然声明 `none`，其余仓库仍然不声明；`git diff` 对
      `codex/config/gitea-governance.json` 无改动。
- [ ] AC-6 `codex/runtime/tests/test_deployment_lifecycle.py` 与
      `codex/tests/test-mark-completed-issues.sh` 覆盖三档各自的分支与未知取值分支；
      `bash codex/tests/smoke.sh` 全绿。
- [ ] AC-7 `03` §3 那句「作者不必为了让 Issue 能收尾而少声明一份该写的验证记录」在改动后对
      **三档**都成立，并在 §11 写明它为什么成立（`application-deploy` 那一档靠该取值的定义
      「每一次 merge 都会被部署」保证等待有终点）。
- [ ] AC-8 `02` §9 与 `skill-for-claude/issue-session-flow/SKILL.md` 里描述该判定的文字与新
      规则一致，不留下「只看有没有声明 `none`」的旧表述。
- [ ] AC-9 用 LocalWMS 真实 checkout（缺省档）做改动前后对比：同一批 Issue 由
      `skip requires-deployment` 变成 `set-completed deployment-not-guaranteed`，全程只跑计划
      模式、不带 `--apply`、不写任何 Issue。

## 接口、数据与兼容性影响

- **manifest schema**：`deployment_lifecycle` 仍是可选键，取值域从 2 个扩到 3 个。现有唯一的
  声明（`aisoft-platform: none`）语义不变。
- **`application-deploy` 的语义收紧**：由「有链路」变为「有链路且合并即部署」。目前**没有任何
  仓库**声明它，因此这次收紧不改变任何仓库的现行行为；未来声明它等于承诺这条链路覆盖每一次
  merge，不确定就不要声明。
- **工具输出**：`emit` 新增一个 `reason` 取值 `deployment-not-guaranteed`，字段结构不变。
- **扁平安装**：`/usr/local/share/aisoft/gitea-governance.json` 与
  `/usr/local/libexec/aisoft/` 下的旧副本要重装才跟上（`03` §11 已有的注意事项）。本次不改
  broker typed 操作表，因此不需要重装 broker。
- **回读兼容**：旧工具读到新缺省（未声明）时行为与今天一致——未声明的仓库在旧工具里本来就走
  `!= none` 分支；差异只出现在显式声明 `application-deploy-selective` 的 manifest 上，而本次
  不做任何这样的声明。

## 风险与回滚约束

- 缺省放宽后，「已合并但部署还没跑完」的 Issue 会先拿到 `completed`。上文两条已论证该窗口
  自愈且不可能反向覆盖真实部署。
- 回滚 = revert 本 PR：manifest 数据无改动，标签写入是幂等的 set 操作，无迁移、无状态残留。
  已经被写成 `completed` 的 Issue 不会被 revert 改回去，这与 `03` §11「降级是人的决定」一致。

## 授权（AGENTS.md 治理文件条款）

本 spec 明确授权修改：`codex/runtime/aisoft_gitea_governance/contract.py`、
`codex/tools/mark-completed-issues.sh`、对应测试、`03`、`02` 与
`skill-for-claude/issue-session-flow/SKILL.md` 的相关段落。**不授权**修改 `AGENTS.md`、
controller、CI/部署脚本、broker 与 typed 操作表。

## 非目标

- 不给任何仓库补写 `deployment_lifecycle` 声明（谁是「合并即部署」需要各自的证据，另开 Issue）。
- 不回填 LocalWMS 那 5 个没有终态标签的 Issue（属该仓库自己的 Issue 与会话）。
- 不改 `03` §3 关于「何时声明 `verification`」的判据本身（#168 的结论保持不变）。
- 不给 `mark-completed-issues.sh` 增加标签读取，也不改 broker 的 `REQUEST_DENIED` 文案。
- 不新增生命周期标签。
