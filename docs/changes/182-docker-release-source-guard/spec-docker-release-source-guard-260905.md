---
issue: 182
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/182
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - ci-change
  - platform-governance
depends_on: []
status: approved
branch: change/182-docker-release-source-guard
created: 2026-09-05
updated: 2026-09-05
---

# Spec: docker-release installer 接入 source guard，Issue 65 闸门收窄到发布语义面

## 目标与原因

让 `docker-release/install.sh` 与其余五个 installer 一样，在安装前打印源 checkout 的
provenance，并在源落后 upstream 时 fail-closed 拒装；同时以显式、可复核的方式处理挡在
前面的 Issue 65 证据闸门，而不是绕过它。

原因见 `06` 踩坑 20：每个 installer 都从 `$ROOT`（源 checkout）取安装源，checkout 落后
remote 时它们会忠实地装旧内容并如实报成功。`docker-release/install` 是这条防线上唯一
剩下的缺口，其下游症状是「docker-release 用旧 capability gate」。

## Issue 65 证据闸门的处理方式与理由（AC-5）

### 闸门原样

`codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh` 在 preflight 前置与
lifecycle 后置两处，把 `docker-release/` 相对 delivery base `7ef7fa2` 的
`git diff --name-only` 输出**逐字**比对一个两行常量。它是 name-only 语法闸门，不作语义
判断，用途是让 Issue 65 的 real-release 证据与实际发布树保持一致。正因为它是语法的，
「我这个改动无害」本身不构成通过理由。

### 采用的路径与理由

平台于 2026-09-05 在 Issue 182 上裁定采用**路径 3**：把 pin 从「整个 `docker-release/`
目录」收窄到「`docker-release/` 的发布语义面」，以显式豁免清单排除不参与发布语义的文件，
当前清单只有 `docker-release/install.sh` 一条。

理由：

- `install.sh` 只把已交付的树安装到目标机。它不进 release manifest，不被 transport 读取，
  也不参与 capability gate 判定。Issue 65 的 real-release 证据从未对它作出任何断言，
  因此改动它在原理上不可能使那份证据失效。
- 路径 1（把 `install.sh` 加进 `expected_docker_release_diff`）会把「docker-release 树
  == Issue 65 证据所证之树」这条不变量降格成一份随手扩张的白名单：加进 diff 允许列表的
  文件与被证据覆盖的文件从此再也分不开。
- 路径 2（重跑 Issue 65 的 real-release E2E 取新证据）最严谨，但需要独立授权与真实 Docker
  环境，代价与本次收益不成比例。

### 收窄之后闸门仍然保证什么

- `docker-release/` 下**除豁免清单以外**的每一个路径，相对 delivery base 的 diff 仍逐字
  钉死为原来那两个文件；未跟踪文件检查、`codex/runtime/aisoft_release` 的 diff 钉死、
  以及运行中 `docker_release_tree` 不得改变的后置检查全部保持不变。
- 豁免是一份**枚举**而不是一条谓词：闸门仍然是 name-only 语法判断，扩张它仍然需要显式
  改这份清单并写明理由，而不能靠「这个改动无害」的论证通过。

## Acceptance criteria

- [ ] **AC-1** `docker-release/install.sh` 在安装前输出源 checkout 的 commit（含 upstream 同步状态）与 `matrix revision`、`schemas` 两个可读量，幂等路径上同样出现。
- [ ] **AC-2** 源 checkout 落后 upstream 时 fail-closed，且在第一次文件系统写入之前拒绝；无 remote、detached HEAD、取不到 remote ref、非 git 目录一律降级为警告后正常安装。
- [ ] **AC-3** 复用 `codex/lib/install-source-guard.sh`，不新增第二份实现。
- [ ] **AC-4** `docker-release/install` 回到 `codex/tests/test-installer-source-guard.sh` 的 `INSTALLERS` 数组，三条路径全部覆盖；同时删掉该文件里说明本 Issue 缺口的那段注释。
- [ ] **AC-5** Issue 65 的 evidence gate 以路径 3 被显式处理（不是绕过），处理方式与理由写在本 spec；`bash codex/tests/smoke.sh` 全绿。
- [ ] **AC-6** `06-运维手册与踩坑集.md` 踩坑 20 把 `docker-release/install` 从「暂无闸门」改为已覆盖。

## 接口、数据与兼容性影响

- `docker-release/install.sh` 新增一条拒装路径：源 checkout 落后 upstream 时以非零码退出且零写入。安装成功路径的产物与文件模式不变，`codex/tests/test-docker-release-install.sh` 的幂等断言与产物清单不受影响。
- CI 判据变更仅限上述两处 diff 断言的比较集合，evidence 文件本身、delivery base SHA、sha256 常量与 compatibility 矩阵全部不动。
- 无 schema、无数据、无迁移、无外部契约变更。

## 风险与回滚约束

- 单一提交内可完整 revert：改动集中在四个文件，无生成物、无状态、无迁移。
- 收窄闸门后 `install.sh` 不再受 Issue 65 证据钉死；覆盖它的是 `test-docker-release-install.sh`（安装产物与幂等）与 `test-installer-source-guard.sh`（三条源状态路径），两者都在 `smoke.sh` 内。
- 豁免清单被后续变更滥用是治理风险而非技术风险；缓解手段是清单在 harness 内逐条注明排除理由。

## 非目标

- 不改 docker-release 的发布语义、schema、compatibility 矩阵、transport 或 CLI。
- 不改其余五个 installer（`#171` 已交付）。
- 不改 `sync/install.sh`（取源方式不同，需单独核对；若确认同因再另开 Issue）。
- 不重跑 Issue 65 的 real-release E2E，不取新证据，不动 delivery base。

## 未决问题

无。
