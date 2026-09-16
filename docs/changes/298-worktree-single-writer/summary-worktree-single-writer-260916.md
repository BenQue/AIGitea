---
issue: 298
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/298
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: change_type=platform 属强制 complex 类型；本次给 broker git.push.change 增加归属闸门与新返回字段，并改写 03 与 issue-session-flow 的治理合同，属外部契约与 Agent 治理变更
risk_flags:
  - functional-change
  - external-contract
  - shared-core
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-worktree-single-writer-260916.md
  spec: spec-worktree-single-writer-260916.md
  plan: plan-worktree-single-writer-260916.md
  verification: verification-worktree-single-writer-260916.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/298-worktree-single-writer
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/300
created: 2026-09-16
updated: 2026-09-16
---

## 问题/需求总结

change worktree 目前只有「建」的约束，没有「进」的约束。平台合同要求并行会话各自
worktree，但任何会话都能 `cd` 进别人的 change worktree 执行 `git rebase` / `git commit` /
`git checkout`——这三个都是纯本地操作，不经过 broker，平台侧零感知、零记录。

2026-09-16 NewEMaint #96 实际中招：该会话在 `AWAITING_PR_CONFIRMATION` 之后核验的是
`327fc06`，push 之后从 `gitea.pull.read` 读回的 head 是 `b576525`，多出 61 行它从未读过的
内容。这一次结果正确，但正确来自运气，不来自流程。

## 影响范围

- `codex/runtime/aisoft_host_access/broker.py`：`git.push.change` 的前置校验与返回体。
- `codex/runtime/aisoft_loop/`：新增归属标记的写入命令与只读扫描命令。
- `03-Issue-Spec-Plan与单闸门开发流程.md`：单写者归属合同。
- `skill-for-claude/issue-session-flow/SKILL.md` 与 `codex/skills/issue-session-flow/SKILL.md`：
  同一条合同的两侧措辞与 Red Flag。
- `06-运维手册与踩坑集.md`：新增一条踩坑，承接踩坑 15。
- `codex/tests/smoke.sh`、`codex/runtime/tests/test_host_access.py`：闸门与文本守卫。

不改：broker 的 typed 操作集合与参数集合（不新增操作、不给既有操作加参数），因此
`operation_count` 与 `arguments` 不变，既有调用方不会因为参数集合变化而失败。

## 初步方案与建议

1. change worktree 的 git dir 内放一份可机读归属标记，记录 Issue 号、分支、创建会话 id。
2. `git.push.change` 读该标记；缺失、不匹配或调用方身份不一致时 fail closed，给独立错误码。
3. 新增只读扫描命令，枚举本机全部 change worktree，报告 HEAD 与最近一次 broker push 的关系。
4. `git.push.change` 返回体带本次推送的 40 位 SHA 与该分支上一次 push 的 SHA。

## 风险

- **归属机制是协作式的，不是安全边界**：同机同用户下，B 能读到的标记 B 也能伪造。本次目标是
  让意外改写变成会停下的事件，不是防御蓄意的 agent。这条必须写进 spec 的非目标。
- **闸门生效需要两台重装**：broker 运行时读的是 `/usr/local/lib/aisoft-host-access/`，合并后
  需要在 Mac 与 gitea-ci VM 各跑一次 `install-host-access-broker.sh`（需要 sudo，由人执行）。
  重装之前，仓库里的新行为不会作用于任何真实 push。
- **对既有在途 worktree 是一次 flag day**：闸门上线后，没有标记的既有 change worktree 推送会被
  拒绝，必须先补一次 claim。错误信息里要直接给出补救命令。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: change_type=platform 属强制 complex 类型；本次给 broker git.push.change 增加归属闸门与新返回字段，并改写 03 与 issue-session-flow 的治理合同，属外部契约与 Agent 治理变更
risk_flags:
  - functional-change
  - external-contract
  - shared-core
  - agent-governance
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

- `codex/runtime/aisoft_loop/classification.py:55` 的 `FORCED_COMPLEX_TYPES` 含 `platform`：
  `change_type=platform` 单独一项即强制 complex，与 risk_flags 无关。
- `codex/runtime/aisoft_loop/change_control.py:40`：`gitea-governance.json` 里 `aisoft-platform`
  未声明 `change_control`，解析回落到 `production`，因此走 production complex 路径，
  `required_docs` 必须含 `spec` 与 `plan`。
- `contract_effect=add`：`git.push.change` 新增一条拒绝条件与两个返回字段，是新增的外部可观察
  行为，不是恢复既有行为。
- `required_docs` 追加 `verification` 的依据是 `03` §3「何时声明 verification」的判据行二：
  只读扫描命令要对本机真实 worktree 执行，闸门要对真实安装的 broker 执行，这两类证据 required
  CI 复现不了。声明它不表示本次要部署。
- AGENTS.md 已写死「Agent 或平台治理变更一律按 complex 处理」，本次同时改 broker 行为与
  `AGENTS.md` 之外的治理文档（`03`、两份 issue-session-flow），落在该条内。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文已给出六条可测验收标准；spec 把其中两处留给合同确认的口径写成显式决策
  （调用方身份的载体、扫描命令 GAP 的判定口径），并给出推荐取值。
