---
issue: 304
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/304
change_type: maintenance
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: unchanged
reason: 仓库合同与代码不动，只把 #298 已合并的 broker worktree 归属闸门装到两台主机并读回验收
risk_flags:
  - host-runtime-install
required_docs:
  - summary
  - verification
documents:
  summary: summary-reinstall-worktree-owner-gate-260916.md
  verification: verification-reinstall-worktree-owner-gate-260916.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/304-reinstall-worktree-owner-gate
pr_url:
created: 2026-09-16
updated: 2026-09-16
---

## 问题/需求总结

#298 / PR 300（merge `f6e2e50`）给 broker `git.push.change` 加了 change worktree 单写者归属
闸门。合同已经合并进 `main`，但两台主机上运行中的 broker 运行时早于 #300，闸门在主机上
从未生效。merged source ≠ applied runtime。

本次不改仓库里的任何代码或 manifest——两个 installer 本来就已经收录该模块。要做的是
在 Mac 与 gitea-ci VM 两台执行既有的、版本化的、幂等的 `install-host-access-broker.sh`
（需要 `sudo`，由人执行），然后把 Issue 正文里四条可测验收标准逐条读回成真实证据。

## 影响范围

- 主机状态：Mac 与 gitea-ci VM 的 `/usr/local/lib/aisoft-host-access/`（root-scoped 安装面）。
- 仓库：只新增 `docs/changes/304-reinstall-worktree-owner-gate/` 两份语义文档，
  并在 `06-运维手册与踩坑集.md` 补一条踩坑——本次的失效形态与既有踩坑 20 不同型。
- 不改：`codex/` 下任何脚本、runtime、manifest、测试；不改 `AGENTS.md`；不改 CI。

## 初步方案与建议

1. 人在 Mac 与 gitea-ci VM 各执行一次 `sudo bash codex/install-host-access-broker.sh`。
   源 checkout 必须是 `/Users/benque/MyDocs/AISoftPlatform`（已在 `e5ed35e`，与
   `origin/main` 同步、工作区干净），否则 installer 的 staleness 闸门会 fail-closed，
   或者忠实地装一份旧内容并如实报成功（06 踩坑 20 的变体）。
2. 由本会话读回四条验收标准，含两条反向证明。
3. 把读回结果写进 verification 文档。

## 风险

- broker 是全平台唯一的 Gitea/Git 访问路径，重装失败会同时影响两台。缓解：installer 幂等，
  并为每个被覆盖文件留 `.previous` 备份；回滚是把 `.previous` 复原或用上一个 commit 重跑
  installer。
- 闸门一旦在主机上生效，此后每个没有 `claim-worktree` 的 change 会话推送会被拒为
  `WORKTREE_UNCLAIMED`。这正是 #298 已批准并合并的预期行为，不是本次新增的决策；
  但它是一次平台范围的行为激活，对并行会话可见，需在合同确认时知情。
- VM 侧的已安装 `broker.py` 无法用任何 typed 操作从 Mac 读取。该台的 AC-1 证据只能取自
  installer 自己打印的 `source commit` / `source operations` 两行，以及重装后 VM 侧
  `host.access.audit` 的 `PASS`。

## AI 判级

```yaml
change_type: maintenance
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: unchanged
reason: 仓库合同与代码不动，只把 #298 已合并的 broker worktree 归属闸门装到两台主机并读回验收
risk_flags:
  - host-runtime-install
required_docs:
  - summary
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- **`contract_effect=unchanged`**：产品合同由仓库定义，#298 合并时就已经改完。本次让主机状态
  向合同收敛，合同本身不动一个字节。
- **无 forced complex 触发**：本次 diff 里没有功能新增或变更、没有 schema/迁移、没有外部契约、
  没有新的认证/权限/安全决策（#298 已经做完并合并）、没有改共享核心组件的代码、没有跨模块或
  跨服务、没有改 CI/制品/部署/回滚脚本、没有改 Agent 或平台治理文件。`type/maintenance` 不在
  `FORCED_COMPLEX_TYPES`；`host-runtime-install` 不在 `FORCED_COMPLEX_RISKS`。
- **`deployment` 不适用**：AGENTS.md 的强制规则针对的是「CI/制品/部署/回滚**变更**」。本次不改
  任何部署脚本，只是执行一个既有的、已验证的、版本化的、幂等的 installer——这正是 AGENTS.md
  允许的形态。
- **`platform-governance` 不适用**：AGENTS.md 明确规定治理文件先由独立受控步骤应用并停止，
  由后续 fresh run 实施 runtime。#298 是那个受控步骤，#304 就是它规定的后续 run，
  不是第二次治理变更。
- **范围局部、可简单 revert**：仓库侧只有两份新文档加一行踩坑表；主机侧有 `.previous` 备份。
- **声明 `verification`**：判据是证据来源而不是复杂度。四条验收标准全部是主机读回，
  diff review 与 required CI 都复现不了。
- **本次已取得的一手证据**（三条，都在重装之前）：
  - 已安装 `broker.py` 的 `grep -c pushed_head` 为 `0`；`/usr/local/lib/aisoft-host-access/`
    下没有 `aisoft_worktree_owner.py`。
  - 源码 runtime 反向证明成立：错误 session 与缺失 session 都被拒为 `WORKTREE_OWNER_MISMATCH`。
    闸门代码本身是好的，缺陷纯粹是没装。
  - 已安装 runtime 对同一次错误 session 的调用返回 `PASS` 并真的推送了，返回体没有
    `pushed_head`，本地 marker 的 `last_push_head` 事后仍是 `null`。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文已给出四条可测验收标准。
- 边界判断一条，供确认时否决：本次判 `small` 的关键是「执行既有 installer ≠ 部署变更」与
  「应用已批准的治理合同 ≠ 新的治理变更」。若认为重装 broker 这一动作本身应当按 complex
  对待，请在确认点直接改判，本会话补 spec 与 plan。
