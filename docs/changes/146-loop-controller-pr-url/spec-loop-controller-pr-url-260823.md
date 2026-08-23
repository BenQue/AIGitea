---
issue: 146
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/146
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/146-loop-controller-pr-url
created: 2026-08-23
updated: 2026-08-23
---

# Spec：Controller 建 PR 后自动回填 pr_url

## 1. 目标

让 Loop/Controller 路径也把 `pr_url` 写进 summary，并让 Gitea 生命周期标签与 summary front matter 不再各说各话。

## 2. 先纠正 Issue 正文的一处判断：那两条约束不成立

Issue §范围 把两条约束列为「最硬的一处」和「同样挡路」：

1. `validate_provider_commit` 要求 provider 跑完工作树干净；
2. 它要求 `base_sha..HEAD` 之间每条 commit 的 subject 含 `#N` 与 ticket id。

**读代码后这两条都不挡路**，因为 `controller.py:185`：

```python
provider_base_sha = self.git.head_sha()
```

`provider_base_sha` 在**每一轮循环开头**取值。Controller 在第 N 轮末尾产生的 commit，位于第 N+1 轮 `base_sha` 之前，因此**根本不在 `base_sha..HEAD` 这个窗口里**——ticket-id 规则看不到它。清洁工作树的要求同理：只要 Controller **提交**而不是只写文件，下一轮 `git status --porcelain` 就是空的。

真正的约束只剩一条，而且是充分必要的：**Controller 必须提交，不能只写。** 写而不提交才会在下一轮撞上 `provider must leave a clean worktree after committing`。

这条更正记在这里而不是默默按对的做，是因为 Issue 正文已经公开表述过一次；照着它走的人会去设计一套并不需要的豁免机制。**本变更不对 `validate_provider_commit` 做任何豁免、任何放宽。**

## 3. 裁决一：写在 `create_pr` 与 CI 轮询之间

```
create_pr → _set_lifecycle("pr-open") → 【回填 + 提交 + push，更新 head_sha】→ get_commit_status(head_sha)
```

理由：

- **这是 PR 号第一次存在的地方**，也是唯一一处不需要等待就能拿到它的地方；
- 放在下一轮开头会让「PR 已建但 Loop 中途终止」留下一个永远不会被回填的变更——恰恰是本 Issue 要消灭的形态；
- 放在 `_finish` 里则拿不到 CI 覆盖（见 §3.1）。

### 3.1 附带修掉一个既有的证据缺陷

今天的顺序是「push → 建 PR → 对**那个** `head_sha` 轮询 CI → READY_FOR_REVIEW」。之后人手工回填 `pr_url` 再推一次，分支 HEAD 就变了，而 Loop 记录的 CI 成功仍指向旧 commit。**Loop 宣布「CI 通过」的那个 commit 不是分支最终的 HEAD。**

把回填放进 CI 轮询之前，`head_sha` 随之更新，CI 证据从此对应分支真实 HEAD。这不是本 Issue 的目标，但顺序一旦排对就自然成立，值得写明。

### 3.2 保留 `_set_lifecycle` 在原位

标签在 `create_pr` 之后立刻推进（不动）。PR 此刻确实已开，标签说 `pr-open` 是真话；即使随后回填失败并升级，标签也不该退回去。

## 4. 裁决二：新增一个窄到只能干这件事的提交方法

`LocalGit` 新增 `commit_paths(paths, subject)`：

- 先读 `git status --porcelain`，**要求变更集合恰好等于声明的路径集合**；多一个文件就 `ProviderError`，不做 `git add <path>` 了事；
- 然后 `git add -- <paths>` 与 `git commit -m <subject>`，返回新的 `head_sha`。

为什么是「恰好相等」而不是「包含」：Controller 第一次在 change 分支上产生自己的 commit，此前所有 commit 都来自 provider 并受 `validate_provider_commit` 校验。一个能顺手把工作树里其它东西一起提交的方法，等于在那条校验旁边开了一扇没人看守的门。恰好相等意味着「工作树里有别的东西」这件事本身就是异常，必须停下来。

### 4.1 被否决的选项

- **让 provider 去写**：provider 是可替换的外部适配器（`IMPLEMENT_PROVIDER` 可为 codex/claude/none），把一条治理不变量寄托在它的实现上，等于让不变量随 provider 变；
- **`git commit -a`**：正是 §4 要防的那扇门；
- **不提交、留给人**：那就是今天的状态。

## 5. 裁决三：URL 由 summary 自己的 `gitea_url` 推导，不用 `pr["html_url"]`

新增 `documents.backfill_pr_number(repo, issue_number, pr_number)`，内部用 `_pull_url_prefix()` 从 summary 的 `gitea_url` 推出 `<prefix>/pulls/<number>` 再委托给 `backfill_pr_url()`。

**不用上游 `html_url`** 的理由是实测的：同一套本机 Gitea 里，API 返回的 `html_url` 用 `gitea-ci.orb.local:3000`，而 runner 日志里的仓库地址是 `localhost:3000`。base URL 的渲染差异是环境事实，不是错误；直接把 `html_url` 喂给 `backfill_pr_url` 的严格前缀校验，会让一次健康的 Loop 因为一个纯粹的书写差异升级成人工介入。

代价：失去「Gitea 说的 URL 与 summary 说的 URL 是否一致」这个交叉校验。接受——`pr_number` 本身来自 Gitea 响应，仓库归属由 `create_pr` 的调用坐标保证，交叉校验能抓到的额外情形接近于零。

## 6. 裁决四：失败一律升级为 NEEDS_HUMAN_DECISION

`backfill_pr_url` 的 fail-closed 路径有三种：summary 没有 `pr_url` 键、已有一个**不同的**非空值、URL 与 `gitea_url` 不自洽。三种都说明文档的前提被破坏，Controller 必须停下来并把原文消息带出去，而不是崩溃、也不是跳过。

处置与既有的 `validate_provider_commit` 失败一致：`_set_lifecycle("awaiting-triage")` + `_finish(NEEDS_HUMAN_DECISION, ...)` + 评论。

**不跳过**：跳过就是把静默漏做原样保留下来，只是多了一次尝试。

## 7. 裁决五：同时推进 summary 的 `status`

`backfill_pr_url()`（#142 spec §4.1）已经在写 `pr_url` 的同时把 `status` 推进到 `pr-open`，本变更直接沿用，不加开关。这正好消除 §问题陈述里那处记录分裂。

已核实无副作用：`_revalidate` 经 `load_contract` 从 **Gitea 标签**读生命周期（`allowed_lifecycle=("pr-open",)`），不读 summary 的 `status` 字段。

## 8. Acceptance criteria

- [ ] Loop 建完 PR 后，summary 的 `pr_url` 非空且等于 `<gitea_url 前缀>/pulls/<PR 号>`；
- [ ] summary 的 `status` 与 Controller 已经写下的 Gitea 标签一致（都是 `pr-open`）；
- [ ] 回填产生的 commit 只包含那一个 summary 文件，且有负向测试：工作树里多一个脏文件时提交被拒；
- [ ] 回填之后 `head_sha` 更新，CI 轮询针对的是新的 HEAD；
- [ ] 幂等：`pr_url` 已正确时不产生 commit、不 push；
- [ ] `backfill_pr_url` 的三条 fail-closed 路径都升级为 `NEEDS_HUMAN_DECISION` 并带出原文消息，不崩溃、不跳过；
- [ ] **不对 `validate_provider_commit` 做任何豁免或放宽**，且有测试证明普通 provider commit 仍被同一条 ticket-id 规则拦住；
- [ ] Codex 侧文档能被 grep 到该步骤的描述，且描述为「Controller 自动完成」而非新增人工步骤；
- [ ] `bash codex/tests/smoke.sh` 全过。

## 9. 明确不做

- 不改 #142 的「`pr_url` 只写 summary」裁决；
- 不改 `backfill_pr_url()` 既有的幂等与 fail-closed 语义；
- 不放宽 `validate_provider_commit`；
- 不改 `LocalGit.push()` 的 remote 解析（它硬编码 `origin`，与 broker 依 manifest `git_remote_name` 解析不同；这是既有差异，超出本 Issue 范围）；
- 不追溯修补任何已有变更文档。
