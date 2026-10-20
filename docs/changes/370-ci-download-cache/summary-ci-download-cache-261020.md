---
issue: 370
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/370
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改平台仓 CI workflow 与必需检查里的 PAT helper 构建脚本，给共享 runner 引入持久下载缓存与站点级 actions 镜像，属于 CI、跨站点基础设施与平台治理文件变更
risk_flags:
  - ci-change
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-ci-download-cache-261020.md
  spec: spec-ci-download-cache-261020.md
  plan: plan-ci-download-cache-261020.md
  verification: verification-ci-download-cache-261020.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/370-ci-download-cache
pr_url:
created: 2026-10-20
updated: 2026-10-20
---

## 问题/需求总结

平台仓必需检查 `CI / verify (pull_request)` 每次都实时访问三处外网：`actions/checkout@v4` 从 GitHub 克隆、PAT helper 测试从 `go.dev/dl` 下载 Go 工具链、`go` 从 `proxy.golang.org` 拉模块。2026-10-17 三处各断过一次（run 1914、job 2129、run 1921/job 2137），代码步骤本身没问题，只能人工 Re-run。合同与验收见 spec。

## 影响范围

- `.gitea/workflows/ci.yml`（治理文件）：checkout 改用本站 Gitea 镜像并钉 commit SHA；PAT helper 步骤传入持久缓存目录。
- `codex/tests/test-gitea-pat-helper-linux.sh`：工具链归档与 Go 模块走可选持久缓存，命中前后都按既有 pin 校验；下载加有限重试；构建与测试在 `GOPROXY=off` 下离线运行。
- `codex/tests/test-gitea-pat-helper-linux-gates.sh`：补缓存命中、缓存被篡改两个黑盒场景。
- `01-基础设施-VM-Gitea-Runner.md` §4：记 as-built 与回滚。
- 站点侧一次性前置（负责人执行）：本站 Gitea 建公开组织 `actions` 与 GitHub `actions/checkout` 的拉取镜像。

## 初步方案与建议

见 spec。缓存放在 runner 用户自己的 `$HOME/.cache/aisoft-ci`，不需要 sudo、不改 act_runner 配置、不改 Gitea `app.ini`。

## 风险

- act_runner 1.0.7 对 `uses:` 写完整 `http://` URL 的支持要靠真实 CI 运行证实；不支持时停下来报，不自行改 runner 配置。
- 冷缓存第一次仍需外网，这一点写进 as-built，不伪称已离线。
- 工作流里出现站点 Gitea 地址，与并行中的 R13（站点外置守卫）有交集，合并顺序在 PR 阶段核对。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改平台仓 CI workflow 与必需检查里的 PAT helper 构建脚本，给共享 runner 引入持久下载缓存与站点级 actions 镜像，属于 CI、跨站点基础设施与平台治理文件变更
risk_flags:
  - ci-change
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`「判级与确认」：CI/制品/部署/回滚、平台治理一律 complex；`.gitea/workflows/ci.yml` 属治理文件。
- 验收证据（断网时缓存命中、runner 上真实运行）不能由 diff review 与 required CI 复现，故追加 `verification`。

### 缺失的 acceptance criteria 或决策

- 无。镜像命名与缓存位置的默认取法写在 spec，确认点 1 可调整。
