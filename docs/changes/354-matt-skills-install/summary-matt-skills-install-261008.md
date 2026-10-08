---
issue: 354
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/354
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 在真实主机切换 Matt 受管快照与 provider 插件来源，改变两侧会话可发现的技能集合，并要求备份、失败恢复与 N-1 回滚，强制 complex。
risk_flags:
  - agent-governance
  - platform-governance
  - rollback
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-matt-skills-install-261008.md
  spec: spec-matt-skills-install-261008.md
  plan: plan-matt-skills-install-261008.md
  verification: verification-matt-skills-install-261008.md
confidence: high
override_reason: ''
depends_on:
  - 355
status: approved
branch: change/354-matt-skills-install
pr_url:
created: 2026-10-08
updated: 2026-10-08
---

## 问题/需求总结

#352 / PR #353 把 Matt v1.3.1（37 个技能）合并进源码，但没有在任何主机上安装。当前 Mac 的三个
分发面仍是旧版本：Codex 受管快照 v1.2.2（35 个技能）、Codex 独立插件 1.2.3、Claude 独立插件 1.2.3。
`check-installed-drift` 在 install-skills 面因此报 GAP。

本票在当前 Mac（`/Users/benque`）上把这三个面按受控合同处理到位，并在两个 provider 的真实
fresh session 里验收。仓库内只新增本目录的合同与证据；不改 runtime、installer、Agent 源或治理文件。

## 与 #355 的依赖

#355 是 source 层：它交付平台自有、钉在 `24fe0ef7737efae15c87225755e9f6f5965e4888` 的 Claude
marketplace 条目，以及 Claude 侧的 v1.3.1 边界规则。官方 marketplace 仍把 Matt 钉在 1.2.3 时期的
commit，所以 Claude 插件的升级入口只能来自 #355。

| 本票内容 | 是否依赖 #355 合并 |
|---|---|
| Codex 受管快照安装、重复安装、N-1 回滚（T02） | 否 |
| Codex fresh session 验收（T03） | 否 |
| Claude 插件切换到平台 pin（T04） | 是 |
| Claude fresh session 验收（T05） | 是 |
| 唯一最终 PR（T06） | 是，PR 含两阶段证据 |

`depends_on` 因此声明 355。superpowers 不在本票范围。

## 授权与执行记录

2026-10-08 用户在会话 65e1a492-eac2-4289-b459-f4322ea932bf 的确认点 1 确认本合同并启动：

- C1 执行节奏：分两阶段。现在执行阶段一，#355 合并后按启动规则执行阶段二，最后一个 PR。
- C2 Codex 独立插件：不动，只报告。
- C3 `SAPWMOdataPDA` 的项目级 Claude 插件记录：不动，pin 检查的那条 DRIFT 记为已知残留。

确认授权合同内的备份、安装、回滚演练、fresh session 与证据记录。它不授权 push、PR、merge、
VM 安装或合同路径清单之外的写入。

## 影响范围

| 对象 | 绑定或范围 |
|---|---|
| Repository / Issue | admin/aisoft-platform / #354 |
| Branch | change/354-matt-skills-install |
| Worktree | /private/tmp/issue-354-matt-skills-install |
| 单写者 | Claude Code 会话 65e1a492-eac2-4289-b459-f4322ea932bf，已 claim |
| 平台 source pin（阶段一） | `8162fe7d71dd58b13ca80ef26467a2549973f4df`，2026-10-08 经 broker fetch 读回的 origin/main |
| 平台 source pin（阶段二，P2） | `b356085d1d507ba0d66fe3b8d118e4a57edf7075`，#355 / PR #356 的 merge commit |
| 上游固定目标 | v1.3.1，tag object `0b6cee10f260a2e048279cf737bfd3e37b1fce0b`，commit `24fe0ef7737efae15c87225755e9f6f5965e4888` |
| 目标主机 | 当前 Mac，target-home `/Users/benque` |
| 仓库内改动 | 仅 `docs/changes/354-matt-skills-install/` |
| Merge policy | manual |

## 初步方案与建议

按 [spec](spec-matt-skills-install-261008.md) 的安装合同分两阶段执行，按
[plan](plan-matt-skills-install-261008.md) 的 ticket 顺序推进，结果写入
[verification](verification-matt-skills-install-261008.md)。

建议分两阶段、最后一个 PR：阶段一现在就能做，它与 #355 无关，做完 install-skills 面的 GAP 即可
读回；阶段二等 #355 合并后按规则执行。另一种做法是等 #355 合并后一次完成，代价是 Codex 侧在此之前
一直停在 v1.2.2。两种做法的证据要求相同，由人在确认点 1 选定。

## 风险

- 安装器的 `--rollback` 只恢复 Matt 快照与入口，不恢复 8 个平台 adapter；整个写入范围的恢复要靠
  安装前的备份。
- Matt 与 gstack 都有 `retro`。安装后 `~/.agents/skills/retro` 指向 Matt，`gstack/retro` 原样保留，
  裸名称在会话里是否被正确消歧只能靠 fresh session 验证。
- Codex 独立插件 1.2.3 仍启用，它与受管 v1.3.1 的同名技能并存。本票只报告其状态，不修改。
- Claude 插件 CLI 回滚得到的是官方 marketplace 当前 pin（`c55ee46`），不是安装前记录的 `2ab9580`；
  逐字节回到安装前状态需要恢复备份文件。
- 本机还有一条项目级 Claude 插件记录属于平台范围之外的项目，按默认处置不动它，pin 检查会因此保留
  一条 DRIFT。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 在真实主机切换 Matt 受管快照与 provider 插件来源，改变两侧会话可发现的技能集合，并要求备份、失败恢复与 N-1 回滚，强制 complex。
risk_flags:
  - agent-governance
  - platform-governance
  - rollback
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- Issue 正文拟判级 platform / complex / manual，要求 complex 安装合同。
- `type: platform` 属于强制 complex 类型；`agent-governance`、`rollback` 是强制 complex 风险。
- 技能集合变化：新增 `implement-spec`、`pr`、`retro`，移除 `resolving-merge-conflicts`。
- 验收证据来自真实主机与 provider 会话，diff review 与 required CI 无法重放，所以声明 verification。
- AISoftPlatform 的 `routine_auto_merge_enabled=false`，固定 manual。

### 缺失的 acceptance criteria 或决策

Issue 的 6 条 AC 完整可测。三项执行选择待人在确认点 1 决定，见 spec「待确认的选择」。
