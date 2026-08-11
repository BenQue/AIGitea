---
issue: 81
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/81
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 治理文件 AGENTS.md 的目录节恢复为与当前仓库实际结构一致；按强制规则以 complex 流程执行
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-agents-directory-refresh-260811.md
  spec: spec-agents-directory-refresh-260811.md
  plan: plan-agents-directory-refresh-260811.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/81-agents-directory-refresh
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/84
created: 2026-08-11
updated: 2026-08-11
---

## 问题/需求总结

AGENTS.md 是两个 provider 每会话必读的共享合同，但其「## 目录」一节停在早期结构：只列
01–09 与三个 codex 条目。12–15 分册、architecture/、docker-release/、sync/、codex/runtime/、
codex/vendor/、codex/tools/、codex/config/、skill-for-codex/、templates/docs/agents/、archive/
全部缺席，两个「12」分册也无从区分。目录失真直接损害 agent 寻路。

## 影响范围

仅 `AGENTS.md` 的「## 目录」小节。不改工作原则、初始化与开发编排、Git 三节的任何一行。

## 初步方案与建议

按当前仓库一级结构逐项补全；两个「12」用完整文件名区分并注明 Linux 版文件名保留历史提案
名的原因；archive/ 标注「只读参考」。

## 风险

- AGENTS.md 是本次运行正在遵循的治理文件：本 Change 是「只修改治理合同的受控步骤」，
  不含任何 runtime 实施；合并后由后续 fresh run 重新读取。
- smoke 含指令合同静态断言，必须以真实运行结果为准。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 治理文件 AGENTS.md 的目录节恢复为与当前仓库实际结构一致；按强制规则以 complex 流程执行
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 内容本身是文档索引恢复（contract_effect=restore），但目标文件是 `AGENTS.md`，命中
  「修改 AGENTS.md、Agent 行为……一律 complex」的强制规则，不得降级。

### 缺失的 acceptance criteria 或决策

无。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| 目录节覆盖全部一级结构 | PASS | 见 spec AC-1 清单逐项比对 |
| diff 限于「## 目录」小节 | PASS | `git diff` 唯一 hunk 位于 §目录 |
| `bash codex/tests/smoke.sh` | PASS（叠加 #82 修复验证） | 本分支自身运行在已知 #82 缺陷（evidence mode 断言，见 PR #83）处终止；按 #77 先例临时叠加该单行修复后全套通过（`Ran 325 tests … OK` + 静态检查），随后还原并确认 worktree 干净 |
| 远端 CI / 人工合并 | NOT RUN | 平台仓库当前无 required CI context；等待人工合并 |
