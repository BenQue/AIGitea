---
issue: 396
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/396
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
  - platform-governance
depends_on:
  - 391
status: approved
branch: change/396-site-externalization
created: 2026-10-20
updated: 2026-10-21
---

# #396 验证记录

## 基线与范围

- 基线：`origin/main` = `08be6f4`（R10a 合并，含 R10c）
- 环境：macOS，bash 3.2 系统 shell；broker 源码 runtime（未重装），已安装 broker 作对照
- 本记录证明 spec AC1–AC5；AC6 是合并后负责人执行的现场步骤，当前 NOT RUN

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `aisoft_host_access.cli validate`（真实与夹具 manifest） | PASS | 两份均 `operation_count: 34`、`merge_operation_count: 0`、`project_count: 7` |
| `test_another_site_validates_without_code_changes` | PASS | 整组 `site` 换成另一台机器、账号、路径与 https Gitea 后合同 PASS，`host-operator` 身份解析为新账号；`aisoft_host_access/*.py` 不含 `benque`、`gitea-ci`、`/Users/`（AC1） |
| `test_site_values_are_checked_by_shape_and_cross_reference` | PASS | 十种非法值逐个被拒，报错各自对应：相对路径、未规范化、文件系统根、凭据根在平台检出内、在项目检出内、`gitea_url` 与 `base_url` 不一致、机器名非标识符、registry 带凭据、带 query、模板占位；另有 owner 不一致、缺键、`mac_host` 残留旧键、平台 `mac_checkout` 不一致四种（AC1） |
| 守卫反向证明，真实 worktree | PASS | 往 `templates/project/AGENTS.md` 追加 `smoke-test`：`1 project-name hits (baseline 0)`，rc=1；追加 `gitea-ci.orb.local`：`1 site-value hits (baseline 0)`，rc=1；还原后 `PASS: project-leak (10 baseline files, 40 hits; site 19 files, 82 hits)`，rc=0（AC2） |
| `test_real_manifests_catch_public_test_name_and_site_host` | PASS | 同一反向证明以真实 manifest 固化为单测，删掉后恢复绿（AC2） |
| 清零位置 | PASS | 基线 `site_files` 与 `files` 均不含 `contract.py`、`skills/`、`templates/`、四个注释文件（AC3）；`codex/tools/gitea-pat-helper/README.md` 按决定 5 的「`codex/tools` 文档」一并进基线 |
| `test_host_access`、`test_host_access_complete_reads`、`test_credential_rotation` | PASS | 268 条 OK |
| `codex/tests/test-host-access-broker.sh` | PASS | 新增 `site` 八键、`mac_host` 无旧键、owner 等于运维账号三条 jq 断言 |
| 源码 runtime 对照已安装 broker：`host.access.audit` 七个项目 | 一致 | 五个 PASS；myapp、smoke-test 两边都是 `BLOCKED_EXTERNAL` / `CREDENTIAL_UNAVAILABLE`（Mac 上本无这两个 public 测试仓凭据，既有基线）（AC4） |
| 源码 runtime 对照已安装 broker：`orbstack.vm.units.read` | 一致 | 两边 PASS，`machine: gitea-ci`，1 个单元；证明 `site.orbstack_machine`/`orbstack_user` 的新读取路径真实可用（AC4） |
| `codex/tests/test-registry-preflight.sh` | PASS | 新用例：模板占位未替换时落在 `stage=config` 并指出 `site.npm_registry`，不发起连接 |
| `usage-bundle.sh --verify` | PASS | `VERIFIED 1.5.0`（AC5） |
| `bash codex/tests/smoke.sh` | 见下文 | |

## 合并后（AC6，NOT RUN）

负责人两台重装 broker 后，会话读回 `check-installed-drift` 的 `install-host-access-broker` 面（期望 34/34 PASS）与 `host.access.audit`（期望同上表）。
