---
issue: 423
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/423
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
branch: change/423-karpathy-principles
created: 2026-10-22
updated: 2026-10-22
status: pending
---

# Verification：共享工程原则

## 基线与范围

- 基线：fresh `origin/main` = `58b06590c1539ffdeb8af9e0d5a95b78090edb6b`。
- 上游研究 pin：`2c606141936f1eeef17fa3043a72095b4765b9c2`；已读 SKILL.md、CLAUDE.md、Cursor rule、EXAMPLES.md 与 plugin.json。
- 2026-10-22 用户确认 #423，补充纲领性定位和 Claude Code 独立审议。正文共四项工程原则，无具体开发步骤；runtime、CI/安装脚本、根 AGENTS.md 未修改。
- T01 治理写入随本次原子提交结束；T02 fresh Claude Code 审议尚待执行。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 提案 apply-check / 文档合同 | PASS | 研究阶段检查通过；实施后 reverse apply-check 与 check-change-documents 两项 PASS |
| git diff --check | PASS | 治理文字与发布登记无空白错误 |
| usage-bundle.sh --verify --baseline-ref 58b06590c1539ffdeb8af9e0d5a95b78090edb6b | PASS | 1.14.0；历史发布前缀未改 |
| usage-bundle.sh --build + 三端字节/相对链接核对 | PASS | 隔离输出 `/private/tmp/aisoft-423-bundle-mj5t1t3r`；Claude/Codex/Cursor 参考文档字节相同，入口链接可解析；adapter 只在 Codex 落点 |
| broker Issue 状态与判级 | PASS | #423 updated，approved + type/platform + complexity/complex；启动确认不含 PR 提交 |
| 上游排序示例的判别力复核 | PASS | 同分顺序不同的两个结果均通过其 score 断言，不能证明 tie-break 修复 |
| 完整 smoke / 六场景独立审议 | NOT RUN | T02 待执行；不以局部检查替代 |
| required CI / 全局安装 / provider-session 效果 / 项目采用 / 部署 | NOT RUN | 未 push 或建 PR；后四项不在本次源码授权范围 |

发布包 digest：`sha256:a38dd340826e4ed137b6568bcec370a47f162744141639c4cc99a4ad9046a1dd`；原则 SHA-256：`52cb1fbfc664eaf7fa2e167a11c9a6c6d8d5f0ae5a8629ff9160e31631737f31`。

## Acceptance criteria 结果

AC-1 的 source/local 分发检查 PASS；AC-2–AC-6 等待 T02 完整回归与独立审议，不冒充真实模型效果证明。

## 交叉审查

T01 提交后发起 fresh Claude Code，只读审查该 exact head；先重读本轮批准合同与根 AGENTS.md。
审查结论未返回前不填 PASS，也不进入确认点 2。

## 遗留风险与未完成项

待 T02 full smoke、六场景审议与另一提供者审议；仅源码与隔离导出完成，尚未安装、生效到项目或交付 PR。
