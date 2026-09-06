---
issue: 178
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/178
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写 governance manifest 中 emaintenance 的 analysis_provider 声明，决定 NewEMaint 上是否存在一个有写权限的自动判级 writer，属 Agent 与平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-emaintenance-analysis-provider-260906.md
  spec: spec-emaintenance-analysis-provider-260906.md
  plan: plan-emaintenance-analysis-provider-260906.md
  verification: verification-emaintenance-analysis-provider-260906.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/178-emaintenance-analysis-provider
pr_url:
created: 2026-09-06
updated: 2026-09-06
---

## 问题/需求总结

`codex/config/host-access-broker.json` 里 `emaintenance` 的
`vm_profile.analysis_provider` 声明 `claude`，但 `gitea-ci` VM 上没有可用的
Claude 运行时：二进制在 `~/.npm-global/bin` 且不在 `coder` 的 PATH 上，那个
文件本身是指向 `claude.exe` 的软链，也未认证。`claude-analyzer.sh:13` 的
`command -v claude || exit 2` 在第一行就硬失败。

这个取值不是从证据来的。#152 按「同类项目惯例」给四条 internal-application
profile 一律选了 `claude`，而那四条声明当时没有一条被验证过。LocalWMS #66 的
canary 第一次把这条链真的接上，才发现它接不通；#164 据此把 `localwms` 改成
`codex`，并把余下三条留给本 Issue。

**本 Issue 的范围只剩一条。** `rsdesign` 与 `sfm` 已随 #252 退出平台并从
manifest 删除（2026-09-05 评论把范围收窄到 `emaintenance` 一行）。当前 manifest
只有三条 vm_profile：`aisoft-platform` 与 `localwms` 都是 `codex` +
`timer_unit: null`，`emaintenance` 是 `claude` + timer active。

`emaintenance` 是这条死声明**同时还是承重的**那一条：
`aisoft-agent@emaintenance.timer` 每 15 分钟真在跑，每一跳都走到
`analyze-claude.sh` 然后 fail-closed 空转。

## 影响范围

**产品代码零改动。** `analysis_provider` 的取值集合在 `contract.py:514` 是封闭的
`{claude, codex, none}`，`none` 本来就合法；schema、CLI、profile 生成逻辑一律不动。

| 文件 | 改动 |
|---|---|
| `codex/config/host-access-broker.json` | `newemaint.vm_profile.analysis_provider`：`claude` → `none`（1 行） |
| `codex/runtime/tests/test_host_access.py` | 新增 `test_emaintenance_profile_names_no_analysis_provider`（把取值与 `profile-spec` 输出逐字钉住，注释写明依据）；更新 `test_undeclared_profile_bytes_are_byte_identical_to_pre_112_shape` 的一处字面量并说明它为何跟着 manifest 走 |

**不改**：`implement_provider`（仍 `none`）、`timer_unit`（仍
`aisoft-agent@emaintenance.timer`）、`contract.py:520` 的 timer 白名单、
`codex/config/gitea-governance.json`、其余四个项目条目、任何 agent 脚本或 runtime。

## 初步方案与建议

### 这一个字段决定的是什么

不是「用哪个模型」，而是「NewEMaint 仓上是否存在一个有写权限的自动 writer」。
链路是：timer → `project-poll.sh` → `provider-poll.sh:33` 把
`needs-analysis` 的**全部** Issue 取出来逐条跑 →
`analyze-<provider>.sh` 对每条做五件事：只读 analyzer 判级、建 change worktree、
写 `docs/changes/N-slug/summary-*.md`、`git commit`、`git push -u origin
change/N-slug`，最后 `apply-analysis` 写 `type/*`、`complexity/*` 与一条审计评论。

那条 push 不经 broker，是脚本自己发的。#243 之后经 broker 新建的 Issue
必带入口标签（`entry_label` 已是必填，取值只能是 `needs-analysis` 或
`triage/needs-triage`），而 timer 正是按前者领活。

### 三个方向与裁定

| 方向 | 取值 | 结果 |
|---|---|---|
| A | `codex` + timer 保持 active | 立即上线自动判级 |
| B | `codex` + `timer_unit: null` | 与 localwms 同形态，配置正确但不自动触发 |
| **C（采纳）** | `none` + timer 不动 | 消除假声明，不启用任何 provider |

**裁定 C。** 两条理由，第二条是决定性的。

**一、B 表达不了它想表达的东西，还会造出一个 fail-open。**
`timer_unit` 是一条记录，不是一个开关：`profiles.py:289` 渲染的 profile 只有
九个键，`timer_unit` 一个都不在里面；全仓没有任何代码对
`aisoft-agent@*.timer` 调 `systemctl`（broker 里仅有的 `systemctl` 调用是
`broker.py:3949` 对 act_runner 的只读 `show`）。把它改成 `null` 不会停掉那个
timer，只会让 manifest 开始说一件假话。真要停必须在 VM 上 sudo，而且**必须早于
重装**——这正是踩坑 24 记的单向门。于是 B 的失败模式是：人执行了重装与 `apply`、
却没有先停 timer，结果 `ANALYSIS_PROVIDER=codex` 落地而 timer 照常触发，
**A 的运行时效果在 B 的标签下交付，且没有 canary**。这个 fail-open 是本变更
制造的，不是它消除的。

**二、把值设成 `codex` 就是在断言一条可用链路，而 NewEMaint 没有这份证据。**
Issue 自己的 AC 写着「改值前有一次该仓库自己的只读 canary 产出物作证」。
`localwms` 之所以是 `codex`，是因为它先跑了 LocalWMS #66 的 canary，#164 才
改的值——房子的规矩不是「声明 codex」，是「证明了才声明」。而且这条断言会比
今天的 timer 状态活得更久：即使按 B 把 timer 关掉，日后任何一次重开都会跑一条
从未验证过的链。所以 canary 是命名 `codex` 的前置，与 timer 开关无关。

**C 做到了 A 与 B 都没做到的事：今天就能把全部验收标准真正满足。**
`provider-poll.sh:32` 的 `if [[ "$ANALYSIS_PROVIDER" != none ]]` 让整个 analysis
分支被跳过，`IMPLEMENT_PROVIDER=none` 让 implementation 分支也被跳过，timer 每跳
干净退出 0。今天的 fail-closed 空转随之消失，假声明被消除，零主机侧顺序依赖，
零未满足的前置。启用 codex 连同它的 canary 成为一件独立的、需要人认账的事。

### `timer_unit` 与白名单为什么原样不动

timer 当前确实是 active，`timer_unit` 如实记录了这件事，改它就是让 manifest
说假话。`contract.py:520` 的白名单同理：条目对应一个真实存在且正在运行的 unit。
（若将来按 A 或 B 处置并真的停用了 timer，那时再一并收紧，顺序按踩坑 24。）

### 本变更声明 `verification`

按 `03` §3 的判据——判据是验收证据的来源，不是变更的题材：

| AC | 证据来源 | 能否由 diff + required CI 复现 |
|---|---|---|
| AC-1 manifest 取值 | 仓库 diff | 能 |
| AC-2 `implement_provider` / `timer_unit` 不变 | 仓库 diff | 能 |
| AC-3 VM 上 `emaintenance.env` 的 `ANALYSIS_PROVIDER` 与文件模式 | 重装 + provision 后的主机侧状态 | **不能** |
| AC-4 `--action read-back` 返回 PASS | 同上 | **不能** |

另外，改动前的基线（`vm.profile.plan` 当前返回 `no-op`）**只有现在观测得到**，
合并后无法重放。`aisoft-platform` 的 `deployment_lifecycle` 是 `none`，按
`03` §11 的合取表，声明了 `verification` 仍然到 `completed`。

## 风险

- **合并不等于生效。** broker 运行时读的是安装态副本
  `/usr/local/share/aisoft/host-access-broker.json`。重装之前 VM 上
  `emaintenance.env` 仍是 `ANALYSIS_PROVIDER=claude`，timer 继续 fail-closed
  空转。这是预期，不是回归。见 verification 的交接项。
- **重装漏一台**：踩坑 20 的原样重演。判别方法是重装后 `vm.profile.plan`
  应当**不再返回 `no-op`**；仍是 `no-op` 说明漏装，不是「没有变化」。
- **本变更不解决「NewEMaint 要不要自动判级」**，它把这个决定明确留空。
  在有人做出该决定之前，NewEMaint 的 Issue 判级由人或由 Issue 会话完成，
  与今天的实际状态一致（今天那条链从未成功产出过一次）。
- **回滚** = revert 本 PR；若彼时已重装，revert 后需再重装一次并重跑
  `--action apply` 才能让 VM 回到旧声明。无 schema、无迁移、无数据。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写 governance manifest 中 emaintenance 的 analysis_provider 声明，决定 NewEMaint 上是否存在一个有写权限的自动判级 writer，属 Agent 与平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`：「Agent 或平台治理变更一律按 complex 处理」。本变更改的是
  canonical governance manifest 中决定「哪个 AI 运行时代表 NewEMaint 执行判级」
  的字段，两个条件都命中。
- `classification.py:55` `FORCED_COMPLEX_TYPES` 含 `platform`；
  `FORCED_COMPLEX_RISKS` 含 `platform-governance` 与 `agent-governance`；
  `route()` 另按 `contract_effect in {add, change}` 强制 complex。三条独立路径
  都指向 complex。
- `contract_effect: change` 而不是 `restore`：`restore` 是「恢复曾经成立、
  后来退化的产品合同」。claude 链在 NewEMaint 上**从未成立过**，没有东西退化；
  本变更推翻的是 #152 那次被记录在案的决定，平台声明的合同确实变了。
- 复杂度不因「只改一个字段」下调：这一个字段决定的是该仓上是否存在一个有写权限
  的自动 writer。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文「每条 profile 各自成立」那组 AC 已可测，本变更逐条映射到
  spec 的 AC-1..AC-4。唯一的开放决策——三个方向选哪个——由人在确认点 1 授权
  本会话裁定，依据与结论写在上文「三个方向与裁定」，并在 spec §6 列为非目标。
