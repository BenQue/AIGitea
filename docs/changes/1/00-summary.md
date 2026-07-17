---
issue: 1
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/1
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 Claude Code provider adapter 并改动 provider 路由与 Agent 治理文件，命中强制复杂规则
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - security
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
status: analyzed
branch: change/1
pr_url:
created: 2026-07-17
updated: 2026-07-17
---

## 问题/需求总结

平台已具备 provider-neutral 的 Loop runtime：controller、合同校验、状态与锁、worktree、Git/Gitea adapter、deterministic verifier、标签状态机和四种终态都不含 provider 专属逻辑。Codex adapter 已通过 synthetic 套件、project-profile 隔离、VM 禁用式安装和一个明确限定的 real complex pilot。

当前只剩 Claude Code 一侧没有接入：Claude 只能作为 provider adapter 复用同一外层，不得复制第二套状态机、标签逻辑或终态判断。本 Issue 追踪这一次 parity 接入。

本仓库是平台的 control repository，不是应用部署目标；rsDesign 只是历史 pilot 证据，不得成为默认仓库、端口、verifier 或部署合同。

## 影响范围

- `codex/runtime/aisoft_loop/cli.py`：目前把 implementation provider 硬编码为 `codex-provider.sh`，无 provider 选择。
- `codex/runtime/aisoft_loop/provider.py`：环境变量白名单只透传 `CODEX_MODEL`。
- `codex/agent/provider-poll.sh`：显式拒绝 `IMPLEMENT_PROVIDER=claude`（parity gate），并调用中央 source 中不存在的 `analyze.sh`。
- `codex/agent/`：缺少 Claude 侧的 analyzer 与 provider adapter 脚本。
- 仓库根：缺少被跟踪的 Claude 入口，无法消费共享规范源。
- `codex/tests/smoke.sh`、`codex/tests/test-agent-runtime.sh`：parity gate 被两处断言钉死；危险参数禁令只覆盖 Codex。
- 文档：`04`、`08`、`README` 需要记录 parity 状态。

不受影响：controller、contract、state、verifier、gitea、classification 的既有行为；CI；制品；应用部署。

## 初步方案与建议

在既有 provider 接缝后面新增一个 Claude adapter 进程，不新增第二套外层：

1. 先盘点 VM 上真实的 Claude 入口与配置边界（只读，不打印凭据）。
2. 补齐中央 source 的 Claude analyzer 入口，消除 `provider-poll.sh` 对未跟踪脚本的依赖。
3. 新增 `claude-provider.sh`，满足与 Codex 完全相同的 provider result JSON schema 与 changed-path 校验。
4. 让 `cli.py` 按 `IMPLEMENT_PROVIDER` 选择 adapter，保留 Codex 既有环境变量兼容。
5. parity 测试全绿后，才放开 `provider-poll.sh` 的路由。
6. 默认仍为 `IMPLEMENT_PROVIDER=none`。

## 风险

- **治理风险**：改动 provider 路由与 Agent 行为文件，必须由 spec 逐项显式授权。
- **假 parity**：Claude adapter 若绕过 verifier 或自述通过，会制造假绿；外层必须继续独立验证。
- **凭据串味**：Claude 与 Codex 的配置与认证必须保持独立，任一方的配置不得被删除或覆盖。
- **默认漂移**：放开路由后若默认值意外变成 `claude`，等于未经批准启用 Loop。
- **provider 回退**：active Issue 上自动在 provider 间回退会破坏状态一致性，必须禁止。
- **pilot 泄漏**：rsDesign 的仓库、端口或部署脚本不得进入通用 runtime 或 fixture。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 Claude Code provider adapter 并改动 provider 路由与 Agent 治理文件，命中强制复杂规则
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - security
required_docs:
  - 00-summary.md
  - 01-spec.md
  - 02-plan.md
confidence: high
override_reason: ''
```

### 判级证据

- Issue 显式请求 `complexity/complex`，按合同不得自动降级。
- `type/platform` 与 `contract_effect: add` 各自独立触发强制复杂规则。
- 变更涉及 Agent 行为、provider 路由与平台治理文件，命中 `AGENTS.md:11` 的强制 complex 清单。
- 变更触及共享 runtime 入口 `cli.py` 与 `provider.py`，属于 shared-core。
- `codex/agent/provider-poll.sh:13` 当前显式拒绝 Claude implementation，改动它即改变平台启用边界。
- 基线 `84377e7` 上 `bash codex/tests/smoke.sh` 全绿：72 个 Python 测试加全部静态契约检查。

### 缺失的 acceptance criteria 或决策

- VM 上真实的 Claude `analyze.sh`、`implement.sh`、`poll.sh`、skills 与配置尚未盘点：`/home/coder/` 对运维用户不可读，本次会话未获得读取授权。该结果会改变实现方向，详见 `01-spec.md` 的未决问题。
