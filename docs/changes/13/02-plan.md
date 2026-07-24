---
issue: 13
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/13
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - external-contract
  - authentication-authorization
  - cross-service
  - ci-deployment
depends_on: []
status: contract-ready
branch: change/13
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Implementation plan

## 任务分解

1. 将已确认的 Linux/GitHub→Gitea 目标设计文档纳入 `change/13`，保持“目标设计不等于已实施”状态。
2. 先实现 mock GitHub/Gitea Git 与 REST 的 shell harness，固定 same/new/rewrite/conflict/pending/redaction 预期。
3. 实现 token-file credential helper和 `inbound-sync.sh reconcile`：profile 校验、flock、fetch、ancestry、branch/PR 幂等、pending、原子状态写入。
4. 实现 profile 示例、安装脚本和 disabled systemd service/timer，确保安装幂等且不创建或复制 secret。
5. 把 `bash -n`、ShellCheck 和 synthetic tests 接入平台 smoke，增加禁止 main/mirror/force/merge API 的静态断言。
6. 更新 README、07、12 和 runbook 的实施状态、使用命令、监控、回滚和正式环境迁移边界。
7. 在不启用 timer 的前提下核对真实 `newrsdesign` 两端 SHA和外部身份；有凭据时执行 one-shot POC，无凭据或权限时如实记录 `BLOCKED_EXTERNAL/NOT RUN`。

## 涉及文件

- `12-Linux-GitHub-Gitea-双服务器自动部署方案.md`
- `sync/inbound-sync.sh`
- `sync/git-credential-token-file.sh`
- `sync/install.sh`
- `sync/templates/project.env.example`
- `sync/systemd/aisoft-inbound-sync@.service`
- `sync/systemd/aisoft-inbound-sync@.timer`
- `sync/tests/test-inbound-sync.sh`
- `sync/tests/test-install.sh`
- `codex/tests/smoke.sh`
- `README.md`
- `07-内网与生产平移路线.md`
- `skill-for-codex/references/onboarding-runbook.md`
- `docs/changes/13/`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash sync/tests/test-inbound-sync.sh` 的 profile/path/mode cases |
| AC-2 | mock git argv、临时 config 和 sentinel secret 扫描 |
| AC-3 | rewrite、无共同历史、不合法 SHA cases，断言无 push/API mutation |
| AC-4 | conflicting branch case与静态 forbidden push/API 扫描 |
| AC-5 | same SHA 两次、active PR + new SHA pending cases |
| AC-6 | mock create-PR payload断言 base/head/body provenance |
| AC-7 | stdout/stderr/argv/state 全量 sentinel 扫描 |
| AC-8 | `bash sync/tests/test-install.sh` 连续安装两次并比较 manifest；`systemd-analyze verify` 若可用 |
| AC-9 | `bash sync/tests/test-inbound-sync.sh` + `bash codex/tests/smoke.sh` |
| AC-10 | `git ls-remote` 两端 SHA、Gitea 权限读回、`systemctl is-enabled/is-active` 和 one-shot 实证写入 `03-verification.md` |

## 部署与回滚

本变更只部署同步组件到非生产 POC，且 timer 默认禁用。验收要求安装两次结果一致、手工 reconcile 两次幂等，并故意制造 history rewrite 或冲突分支验证无 mutation。回滚为停止/disable unit、撤销 bot credential、保留 state 和既有 PR审计记录；不删除 Gitea `main` 或应用制品。
