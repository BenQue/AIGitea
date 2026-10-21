---
issue: 412
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/412
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/412-governance-table-writeback
created: 2026-10-21
updated: 2026-10-21
---

# 治理表回写

## 目标与原因

路线图与 E2E 验收表是判断「平台整改到哪了、是否真被用起来」的唯一两张表，但状态列一直靠「下一批顺手改」，两轮都没兑现：
终审时路线图第二轮 10 行过期，E2E 表缺一次恢复演练与三次采用的 main 读回。本批一次回写到事实，并把回写定为每个平台批次
在自己 PR 里完成的固定步骤，收尾时读回。

## Acceptance criteria

- [ ] AC-1 路线图第二轮 11 行的状态与 Gitea 读回一致：每行写 Issue、PR 编号与合并 SHA 前 7 位，发了使用层版本的写版本号；推荐顺序下的段落改成现状（第二轮已全部合并，退出条件另行判断）。
- [ ] AC-2 E2E「验收记录」追加 NewEMaint #313 test 数据库恢复演练一行：PR 322、合并 `dfe04df`，覆盖阶段与未覆盖如实写（AC-5 由负责人以回执判过并记录例外，生产 NOT RUN）。
- [ ] AC-3 E2E「采用记录」HSDB、LocalWMS、SFM、SFM（Cursor 落点）四行的 `--project-status` 列换成各项目 `main` 合并 SHA 上 `aisoft bundle status` 的真实读回；LocalWMS 另写 workflow 无 `uses:`；SFM 文档检查的遗留 GAP 如实写。
- [ ] AC-4 `03` §7 新增「治理表回写（平台仓）」：本批在路线图与 E2E 表的行在本批 PR 里写成合并后状态，确认点 2 前核对，收尾读回 `origin/main`；不属于任何平台批次的项目侧事件由明确列入合同范围的批次补写，不靠顺手。`03` 来历表加 #412 行，`AGENTS.md` 一行指针且总大小仍 ≤ 5 KB，两张表的「用法」行与规则一致。
- [ ] AC-5 smoke 用 `require_heading` 钉住新小节；删掉该标题时 smoke 失败（反向证明），恢复后 `bash codex/tests/smoke.sh` 通过；`grep -Fq` 棘轮基线不变。
- [ ] AC-6 不改技能、runtime、broker、模板与 `usage/`；`git diff --stat origin/main` 只含上述文件与本 change 目录。

## 接口、数据与兼容性影响

只改文档与一行 smoke 钉子。不改使用层发布包成员，不发新版本，不需要重装。

## 风险与回滚约束

纯文档，revert 本 PR 即回滚。并行批次若先合并并改了同一张表，按 merge commit 集成 main，表格冲突从 `origin/main` 重建只补本批的行。

## 非目标

- 不做工具自动生成或校验表格状态（终审明确不建议）。
- 不改 `issue-session-flow` 技能与确认点 2 候选格式。
- 不补第一轮各行，不处理 SFM 文档检查的遗留 GAP（R12 LEGACY 范围）。

## 未决问题

无。
