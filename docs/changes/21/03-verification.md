---
issue: 21
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/21
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-change
  - deployment
  - migration
  - destructive-operation
  - rollback
  - platform-governance
depends_on: []
status: blocked
branch: change/21
pr_url:
created: 2026-08-02
updated: 2026-08-03
---

# Verification

## 当前结论

平台 host-role 合同、fail-closed guard、installer、fixtures、测试和文档已实现并通过本地
验证。2026-08-03 用户确认 #21 为最终架构合同；正式 `rsdesign-new` Issue #13 已改写为
AppServer migration，旧 reboot auto-restore candidate 已在 branch source 中撤销。prerequisite
PR #14 的 final head required CI 已 PASS，并已由人工合并为
`3323ab214b4222733715cacc536905392c042b60`。merge SHA 的 build-only Actions run/job #341
在 2 秒后失败；只读复核确认 `gitea-ci` 尚无 host-role guard/profile，且该 SHA artifact 未
生成，符合 fail-closed 设计。Issue #13 保持 open，旧 runtime 保持健康；AppServer live
Gate、旧 runtime stop、后续清理与 `prod-sim` 删除均未执行。

## 环境与版本

- Planning baseline：`48d47f7edd4cc9190f80886260b974477fc20236`
- Source baseline：`origin/main@b806317cc87a58049719fff103af2c9d7c14ed56`
- 2026-08-03 恢复时平台 `origin/main` readback：
  `7021224118a9d6b0bbb9e9cdd6ea5d4cbbb791bc`
- Candidate branch：`change/21`，跟踪 `origin/change/21`
- 恢复前已推送实现/文档 HEAD：`6250ed35d8065c0be51d33eff9350611a5efefff`
  - `64fe9e8 feat(platform): add fail-closed host role guard`
  - `c3c310a docs(platform): separate scm and app server roles`
  - `c61b29a docs(platform): record issue 21 contract blocker`
  - `6250ed3 docs(platform): record rsdesign migration handoff`
- `rsdesign-new` prerequisite PR：
  `http://gitea-ci.orb.local:3000/admin/rsdesign-new/pulls/14`
  - final head：`71452d5cfa93f372bbc81b5ef01f5876bd9572cc`
  - required CI：Actions run/job #340，`CI / test (pull_request)`，PASS in 53s
  - state：merged at `2026-08-03T08:05:52+08:00`
  - merge SHA：`3323ab214b4222733715cacc536905392c042b60`
  - merge SHA status：Actions run/job #341，
    `Build & Publish Test Artifact / build-and-publish (push)`，FAIL in 2s
  - PR 正文只有 `Refs #13`，因此 live Issue #13 保持 open
- 实时 Issue #21：open；标签精确包含 `type/platform`、`complexity/complex`、`approved`
- `gitea-ci`：hostname `gitea-ci`，machine ID
  `c7a9c69b3f604cc4b4c37123ab93e472`，Ubuntu 26.04 ARM64，running
  - `jq` 存在；live guard/profile 均缺失；merge SHA artifact 缺失
  - legacy `3100`/`8091` 仍监听，`8091/api/health` 返回 `status=ok`
  - branch-only `pm2-gitea-runner.service` candidate 仍为 `disabled/inactive`
- AppServer：hostname `AppServer`，machine ID
  `149f0a0e2e1a4c1982289abeb01145d5`，running
  - `jq`、live guard/profile、`/opt/incoming`、`/opt/rsdesign-test` 均缺失
  - `3100`/`8091` 均无 listener
- `prod-sim` baseline：name `prod-sim`，ID
  `01KX3FFXSJVYPDHZVY4MZB7CQZ`，Ubuntu `resolute` ARM64，running，磁盘约
  3.9 GB。该读取仅属于计划第 1 步 baseline，不代替 AC-10 的删除前双轮 inventory。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| worktree/branch/upstream/baseline | PASS | 编辑前从 detached HEAD 显式切换到已有且无人占用的 `change/21`；`git branch --show-current` 精确为 `change/21`；切换时 HEAD、`origin/change/21` 与 planning baseline 均为 `48d47f7edd4cc9190f80886260b974477fc20236` |
| `git fetch origin` + live Gitea Issue #21 | PASS | 开始时 `origin/main` 为 `b806317cc87a58049719fff103af2c9d7c14ed56`，远端 planning branch 为 `48d47f7edd4cc9190f80886260b974477fc20236`；Issue open 且所需三个标签仍存在。2026-08-03 恢复时 `origin/main` 已前进为 `7021224118a9d6b0bbb9e9cdd6ea5d4cbbb791bc`，未把其混入本 Change |
| Context7 OrbStack docs + local `orb --help`/`orb delete --help` | PASS | 官方文档与本机 OrbStack 2.2.1 help 共同确认 `list`/`info`/`delete` 语义；delete 永久删除 VM 文件，唯一允许的未来命令保持为 `orb delete --force prod-sim`，禁止 `--all` |
| schema/catalog/example JSON parse | PASS | versioned schema 定义 `scm-ci`、`appserver-test`、`appserver-prod`；catalog 使用固定 action/resource pair，未知值 fail closed |
| `bash codex/tests/test-host-role-guard.sh` | PASS | allow/deny、mutation order、identity mismatch、mode、缺字段、未知 capability、重复输出、Secret marker 均通过；禁止 action 未创建 mutation marker |
| `bash codex/tests/test-install-host-role.sh` | PASS | 仅安装 guard/schema/catalog/example；重复执行通过；不创建 live profile、Secret、service、timer 或 deployment |
| changed shell `bash -n` | PASS | `codex/tools/verify-host-role.sh`、`codex/install-host-role.sh` 及新增/修改 tests 均通过 |
| ShellCheck | PASS | 所有本 Change 新增或修改的 shell 文件通过 |
| `bash codex/tests/smoke.sh` | PASS | 实现后、文档后、blocker 记录后、跨仓库 handoff 记录后与 merge evidence 记录后各运行一次；每次均为 105 项 Python tests 及全部 shell/static smoke 通过 |
| documentation state review | PASS | README、01/02/06/07/09/12 与 onboarding 已区分 current `scm-ci`、AppServer roles、legacy runtime 和待 Gate 清理；未修改本次运行遵循的 `AGENTS.md` |
| `gitea-ci` baseline inventory | PASS（第 1 步只读） | Gitea/runner/Verdaccio/Mailpit/PostgreSQL/Redis/Nginx/legacy app listeners、systemd/timers、DB 脱敏元数据、artifact/目录引用和 health 已盘点；不等同于第 10 步两轮 pre-delete inventory |
| `rsdesign-new` contract conflict resolution | PASS | 用户确认 #21 优先；live #13 title/body 已改为 AppServer migration；`change/13` 用 additive commits 删除旧 auto-restore source，历史未改写 |
| `rsdesign-new` prerequisite candidate/tests | PASS | build-only workflow、旧入口 deny、AppServer prepare/activate/validator/rollback 与 7 focused tests；fresh SQLite 后 70 files/326 tests、Next build、bash-n、ShellCheck 均 PASS |
| `rsdesign-new` prerequisite PR/CI | PASS | PR #14 exact head `71452d5...` required CI run/job #340 PASS；人工 merge SHA 为 `3323ab2...`，Issue #13 保持 open |
| merge SHA build-only workflow | BLOCKED | run/job #341 FAIL in 2s；workflow 在 checkout 后首先调用 host-role guard，只读复核发现 `gitea-ci` guard/profile 缺失且 exact-SHA artifact 未生成。需 Gate B 明确授权主机 prerequisite 后才能重跑 |
| `rsdesign-new` AppServer migration/old shutdown | BLOCKED | 人工合并已完成，但尚无 Gate B/C。AppServer 仍无 `jq`、guard/profile、`/opt/rsdesign-test` 与 3100/8091 runtime；旧 `gitea-ci` runtime/8091 健康且未停止 |
| SFM smoke cleanup | NOT RUN | 按计划顺序停在第 6 步，未进入所属应用仓库、未终止 3212 |
| MyApp/Redis/Nginx/artifact cleanup | NOT RUN | 未获逐项 Gate，未停止服务、未删除 DB/目录/制品 |
| artifact retention implementation/dry-run | NOT RUN | 按计划顺序尚未进入第 9 步 |
| `prod-sim` pre-delete two-round inventory | NOT RUN | 按计划顺序尚未进入第 10 步；第 1 步 identity baseline 不满足 AC-10 |
| `prod-sim` delete/post-check | NOT RUN | 精确删除虽已获授权，但 AC-10 的依赖、唯一数据与可重建证据尚未全部通过，因此未执行 |
| AISoftPlatform final PR CI | NOT RUN | 平台 final PR 尚未创建；`change/21` branch push 只保存候选与 blocker 证据，不能用应用 prerequisite PR 或 branch push 替代 final acceptance |

## Acceptance criteria 结果

| Acceptance criterion | Result | Evidence |
|---|---|---|
| AC-1 | PASS | schema、catalog、example 与正反 fixtures 已实现；缺字段、未知 role/capability 均 fail closed |
| AC-2 | PASS | 单一 guard 在 mutation 前按固定 capability 判定；`scm-ci` 的 application start/deploy、业务 DB 与长驻 smoke 被拒绝 |
| AC-3 | PASS | production profile/identity 路径固定；owner/mode/parent/hostname/machine ID 检查完整；调用方无 profile/identity override；输出脱敏测试通过 |
| AC-4 | PASS | 指定平台文档与 onboarding 已明确 SCM/CI 与 AppServer 分离，并把同机 runtime 标为 legacy/pending Gate |
| AC-5 | BLOCKED | 合同冲突已解决，应用 prerequisite PR CI PASS 且已人工合并；merge SHA build-only workflow 因 live host-role prerequisite 缺失而 FAIL，仍需独立 Gate B/C。AppServer migration、SQLite/health/rollback 与旧 host shutdown 未执行 |
| AC-6 | NOT RUN | 未进入 SFM 独立 Issue/branch/PR 和 live Gate |
| AC-7 | NOT RUN | 未进入 MyApp inventory/backup/restore 与删除 Gate |
| AC-8 | NOT RUN | 已有第 1 步 baseline，但尚无收口前后成对验证 |
| AC-9 | NOT RUN | retention tool/dry-run 与 Redis/Nginx predicate 尚未实施 |
| AC-10 | NOT RUN | 尚未执行两轮 pre-delete inventory 与完整 dependency/unique-data/rebuild Gate |
| AC-11 | NOT RUN | 未执行任何 VM 删除；`gitea-ci`、AppServer 和其它 VM 均未删除 |
| AC-12 | PASS | 定向 tests、`bash -n`、ShellCheck、五次 full smoke 和禁止 application start 的零 mutation 测试均通过 |
| AC-13 | BLOCKED | 本文件已记录当前精确 SHA/状态/证据，但后续 live Gate、final head、CI 与 PR 尚不存在 |
| AC-14 | PASS（截至阻塞点） | prerequisite PR 已由人合并；未执行未获授权的主机 prerequisite、迁移、服务停止或数据库/目录删除；未扩大 `prod-sim` 授权；未创建平台 final PR、未部署生产 |

## 重复部署/执行

- host-role guard allow：PASS，两次输出一致。
- host-role guard deny：PASS，禁止的 application start 在 mutation 前返回 denied，mutation
  marker 不存在。
- installer：PASS，两次执行结果一致。
- `gitea-ci` inventory：第 1 步 baseline PASS；AC-10 关联的两轮 inventory NOT RUN。
- `prod-sim` 删除只允许执行一次；当前 NOT RUN，未来以删除前双读和删除后双读替代重复
  destructive action。

## 故意失败与回滚

- `scm-ci` 请求 application start：PASS；denied 且零 mutation。
- identity mismatch/profile 权限错误/未知 capability：PASS；均 fail closed。
- installer 重复执行：PASS；未创建 live runtime 配置。
- 应用迁移失败回切：NOT RUN。
- `prod-sim` identity/引用不满足：NOT RUN；预期停止删除。
- `prod-sim` 删除后整机原地 rollback：不可能；恢复路径只能依据版本化最小基线重新创建。

## 操作与授权账本

| Object/action | Authorization | Result |
|---|---|---|
| host-role repository implementation/tests/docs | Issue #21 `approved` 合同内 | PASS |
| `rsdesign-new` contract/candidate/PR | 用户已确认合同优先级；应用 Issue/branch/PR 内实施 | PASS，PR #14 CI PASS 并已由人合并，Issue #13 保持 open |
| `rsdesign-new` host prerequisites/application migration | prerequisite PR 已人工合并；仍需分别取得 Gate B/C | BLOCKED，post-merge 只读核对确认 live 零 mutation |
| SFM process stop | 仍需应用仓 PR 与 live Gate | NOT RUN |
| MyApp service/DB/directory removal | 仍需逐对象 live Gate | NOT RUN |
| artifact/Redis/Nginx apply | 仍需 predicate、dry-run 与 live Gate | NOT RUN |
| exact `prod-sim` delete | 用户已授权，但仅在 AC-10 全部通过后有效 | NOT RUN |
| any other VM delete or `--all` | 未授权且明确禁止 | NOT RUN |

## 观察偏差与副作用核对

- sandbox 内首次 `orb list` 因无法连接 OrbStack backend 超时；在 host context 的只读调用
  成功。前一次超时只记为 `SANDBOX_PATH_BLOCKED`，未把它当作 VM 状态。
- 一次 PM2 只读盘点误用了 `/home/gitea-runner/.pm2`；PM2 尝试创建目录/daemon，但均因权限
  不足失败。后检查未产生目录或 daemon，未停止、启动或更改现有进程。

## 当前 blocker 与恢复条件

合同优先级与人工合并 blocker 已解除。当前 blocker 是 post-merge build-only workflow 的 live
host-role prerequisite 与尚未取得的 Gate B：merge SHA `3323ab2...` 已读回，但 run/job #341
fail closed，`gitea-ci` 无 guard/profile 且 exact-SHA artifact 未生成；AppServer 也无 `jq`、
guard/profile、目标目录或 runtime。Issue #13 保持 open，旧 writer/8091 保持健康。

恢复条件：用户明确授权 Gate B 的精确 live 动作，先在 `gitea-ci` 安装无 Secret 的
guard/schema/catalog 与受保护 `scm-ci` profile，重跑 build-only workflow 并核对 exact-SHA
artifact；再在 AppServer 提供 `jq`、受保护 `appserver-test` profile、目录、operator-owned
配置、artifact/SQLite snapshot 并做 candidate readiness/rollback。Gate B 不包含停止旧
writer、修改 8091、删除目录/数据库/制品或任何 VM；这些仍分别属于 Gate C、后续 cleanup
Gate 和 AC-10/AC-11。

## 遗留风险与未完成项

- `rsdesign-new` merge SHA workflow 当前 FAIL；Gate B/C 阻塞计划第 6 步和所有后续顺序步骤。
- 任何 planning/baseline inventory 都可能漂移，恢复后须重新采集 live state。
- 除精确 `prod-sim` 外的 destructive action 仍需逐项明确授权。
- `prod-sim` 授权不等于 AC-10 已通过；当前不得删除。
- PR 人工合并、CI、应用迁移、部署和所有未执行 live Gate 保持 `BLOCKED/NOT RUN`。
