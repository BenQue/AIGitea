---
issue: 81
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/81
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: contract-drafting
branch: change/81-agents-directory-refresh
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Spec

## 目标与原因

把 `AGENTS.md`「## 目录」一节恢复为当前仓库实际结构的完整索引。该节自早期结构后未更新，
缺失大半个仓库；AGENTS.md 是两个 provider 的每会话合同，索引失真即寻路失真。

## Acceptance criteria

- [ ] AC-1 目录节包含以下条目（名称精确存在于仓库）：`12-Linux-GitHub-Gitea-双服务器自动部署方案.md`、`12-Windows平台自动部署方案.md`、`13-项目结果迁移与内网切换实施手册.md`、`14-Windows部署与迁移验收清单.md`、`15-VMware-Fusion-Windows-ARM原型实施手册.md`、`architecture/`、`docker-release/`、`sync/`、`codex/runtime/`、`codex/vendor/mattpocock/`、`codex/tools/`、`codex/config/`、`skill-for-codex/`、`templates/docs/agents/`、`archive/`。
- [ ] AC-2 两个「12」分册以完整文件名区分，且不重命名任何文件。
- [ ] AC-3 `git diff` 中 `AGENTS.md` 的变更 hunk 全部位于「## 目录」小节；工作原则、
      初始化与开发编排、Git 三节零变更。
- [ ] AC-4 `bash codex/tests/smoke.sh` 真实运行通过。

## 接口/数据/兼容影响

无 runtime、schema、API、部署影响；纯治理文档索引。

## 治理授权

本 spec 明确授权修改的治理文件：仅 `AGENTS.md`（限「## 目录」小节）。本 Change 是独立的
「只修改治理合同的受控步骤」，不实施任何 runtime；合并后的规则由后续 fresh run 读取生效。

## 非目标

- 不修改 AGENTS.md 其它章节；不重命名/合并任何分册；不更新 README 导航（已是全的）；
  不安装或部署任何组件。
