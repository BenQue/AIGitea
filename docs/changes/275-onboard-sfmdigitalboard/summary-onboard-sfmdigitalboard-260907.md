---
issue: 275
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/275
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 重新接入一个已退出项目要改两份治理 manifest、重算 NewEMaint routine pilot 的 non-target 防篡改封印、并恢复一个 Gitea project-agent 身份；命中平台治理、agent 治理与安全强制规则。
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-onboard-sfmdigitalboard-260907.md
  spec: spec-onboard-sfmdigitalboard-260907.md
  plan: plan-onboard-sfmdigitalboard-260907.md
  verification: verification-onboard-sfmdigitalboard-260907.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/275-onboard-sfmdigitalboard
pr_url:
created: 2026-09-07
updated: 2026-09-07
---

## 问题/需求总结

#252（PR #256，2026-09-05）把五个项目统一退出平台治理。2026-09-07 用户定案：
**SFMDigitalBoard 单独重新接入**，其余四个保持退出。

该项目仍在活跃交付——仓上 3 个 open 平台对齐 Issue（#110/#111/#112），另有 4 个
功能会话（5 项需求）因无写通道而无法立案。脱离治理后没有 Issue 载体、判级合同
与标签投影通道。

本次是 #252 的**部分回滚**，不是整体 revert。

## 影响范围

两份 manifest 各加一条，`project_count` 由 5 变 6。broker 对外接口不变：操作目录
仍是 36 条、参数集合逐条不变，变的只是 `--project` 可接受的取值集合。

证据收集发现**五处 Issue 正文未预见的花名册耦合**，它们决定了本次变更的真实形状：

1. `codex/tests/test-host-access-broker.sh` 断言「除 `newemaint` 外任何项目都不得
   声明 `git_remote_name` 键」。SFM 的 checkout `origin` 指向 GitHub，必须声明
   `git_remote_name: gitea`，与该断言直接冲突。
2. `codex/tests/test-host-access-broker.sh` 的 `.project_count == 5`。
3. `codex/runtime/tests/test_host_access.py` 的 `len(projects) == 5`。
4. `codex/runtime/tests/test_host_access.py` 的 `gitea_remote_projects = {"newemaint"}`。
5. `codex/runtime/tests/test_gitea_governance.py` 的 `len(repositories) == 5` 与
   private 集合 `{"LocalWMS", "NewEMaint"}`。

其中第 1 项是唯一有语义风险的一处：删掉 SFM 的 `git_remote_name` 也能让测试变绿，
但那会让 `git.push.change` 推到 GitHub 去——**测试绿着失效**。因此改的是断言不是
数据，并把断言强度提高（声明该键的项目集合精确列举，且取值必须都是 `gitea`）。

## 初步方案与建议

A- 轻接入：`vm_profile: null`，不触碰 `contract.py` 被 #252 收紧的 VM profile
仓库集合与 timer 白名单。已用 AC-4 的零 diff 断言机器验证该路线成立。

## 风险

- 两份 manifest 必须同 commit（`contract.py` 强制两者集合相等），分步提交会让
  broker 在中间态对全部项目 fail-closed。
- NewEMaint 封印必须同 commit 重算，否则 governance contract 直接拒绝加载。
- 花名册耦合的断言全部以静默方式失败（`jq -e` 与 `grep -Fq` 失败不打印任何内容），
  只能靠退出码与基线对比定位。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 重新接入一个已退出项目要改两份治理 manifest、重算 NewEMaint routine pilot 的 non-target 防篡改封印、并恢复一个 Gitea project-agent 身份；命中平台治理、agent 治理与安全强制规则。
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 改动 `codex/config/` 下两份治理 manifest → platform-governance 强制 complex
- 重算 `non_target_repositories_sha256` 防篡改封印 → security
- 恢复 `sfm-board-agent` 身份与其 typed 写通道 → agent-governance
- 花名册被五处测试断言共享 → shared-core

### 缺失的 acceptance criteria 或决策

- 无。三项裁决（接入深度 A-、`change_control: development`、routine `false`）
  已由用户在 2026-09-07 对话中定案并写入 Issue 正文。

### 声明 verification 的理由

人工交接项（重装、身份恢复、凭据落盘、`host.onboarding.check` 回读）不能由
diff review 与 required CI 复现，须单独留证。
