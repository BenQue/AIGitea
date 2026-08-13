---
issue: 111
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/111
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复对象是 5 个平台治理/运维工具的凭据消费合同（新增 GITEA_TOKEN_FILE 形态、内联形态弃用提示、集中式 token 解析、漂移防护检查、运维手册升级顺序规则），触及认证/凭据路径与共享核心组件，属平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - credential-handling
  - shared-core
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-profile-token-file-260813.md
  spec: spec-profile-token-file-260813.md
  plan: plan-profile-token-file-260813.md
confidence: high
override_reason: ''
depends_on: []
status: ready-for-review
branch: change/111-profile-token-file
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/114
created: 2026-08-13
updated: 2026-08-13
---

## 问题/需求总结

四个已接入项目的 VM profile 已按 #61/#70 合同迁移为 `GITEA_IDENTITY` +
`GITEA_TOKEN_FILE`，但 `codex/tools/` 下 5 个平台工具仍只认内联 `GITEA_TOKEN`：
`aisoft-project-check.sh`、`ensure-gitea-collaborator.sh`、`mark-deployed-issues.sh`、
`sync-gitea-labels.sh`、`sync-gitea-repository-settings.sh`。后果是 #106 刚交付的
`aisoft-project-check --remote` 两项远程检查对每个已迁移项目全部 GAP
（`远程配置缺失: GITEA_TOKEN`）。根因是 #106 与 #107 并行推进后「profile 合同前进、
消费者适配未跟上」，且 #107 只修了当时报错的一个消费者（`gitea-readonly.sh`），
未扫全剩余消费者。同批次还暴露了「共享消费者 + 逐项目迁移」的升级顺序依赖
（`common.sh` 收紧后未迁移项目 Loop 立即失败）。

## 影响范围

仅平台仓库：上列 5 个工具、新增共享 token 解析库（`codex/agent/gitea-token.sh`，
随 `install-vm.sh` 既有 `codex/agent/*.sh` 通配安装进 VM，不改安装脚本）、对应
`codex/tests/test-*.sh` 与 `smoke.sh` 接入、新增漂移防护测试、
`06-运维手册与踩坑集.md` 新增升级顺序规则。不修改 AGENTS.md、broker manifest、
CI workflow、`install-vm.sh`，也不重构已适配的 `gitea-readonly.sh` 与
`codex/agent/common.sh`。

## 初步方案与建议

1. 新增共享解析库 `codex/agent/gitea-token.sh`：优先 `GITEA_TOKEN_FILE`
   （非符号链接常规文件 + mode 400/600 + 非空 + 字符集校验，任一违规 fail closed、
   不回退），过渡期回退内联 `GITEA_TOKEN` 并向 stderr 输出弃用提示；两者皆无返回
   独立返回码由调用方按各自合同处置。token 值只进变量与 curl stdin config，
   不进 argv/日志/输出。
2. 5 个工具以双候选路径 source 该库（同目录扁平安装布局优先，仓库布局
   `../agent/` 回退），逐工具保持既有退出合同（project-check 记 GAP、
   mark-deployed 警告后 exit 0、其余 fail fast；collaborator 保持
   `GITEA_BOT_TOKEN` → 解析库 → credential file 的回退链）。
3. 漂移防护：新增全仓扫描测试，断言凡引用内联 `GITEA_TOKEN` 的脚本必须同时
   支持 `GITEA_TOKEN_FILE` 或 source 共享库。
4. `06-运维手册与踩坑集.md` 踩坑集新增 🕳️19：共享消费者 + 逐项目迁移的
   升级顺序规则（先迁完全部 profile 再收紧共享消费者，或消费者过渡期双形态）。

## 风险

- 触及 5 个治理/运维工具的凭据路径：以「解析集中一份 + 每工具两种形态与
  fail-closed 测试 + sentinel 防泄漏断言」控制；单 PR revert 即完整回滚，
  无状态残留。
- `ensure-gitea-collaborator.sh` 存在 VM 扁平安装布局：共享库落点选
  `codex/agent/`，被 `install-vm.sh` 既有通配自动覆盖，不改安装脚本；
  双候选 source 兼容两种布局。
- 内联形态弃用提示写入 stderr，可能出现在既有调用方日志中：属预期的迁移
  信号，不改变退出码与 stdout 机器可读输出。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修复对象是 5 个平台治理/运维工具的凭据消费合同（新增 GITEA_TOKEN_FILE 形态、内联形态弃用提示、集中式 token 解析、漂移防护检查、运维手册升级顺序规则），触及认证/凭据路径与共享核心组件，属平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - credential-handling
  - shared-core
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- 受影响 5 工具均为平台治理/运维写路径或检查器（标签写入、仓库设置 PATCH、
  协作者权限治理、生命周期标签变更、对齐检查器），修改其凭据消费合同命中
  AGENTS.md 强制规则「认证/权限/安全」与「Agent 或平台治理变更一律 complex」。
- AC-3 要求 token 解析集中为共享实现供全部工具复用，命中「共享核心组件」。
- AC-5 修改 `06-运维手册与踩坑集.md` 治理文档，需 complex spec 显式授权。
- 证据核对（origin/main 387ac5d）：`aisoft-project-check.sh:177`、
  `sync-gitea-labels.sh:34`、`mark-deployed-issues.sh:9`、
  `sync-gitea-repository-settings.sh:12` 将 `GITEA_TOKEN` 列为必需；
  `ensure-gitea-collaborator.sh:147` 仅在 bot_token 回退链读内联。全仓扫描
  确认 shell 侧内联消费者仅此 5 个（`gitea-readonly.sh`、`common.sh` 已适配，
  `sync/inbound-sync.sh` 本就只认 `GITEA_TOKEN_FILE`）。

### 缺失的 acceptance criteria 或决策

- AC-2 的四项目真实读回依赖 VM 环境与已迁移 profile；本变更在 Mac 侧以等价
  fixture 覆盖判定逻辑（remote-ready 闸门只取决于 env 形态），实测读回由合并
  后的运维会话复核（见 plan 部署节）。

## 状态记录

- 2026-08-13：判级评论已发（Issue #111 comment 3046）；spec/plan 完成，进入
  ready-for-review。标签投影（complexity/complex + type/bugfix 等）属
  controller/projector 职责，Mac 会话 broker 无标签 typed 操作，未在本会话执行。
- 2026-08-13（交付）：T01–T04 完成；`bash codex/tests/smoke.sh` 全绿（Python 运行时
  335 用例 OK）；漂移防护负向自测通过（canary 被点名后移除）。最终 PR #114 已创建
  （head b2fe9dc），停在人工合并。
