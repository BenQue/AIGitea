---
issue: 320
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/320
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/320-push-head-anchor
created: 2026-10-02
updated: 2026-10-02
---

# Verification

## 基线与证据分层

- source：fresh origin/main `5c2cd726c9aeaee9d17541d8feb049e33881bbac`；歧义四处 live source 读取确认。
- local：isolated tuple/claim 已完成；resolver/check-change-documents/apply-check/diff-check 与治理源未变检查 PASS；详见 evidence/contract-preparation.json。
- CI：NOT RUN（尚未 push/PR）。
- installed：NOT RUN（不在授权范围）。
- real model：NOT RUN。
- remote push/backfill/CI repair 事件：NOT RUN。
- merge/deploy：NOT RUN。

## 四场景与负向矩阵（待 T02 执行）

| 场景 | 本次验证锚 | 合格读回 | 必須停止 |
|---|---|---|---|
| 首次 push | 确认候选 head A | pushed_head=A | candidate 验证后未知变为 X 或读回 X |
| PR summary-only 回填 | 新 commit B，唯一 mapped summary、实际 URL/status 与文档检查通过 | pushed_head=B | 比对 A、漏校验或混入其它文件 |
| 范围内 CI 修复 | 新 commit C，合同范围/final diff/必要测试 fresh 验证 | pushed_head=C | 比对 A/B、越范围或验证未通过 |
| 他人改写 | 仍为本会话已验证 C | 不允许自动刷新成未知 X | session/branch 不符、未知改写或 pushed_head=X |

A/B/C/X 为桌面推演标识，实施验收需使用固定不同的 40 位 lowercase 合成 SHA；只证明治理规则判断，不是 broker/runtime 或 remote 事件测试。

## 执行收据

用户已确认完整合同/启动；T01 已应用六份治理文案，与批准 patch 一致，scope guard、git diff --check 和文档检查 PASS。收据为 evidence/t01-governance-apply.json。T02 fresh read、四场景/负向矩阵、targeted tests 与 full smoke 均 NOT RUN，留待 fresh run；不勾选尚未完成的验收项。

## 判级与流程 GAP

平台 projector 已投影并独立读回 `platform/complex` 为 `projected`；lifecycle 为 `spec-drafting`。canonical `triage/*` 写入被 extension writer 拒绝（REQUEST_DENIED），标记 GAP；没有扩大权限或修改 broker。推荐 category=bug/state=ready-for-agent 已记录在 Issue brief，尚未投影成功。

## 受控步骤停止边界

本运行仅 T01：治理文字应用、范围检查、本地原子提交与收据。未进入 T02，也未进行 push/PR/CI/install/real-model/live/merge/deploy。fresh run 必须从本 worktree 重新读取六份已修改指导、AGENTS 与 approved spec/plan，再按 T02 执行；无需再次合同确认。
