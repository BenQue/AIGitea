---
issue: 290
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/290
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - deployment
status: approved
branch: change/290-scm-test-deploy
created: 2026-09-11
updated: 2026-09-11
---

# 计划

| Ticket | blocked_by | 内容 | 验收 |
|---|---|---|---|
| T01 | [] | 独立合同与说明调整，提交后停止 | AC-5 |
| T02 | [T01] | 下一轮重读合同，实现scm-ci/test条件及矩阵/生命周期测试 | AC-1–4 |
| T03 | [T02] | 回归、diff审查、唯一manual PR确认 | AC-1–5 |
| T04 | [T03] | 用户批准方案 B；独立治理合同增补，提交后停止 | AC-6–7 |
| T05 | [T04] | fresh run 重读；固定历史/当前范围检查器、正反例、offline 回归与 smoke 接入 | AC-1–7 |
| T06 | [T05] | focused/full 回归，更新同一 PR，最终 exact head required CI 验收 | AC-1–7 |

T01不实施runtime；T02无需重复询问本次已明确的行为选择。不得在T01改AGENTS。

预期验证：PYTHONPATH=codex/runtime:. python3 -B -m unittest discover -s codex/runtime/tests -p 'test_release*.py'；矩阵须有production零副作用反例。semantic docs check、git diff --check。无shell修改则不增加shell专项。
source可Git revert；部署/数据库回滚不由该source变更执行。现场始终NOT RUN直到独立回执。

## 执行读回（2026-09-11）

- T01：PASS，独立合同提交 `7590643`，原任务已停止。
- T02：PASS，新任务重读后完成，本地 commit `b2cc0a3`；生产仍拒绝，测试例外与失败路径已本地验证。
- T03：本地 107 项回归、文档检查、diff 审查 PASS；用户已确认提交，唯一 manual PR #291 已开放。
  远端 required CI 因历史 #65 runtime 范围闸门 FAIL，精确原因见 verification。
- T04：用户已明确“同意方案 B”，本轮只落地 spec/plan/summary/verification 增补并停止。
- T05/T06：NOT RUN，交由 fresh run 按本次批准继续；不重新询问 push/PR 授权。

## T05/T06 实施与验证步骤

1. 读取本 spec 的固定 baseline、exact 六行 runner 修订、hash 和文件范围。检查器拒绝未知路径/
   字节/模式、symlink、ignored 文件及 baseline 缺失，不接收 caller override。
2. 从本地 Git object 创建固定历史临时 clone，仅跑原 fake harness；旧 real harness/evidence/
   matrix 原字节保持。检查当前范围在子进程与当前测试前后均执行。
3. 新增 checker 正例与负例：runner 额外一字节、production/unknown action 放行、其它 runtime/
   transport 漂移、新增/删除/改名/执行位/symlink/ignored .py/.pyc、matrix/evidence/harness/
   fixture 漂移、baseline 缺失、执行中 drift。验证任一子检查或测试失败均导致整体失败，无 fallback。
4. 补充 scm-ci/test offline-bundle 部署、幂等和失败回滚；原 Registry、角色矩阵、生产拒绝保持。
5. 执行 focused checker 测试及 `PYTHONPATH=codex/runtime:. python3 -B -m unittest discover -s codex/runtime/tests -p 'test_release*.py'`。
6. 执行新 checker 的完整 fake/history/current 路径；执行 `bash -n codex/tests/smoke.sh`、
   ShellCheck（可用时）、`bash codex/tests/smoke.sh`、check-change-documents、git diff --check。
7. 再核对旧 evidence hash。通过后本地原子提交，并经 broker 更新唯一 #291；最终 exact head 的
   required context 通过才 READY_FOR_REVIEW，manual 合并保留给人。

新检查器与测试必须在当前 checkout 执行，历史 fake 回归不能代替当前行为验收；当前 real Docker、
installed/company-live 继续 NOT RUN。测试失败时按已批准范围修复，无理由不重复整套验收。
