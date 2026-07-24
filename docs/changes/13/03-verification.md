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
status: pending
branch: change/13
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Verification

## 环境与版本

- Commit SHA: 待实现提交
- Artifact: `sync/` versioned source；无应用制品
- Environment: macOS synthetic harness；真实 POC 为 `gitea-ci` / profile `newrsdesign`
- GitHub baseline: `3b147c8777dfc32a745cb27412dec0447e8efcb5`（2026-07-24 实时 `ls-remote`）
- Gitea baseline: `49033a12d14862708fa9c20cfce7c0f974f27d7d`（2026-07-24 实时 `ls-remote`）

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash sync/tests/test-inbound-sync.sh` | NOT RUN | 待实现后填写 |
| `bash sync/tests/test-install.sh` | NOT RUN | 待实现后填写 |
| `bash codex/tests/smoke.sh` | NOT RUN | 待实现后填写 |
| GitHub/Gitea main SHA 读回 | PASS | 上述两个 SHA 与 Issue 声明一致 |
| sync identity 权限读回 | NOT RUN | 尚未配置专用 credential |
| timer enabled/active 状态 | NOT RUN | 尚未安装 POC unit |

## Acceptance criteria 结果

AC-1 至 AC-9 等实现和 synthetic 命令后填写。AC-10 必须把代码验证与真实权限/one-shot 证据分开。

## 重复部署

- 第一次：NOT RUN；隔离目标前缀安装 sync runtime。
- 第二次：NOT RUN；重复安装并比较 manifest；真实 POC 再连续 reconcile 同一 SHA两次。

## 故意失败与回滚

- 失败场景：NOT RUN；synthetic history rewrite/conflicting branch，真实 POC不伪造上游历史。
- 停止/回滚结果：NOT RUN；预期无 push/PR mutation，timer 保持 disabled。
- 数据恢复验证：不适用；仅保留 last-successful/pending 状态文件和 Git cache。

## 遗留风险与未完成项

- 专用 GitHub read-only credential、Gitea bot、分支保护和真实 one-shot POC 需要外部服务权限；缺少任一项不得把 AC-10 标记 PASS。
