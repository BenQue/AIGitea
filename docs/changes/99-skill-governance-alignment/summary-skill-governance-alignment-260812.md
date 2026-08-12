---
issue: 99
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/99
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 Claude/Codex 技能、项目指针模板、漂移验证和 #89 CI 记录对现行平台合同的一致性
risk_flags:
  - agent-governance
  - ci-change
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-skill-governance-alignment-260812.md
  spec: spec-skill-governance-alignment-260812.md
  plan: plan-skill-governance-alignment-260812.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/99-skill-governance-alignment
pr_url:
created: 2026-08-12
updated: 2026-08-12
---

## 问题/需求总结

2026-08-12 review 发现 Claude skill 直接指导 `git fetch && git rebase`、Codex runbook 仍写新
`change/N`、项目模板遗漏 small 前置、Claude drift 只做单向内容比较，以及 #89 把 runner 前置
PASS 与首次远端 CI 状态混写。这些均偏离 #57/#60/#61/#75 与当前 AGENTS 合同。

## 影响范围

- Claude skill 的 broker 与部署边界。
- Codex onboarding runbook 的 readable 消费路径。
- 项目 `AGENTS.md` 常驻指针模板。
- Claude skill exact installer、双向 drift 与临时 HOME tests。
- #89 历史验收记录的事实分层。

## 初步方案与建议

恢复 typed broker 与 readable tuple；补全 small 直进条件；让 Claude 安装目标成为 exact managed
tree，unexpected/missing/content drift 均 fail closed；明确 #90 final head 的首次 CI 为 FAIL，同时
保留 required-context 三件套后续边界。

## 风险

涉及 Agent 治理与安装器，强制 complex。installer 只管理固定 skill 子树，拒绝 symlink target，
不读取凭据；测试只使用 `mktemp` HOME。合并前不重装任何 live skill。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 Claude/Codex 技能、项目指针模板、漂移验证和 #89 CI 记录对现行平台合同的一致性
risk_flags:
  - agent-governance
  - ci-change
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 修改 Agent skill、共享项目模板和 CI 验收语义，命中强制 complex。
- 用户已逐项批准范围；本 Change 的 spec 明确授权治理文件。

### 缺失的 acceptance criteria 或决策

无。

## 验收结果

| 检查项 | 结果 | 证据 |
|---|---|---|
| broker/readable/deployment 文本 | PASS | direct fetch/rebase 与 NewEmaint `change/N` 残留 absent；模板前置齐全 |
| drift negative fixtures | PASS | missing/content/unexpected + exact reinstall；symlink target fail closed |
| `bash -n` / ShellCheck | PASS | 3 个修改 shell/test 脚本 0 findings |
| `bash codex/tests/test-install-claude-skills.sh` | PASS | 临时 HOME；success 输出一次 |
| `bash codex/tests/smoke.sh` | PASS | 325 tests OK；static smoke passed |
| live Codex/Claude skill reinstall | NOT RUN | 只在本 PR 人工合并后分别执行 |
| PR final-head CI | PENDING | push/PR 后真实读回 |
| 合并/部署/标签/required-context | NOT RUN | 明确不授权 |
