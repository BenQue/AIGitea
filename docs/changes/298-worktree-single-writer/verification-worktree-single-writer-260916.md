---
issue: 298
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/298
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - functional-change
  - external-contract
  - shared-core
  - agent-governance
  - platform-governance
depends_on: []
status: pending
branch: change/298-worktree-single-writer
created: 2026-09-16
updated: 2026-09-16
---

# Verification · change worktree 单写者归属

## 基线与范围

- Commit SHA: 待填写
- 基线：`origin/main` = `9a2fa118bb86860372e6c90e08c917641aeba563`
- 环境: Mac（`/private/tmp/issue-298-worktree-single-writer`），Python 3 源码树直跑，未重装 broker
- 本记录负责证明的 acceptance criteria: AC-3（本机真实 worktree 的只读扫描）、
  AC-2 与 AC-4 在**未重装**前提下用源码树 runtime 的一次真实执行；其余 AC 由 required CI 复现。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待执行 | NOT RUN | 待填写 |

命令与输出照实抄。改动前才观测得到的证据（基线状态、改动前后对比、先看着测试红）
只有写在这里才留得下来——改动合并后就无法重放。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待填写 | 待填写 |
| AC-2 | 待填写 | 待填写 |
| AC-3 | 待填写 | 待填写 |
| AC-4 | 待填写 | 待填写 |
| AC-5 | 待填写 | 待填写 |
| AC-6 | 待填写 | 待填写 |

## 遗留风险与未完成项

- 两台重装（`sudo bash codex/install-host-access-broker.sh`，Mac 与 gitea-ci VM）需要 sudo，
  不由本次会话执行，合并后由人执行；在此之前运行中的 broker 仍读旧代码，闸门不生效。
  本记录只证明源码树 runtime 的行为，不证明已安装 broker 的行为。

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
