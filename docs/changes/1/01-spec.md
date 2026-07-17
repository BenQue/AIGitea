---
issue: 1
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/1
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - security
status: contract-drafting
branch: change/1
pr_url:
created: 2026-07-17
updated: 2026-07-17
---

# Spec

## 目标与原因

让 Claude Code 以 **provider adapter** 的身份接入既有的 provider-neutral Loop runtime，与 Codex 达成 parity。

平台已经把接缝切在进程边界上：`CommandProvider` 接受任意 argv，用私有临时文件交换严格 schema 的 request/result JSON。因此接入 Claude 不需要第二套外层——controller、合同校验、状态与锁、worktree、Git/Gitea adapter、deterministic verifier、标签状态机和四种终态全部复用。

本变更的价值在于消除单 provider 依赖，并把「Claude 分析路径只存在于 VM、不在中央 source」这个既有缺口补上。

## Acceptance criteria

- [ ] AC-1 `docs/changes/1/00-summary.md`、`01-spec.md`、`02-plan.md` 存在并关联 Issue 1，实现开始前已提交到 `change/1`。
- [ ] AC-2 本 spec 逐项列出并显式授权本次允许改动的 Agent、provider、路由、skills 与治理文件；未列入清单的治理文件不得改动。
- [ ] AC-3 Claude 与 Codex 使用同一 project-profile fixture、controller、verifier、state schema、lock 模型、Git/Gitea mutation、标签集合与终态集合；runtime 中不存在 provider 专属的状态机分支。
- [ ] AC-4 Claude adapter 的输出通过与 Codex 完全相同的 `ProviderResult.from_json` 严格 schema 校验与 `_validate_changed_path` 路径校验，非法输出以 `ProviderError` 失败而不是被容忍。
- [ ] AC-5 共享 parity 测试覆盖八种情形：成功、verifier 反馈、CI 反馈、范围扩张、外部阻塞、同根因三次上限、总轮数上限、token 脱敏；并断言 adapter 不执行任何 merge 或 deploy 操作。
- [ ] AC-6 可执行 runtime 与 fixture 中不含 rsDesign 的仓库名、端口或部署脚本默认值，由 `codex/tests/smoke.sh` 既有的 rsdesign 禁令断言覆盖新增文件。
- [ ] AC-7 `IMPLEMENT_PROVIDER` 默认值在 `templates/agent/project.env.example` 与 `provider-poll.sh` 中均保持 `none`；安装脚本不 enable 或 start 任何 timer，不生成 profile。
- [ ] AC-8 active Issue 不存在自动 provider 回退：一个 Issue 的 provider 切换必须显式指定，且在切换前状态已结束或已迁移，测试对此有断言。
- [ ] AC-9 Claude 与 Codex 的配置与认证保持独立：Claude 认证只经由 `HOME` 指向的 `~/.claude` 生效，不复制 token，不透传凭据类环境变量；`~/.codex/` 既有配置不被删除或覆盖。
- [ ] AC-10 `bash codex/tests/smoke.sh`、Python 单元测试、`bash -n`、可用时的 ShellCheck、安装幂等性与 token 泄漏检查全部通过，并记录真实输出。
- [ ] AC-11 VM 安装以禁用模式验证：不复制凭据、不启动 timer，两次安装 manifest 一致。
- [ ] AC-12 回滚方式被记录并被证明：把 implementation provider 改回 `none` 即可回滚，且不影响分析、CI、制品与应用部署。
- [ ] AC-13 工作止于 `READY_FOR_REVIEW`；adapter、controller 与 CI 均不合并 PR，合并仍是人的动作。
- [ ] AC-14 中央 source 提供被跟踪的 Claude analyzer 入口，`provider-poll.sh` 不再引用任何未跟踪的脚本；`install-vm.sh` 能完整安装 Claude 路径所需的全部文件。
- [ ] AC-15 Claude adapter 被禁止使用绕过审批的参数，`codex/tests/smoke.sh` 对 `--dangerously-skip-permissions` 的禁令断言存在并通过。

## 接口、数据与兼容性影响

**provider 接缝（不变）**：request/result JSON schema、字段集合、`changed_files` 路径规则、私有临时文件与 0600 权限均不变。Claude adapter 复用同一契约。

**新增的显式授权改动清单**（AC-2 的落点）：

| 文件 | 改动 | 理由 |
|---|---|---|
| `codex/agent/claude-provider.sh` | 新增 | Claude implementation adapter |
| `codex/agent/claude-analyzer.sh` | 新增 | Claude analyzer adapter |
| `codex/agent/analyze-claude.sh` | 新增 | Claude 分析编排入口，取代未跟踪的 `analyze.sh` |
| `codex/agent/provider-poll.sh` | 修改 | 放开 implementation 路由；改调被跟踪的分析入口 |
| `codex/runtime/aisoft_loop/cli.py` | 修改 | 按 `IMPLEMENT_PROVIDER` 选择 adapter |
| `codex/runtime/aisoft_loop/provider.py` | 修改 | 环境变量白名单增加 Claude 模型变量 |
| `codex/install-vm.sh` | 修改 | 安装 Claude 路径所需文件 |
| `CLAUDE.md` | 新增 | 被跟踪的 Claude 入口，仅声明对共享规范源的导入 |
| `codex/tests/smoke.sh` | 修改 | parity gate 断言与危险参数禁令 |
| `codex/tests/test-agent-runtime.sh` | 修改 | parity gate 回归 |
| `codex/runtime/tests/` | 新增/修改 | parity 测试 |
| `templates/agent/project.env.example` | 修改 | 注释说明 provider 取值 |
| `04`、`08`、`README` | 修改 | 记录 parity 状态 |

**兼容性**：`CODEX_PROVIDER_SCRIPT` 环境变量继续被识别，既有 VM 安装不因本变更失效。`IMPLEMENT_PROVIDER=codex` 的行为逐字节不变。

**数据**：无 schema、无迁移、无历史数据影响。

## 风险与回滚约束

- 本次变更不得修改仓库根 `AGENTS.md`、controller、contract、state、verifier、gitea、classification 的既有行为，也不得改动 CI、部署脚本或生产环境。
- 授权清单之外的治理文件不得改动。
- parity 测试未全绿前，`provider-poll.sh` 的 implementation 路由不得放开。
- 回滚边界：`IMPLEMENT_PROVIDER=none` 即完全停用 Claude implementation，analyzer、CI、制品与部署不依赖 Loop，因此回滚无外溢。
- 既有 Claude/Codex 认证、旧脚本与 skills 在另行批准前不得删除。

## 非目标

- 把 AISoftPlatform 作为应用部署。
- 启用生产部署工作流。
- 让 Claude 成为长期默认 provider。
- 在另行批准前删除 Codex 或遗留 Claude 的凭据与脚本。
- 为 rsDesign 或任何具体应用加入专属行为。
- 修改 Claude Code 侧的 skills 内容以形成第二套合同；skills 只引用共享平台合同。

## 未决问题

无。

VM 上遗留的 Claude 入口形态曾是候选未决项，现已由项目原则决定：凡共享物必须是 Gitea 中被跟踪的中央 source，因此中央仓库提供被跟踪的 Claude analyzer 入口，VM 上未跟踪的同名脚本按遗留物取代。凭据不在此列，仍只存在于 mode-600 文件中。对 `/home/coder/` 的只读盘点是执行期的核对动作，记录在 `02-plan.md` 任务 1，不改变上述方向。
