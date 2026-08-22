---
issue: 136
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/136
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
depends_on: []
status: contract-drafting
branch: change/136-broker-force-with-lease
pr_url:
created: 2026-08-22
updated: 2026-08-22
---

# Spec · `git.push.change` 改用 force-with-lease

## 目标与原因

让已推送的 change 分支在 `main` 前进并 rebase 之后仍能通过 broker 推送，
同时不放松线性历史与新鲜基线这两条既有保证，也不引入无保护的 force。

安全性不来自新增信任，而来自治理合同**已经**成立的前提：

1. **单写者**——change 分支与 Issue 一一绑定，可读命名元组由 `select_change_name` 强制唯一；
2. **`main` 受保护**——`change_branch()` 已把可推送 refspec 限定为 `change/*`，
   `main` 的 `enable_force_push: false` 由 `host.access.audit` 核对，force 够不到 `main`；
3. **lease 而非裸 force**——远端在读取 sha 之后被别人改动时拒绝而不是覆盖；
4. `BASE_BRANCH_STALE` 与 `MERGE_COMMIT_DENIED` **保持不变**。

## Acceptance criteria

- [ ] **AC-1 lease 形式**：`git.push.change` 使用
      `--force-with-lease=refs/heads/<branch>:<remote-sha>`，`<remote-sha>` 由推送前的
      `git ls-remote --heads` 读取；argv 中不出现裸 `--force` 或 `-f` token。
- [ ] **AC-2 竞态拒绝**：远端分支在读取 sha 之后被改动时，推送被拒绝并返回
      `REMOTE_BRANCH_MOVED`，远端 sha 保持为对方写入的值，不被覆盖。
- [ ] **AC-3 首次推送**：远端分支不存在时使用空 expectation（`refs/heads/<branch>:`），
      分支正常创建；该形式在 ref 已存在时按 git 语义拒绝，不退化为无保护推送。
- [ ] **AC-4 既有约束不变**：`BASE_BRANCH_STALE` 与 `MERGE_COMMIT_DENIED` 行为不变，
      各有独立回归测试，且两者都在任何 `git push` 命令发出**之前**触发。
- [ ] **AC-5 复现路径**：回归测试覆盖 推送 → `main` 前进 → `BASE_BRANCH_STALE`
      → rebase → 再推送成功，且断言 rebase 后的推送确为 non-fast-forward。
- [ ] **AC-6 全量绿**：`bash codex/tests/smoke.sh` 全绿。

## 接口、数据与兼容性影响

- **typed 操作清单不变**：不新增、不删除、不改名任何 operation；
  `git.push.change` 的 `arguments` 仍为 `["branch"]`，manifest 与 CLI 表面零变化。
  调用方仍然不能传 remote name、URL、refspec 或 command。
- **新增错误码 `REMOTE_BRANCH_MOVED`**：属新增的可辨识失败分支，
  原先该场景返回 `HOST_COMMAND_FAILED`。调用方按未知码处理仍安全（fail closed）。
- **`ls-remote` 解析收紧**：object id 必须匹配既有的 `COMMIT_SHA_RE`，
  否则 `RESPONSE_SCHEMA_INVALID`。远端返回的字节现在会进入 argv，必须先验证。
- **无 schema、无数据迁移、无凭据面变化**。

## 风险与回滚约束

- force 的作用面被两层夹住（refspec 限定 `change/*` + `main` 保护），
  且 lease 使拒绝而非覆盖成为默认失败模式。
- `stale info` / `non-fast-forward` / `fetch first` 三个标记只在远端位置不符时出现，
  不会与凭据或网络故障混淆；其余非零返回仍归入 `HOST_COMMAND_FAILED`。
- 回滚方式：`git revert` 本 PR 后按同一 installer 重装两台主机的 broker，
  即回到裸 push 行为（互锁缺陷随之恢复，但无数据损失）。
- **循环依赖**：本变更修的正是推送机制本身，而承载它的分支要用当前有缺陷的机制推上去。
  实现期间必须一次性推送，不得分批。

## 非目标

- 不新增 `git.branch.delete` typed 操作（Issue 正文的备选方案）。
- 不修改 `skill-for-claude/SKILL.md` 第 5 条对 `BASE_BRANCH_STALE` 的处置指导，
  也不修改 `06-运维手册与踩坑集.md`。二者是 agent 行为/治理文档，按 `AGENTS.md`
  必须由独立的、只修改治理合同的受控步骤应用；本 PR 只交付 runtime 与测试。
  现行指导（停止当前 pass 并升级）在本变更之后仍然安全，只是偏保守。
- 不改变 `main` 的 branch protection，不放松 `enable_force_push`。
- 不执行两台主机的 broker 重装（需独立部署授权）。

## 未决问题

- 无。
