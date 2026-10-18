---
issue: 380
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/380
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - rollback
  - platform-governance
depends_on:
  - 377
status: verified
branch: change/380-fixture-manifests
created: 2026-10-18
updated: 2026-10-18
---

# #380 验证记录

## 基线与范围

- 基线：`origin/main` = `8fa4458`
- 代码与测试的验证对象：`d2f22b5`（本记录随后的 commit 只改本目录文档与 plan 状态，最终 head 另跑全量 smoke）
- 环境：macOS 本机（Darwin 27.0.0，Python 3.14，`/opt/homebrew/bin/rg`）
- 本记录负责证明的 acceptance criteria：AC1–AC7，以及 Codex 独立审查

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 夹具 `aisoft_host_access.cli validate` | PASS | `project_count` 7、`operation_count` 38；封印摘要按 `exclude_name='AlphaApp'` 重算为 `764bed75…e3ec` |
| 逐文件 Python 用例数（AC3） | PASS | 改前改后相同：test_host_access 204、test_gitea_governance 55、test_routine_merge 26、test_dependency_integration 13、test_dependencies 7、test_credential_rotation 34、test_change_control 14、test_deployment_lifecycle 7、test_vendored_change_templates 5、test_controller 51、test_main_integration 33，全部 OK |
| 改读夹具的 shell 测试 | PASS | bootstrap、rotate、host-access-broker、mark-completed、agent-runtime 全过；project-check 63 → 64 个用例（新增“未设置覆盖时不打印 NOTE”一例） |
| 候选副本删掉真实 manifest 的 NewEMaint（AC3） | PASS | 本分支 `git archive` 副本删掉两份真实 manifest 中的 NewEMaint 条目（7 → 6）：上述 Python 模块与 6 个 shell 测试全绿（`GovernedHostRunnerTests` 需要 git 仓库，`git init` 后 8 个用例 OK）。同样操作在 `origin/main` 副本上：test_gitea_governance 4 failures 31 errors、test_routine_merge 20/4、test_credential_rotation 2/31、test_dependency_integration 7/1 |
| 测试中残留的已注册应用项目名 | PASS | 改动的 18 个测试文件与夹具 `rg -i 'newemaint|localwms|sfmdigitalboard|sfm-|hsdb'` 零命中 |
| smoke 守卫正反例 | PASS | 守卫自带 7 条样例自检（5 条应命中）；在 `codex/runtime/tests/` 临时放入三种写法（`"codex" / "config" / …`、`'codex/config' / name`、`parents[2] / "config/…"`）各自让守卫失败，删除后通过 |
| `test-install-host-access-broker.sh`、`test-host-access-broker.sh` | PASS | installer 不再安装回滚工具，预置的已装副本与 `.previous` 被删除 |
| `test-installed-drift.sh` | PASS | 35 个用例；回滚工具与 keychain helper 同样报 `retired-target-present`；installer pin 更新为新文件 sha256 `81883aac…866f` |
| `usage-bundle.sh --verify --baseline-ref origin/main` | PASS | `VERIFIED 1.0.0`，本票不改发布包成员 |
| `python3 -B codex/tests/check-project-leak.py` | PASS | 14 个基线文件 92 处 → 13 个文件 59 处 |
| `bash codex/tests/smoke.sh` | 见下 | 首跑（`6392047`）Python 回归 1238 个用例 OK，最后的 `check-change-documents` 因本记录尚未写入报 GAP（预期）；修复审查发现并写入本记录后在最终 head 重跑 |
| Codex 独立审查（Herdr 只读会话） | FAIL → 待复核 | 首轮 1 个 P1、2 个 P2：守卫的 classification 排除 glob 未生效、正则漏掉 Path 拼接写法、project-check 覆盖后输出未标明来源；`d2f22b5` 修复。其余核对通过：夹具与真实 manifest 除改名与封印外字节等价，方法数逐文件一致，installer 删除与漂移 absent 对称，经 broker 入口的 13 个拒绝请求按预期原因拒绝，归档文件与原文件字节一致 |

## 未执行项

- broker 重装与已装副本删除的 live 读回：需负责人合并后在 Mac 用 sudo 运行 `codex/install-host-access-broker.sh`，再跑 `check-installed-drift.sh`，NOT RUN。
- `codex/tools/gitea-pat-helper/` 的 Go 测试与 `integration/test-gitea-pat-helper-process.py` 仍读真实 manifest，按合同非目标保留，已列入守卫允许清单。
