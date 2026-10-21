# AGENTS.md · <项目名>

<!-- 从 AISoftPlatform templates/project/ 复制后：替换全部 <占位符>，删除本注释。
     前两节是平台常驻指针，除更新事实外不要删改；「工具分工」是平台等价原则，原样保留；
     「项目事实」按项目如实填写。 -->

## 平台声明（常驻指针）

本仓库由 AISoft 平台治理。合同源是本仓 `.aisoft/platform-usage.md`（平台使用合同），所用版本以
`.aisoft/platform-usage.lock.json` 的 `bundle_version` 为准；平台仓只是工具与发布包的来源，平台前进
不改变本仓已 pin 的合同。会话内可调用 `aisoft-platform` 技能。

- 任何需求、缺陷、变更先建 Gitea Issue；Issue `N` 是唯一主键。
- 新变更使用可读元组：分支 `change/N-短描述`、目录 `docs/changes/N-短描述/`、
  文档 `<role>-<短描述>-<YYMMDD>.md`（summary front matter `documents` 映射）、唯一 PR
  `Closes #N`。纯数字名称只对已存在的历史对象作读取或维护兼容；新 writer、first push 和
  first PR 不得创建。
- 最终 PR merge 是唯一交付硬闸门，只由人合并。会话与 project agent 自身不 merge、
  不直推受保护 `main`、不擅自部署。
- Gitea/Git 写操作走 host-access broker 的 typed 操作，不拼 raw token、不绕过治理通道。

## 每 Issue 开发路径

`$triage #N` → 映射的 summary → AI 判级。只有范围局部、可简单 revert、有可测验收且不触发
任何强制风险的 small，在 `approved` 复核后才能跳过 spec/plan 直进实现。complex 按 governance
manifest 中本仓的 `change_control`：`production`（未声明时的默认）必须先 `$to-spec #N` →
`$to-tickets #N`（plan 的 Txx 依赖图），再经 `approved` 复核后 `$implement #N Txx`；
`development` 不写 spec/plan，验收标准取自 Issue 正文，`approved` 复核后以合成 `T01` 实现。
普通编译/测试/CI 失败自主修复；合同冲突、范围扩张、破坏性迁移、安全决策、三次同因失败
必须停下升级给人。

日常会话默认只有两个确认点：确认 Issue 合同并开始实现；本地实现与验证完成后确认
提交唯一最终 PR，并固定 exact Issue/branch。merge 后的终态核对、文档检查、
worktree/本地分支清理与归档按确定性流程完成，不再询问。PR merge 不传递任何部署授权。

## 工具分工

Claude Code 与 Codex 共用同一平台合同，能力等价、可互换、不分主辅；两个模型互相取长补短、目标一致，
都不各自发明流程。

## 项目事实（按项目填写）

本节固定为下列条目、不超过 2 KB（`aisoft project-check` 的 `agents-budget` 超出时提示）；其余项目规则写进项目文档，
在「项目规则」条目链接，不在本文件展开。

- 技术栈：<语言/框架/数据库>
- 安装：`<命令>` · 测试：`<命令>` · 构建：`<命令>` · 迁移：`<命令>`
- 健康端点：`<路径>`（返回内容含精确 release SHA）
- **交付形态（由本项目的 delivery profile 与本文件声明和实现，平台不强制统一）**：
  <Linux 容器化 | Linux 原生 | Windows | 其它>；
  流程不变量对所有形态一致：不可变制品、测试与生产同字节晋级、部署前备份、健康检查、
  可回滚、生产 script-only。
- 部署方案位置：<项目内 docs/ 或脚本目录路径>（部署步骤、脚本、参数与环境差异都在此声明与实现；
  平台只给环境级原则，不是部署步骤事实源）
- 发布 producer：`release_producer: <local 或 github>`（一个项目只能一种；local = 本机以钉版本 SDK 容器
  构建并本地测试，github = GitHub Actions 构建候选，适用条件见 onboarding-runbook §4.5）
- 发布传输：`transport: <github-release 或 offline-bundle 或 其它>`（已测试发布包进入公司的介质；
  公司侧只核验校验和与 release SHA 并独立授权部署，GitHub 不进入公司信任链）
- 禁改边界：<受保护路径/数据/配置，如 migrations 历史、.env、生产脚本>
- 选用工具与 required CI：<Claude / Codex / Cursor>；<required status contexts>
- 项目规则：<项目文档链接，如 docs/agents/、docs/adr/、编码规范>
