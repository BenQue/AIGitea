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

- source：fresh origin/main `5c2cd726c9aeaee9d17541d8feb049e33881bbac`；歧义四处 source 读取确认。
- local：isolated tuple/claim 已完成；resolver/check-change-documents/apply-check/diff-check 与治理源未变检查 PASS；详见 evidence/contract-preparation.json。
- CI：NOT RUN（尚未 push/PR）。
- installed：NOT RUN（不在授权范围）。
- real model：NOT RUN。
- remote push/backfill/CI repair 事件：NOT RUN。
- merge/deploy：NOT RUN。

## 四场景与负向矩阵（T02 已执行合成推演）

| 场景 | 本次验证锚 | 合格读回 | 必須停止 |
|---|---|---|---|
| 首次 push | 确认候选 head A | pushed_head=A | candidate 验证后未知变为 X 或读回 X |
| PR summary-only 回填 | 新 commit B，唯一 mapped summary、实际 URL/status 与文档检查通过 | pushed_head=B | 比对 A、漏校验或混入其它文件 |
| 范围内 CI 修复 | 新 commit C，合同范围/final diff/必要测试 fresh 验证 | pushed_head=C | 比对 A/B、越范围或验证未通过 |
| 他人改写 | 仍为本会话已验证 C | 不允许自动刷新成未知 X | session/branch 不符、未知改写或 pushed_head=X |

A/B/C/X 为桌面推演标识，实施验收需使用固定不同的 40 位 lowercase 合成 SHA；只证明治理规则判断，不是 broker/runtime 或 remote 事件测试。

## 执行收据

用户已确认完整合同/启动；T01 已应用六份治理文案，与批准 patch 一致，scope guard、git diff --check 和文档检查 PASS。收据为 evidence/t01-governance-apply.json。T02 在用户“下一步”的 fresh turn 已重读新指导。六文件条款审查与17例合成桌面推演 PASS；38项现有定向测试 PASS；Standards/Spec 两轴独立审查均0项发现。sandbox 全量 smoke 因 localhost bind Operation not permitted 中断，已在受控 host 用同一命令重跑，受控 host 重跑 exit=0，978 runtime tests / OK，全部 static smoke checks PASS。

## 判级与流程 GAP

平台 projector 已投影并独立读回 `platform/complex` 为 `projected`；lifecycle 已在合同确认后投影为 `approved`。canonical `triage/*` 写入被 extension writer 拒绝（REQUEST_DENIED），标记 GAP；没有扩大权限或修改 broker。推荐 category=bug/state=ready-for-agent 已记录在 Issue brief，尚未投影成功。

## 受控步骤停止边界

前一运行仅 T01：治理文字应用、范围检查、本地原子提交与收据，并在 head 05e555d441dc8db871454f1e67ce197e1d071eea 停止。用户“下一步”启动本次 fresh T02，先重新读取六份新指导、AGENTS/README/04 与 approved spec/plan，记录 t02-fresh-read.json，再执行验证；无需再次合同确认。push/PR/CI/install/real-model/live/merge/deploy 仍 NOT RUN。

## T02 已执行的验证与边界

- Source/local：六文件 clause evidence 与17例桌面推演 PASS。A/B/C/X 是 a/b/c/d 各重复40次的固定 SHA；恢复首次旧锚时，summary-backfill-new-head 与 in-contract-CI-new-head 被错误停止。详见 evidence/t02-scenarios.json 与 evidence/t02-scenario-review.md。该规则解释器仅用于文案推演，不是实际 broker/runtime，也不是模型行为测试。
- 既有定向回归：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest tests.test_routine_merge.SessionContractTests tests.test_parity tests.test_matt_snapshot -v`：38 tests / OK，日志与收据为 evidence/t02-targeted.log、evidence/t02-targeted-receipt.json。
- 全量回归：`LC_ALL=C PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh`，首次 sandbox exit=1/114.8s，失败点 localhost fixture bind PermissionError。保留 evidence/t02-smoke-sandbox-receipt.json 和压缩日志；未修改 tests/fixture/合同。同一命令受控 host 重跑 exit=0，978 runtime tests / OK，runtime 87.654s；完整 smoke PASS，总耗时 212.14s。日志 evidence/t02-smoke-host.log.gz 与收据 evidence/t02-smoke-host-receipt.json 保留原始结果，首次 sandbox failure 不删除。
- Review：按 code-review 技能并行独立审查；Standards 0项发现、Spec 0项发现，报告为 evidence/t02-code-review.md；范围固定 source base 5c2cd726…T01 head 05e555d4。T02 仅增加映射文档与验证证据，未改批准治理源。
- Installed/live、真实模型、remote push/summary-backfill/CI-repair 事件、merge/deploy：全部 NOT RUN。CI 尚无 PR，不能由本地 smoke 推定 required context 已通过。

## AC 对照与候选边界

| AC | Source/local 证据 | 当前结论 |
|---|---|---|
| AC-1 | 六文件 clause evidence；首次A/回填B/修复C推演；旧锚两项负向 | PASS |
| AC-2 | 17场景覆盖授权、scope、session/branch、未知改写、fresh验证、漏读回及head不匹配 | PASS |
| AC-3 | 六文件等价审查、四场景/负向矩阵、双轴review、38定向与978全量回归 | PASS |
| AC-4 | 保留 sandbox 失败及同命令 host PASS；CI/installed/model/remote events/merge/deploy NOT RUN | PASS（分层报告） |
| AC-5 | T01 已在前轮停止；T02 fresh-read收据；runtime/AGENTS scope guard | PASS |

本地候选准备完成不代表交付。最终提交仍需 exact #320/change/320-push-head-anchor/manual 确认，之后才可 push/唯一 PR/required CI；达到 READY_FOR_REVIEW 后由人合并。canonical triage 投影 GAP 如实保留，不借本 Issue 修改 broker。
