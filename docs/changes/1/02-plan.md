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

# Implementation plan

## 任务分解

按依赖顺序排列，每个任务可独立验证。测试先行：先看到失败，再实现。

1. **盘点 VM Claude 入口（只读）**
   记录 `~coder/agent/` 下真实存在的 Claude `analyze.sh`、`implement.sh`、`poll.sh`、skills 与 provider 配置，以及认证边界。不打印任何凭据。
   *前置条件*：`/home/coder/` 当前对运维用户不可读，需要人提供只读访问或代跑列表命令。若无法获得，按遗留物处理并在 PR 中记录该限制。

2. **写失败的 parity 测试**
   在 `codex/runtime/tests/` 增加 provider parity 用例：成功、verifier 反馈、CI 反馈、范围扩张、外部阻塞、同根因三次、总轮数上限、token 脱敏、无 merge/deploy。使用 mock provider，覆盖 Codex 与 Claude 两条路由。先运行并确认失败。

3. **runtime 支持 provider 选择**
   `cli.py` 按 `IMPLEMENT_PROVIDER` 解析 adapter 脚本路径，保留 `CODEX_PROVIDER_SCRIPT` 兼容并新增 `CLAUDE_PROVIDER_SCRIPT`；`provider.py` 环境变量白名单增加 Claude 模型变量，不新增任何凭据类变量。

4. **实现 Claude adapter**
   `claude-provider.sh`：一次受限 provider turn，禁用绕过审批参数，输出经 `aisoft_loop.cli validate-provider` 校验。结构与 `codex-provider.sh` 对称。

5. **补齐中央 source 的 Claude 分析路径**
   `claude-analyzer.sh` 与 `analyze-claude.sh`，与 Codex 侧对称；`provider-poll.sh` 改为调用被跟踪的入口，消除对 `analyze.sh` 的未跟踪依赖。

6. **新增被跟踪的 Claude 入口**
   仓库根 `CLAUDE.md`，内容仅为对共享规范源的导入声明，不复制任何合同文本。

7. **放开 implementation 路由**
   仅在任务 2 的 parity 测试全绿后，修改 `provider-poll.sh` 的 provider 校验，并同步更新 `smoke.sh` 与 `test-agent-runtime.sh` 中钉住 parity gate 的两处断言。默认值保持 `none`。

8. **加固危险参数禁令**
   `smoke.sh` 增加对 `--dangerously-skip-permissions` 的禁令断言，与既有 Codex 禁令并列。

9. **安装脚本与幂等性**
   `install-vm.sh` 安装 Claude 路径所需全部文件；在一次性 HOME 连续安装两次，确认 manifest 一致、无 profile、无凭据、无 timer 启用。

10. **文档与证据**
    更新 `04`、`08`、`README` 的 parity 状态；记录真实命令输出。

## 涉及文件

新增：`codex/agent/claude-provider.sh`、`codex/agent/claude-analyzer.sh`、`codex/agent/analyze-claude.sh`、`CLAUDE.md`、`codex/runtime/tests/test_parity.py`

修改：`codex/agent/provider-poll.sh`、`codex/runtime/aisoft_loop/cli.py`、`codex/runtime/aisoft_loop/provider.py`、`codex/install-vm.sh`、`codex/tests/smoke.sh`、`codex/tests/test-agent-runtime.sh`、`templates/agent/project.env.example`、`04-Agent编排与定时任务.md`、`08-Codex双工具共存与实施.md`、`README.md`

不改动：`controller.py`、`contract.py`、`state.py`、`verifier.py`、`gitea.py`、`classification.py` 的既有行为；`AGENTS.md`；CI 与部署脚本。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `test -f docs/changes/1/00-summary.md docs/changes/1/01-spec.md docs/changes/1/02-plan.md`；人工复核 Issue 关联 |
| AC-2 | 人工复核：`git diff --name-only origin/main` 的每个治理文件都在 spec 授权清单内 |
| AC-3 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests`；人工复核 runtime 无 provider 专属状态机分支 |
| AC-4 | `python3 -m unittest tests.test_parity` 中的非法 schema 与非法 changed_files 用例 |
| AC-5 | `python3 -m unittest tests.test_parity` 八种情形用例全绿 |
| AC-6 | `bash codex/tests/smoke.sh` 中既有的 rsdesign 禁令断言 |
| AC-7 | `bash codex/tests/smoke.sh` 的 `IMPLEMENT_PROVIDER=none` 断言；`bash codex/tests/test-agent-runtime.sh` |
| AC-8 | `python3 -m unittest tests.test_parity` 的 provider 切换用例 |
| AC-9 | `bash codex/tests/smoke.sh` 的 token 泄漏断言；人工复核 `provider.py` 环境变量白名单不含凭据变量 |
| AC-10 | `bash codex/tests/smoke.sh`（含 `bash -n`、ShellCheck、72+ Python 测试），记录真实输出 |
| AC-11 | 一次性 HOME 连续两次 `bash codex/install-vm.sh "$TMPHOME"`，对比 manifest；`systemctl --user list-timers` 确认无启用 |
| AC-12 | 设置 `IMPLEMENT_PROVIDER=none` 后重跑 `provider-poll.sh`，确认 implementation 不执行、analyzer 不受影响 |
| AC-13 | `python3 -m unittest tests.test_parity` 的终态用例；人工复核无 merge/deploy 调用 |
| AC-14 | `bash codex/tests/smoke.sh` 断言 `provider-poll.sh` 引用的脚本均存在于仓库；`bash codex/install-vm.sh` 安装清单包含 Claude 路径 |
| AC-15 | `bash codex/tests/smoke.sh` 的 `--dangerously-skip-permissions` 禁令断言 |

## 部署与回滚

**部署**：无。AISoftPlatform 是平台 control repository，不是应用部署目标，因此不需要 `03-verification.md` 的部署验证章节。

**回滚**：把 implementation provider 改回 `IMPLEMENT_PROVIDER=none` 即完全停用 Claude implementation。analyzer、CI、制品与应用部署都不依赖 Loop，因此回滚不产生外溢影响。既有 Codex 与 Claude 的认证、脚本与 skills 不删除。

**失败升级**：合同冲突、范围扩张、破坏性迁移、安全决策、缺凭据或外部阻塞、同一根因连续三次失败或达到预算上限时，停止并升级给人，输出已完成项、失败验证、根因、已尝试方案与待决问题。
