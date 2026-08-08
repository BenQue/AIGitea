---
issue: 60
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/60
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
depends_on:
  - 57
status: pending-pr
branch: change/60
pr_url:
created: 2026-08-08
updated: 2026-08-08
---

# Matt root instruction verification

## 环境与版本

- Repository: `/private/tmp/aisoft-change-60`
- Branch: `change/60`
- Approved contract head: `2f8f4e84a599c6ffe090f9286d95e2bbb4694d58`
- T01 commit: `bbbdf63`
- T02 commit: `8124dfa`
- Python: `3.14.4`
- ShellCheck: `/opt/homebrew/bin/shellcheck`

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash -n codex/tests/smoke.sh` | PASS | 修改后的 smoke 语法有效 |
| `shellcheck codex/tests/smoke.sh` | PASS | 新增字面 skill/反引号断言无 ShellCheck finding |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s codex/runtime/tests -p 'test_*.py'` | FAIL | 计划原命令缺少 runtime import path；收集 27 个入口，24 个 `ModuleNotFoundError`，未误记为产品回归 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_*.py'` | PASS | 使用仓库 smoke 的既有 import 环境，240 tests 全部通过 |
| `PYTHONDONTWRITEBYTECODE=1 bash codex/tests/smoke.sh` | PASS | 240 tests `OK`，最终输出 `Codex platform static smoke checks passed.`；新增 AC-1–AC-6 断言通过 |
| Docker image-store real E2E | NOT RUN | smoke 只验证既有 harness 的 `NOT RUN` 输出；本 Issue 不启动 Docker daemon 或部署环境 |
| `git diff --check` | PASS | 当前实现无 whitespace error；最终文档提交前后均需重跑 |
| 高置信 Secret pattern scan | PASS | 当前 Issue diff 未命中 private key、GitHub/OpenAI-style key、Authorization token 或长值 credential assignment |
| Gitea Issue #60 authenticated read-back | PASS | 2026-08-08：Issue open；labels 精确含 `approved`、`complexity/complex`、`type/platform` |
| 最终 Gitea PR | NOT RUN | 等待本 T03 提交、push 与唯一 `Closes #60` PR 创建后回填 |

## Acceptance criteria 结果

- AC-1：PASS。根级指令改用语义角色、`documents` 映射与新 basename；四个数字 basename 只读兼容。
- AC-2：PASS。两份指令均路由到 `$aisoft-matt-workflow`、`$setup-matt-pocock-skills`、tracker `Other` 与三份既有模板。
- AC-3：PASS。两份指令均固定 Matt 四步主路径，并保留 small 的 summary/classification/`approved` gate。
- AC-4：PASS。四个 `gitea-*` 开发 skill 仅为兼容 adapter；`gitea-platform-ops` 保持独立运维职责。
- AC-5：PASS。Agent local commit、Controller push/PR/CI、human merge、独立部署授权与 `IMPLEMENT_PROVIDER=none` 均有静态断言。
- AC-6：PASS。`triage/ready-for-agent` 与 `approved` 分离；auto-merge、protected-main push、force-push、静默全局 skill 更新、越权 live 标签与部署均被禁止。
- AC-7：PASS。focused syntax/ShellCheck、修正 import path 后的 240-test suite、完整 smoke、diff 与 Secret 检查通过；原始 Python 入口失败单独保留。
- AC-8：PENDING。实现验证完成；尚待创建唯一最终 PR 并停止在人工 merge gate。

## 未运行与独立门禁

- 用户级或 VM live Matt skills 安装、更新或删除：`NOT RUN`。
- live triage labels provision/read-back、runtime/Controller 修改、provider 启用或 timer 启动：`NOT RUN`。
- PR merge：`NOT RUN`，只允许人工操作。
- Deployment：`NOT RUN / NOT APPLICABLE`，本 Change 不部署应用或生产环境。

## 回滚

- 人工 revert 最终 PR；Issue #57 已合并的 runtime、vendor snapshot、adapter 和 legacy reader 不回滚。
- 本 Change 未修改 live skills、labels、provider、timer 或部署环境，因此没有外部运行态回滚动作。

## 遗留风险

- Gitea required CI 与最终 PR 状态必须在 PR 创建后只读回查；未配置或未运行的 context 不得写成通过。
