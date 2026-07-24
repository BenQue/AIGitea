---
issue: 12
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/12
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正合批 PR 的部署状态回写、仓库分支收尾和本地清理工具三个共享自动化合同
risk_flags:
  - platform-governance
  - ci-deployment
  - repository-settings
  - destructive-operations
depends_on: []
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
status: analyzed
branch: change/12
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

## 问题/需求总结

平台从“一 Issue 一 PR”演进到合批 PR 后，三处收尾仍依赖旧假设：部署 workflow 从 merge subject 的 `change/N` 只取一个 Issue；Gitea 仓库未统一启用 merge 后删除源分支；本地清理脚本在 macOS Bash 3.2、`set -u`、空 `REMOVE` 数组且使用 `--apply --branches` 时会在分支清理前退出。结果是非首 Issue 卡在旧生命周期、远端已合并分支持续累积、本地回收需要人工兜底。

## 影响范围

- 新增通用、可复制到接入仓库的 deployed 回写脚本与 mock 回归。
- 新增显式仓库坐标的 Gitea 设置同步脚本，只设置并读回 `default_delete_branch_after_merge=true`。
- 把当前未版本化的 `~/.aigitea/aigitea-cleanup-merged.sh` 收编为仓库内权威源并修复空数组路径。
- 更新 `codex/tests/smoke.sh`、接入 runbook、CI/运维文档。
- 不直接修改 `SFMDigitalBoard`、`rsdesign-new` 或其它应用仓库；它们通过各自 Issue/PR 采用该版本化工具。

## 初步方案与建议

deployed 回写从 merge commit body 中提取所有独立成行的 `Closes #N`，去重后逐项处理；只有正文没有任何匹配时才回退旧的 `change/N` subject。每次 GET 当前 Issue 和仓库 labels，保留 type、complexity 和非生命周期标签，仅把七个生命周期标签替换为 `deployed`，不得硬编码 label ID。回写保持 best-effort：部署成功事实不能因记账 API 失败变红，但日志必须脱敏并给出失败 Issue。

远端分支自动删除由单独脚本对显式 `GITEA_URL/OWNER/REPO` 执行 PATCH 和 GET 读回，禁止全实例隐式遍历。Mac 清理脚本保持 dry-run、无 `-D`、无 `--force`、不清理脏/未合并/活跃 worktree，并增加空数组 regression。

## 风险

- `PUT labels` 若只写 `deployed` 会删除 v3 的 type/complexity 标签，破坏三维标签合同。
- 从任意 `#N` 文本提取会误标 Issue；必须只接受独立成行的 `Closes #N`。
- 把 Gitea token 放到 curl argv 或日志会泄露凭据。
- 自动删远端分支设置会改变合并后的仓库行为，必须显式目标、读回并可关闭回滚。
- 本地清理属于破坏性动作；测试只能在临时仓库运行，默认路径仍必须 dry-run。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修正合批 PR 的部署状态回写、仓库分支收尾和本地清理工具三个共享自动化合同
risk_flags:
  - platform-governance
  - ci-deployment
  - repository-settings
  - destructive-operations
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
  - 03-verification.md
confidence: high
override_reason: ''
```

### 判级证据

- `SFMDigitalBoard/.gitea/workflows/deploy.yml` 当前只从 merge subject 提取一个 `change/N`，并以固定 label ID 替换全部标签。
- `~/.aigitea/aigitea-cleanup-merged.sh` 的 apply worktree 循环直接展开空 `REMOVE[@]`，已在 macOS Bash 3.2 复现 `unbound variable`。
- 当前平台仓库没有版本化的 deployed 回写或仓库设置同步工具。
- 该变更涉及 CI/部署记账、Gitea 仓库设置和删除操作，全部命中强制 complex。

### 缺失的 acceptance criteria 或决策

- 无；保留 type/complexity、best-effort 回写、默认 dry-run 和显式仓库目标已由现有平台合同确定。
