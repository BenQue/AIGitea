---
issue: 391
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/391
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - agent-governance
  - platform-governance
depends_on:
  - 389
status: verified
branch: change/391-automation-engine-exit
created: 2026-10-20
updated: 2026-10-20
---

# #391 验证记录

## 基线与范围

- 基线：`origin/main` = `0192a8e`（R9 合并）；交叉审查 PASS 的源码 head = `da3b9ca`，本记录随后单独提交
- 环境：macOS，bash 3.2 系统 shell；broker 源码 runtime（未重装）
- 本记录负责证明 spec AC1–AC9；AC10 是合并后负责人执行的现场步骤，列在末尾，当前 NOT RUN

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh` @ `da3b9ca` | PASS | rc=0；runtime 单测 705 条 OK，漂移夹具 34 条 OK，`Codex platform static smoke checks passed.`（此前每轮修复后各跑一次，均 rc=0；首跑红在 `#355 AC-5` 成对短语，已改） |
| `aisoft_host_access.cli validate`（真实与夹具 manifest） | PASS | 两份均 `operation_count: 34`、`merge_operation_count: 0`、`project_count: 7` |
| `aisoft_gitea_governance.cli validate`（真实与夹具） | PASS | 两份均 `result: PASS`、`repository_count: 7` |
| 源码 runtime `host.access.audit`，候选 manifest，七个项目 | 5 PASS / 2 BLOCKED_EXTERNAL | aisoft-platform、hsdb、localwms、newemaint、sfm-digital-board：PASS，merge 白名单 `['admin']`；myapp、smoke-test：`CREDENTIAL_UNAVAILABLE`，已安装 broker 对这两个项目给出同一结果，是 Mac 上没有这两个 public 测试仓凭据的既有基线，与本变更无关 |
| `bash codex/tools/check-installed-drift.sh --source-only` | PASS | `RESULT PASS`，六个安装面 |
| `bash codex/tests/test-installer-source-guard.sh` | PASS | `6 installers x 3 source states` |
| `bash codex/tools/usage-bundle.sh --verify` | PASS | R10c（PR 393）先合并并发布 1.3.0；本批撤回本地未发布的 1.3.0（`f23bf1f`），以 merge commit `dba89a8` 干净集成 `149e469`，再改发 `1.4.0`，`VERIFIED 1.4.0 sha256:18aa7e2a…` |
| `python3 codex/tests/check-project-leak.py --root .` | PASS | 4 个基线文件、11 处命中，与基线相同；`emaintenance` 随 VM profile 退出转入 `retired` |
| `check-change-documents --repo .` | PASS | `changes=179 pass=2 gap=0` |
| `apply-classification-labels.sh --verify 391` | projected | `type/platform` + `complexity/complex` |
| ShellCheck / `bash -n`（改动的 shell） | PASS | smoke 内与单独运行 |
| Codex 只读交叉审查 | PASS（第 6 轮） | 项目库 `codex-review-391.md`；第 1–5 轮共 11 条发现均为文档残留措辞，逐轮修复 |

## 集成 main

- R10c（#392，PR 393）在本 PR 之后先合并，`origin/main` 前进到 `149e469`。broker 要求集成 merge 的树等于 [Issue tip, main] 的纯 merge-tree，所以先以 `f23bf1f` 撤回本地未发布的 1.3.0 记录，再以 merge commit `dba89a8` 无冲突集成（不 rebase），之后在其上发布 `1.4.0`。
- `bash codex/tests/smoke.sh` 在内容相同的树上（首次集成尝试 `f12fd4c`，与本次集成后除本文件外逐字节相同，`bundle.json` 摘要同为 `18aa7e2a…`）：rc=0；runtime 单测 710 条 OK，漂移夹具 34 条 OK。
- Codex 只读集成审查（第 7 轮，同一树）：PASS，见项目库 `codex-review-391.md`；唯一 P3 是本节缺失，已补。
- 集成前 head `1aa48d7` 的 PR CI `CI / verify (pull_request)`：success。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 迁出说明与 grep | PASS（带说明） | `archive/automation-engine-exit-261020.md` 列全部删除路径与最后 commit `0192a8e`；`git grep` 五个词在 `docs/changes/`、`archive/`、`docs/adr/`、`06` 踩坑表之外只剩两类：governance 冻结的 `routine_merge_agent_policy.allowed_operation`（方案 A，R16 清理）与 smoke/测试里的退役负向守卫 |
| AC2 Loop 代码退出 | PASS | T02 删除 6 个模块、10 个脚本、systemd、install-vm、templates/agent 与 7 个只测 Loop 的测试；`cli.py` 只剩会话工具子命令 |
| AC3 broker 39 → 34 | PASS | validate 34/0；`test-host-access-broker.sh`、`test_host_access.py` 新增退役断言；installer 删除已装 `project-profile-migration` 与 `profiles.py` |
| AC4 manifest | PASS（带说明） | LocalWMS merger 两份 manifest 均为 `null`；`vm_profile` 与 `vm_profile_policy` 删除，改为 `vm_runtime.runtime_user`；七项目 audit 见上表。方案 A 下 `routine_merge_agent_policy` 与夹具 pilot 保留 |
| AC5 installer 为 6 | PASS | drift source-only、source guard、漂移夹具测试 |
| AC6 文档 | PASS | README、01、03、04、05、06、08、14、GLOSSARY、技能、模板、docs/agents、usage/CONTRACT；Codex 六轮复核 |
| AC7 治理文件受控步骤 | PASS | `0398c09` 只含 `AGENTS.md`、删除 `codex/global-AGENTS.md` 与对应 smoke 钉子，提交后重读再改 runtime |
| AC8 smoke、泄漏、发布包 | PASS | 见上表与「集成 main」 |
| AC9 交叉审查与判级投影 | PASS | Codex 第 6 轮 PASS；`--verify 391` = projected |
| AC10 合并后现场 | NOT RUN | 需负责人合并后执行：两台重装 broker 与技能、VM 清理、删 `localwms-routine-merger`、读回 |

## 遗留风险与未完成项

- 方案 A（待负责人在确认点 2 前确认）：routine 的 governance schema、audit routine 段与 K1 routine 凭据种类保留并停用，R16 清理。
- `aisoft_main_integration.py` 按 `aisoft-loop` 目录解析模板的一支成为死路径（非目标，R14/R16）。
- `get-issue`、`list-issues`、`apply-analysis` 按任务书保留但当前无调用方，去留交 R11。
- 已安装 runtime 在两台重装前仍认识 39 个操作；AC10 读回前不能说 installed 已生效。
