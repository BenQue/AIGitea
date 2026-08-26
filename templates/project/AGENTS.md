# AGENTS.md · <项目名>

<!-- 从 AISoftPlatform templates/project/ 复制后：替换全部 <占位符>，删除本注释。
     前两节是平台常驻指针，除更新事实外不要删改；后两节按项目如实填写。 -->

## 平台声明（常驻指针）

本仓库由 AISoft 平台治理（合同源：`~/MyDocs/AISoftPlatform/`，VM 侧
`/mnt/mac/Users/benque/MyDocs/AISoftPlatform/`；会话内可调用 `aisoft-platform` 技能）。

- 任何需求、缺陷、变更先建 Gitea Issue；Issue `N` 是唯一主键。
- 新变更使用可读元组：分支 `change/N-短描述`、目录 `docs/changes/N-短描述/`、
  文档 `<role>-<短描述>-<YYMMDD>.md`（summary front matter `documents` 映射）、唯一 PR
  `Closes #N`。纯数字名称只有在 Controller 从 manifest-fixed remote 或 Git history 读回
  evidence 后才能读取或维护兼容；新 writer、first push 和 first PR 不得创建。
- 最终 PR merge 仍是唯一交付硬闸门。manual 由人合并；只有平台判定 eligible、仓库显式启用、
  提交确认明确授权且最终 head hard gates 全过的 routine small，才允许独立 per-project merger 合并。
  会话/provider/project agent 自身不 merge、不直推、不擅自部署。
- Gitea/Git 写操作走 host-access broker 的 typed 操作，不拼 raw token、不绕过治理通道。

## 每 Issue 开发路径

`$triage #N` → 映射的 summary → AI 判级。只有范围局部、可简单 revert、有可测验收且不触发
任何强制风险的 small，在 `approved` 复核后才能跳过 spec/plan 直进实现；其余 complex 必须先
`$to-spec #N` → `$to-tickets #N`（plan 的 Txx 依赖图），再经 `approved` 复核后
`$implement #N Txx`。
普通编译/测试/CI 失败自主修复；合同冲突、范围扩张、破坏性迁移、安全决策、三次同因失败
必须停下升级给人。

日常会话默认只有两个确认点：本地实现与验证完成后确认提交唯一最终 PR，并固定 exact
Issue/branch 与 `manual|routine-auto` policy；merge 后完成终态核对、文档检查和 worktree/本地分支
清理，再确认归档。routine 授权允许当前合同内 CI 修复继续，但实际 merge 必须钉住最终 exact SHA。
PR merge 不传递任何部署授权。

## 工具分工（默认偏好，非硬规则）

- **Claude Code（Mac 交互）**：开发与设计——需求澄清、spec/plan、实现、测试、重构。
- **Codex**：维护与部署——headless 分析、运维排障、部署验收。
- 平台 provider 中立：二者共用同一合同，可互换补位；自动化由项目 profile 的
  `ANALYSIS_PROVIDER`/`IMPLEMENT_PROVIDER` 显式选择（默认 `none`）。

## 项目事实（按项目填写）

- 技术栈：<语言/框架/数据库>
- 安装：`<命令>` · 测试：`<命令>` · 构建：`<命令>` · 迁移：`<命令>`
- 健康端点：`<路径>`（返回内容含精确 release SHA）
- **交付形态（按本项目的 delivery profile 决定，平台不强制统一）**：
  <docker-release/v2（参照 NewEMaint）| PM2/tar.gz legacy adapter | Windows/IIS | 其它>；
  流程不变量对所有形态一致：不可变制品、测试与生产同字节晋级、部署前备份、健康检查、
  可回滚、生产 script-only。
- 禁改边界：<受保护路径/数据/配置，如 migrations 历史、.env、生产脚本>
