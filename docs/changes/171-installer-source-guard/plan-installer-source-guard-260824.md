---
issue: 171
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/171
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/171-installer-source-guard
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan · installer source guard（#171）

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `codex/lib/install-source-guard.sh` 抽取；`install-host-access-broker.sh` 改用它，外部行为不变（AC-3） | - | done |
| T02 | 四个 installer 各接一次闸门与可读量（AC-1、AC-2） | T01 | done |
| T03 | `test-installer-source-guard.sh` 与 smoke 注册（AC-4、AC-5） | T02 | done |
| T05 | `docker-release/install.sh` 接入 | T02 | **切出 #182**（Issue #65 evidence gate，见 spec §4） |
| T04 | `06` 踩坑 20 覆盖范围扩到全部 installer（AC-6） | T02 | done |

T01 是可独立验收的垂直切片：抽完即可用既有的
`bash codex/tests/test-install-host-access-broker.sh` 判定「外部行为没变」——
该测试一个断言都不放宽。T02 逐个接入；T03 把六个 installer 的三条路径钉进 smoke；
T04 只动文档。T05 在 T02 期间被 `smoke.sh` 的
`FAIL: docker-release differs outside the Issue #65 evidence-gated scope` 拦住，
改动已写完并验证过，随 #182 交付。

## Expected touch points

- **T01**：`codex/lib/install-source-guard.sh`（新增）、`codex/install-host-access-broker.sh`、
  `codex/tests/test-install-host-access-broker.sh`（`make_source_tree` 补上新库；断言不变）
- **T02**：`codex/install-vm.sh`、`codex/install-host-role.sh`、`codex/install-skills.sh`、
  `architecture/install.sh`（`docker-release/install.sh` 切出 #182）
- **T03**：`codex/tests/test-installer-source-guard.sh`（新增）、`codex/tests/smoke.sh`
- **T04**：`06-运维手册与踩坑集.md`（踩坑 20 一行）

范围提示，不授权扩大 spec §5 的授权清单。

## T01 实现要点

1. 库带 shebang 与 `set -euo pipefail`（与 `codex/agent/common.sh` 同惯例），
   只定义函数，顶层不执行任何动作。
2. `aisoft_install_source_line()` 固定 `printf 'source %-11s %s\n' "$1:" "$2"`。
   核对：`checkout:`(9)、`commit:`(7)、`operations:`(11) 三个 label 补齐到 11 后
   分别得 3 / 5 / 1 个空格，与 #162 现有输出逐字节相同。
3. `aisoft_install_source_guard()` 的探测顺序与 #162 一致：
   `command -v git` → `rev-parse --git-dir` → `symbolic-ref --quiet --short HEAD`
   → `rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'`
   → `rev-parse --verify --quiet "<upstream>^{commit}"`
   → `rev-list --count HEAD..<upstream>` 与 `<upstream>..HEAD`。
   每一步失败都归入某条**警告**路径，不归入拒绝——**探测不到不等于落后**。
4. WARNING / ERROR 文本沿用 #162 原文，只把固定的 `install-host-access-broker`
   换成参数。`(#162)` 这个缺陷引用保持原样：改它会改变已验收的输出。
5. 调用方以 `# shellcheck disable=SC1091` + `source "<root>/codex/lib/install-source-guard.sh"`
   接入（仓库既有惯例，见 `codex/agent/*.sh`）。
6. `install-host-access-broker.sh` 删掉内联实现，改为
   `aisoft_install_source_guard install-host-access-broker "$ROOT" operations "$(...)"`；
   原有的长篇根因注释迁进库，不丢。

## T02 接入点（务必在第一次写入之前）

| installer | 插入位置 |
|---|---|
| `codex/install-vm.sh` | `SHARE_DIR` 赋值之后、第一个 `install -d` 之前 |
| `codex/install-host-role.sh` | `CONFIG_DIR` 赋值之后、`install -d` 之前 |
| `codex/install-skills.sh` | 变量与 `matt_*` 赋值之后、`install -d` 之前 |
| `architecture/install.sh` | `--prefix` 校验之后、`install -d` 之前（保留 `exit 2` 的既有语义） |
| ~~`docker-release/install.sh`~~ | ~~路径变量赋值之后、`install -d` 之前~~ —— 切出 #182 |

## T03 测试设计

一份源树、三段 git 状态、五个 installer。全部离线：本地 `git init --bare` 当 remote，
`git push` 走文件路径，不触网。

源树只复制 installer 实际读取的顶层目录（`codex/`、`architecture/`、`docker-release/`、
`templates/`、`skill-for-codex/`，约 5 MB），比 #162 的逐文件清单粗，
但六个 installer 的读取面合起来就是这几个目录。

| 段 | git 状态构造 | 对五个 installer 的断言 |
|---|---|---|
| level | `init` → `commit` → `push -u` | 退出 0；含 `source commit:` 与该 installer 的可读量行；`level with origin/main`；安装产物存在 |
| behind | `commit --allow-empty` + `push`，再 `reset --hard HEAD~1` | **非零退出**；含 `1 commit(s) behind origin/main` 与 `merge --ff-only`；**安装根仍不存在**（零写入） |
| no remote | `branch --unset-upstream` + `remote remove origin` | 退出 0；stderr 含 `WARNING: <installer>:` 与 `has no upstream`；安装产物存在 |

每个 installer 每段用独立安装根：

| installer | 调用方式 | 安装产物断言 |
|---|---|---|
| `install-host-access-broker` | `AISOFT_HOST_ACCESS_INSTALL_ROOT` | `usr/local/libexec/aisoft/host-access-broker` |
| `install-host-role` | `AISOFT_HOST_ROLE_INSTALL_ROOT` | `usr/local/libexec/aisoft/verify-host-role` |
| `install-vm` | `$1` = 安装根 | `.local/lib/aisoft-loop/aisoft_loop/cli.py` |
| `install-skills` | `$1` = 安装根 | `.agents/skills/aisoft-platform/SKILL.md` |
| `architecture/install` | `--prefix` | `bin/aisoft-architecture` |
| ~~`docker-release/install`~~ | ~~`AISOFT_DOCKER_RELEASE_INSTALL_ROOT`~~ | 切出 #182；`INSTALLERS` 数组用注释保留缺口说明 |

git 身份用 repo-local `user.name`/`user.email` 与 `commit.gpgsign=false`，
不依赖宿主全局配置（与 #162 测试同）。

detached HEAD 与非 git 目录两条降级路径已由
`test-install-host-access-broker.sh` 覆盖，且实现是同一份库，不再重复六遍。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-installer-source-guard.sh`（level 段逐 installer 断言 `source commit:` 与 §2.3 的可读量行；install-host-role / architecture / docker-release 三个 installer 的第二次运行即幂等路径由既有测试覆盖） |
| AC-2 | 同上（behind 段断言非零退出 + `1 commit(s) behind origin/main` + 安装根零写入；no-remote 段断言 `WARNING` 后仍成功安装） |
| AC-3 | `bash codex/tests/test-install-host-access-broker.sh` 未放宽任何断言即通过；另用同一 checkout 对新旧 broker installer 做三态输出 `diff`（level+no-op / behind / no-upstream），逐字节相同；`rg -c 'rev-list --count' codex/lib/install-source-guard.sh` 为 1 且五个 installer 各为 0 |
| AC-4 | 该测试文件存在且被 `smoke.sh` 执行 |
| AC-5 | `bash codex/tests/smoke.sh` |
| AC-6 | review `06-运维手册与踩坑集.md` 踩坑 20 含逐 installer 的可读量与判别方法 |

## 部署与回滚

无部署影响：本变更只改安装脚本的前置校验与输出，不改安装内容、不触及运行中的服务、
不改 CI 或部署流水线，因此不映射 `verification` 文档。

回滚 = revert 本 PR。合并后需由人在 **Mac 与 gitea-ci VM 两台**重跑相应 installer
让新版本生效——这是操作前置步骤，与本变更的交付闸门（人合并 PR）分离。
