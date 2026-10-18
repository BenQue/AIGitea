# 参考实现迁出说明（#383，R8）

2026-10-19 起，下列参考实现与只为它们存在的测试、harness、夹具和证据闸门从平台 `main` 删除
（ADR 0001 D1/D5，整改路线 R8）。平台不再提供任何交付形态的实现或 installer；采用方在项目仓自带副本并按自己的 pin 维护。
本目录不保存被删的树，需要时从 Git 历史取。

## 怎么取历史版本

- 最后完整存在于平台 `main` 的 commit：`80a38dc`（#383 的合并基）。例：
  `git archive 80a38dc docker-release codex/runtime/aisoft_release | tar -x -C <目录>`。
- 已知外部 pin（2026-10-18 核实，平台不改写历史、不 force-push，这些 commit 永久可取）：
  - 容器发布校验的 27 个文件：`e1290d245553a59b47450438e1d94f0be4269e00`。
  - 公司只读基线 collector、diagnostics 与 schema：`1164318c6a1c40aa9686e9bc6b0d58a79ca714ee`。

## 删除清单与去向

| 路径 | 文件数 | 内容 | 去向 |
|---|---|---|---|
| `docker-release/` | 19 | Docker-first release 合同、schema、兼容矩阵、CLI 与 installer | 采用方项目仓自带副本；解决方案模式见 `02` §0 |
| `codex/runtime/aisoft_release/` | 13 | release runtime（contract、transport、phases、gate、runner） | 同上 |
| `company-delivery/` | 32 | 公司两 VM 离线 handoff operator：runbook、schema、CLI、模板与只读基线 | 采用方项目仓自带副本 |
| `codex/runtime/aisoft_company_delivery/` | 6 | operator CLI 实现（打包时引用 `aisoft_release` 与 `docker-release/`） | 同上 |
| `architecture/reference/newemaint/` | 6 | 单个项目的 inventory、gap report 与 target-candidate declaration/lock | 项目仓；平台只留合成的 `windows/`、`sqlite/` 参考 |
| `codex/tests/fixtures/docker-release/`、`docker-release-v2-lifecycle/`、`docker28-classic/`、`docker-image-store-e2e/` | 16 | 上述实现的测试夹具 | 仅历史 |

单个文件（35 个）：公司基线模块、release/company 单测、证据闸门、E2E harness 与 driver。仅历史。

- `codex/runtime/aisoft_company_baseline.py`
- `codex/runtime/aisoft_company_baseline_diagnostics_v1.py`
- `codex/runtime/aisoft_company_baseline_diagnostics_v2.py`
- `codex/runtime/aisoft_company_baseline_v2.py`
- `codex/runtime/tests/release_test_support.py`
- `codex/runtime/tests/test_company_baseline.py`
- `codex/runtime/tests/test_company_baseline_diagnostics_v1.py`
- `codex/runtime/tests/test_company_baseline_diagnostics_v2.py`
- `codex/runtime/tests/test_company_baseline_v2.py`
- `codex/runtime/tests/test_company_delivery.py`
- `codex/runtime/tests/test_release_architecture_integration.py`
- `codex/runtime/tests/test_release_capability.py`
- `codex/runtime/tests/test_release_cli.py`
- `codex/runtime/tests/test_release_contract.py`
- `codex/runtime/tests/test_release_docker28_compatibility.py`
- `codex/runtime/tests/test_release_evidence_boundary.py`
- `codex/runtime/tests/test_release_gate.py`
- `codex/runtime/tests/test_release_phases.py`
- `codex/runtime/tests/test_release_rollback_compatibility.py`
- `codex/runtime/tests/test_release_runner.py`
- `codex/runtime/tests/test_release_safety.py`
- `codex/runtime/tests/test_release_transport.py`
- `codex/tests/check-release-evidence-boundary.py`
- `codex/tests/integration/docker-release-v2-lifecycle-driver.py`
- `codex/tests/integration/docker28-classic-driver.py`
- `codex/tests/integration/provision-docker28-classic-lab.sh`
- `codex/tests/integration/test-company-delivery-real-release.sh`
- `codex/tests/integration/test-docker-image-store-e2e.sh`
- `codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh`
- `codex/tests/integration/test-docker28-classic-e2e.sh`
- `codex/tests/test-company-delivery-real-release-harness.sh`
- `codex/tests/test-docker-image-store-e2e-harness.sh`
- `codex/tests/test-docker-release-install.sh`
- `codex/tests/test-docker-release-v2-lifecycle-e2e-harness.sh`
- `codex/tests/test-docker28-classic-e2e-harness.sh`

## 随之撤掉的平台闸门

- smoke 中的 docker-release 安装测试、image-store、docker28-classic、v2 lifecycle、company-delivery real-release 段，
  发布证据闸门 `check-release-evidence-boundary.py` 与其回归，相关 shellcheck 名单、JSON 校验、Secret 与项目名守卫、兼容矩阵断言。
- installer 集合由 8 个减为 7 个；`check-installed-drift` 与 source guard 不再登记 `docker-release/install`。
  已安装在主机上的 `/opt/aisoft-docker-release` 与 `/usr/local/bin/aisoft-docker-release*` 平台不代为删除，
  重装来源改为采用方项目仓的副本。

## 保留

`docker-release/v1`、`docker-release/v2` 作为交付形态名称保留在 architecture schema/validator 与 project-check 中，
它们是项目声明里使用的通用词汇，不依赖被删目录。
