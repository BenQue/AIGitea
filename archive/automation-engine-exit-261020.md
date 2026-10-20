# 自动化引擎迁出说明（#391，R10a）

2026-10-20 起，VM 上的 Development Loop（analyzer 轮询、controller、provider adapter、verifier、state）、
routine 自动合并的执行面与 VM profile 迁移从平台 `main` 删除（[ADR 0002](../docs/adr/0002-deterministic-development-flow.md) D2/D4，
整改路线 R10a）。平台只剩一条在用的开发路径：Mac 上的交互会话（或协调者派单的线程）按两个确认点做到唯一最终 PR，人合并。
本目录不保存被删的树，需要时从 Git 历史取。

## 怎么取历史版本

- 最后完整存在于平台 `main` 的 commit：`0192a8e`（#391 的合并基）。例：
  `git archive 0192a8e codex/runtime/aisoft_loop codex/agent codex/systemd codex/install-vm.sh | tar -x -C <目录>`。
- 原 `04-Agent编排与定时任务.md`、`08` §4/§6、`03` §2.1 的全文也在该 commit。

## 删除清单与去向

| 路径 | 文件数 | 内容 | 去向 |
|---|---|---|---|
| `codex/runtime/aisoft_loop/{controller,provider,verifier,state,routine_merge,output}.py` | 6 | Loop controller、provider 调用、verifier、持久 state、routine 资格判定、provider 输出提取 | 会话按两个确认点执行；`redact` 迁入 `gitea.py` |
| `codex/runtime/aisoft_loop/analysis.py` 的 render 支 | — | `render_summary` 及其辅助函数 | summary 由会话按模板写 |
| `codex/runtime/aisoft_loop/cli.py` 的 8 个子命令 | — | `run`、`confirm-pr`、`validate-provider`、`validate-analysis`、`analysis-slug`、`parse-change-branch`、`extract-json`、`render-analysis` | 只保留会话工具子命令 |
| `codex/agent/` 的 Loop 脚本 | 10 | `analyze-claude`、`analyze-codex`、`claude-analyzer`、`claude-provider`、`codex-analyzer`、`codex-provider`、`common`、`loop-controller`、`project-poll`、`provider-poll` | 仅历史；`gitea-token`、`gitea-label-manifest`、`change-merge-range`、`aisoft-project-target` 被 `codex/tools` 引用，保留 |
| `codex/systemd/` | 2 | `aisoft-agent@.service/.timer` 模板 | 仅历史 |
| `codex/install-vm.sh`、`codex/global-AGENTS.md`、`templates/agent/` | 3 | VM user-scope 安装面、VM coder 的 Codex 全局指导、VM profile 模板 | 仅历史 |
| `codex/runtime/aisoft_host_access/profiles.py`、`codex/tools/project-profile-migration.sh` | 2 | VM profile 迁移（plan/apply/read-back/rollback） | 仅历史；broker installer 重装时删除已装副本 |
| broker 的 `RoutineMergeRunner` 与 `gitea.pull.merge.routine` 的执行代码 | — | routine 合并的固定 runner 与全硬门执行 | 合并永远是人 |

单测（7 个文件）：`test_controller`、`test_state`、`test_verifier`、`test_parity`、`test_output`、`test_routine_merge`
（其中的技能短语钉子迁到 `test_session_contract.py`）与 `codex/tests/test-agent-runtime.sh`。仅历史。

## 随之撤掉的平台闸门与操作

- broker 操作 39 → 34：退役 `gitea.pull.merge.routine` 与 `vm.profile.plan/apply/read-back/rollback`；
  manifest 删除项目 `vm_profile` 段与 `mac_host.vm_profile_tool`，`vm_profile_policy` 收窄为 `vm_runtime.runtime_user`
  （`orbstack.vm.units.read` 仍要读它）。LocalWMS 不再声明 routine merger。
- installer 集合由 7 个减为 6 个；`check-installed-drift` 与 source guard 不再登记 `install-vm`，broker 安装面把
  `project-profile-migration` 与 `profiles.py` 列为退役目标。
- smoke 删掉 Loop 脚本、systemd 模板与 `templates/agent` 的存在性检查，改为守卫它们不再出现。

## 合并后由负责人清理（平台不代为删除）

- gitea-ci VM 上 `coder` 家目录：`agent-poll.*` 与 `aisoft-agent@*` 用户单元、`~/.config/aisoft/projects/*.env`、
  `~/.local/state/aisoft-loop/`、`~/.local/lib/aisoft-loop/`、`~/.local/share/aisoft/`、`~/.codex/AGENTS.md`。
- `localwms-routine-merger` Gitea 账号、Mac canonical store 与 VM 下的 `projects/localwms/routine-merge-agent.token`。

## 保留

- 判级规则引擎（`classification.py`）、语义文档 resolver 与合同校验、`change_control`、会话工具（命名、worktree 归属、
  文档检查、PR URL 回填、判级投影、终态）、K1 凭据托管与 `git.push.change`。
- governance manifest 的 routine 字段、`routine_merge_agent_policy`、pilot schema 与 PAT 轮换/bootstrap 中的 routine 凭据种类
  暂留，全部停用，随 R16 与 PAT 周期一起清理。
- `aisoft_main_integration.py` 里按 `aisoft-loop` 安装目录解析模板路径的一支成为死路径，不在本批改动范围（R14/R16）。

## 重建形状

ADR 0002 D3 的阶段 2/3 只在 Mac 上重建：判级与交叉审查用 `codex exec -s read-only` / `claude -p` 的薄封装只输出候选；
满足「重开条件」后，small-direct 的 headless implement 在 worktree 内跑到 `AWAITING_PR_CONFIRMATION`，提交 PR 与合并仍由人确认。
旧 provider adapter 的接口（读合同与失败证据 → 显式 `$implement #N Txx` → 本地 commit → 结构化结果）可以作为封装形状参考。
