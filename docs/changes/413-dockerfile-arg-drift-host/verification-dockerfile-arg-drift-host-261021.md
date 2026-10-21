---
issue: 413
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/413
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - artifact
  - platform-governance
depends_on: []
status: pending
branch: change/413-dockerfile-arg-drift-host
created: 2026-10-21
updated: 2026-10-21
---

# Verification

## 基线与范围

- Commit SHA: 实现 head `79042f01`（下文每条记录写明自己的 SHA；最终候选 head 见交叉审查表最后一行）
- 基线：`origin/main` = `1db191eb`
- 环境: macOS（Darwin 27），python3，Mac 平台检出的 change worktree；未执行 Docker build
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-7

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| T01 反向：新测试跑在 `e38ad533`（未改 `dockerfile.py`） | FAIL（预期） | `test_guarded_global_arg_default_expands_413` 与 `test_guarded_arg_default_keeps_digest_rules_413` 共 3 处失败，全报 `DOCKERFILE_FROM_VARIABLE_UNSUPPORTED` |
| T01 正向：`python3 -m unittest tests.test_architecture_dockerfile`（`8e13f693`） | PASS | Ran 19 tests, OK |
| T02 反向：新测试跑在未改的 `check-installed-drift.py` | FAIL（预期） | 首版测试得到 `(1, 'GAP')`，即终审踩到的 `/etc` symlink-parent 假 GAP；第 1 轮审查后改用 fail-fast seam，在 `1db191eb` 版检查器上三个根（`/`、`//`、`/./`）都以「macos_system_aliases reached the real root」失败，未读到宿主安装面 |
| T02 正向：同一测试（`fe0b374a`） | PASS | Ran 1 test, OK |
| `bash codex/tests/test-installed-drift.sh`（`337355ce`） | PASS | OK |
| Mac 实跑 `bash codex/tools/check-installed-drift.sh --host vm`（`337355ce`） | 退出 2 | `SOURCE {"reason": "host-mismatch", ...}` 后 `RESULT ERROR`，不打印任何 installer 行 |
| NewEMaint `gitea/main` 三份 Dockerfile（api、web、database）经 `_digests` 核验（`79042f01`） | PASS | 各引用 1 个 digest；遗留 `deploy/Server/web-service/Dockerfile` 的 `node:${NODE_VERSION}-alpine` 仍报 `DOCKERFILE_FROM_VARIABLE_UNSUPPORTED` |
| 第 1 轮审查的回归用例跑在 `228db97e` 版 `dockerfile.py` | FAIL（预期） | `test_unguarded_or_unprovable_arg_forms_fail_closed_413` 10 处失败（`|| true`、`; true`、`&`、`| cat`、ENV 遮蔽 ×2、SHELL、反斜线与未闭合引号 ARG 等被误判 PASS），引号内 `BASE=preview` 的合规用例误报失败 |
| 同上跑在 `79042f01` | PASS | Ran 19 tests, OK |
| 第 2 轮审查的回归用例跑在 `12dd1c8d` 版 `dockerfile.py` | FAIL（预期） | `test_unguarded_or_unprovable_arg_forms_fail_closed_413` 4 处失败：命令替换里嵌套引号藏起的 `\|\| true`（3 种写法）与 `&&` 后的子 shell 被判 PASS |
| 同上跑在 `0f729a45`；NewEMaint 三份 Dockerfile 复核 | PASS | Ran 19 tests, OK；三份各引用 1 个 digest |
| 第 3 轮审查的回归用例跑在 `768db821` 版 `dockerfile.py` | FAIL（预期） | 同一测试 4 处失败：`${x:-'"'}` 藏起的 `\|\| true`，与 `ENV "BASE"=`、`ENV BA"SE"=`、`ENV BA\SE=` 三种 ENV 键遮蔽 |
| 同上跑在 `5b136043`；NewEMaint 三份 Dockerfile 复核 | PASS | Ran 19 tests, OK；三份各引用 1 个 digest |
| `bash codex/tools/usage-bundle.sh --release 1.11.0`（`ded11790`，合并前从 main 版重发同号） | PASS | `RELEASED 1.11.0 sha256:319fdc96…`；只追加一个 release |
| `bash codex/tests/smoke.sh`（`228db97e`） | PASS | `Codex platform static smoke checks passed.` |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | `test_guarded_global_arg_default_expands_413`；NewEMaint 三份真实 Dockerfile |
| AC-2 | PASS | `test_unguarded_or_unprovable_arg_forms_fail_closed_413`，含第 1 轮审查补的绕过形态 |
| AC-3 | PASS | `test_guarded_arg_default_keeps_digest_rules_413`；`error()` 断言 stderr 不含 digest |
| AC-4 | PASS | `test_vm_host_on_macos_real_root_is_refused_413`（三种根写法、fail-fast seam 断言未调用）；Mac 实跑退出 2 |
| AC-5 | PASS | 同一测试的 `--source-only` 与合成根分支；漂移夹具全量 OK |
| AC-6 | PASS | 上表三条反向记录 |
| AC-7 | 待最终 smoke | 1.11.0 已发布并 `--verify`；最终候选 head 的 smoke 结果补在下表之后 |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex（gpt-6-astra，reasoning ultra） | 228db97eb3c9f4269cf17765a0205be08dfdc0d6 | FAIL | 3 个 P1：守卫后 `||`/`;`/`&` 吞失败、ENV 遮蔽、SHELL 跳过比较；4 个 P2：引号内伪 ARG 声明、`//` 绕过根判定、反向测试会读宿主根、verification 未填。全部在 `c06a0d43`、`fe0b374a`、`79042f01` 修复并补回归；敌意基础镜像改写 `test`/shell 属构建参数信任边界，按建议在 README 写明不保证 |
| 2 | Claude | Codex（gpt-6-astra，reasoning high） | 12dd1c8df792b1543df7119e20a9372e865e55f2 | 未出结论 | 审查中途被 OpenAI 内容过滤中止，未写 VERDICT；中止前的复现已证明一处 P1：命令替换内嵌套引号让引号剥离正则漏掉 `\|\| true`。`0f729a45` 改为严格左到右扫描并补 4 个回归 |
| 3 | Claude | Codex（gpt-6-astra，reasoning high） | 768db821897f946df5da6121ed3aceca46a9efde | FAIL | 2 个 P1：双引号内 `${…}` 参数展开可藏引号吞掉 `\|\| true`；ENV 键经引号或转义后仍等于 `BASE`。`5b136043` 只接受 `$NAME`/`${NAME}`，守卫前的 ENV 含引号、转义或 `$` 一律判不可证明，补 4 个回归；其余项复核无残余 |

## 遗留风险与未完成项

- 守卫只在构建期于被选中的基础镜像里执行：挡住构建参数漂移到另一个正常镜像，挡不住敌意镜像；README 已写明。
- 未执行 Docker build；守卫语义靠 Docker 官方 ARG/ENV/SHELL 规则与静态用例证明。
- 已装主机的 architecture（target）与漂移检查要等合并后由负责人重装才生效：NOT RUN。
