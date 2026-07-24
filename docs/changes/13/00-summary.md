---
issue: 13
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/13
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 GitHub 到 Gitea 的受控入站同步服务、身份边界、状态机和 systemd 运行合同
risk_flags:
  - platform-governance
  - external-contract
  - authentication-authorization
  - cross-service
  - ci-deployment
depends_on: []
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
status: implemented
branch: change/13
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

## 问题/需求总结

当前 GitHub `BenQue/RSDesignNew` 与本地 Gitea `admin/rsdesign-new` 只有一次性 bootstrap 关系，没有版本化、幂等、失败关闭的后续入站同步。实时核对确认 Issue 声明的两端基线仍准确：GitHub `main@3b147c8777dfc32a745cb27412dec0447e8efcb5`，Gitea `main@49033a12d14862708fa9c20cfce7c0f974f27d7d`。两端具有既定共同历史，可以实现 `sync/github/<full-sha>` → 内网 PR 的受控 POC。

## 影响范围

- 新增独立 `sync/` 组件：reconcile 脚本、token-file Git credential helper、profile 模板、安装脚本和 systemd service/timer。
- 新增 synthetic shell 测试，mock GitHub、Gitea Git 与 REST API。
- 把已确认但尚未进入 `main` 的 `12-Linux-GitHub-Gitea-双服务器自动部署方案.md` 纳入本 Issue 分支。
- 更新 README/07/12 的实施状态与回滚边界。
- 真实 POC 仅针对显式 profile `newrsdesign`；不把 rsdesign 设成平台默认值。

## 初步方案与建议

`inbound-sync.sh reconcile <profile>` 读取 mode 400/600 的 `/etc/aisoft-sync/<profile>.env` 和独立 token files，使用 `flock` 与 `/var/lib/aisoft-sync/<profile>/` 状态目录。脚本只 fetch `GITHUB_REF=refs/heads/main`，验证完整 SHA、last-seen ancestry 与 Gitea `main` 的共同历史；分支固定为 `sync/github/<full-sha>`，同名异 SHA、history rewrite、无共同历史全部失败关闭。

每个项目最多一个活跃 sync PR。相同 SHA 的 branch/PR 重跑幂等；已有其它活跃 sync PR 时只写 `pending-sha`，绝不 force-update。GitHub 与 Gitea token 从 600 文件经专用 credential helper/curl stdin 读取，不进入 argv 或日志。systemd unit 默认只安装、不 enable/start。

## 风险

- token 进入 Git/curl argv、xtrace 或失败日志会造成凭据泄露。
- 把 Gitea `main` 当同步目标、允许 force push 或调用 merge API会绕过内网 PR/CI/人工审批。
- last-seen 状态更新时机错误可能把失败同步误记为成功，掩盖 history rewrite。
- 同名远端分支冲突或活跃 PR 被更新会破坏已评审内容的不可变性。
- 真实最小权限需要 Gitea 分支保护和 GitHub repo-scoped read-only credential 的外部配置；代码测试不能替代权限读回。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 GitHub 到 Gitea 的受控入站同步服务、身份边界、状态机和 systemd 运行合同
risk_flags:
  - platform-governance
  - external-contract
  - authentication-authorization
  - cross-service
  - ci-deployment
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
```

### 判级证据

- Issue 明确要求 `complexity/complex`、systemd、外部 GitHub/Gitea 凭据和写分支/建 PR权限。
- 当前仓库没有 `sync/` runtime、profile、systemd unit 或 reconcile tests。
- `origin/docs/linux-github-gitea-deployment@b8d71e5` 只有目标设计且没有 open PR，不能视为已实施。
- 新增外部系统契约、认证授权、跨服务状态机和平台自动化命中多项强制 complex。

### 缺失的 acceptance criteria 或决策

- 无；目标 repo、ref、两端 SHA、安全边界、timer 默认禁用和验证矩阵均已在 Issue 中明确。
