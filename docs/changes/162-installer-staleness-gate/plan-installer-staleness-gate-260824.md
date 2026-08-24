---
issue: 162
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/162
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
branch: change/162-installer-staleness-gate
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan · installer staleness gate（#162）

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | installer 的 provenance 输出与 staleness fail-closed 闸门（AC-1、AC-2） | - | done |
| T02 | `test-install-host-access-broker.sh` 与 smoke 注册（AC-3、AC-4） | T01 | done |
| T03 | `06` 踩坑 20 补记（AC-5） | T01 | done |

T01 是可独立验收的垂直切片：改完即可手工在本仓库复现两条路径。
T02 把该行为钉进 smoke；T03 只动文档。

## Expected touch points

- **T01**：`codex/install-host-access-broker.sh`
- **T02**：`codex/tests/test-install-host-access-broker.sh`（新增）、`codex/tests/smoke.sh`
- **T03**：`06-运维手册与踩坑集.md`（踩坑 20 一行）

范围提示，不授权扩大 spec §5 的授权清单。

## T01 实现要点

1. 在 `ROOT` 计算之后、`install -d` **之前**插入 provenance + 闸门，
   保证拒绝时文件系统零写入（spec §2.2）。
2. `source_commit()`：`git -C "$ROOT" rev-parse --short HEAD`，失败得 `unknown`。
   先用 `git -C "$ROOT" rev-parse --git-dir` 判定是否 git 工作区，
   并用 `command -v git` 判定 git 是否可用——两条都失败即走警告路径。
3. `source_operations()`：`python3 -c` 读 `.operations` 长度，失败得 `unknown`，不致命。
4. 分支与 upstream：
   - `git symbolic-ref --quiet --short HEAD` 空 → detached → 警告。
   - `git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'` 失败 → 无 upstream → 警告。
   - `git rev-parse --verify --quiet "<upstream>^{commit}"` 失败 → ref 不可解析 → 警告。
   - `git rev-list --count "HEAD..<upstream>"` > 0 → 拒绝。
5. 所有 git 调用加 `2>/dev/null` 并在 `set -e` 下用 `|| true` / `if` 包裹，
   避免探测失败把 installer 打成非零退出——**探测不到不等于落后**（spec §2.2）。

## T02 测试设计

全部离线：用本地 `git init --bare` 目录当 remote，`git push` 走文件路径，不触网。

`make_source_tree()` 只复制 installer 实际读取的源（多一个少一个都会让测试失真）：

```
codex/install-host-access-broker.sh
codex/runtime/aisoft_host_access/          codex/runtime/aisoft_gitea_governance/
codex/runtime/aisoft_change_name.py
codex/config/{host-access-broker,gitea-governance,gitea-labels}.json
codex/tools/{host-access-broker,git-credential-aisoft-host,project-profile-migration}.sh
```

| Case | 源状态构造 | 断言 |
|---|---|---|
| level | init → commit → push -u | 退出 0；含 `source commit:`；`source operations:` 等于真实长度；已安装文件存在 |
| level 二次运行 | 同上再跑一次 | 退出 0；含 `already current (no-op)`；**provenance 仍然打印**（AC-1 覆盖 no-op 路径） |
| behind | push 后 `commit --allow-empty` + push，再 `reset --hard HEAD~1` | **非零退出**；stderr 含 `behind` 与 `1 commit`；**安装根仍不存在**（零写入） |
| no remote | init → commit，不加 remote | 退出 0；stderr 含 `WARNING`；已安装文件存在 |
| detached HEAD | level 源上 `checkout --detach` | 退出 0；stderr 含 `WARNING`；已安装文件存在 |
| non-git | 只复制文件，不 `git init` | 退出 0；stderr 含 `WARNING`；已安装文件存在 |

每个 case 用独立的 `AISOFT_HOST_ACCESS_INSTALL_ROOT`，互不污染。
git 身份用 repo-local `user.name`/`user.email` 与 `commit.gpgsign=false`，
不依赖宿主全局配置。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-install-host-access-broker.sh`（level 与二次运行两个 case 断言 `source commit:` / `source operations:` 与真实 `.operations` 长度一致） |
| AC-2 | 同上（behind case 断言非零退出 + `behind` + 安装根零写入；no-remote / detached / non-git 三个 case 断言 `WARNING` 后仍成功安装） |
| AC-3 | 该测试文件存在且被 `smoke.sh` 执行 |
| AC-4 | `bash codex/tests/smoke.sh` |
| AC-5 | review `06-运维手册与踩坑集.md` 踩坑 20 行含「装了、装的是旧的」判别方法 |

## 部署与回滚

无部署影响：本变更只改安装脚本的前置校验与输出，不改安装内容、不触及运行中的服务、
不改 CI 或部署流水线，因此不映射 `verification` 文档。

回滚 = revert 本 PR。合并后需由人在 **Mac 与 gitea-ci VM 两台**执行
`sudo bash codex/install-host-access-broker.sh` 让新 installer 生效——
这是操作前置步骤，与本变更的交付闸门（人合并 PR）分离。
