---
issue: 354
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/354
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - rollback
  - external-contract
depends_on:
  - 355
status: approved
branch: change/354-matt-skills-install
created: 2026-10-08
updated: 2026-10-08
---

# #354 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 四角色合同、只读基线证据、清单脚本与固定提示词；文档检查与本地 commit | - | completed |
| T02 | 阶段一：备份、安装、重复安装、N-1 回滚与 adapter 恢复、回到 v1.3.1、漂移读回 | T01 | completed |
| T03 | Codex fresh session 四项检查；Codex 独立插件状态报告 | T02 | completed |
| T04 | 阶段二：按启动规则确定 P2，装入 Claude 侧技能，切换 Claude 插件到平台 pin，回滚演练 | T03 | completed |
| T05 | Claude fresh session 检查 | T04 | completed |
| T06 | verification 汇总、逐条 AC review、判级读回、唯一最终 PR 候选 | T05 | in-progress |

T04 另有一个本表之外的前置：#355 已合并。T02、T03 不依赖它。人在确认点 1 若选择等 #355 合并后
一次完成，则 T02 也推迟到 #355 合并之后，顺序不变。

T03 记为 completed 的含义是合同内的尝试与后备路径都已走完；其中模型回合的结论是 GAP / NOT RUN，见 verification。

T01 在确认点 1 之前完成，它不写入 `~/.agents`、`~/.claude`、`~/.codex`。T02 起的每一步都要先取得确认。

## Expected touch points

- T01：`docs/changes/354-matt-skills-install/` 的四份文档，`evidence/inventory.py`、
  `evidence/t01-baseline.json`、`evidence/fresh-session-prompts.md`。
- T02：主机上 spec「阶段一目标路径清单」W1–W8；仓库内 `evidence/t02-codex-managed-install.json`。
- T03：不写主机受管路径；仓库内 `evidence/t03-codex-session.md`。
- T04：主机上 spec「阶段二目标路径清单」X1–X6；仓库内 `evidence/t04-claude-plugin.json`。
- T05：仓库内 `evidence/t05-claude-session.md`。
- T06：verification 与 summary 状态；不改其它文件。

仓库内不触碰本目录之外的任何路径。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `python3 evidence/inventory.py /Users/benque <source>` 生成基线；`git ls-remote --tags` 读回上游；对照 spec 路径清单 |
| AC-2 | 备份后逐文件哈希比对；S4 加 S5 在真实目标上恢复整个写入范围并读回基线摘要 |
| AC-3 | S2 断言全表；S3 前后清单逐项相等；`python3 -m aisoft_loop.matt_snapshot preflight-install` 读回；`check-installed-drift` 的 install-skills 面 |
| AC-4 | S4 读回 v1.2.2 与基线入口摘要；S6 读回与 S2 相等；阶段二的插件回滚演练读回 1.2.3 后回到平台 pin |
| AC-5 | T03 与 T05 的固定提示词输出，逐项对照期望；未执行项记 GAP / NOT RUN |
| AC-6 | verification 的分层结果表；受管安装、Codex 插件、Claude 插件三行分开 |

本票不改 shell 或 runtime，不欠 `smoke.sh`。提交前运行
`python3 -m aisoft_loop.cli check-change-documents --repo .` 与 `resolve-documents 354`，
并对 `evidence/inventory.py` 运行 `python3 -m py_compile`。

## 部署与回滚

无应用部署。主机安装的回滚见 spec：阶段一用 `--rollback` 加 adapter 备份恢复，阶段二用插件 CLI
或恢复备份文件。两处回滚都在真实目标上演练一次。仓库内改动可直接 revert，但 revert 不撤销主机状态。
