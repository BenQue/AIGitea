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
status: verified-local
branch: change/13
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Verification

## 环境与版本

- Commit SHA: 本分支最终实现提交（PR 创建前回填）
- Artifact: `sync/` versioned source；无应用制品
- Environment: macOS synthetic harness；真实 POC 为 `gitea-ci` / profile `newrsdesign`
- GitHub baseline: `3b147c8777dfc32a745cb27412dec0447e8efcb5`（2026-07-24 实时 `ls-remote`）
- Gitea baseline: `49033a12d14862708fa9c20cfce7c0f974f27d7d`（2026-07-24 实时 `ls-remote`）

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash sync/tests/test-inbound-sync.sh` | PASS | 临时 GitHub/Gitea bare repos + mock API 覆盖 same/new/pending、API failure、conflict、history rewrite、profile mode 与 secret scan |
| `bash sync/tests/test-install.sh` | PASS | 连续安装两次 manifest 一致，timer 无 enable symlink，systemd hardening 读回 |
| `bash -n sync/*.sh sync/tests/*.sh` | PASS | runtime、helper、installer 和 tests 语法通过 |
| `shellcheck sync/*.sh sync/tests/*.sh` | PASS | 当前环境 ShellCheck 无诊断 |
| `bash codex/tests/smoke.sh` | PASS | sync tests、98 个 Python runtime 测试及全部 static smoke 通过 |
| GitHub/Gitea main SHA 读回 | PASS | 上述两个 SHA 与 Issue 声明一致 |
| sync identity 权限读回 | NOT RUN | 尚未配置专用 credential |
| timer enabled/active 状态 | NOT RUN | 尚未安装 POC unit |

## Acceptance criteria 结果

- AC-1 至 AC-9：synthetic、语法、ShellCheck 和 smoke 均通过。
- AC-10：两端 baseline SHA 已实时读回；真实 bot 权限、timer 状态和 one-shot 因凭据与目标 Linux 环境未授权保持 NOT RUN。

## 重复部署

- 第一次：PASS（synthetic）；新 SHA 创建一个 immutable branch 和一个 mock PR。
- 第二次：PASS（synthetic）；相同 SHA 复用已有 branch/PR，不重复创建；安装 manifest 也保持一致。

## 故意失败与回滚

- 失败场景：PASS（synthetic）；GitHub history rewrite、conflicting branch 和 API failure。
- 停止/回滚结果：PASS（synthetic）；均在 push/PR mutation 前失败，既有 branch/PR/state 审计保留。
- 数据恢复验证：不适用；仅保留 last-successful/pending 状态文件和 Git cache。

## 遗留风险与未完成项

- 专用 GitHub read-only credential、Gitea bot、分支保护和真实 one-shot POC 需要外部服务权限；缺少任一项不得把 AC-10 标记 PASS。
- 本 PR 不 enable timer、不创建 credential、不写或合并任何应用 `main`。
