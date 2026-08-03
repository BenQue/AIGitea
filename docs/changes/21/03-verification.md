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
首次因 `gitea-ci` 尚无 host-role guard/profile 在 2 秒后 fail closed。用户随后明确授权
Gate B prerequisite 与 Gate B：两台主机已安装 commit `5841e6e...` 对应的无 Secret
guard/profile；同一 job rerun PASS in 40s，exact artifact 已生成。AppServer prepare 幂等、
两次成功 readiness、一次故意 health failure 自动 rollback 与两次显式 rollback 均 PASS。
Gate B 结束时 AppServer candidate 离线，旧 runtime/8091 保持健康；Issue #13 保持 open。
Gate C、后续清理与 `prod-sim` 删除均未执行。

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
- Gate B 前已推送 evidence HEAD：`5841e6e921bba8fe7cee3591ade232331f029170`
- `rsdesign-new` prerequisite PR：
  `http://gitea-ci.orb.local:3000/admin/rsdesign-new/pulls/14`
  - final head：`71452d5cfa93f372bbc81b5ef01f5876bd9572cc`
  - required CI：Actions run/job #340，`CI / test (pull_request)`，PASS in 53s
  - state：merged at `2026-08-03T08:05:52+08:00`
  - merge SHA：`3323ab214b4222733715cacc536905392c042b60`
  - merge SHA status：Actions run/job #341，
    `Build & Publish Test Artifact / build-and-publish (push)`；首次 FAIL in 2s，安装授权
    prerequisite 后同一 job rerun PASS in 40s
  - exact artifact：168,890,220 bytes；SHA-256
    `04911201ecd91be5e77daf3678c19e404fd773fdcf5d46f40d8ea4e455913ebd`
  - PR 正文只有 `Refs #13`，因此 live Issue #13 保持 open
- 实时 Issue #21：open；标签精确包含 `type/platform`、`complexity/complex`、`approved`
- `gitea-ci`：hostname `gitea-ci`，machine ID
  `c7a9c69b3f604cc4b4c37123ab93e472`，Ubuntu 26.04 ARM64，running
  - `jq` 存在；guard/schema/catalog checksum 与 platform candidate 一致；profile
    `root:gitea-runner` mode 640、role=`scm-ci`
  - runner 身份下两次 package allow、artifact publish allow、application start deny/20
  - merge SHA artifact 存在且 checksum/tar safety/关键文件 PASS
  - legacy `3100`/`8091` 仍监听，`8091/api/health` 返回 `status=ok`
  - branch-only `pm2-gitea-runner.service` candidate 仍为 `disabled/inactive`
- AppServer：hostname `AppServer`，machine ID
  `149f0a0e2e1a4c1982289abeb01145d5`，running
  - 新增 `jq 1.8.1`、`libjq1`、`libonig5`，0 upgrade/0 remove；profile
    `root:benque` mode 640、role=`appserver-test`
  - `/opt/incoming`、`/opt/rsdesign-test`、无 Secret `.env`、stable scripts、exact
    artifact、mode 600 target SQLite、release 与三份 rollback backup 已建立
  - Gate B end-state：`current`、同名 PM2、`3100`/`8091` 均为空
- `prod-sim` baseline：name `prod-sim`，ID
  `01KX3FFXSJVYPDHZVY4MZB7CQZ`，Ubuntu `resolute` ARM64，running，磁盘约
  3.9 GB。该读取仅属于计划第 1 步 baseline，不代替 AC-10 的删除前双轮 inventory。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| worktree/branch/upstream/baseline | PASS | 编辑前从 detached HEAD 显式切换到已有且无人占用的 `change/21`；`git branch --show-current` 精确为 `change/21`；切换时 HEAD、`origin/change/21` 与 planning baseline 均为 `48d47f7edd4cc9190f80886260b974477fc20236` |
| `git fetch origin` + live Gitea Issue #21 | PASS | 开始时 `origin/main` 为 `b806317cc87a58049719fff103af2c9d7c14ed56`，远端 planning branch 为 `48d47f7edd4cc9190f80886260b974477fc20236`；Issue open 且所需三个标签仍存在。2026-08-03 恢复时 `origin/main` 已前进为 `7021224118a9d6b0bbb9e9cdd6ea5d4cbbb791bc`，未把其混入本 Change |
| Context7 OrbStack docs + local help | PASS | 官方文档与本机 OrbStack 2.2.1 `run`/`pull`/`push`/`delete` help 共同确认 named-machine command、`/mnt/mac` shared transfer 与 delete 语义；唯一允许的未来删除命令保持为 `orb delete --force prod-sim`，禁止 `--all` |
| Gate B CLI/API documentation checks | PASS | Context7 Ubuntu Server docs + live `apt-cache`/`apt-get -s` 确认 `jq` 安装为 3 new/0 upgrade/0 remove；live Gitea 1.26.4 Swagger 确认单 job rerun 为 `POST /repos/{owner}/{repo}/actions/runs/{run}/jobs/{job_id}/rerun` |
| schema/catalog/example JSON parse | PASS | versioned schema 定义 `scm-ci`、`appserver-test`、`appserver-prod`；catalog 使用固定 action/resource pair，未知值 fail closed |
| `bash codex/tests/test-host-role-guard.sh` | PASS | allow/deny、mutation order、identity mismatch、mode、缺字段、未知 capability、重复输出、Secret marker 均通过；禁止 action 未创建 mutation marker |
| `bash codex/tests/test-install-host-role.sh` | PASS | 仅安装 guard/schema/catalog/example；重复执行通过；不创建 live profile、Secret、service、timer 或 deployment |
| changed shell `bash -n` | PASS | `codex/tools/verify-host-role.sh`、`codex/install-host-role.sh` 及新增/修改 tests 均通过 |
| ShellCheck | PASS | 所有本 Change 新增或修改的 shell 文件通过 |
| `bash codex/tests/smoke.sh` | PASS | 实现后、文档后、blocker、跨仓库 handoff、merge evidence 与 Gate B evidence 记录后各运行一次；每次均为 105 项 Python tests 及全部 shell/static smoke 通过 |
| documentation state review | PASS | README、01/02/06/07/09/12 与 onboarding 已区分 current `scm-ci`、AppServer roles、legacy runtime 和待 Gate 清理；未修改本次运行遵循的 `AGENTS.md` |
| `gitea-ci` baseline inventory | PASS（第 1 步只读） | Gitea/runner/Verdaccio/Mailpit/PostgreSQL/Redis/Nginx/legacy app listeners、systemd/timers、DB 脱敏元数据、artifact/目录引用和 health 已盘点；不等同于第 10 步两轮 pre-delete inventory |
| `rsdesign-new` contract conflict resolution | PASS | 用户确认 #21 优先；live #13 title/body 已改为 AppServer migration；`change/13` 用 additive commits 删除旧 auto-restore source，历史未改写 |
| `rsdesign-new` prerequisite candidate/tests | PASS | build-only workflow、旧入口 deny、AppServer prepare/activate/validator/rollback 与 7 focused tests；fresh SQLite 后 70 files/326 tests、Next build、bash-n、ShellCheck 均 PASS |
| `rsdesign-new` prerequisite PR/CI | PASS | PR #14 exact head `71452d5...` required CI run/job #340 PASS；人工 merge SHA 为 `3323ab2...`，Issue #13 保持 open |
| live host-role prerequisite | PASS | 用户明确授权；`gitea-ci` 与 AppServer guard/profile identity/owner/mode/checksum/allow/deny 全部 PASS；未创建 Secret、service 或 timer |
| merge SHA build-only workflow | PASS after expected fail-closed | run/job #341 首次 FAIL in 2s；安装受保护 `scm-ci` prerequisite 后只重跑同一 job，commit status `success`、`Successful in 40s`；exact artifact checksum/tar safety PASS |
| Gate B artifact/SQLite transfer | PASS | Python SQLite backup API，不读取业务表；source/snapshot/target metadata、SHA-256、mode 与 quick_check PASS；artifact 通过 mode 700 Mac staging，每跳 checksum 一致 |
| Gate B prepare/readiness/rollback | PASS | prepare `created`/`already-present`；两次 exact SHA/PID cwd/direct health成功；bounded loopback health failure rc=1 后自动 rollback；两次显式 rollback；最终 candidate 离线、DB checksum/integrity 恢复 |
| `rsdesign-new` old shutdown/final cutover | BLOCKED Gate C | Gate B readiness PASS；旧 `gitea-ci` 3100/8091 仍健康，未停止 writer、未生成 final backup、未修改 Nginx、未形成迁移完成状态 |
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
| AC-5 | BLOCKED Gate C | prerequisite PR/CI/merge、merge SHA artifact、AppServer exact SHA/SQLite/readiness/health/rollback 均 PASS；Gate B 结束 candidate 离线。停止旧 host、final backup/transfer/activate 与用户入口验收尚未授权/运行 |
| AC-6 | NOT RUN | 未进入 SFM 独立 Issue/branch/PR 和 live Gate |
| AC-7 | NOT RUN | 未进入 MyApp inventory/backup/restore 与删除 Gate |
| AC-8 | NOT RUN | 已有第 1 步 baseline，但尚无收口前后成对验证 |
| AC-9 | NOT RUN | retention tool/dry-run 与 Redis/Nginx predicate 尚未实施 |
| AC-10 | NOT RUN | 尚未执行两轮 pre-delete inventory 与完整 dependency/unique-data/rebuild Gate |
| AC-11 | NOT RUN | 未执行任何 VM 删除；`gitea-ci`、AppServer 和其它 VM 均未删除 |
| AC-12 | PASS | 定向 tests、`bash -n`、ShellCheck、六次 full smoke、live allow/deny/幂等和故意 health failure rollback 均通过 |
| AC-13 | BLOCKED | 本文件已记录当前精确 SHA/状态/证据，但后续 live Gate、final head、CI 与 PR 尚不存在 |
| AC-14 | PASS（截至阻塞点） | prerequisite PR 已由人合并；Gate B prerequisite/readiness 有独立明确授权且结束 candidate 离线；未执行 Gate C、cleanup、数据库/目录/制品删除或任何 VM 操作；未创建平台 final PR、未部署生产 |

## 重复部署/执行

- host-role guard allow：PASS，两次输出一致。
- host-role guard deny：PASS，禁止的 application start 在 mutation 前返回 denied，mutation
  marker 不存在。
- installer：PASS，两次执行结果一致。
- live prepare：PASS，首次 created、重复 already-present，均未启动 PM2。
- live readiness：两次成功；每次随后显式 rollback，最终 current/PM2/listener 为空。
- `gitea-ci` inventory：第 1 步 baseline PASS；AC-10 关联的两轮 inventory NOT RUN。
- `prod-sim` 删除只允许执行一次；当前 NOT RUN，未来以删除前双读和删除后双读替代重复
  destructive action。

## 故意失败与回滚

- `scm-ci` 请求 application start：PASS；denied 且零 mutation。
- identity mismatch/profile 权限错误/未知 capability：PASS；均 fail closed。
- installer 重复执行：PASS；未创建 live runtime 配置。
- 应用 readiness failure：PASS expected failure；bounded loopback fixture 触发 direct health
  failure，stable script 自动恢复 DB/current/PM2，fixture 由 trap 清理。
- 应用显式 rollback：两次 PASS，previous=absent；三份 mode 700 backup 保留。
- `prod-sim` identity/引用不满足：NOT RUN；预期停止删除。
- `prod-sim` 删除后整机原地 rollback：不可能；恢复路径只能依据版本化最小基线重新创建。

## 操作与授权账本

| Object/action | Authorization | Result |
|---|---|---|
| host-role repository implementation/tests/docs | Issue #21 `approved` 合同内 | PASS |
| `rsdesign-new` contract/candidate/PR | 用户已确认合同优先级；应用 Issue/branch/PR 内实施 | PASS，PR #14 CI PASS 并已由人合并，Issue #13 保持 open |
| `rsdesign-new` host prerequisites/readiness | 用户明确授权 Gate B prerequisite 与 Gate B | PASS，结束时 AppServer candidate 离线、旧 runtime 健康 |
| `rsdesign-new` final cutover | 仍需独立 Gate C | BLOCKED，未停止旧 writer/8091、未做 final backup/activate/外部验收 |
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
- `orb pull` 对绝对 `/opt/artifacts/...` source 返回 source-relative path error，未复制任何文件；
  随后按官方文档改用 `/mnt/mac` mode 700 staging，source/Mac/target checksum 一致。

## 当前 blocker 与恢复条件

合同优先级、人工合并、post-merge workflow 与 Gate B blocker 已解除。当前 blocker 是尚未
取得的 Gate C：Gate B 已证明 AppServer exact SHA、SQLite、唯一 PID/cwd、direct health、
自动/显式 rollback 可用，并在结束时将 candidate 恢复为离线；旧 writer/8091 保持健康。

恢复条件：用户单独授权 Gate C 的精确动作，重新读取 live source DB/runtime 后，停止旧
PM2 writer 与 8091 入口，生成 final SQLite backup/checksum/quick-check，传输并 mode 600，
AppServer activate/validate 与外部入口验收；任一步失败即恢复旧 runtime/entry。Gate C 不
隐含 disabled unit/vhost cleanup、目录/DB/release/artifact/backup/log 删除或任何 VM 操作。

## 遗留风险与未完成项

- `rsdesign-new` Gate B 已 PASS；Gate C 仍阻塞计划第 6 步完成和所有后续顺序步骤。
- source readiness snapshot、Mac mode 700 staging、AppServer incoming artifact/DB/release 与
  rollback backups 按禁止删除边界保留，cleanup 另需授权。
- 任何 planning/baseline inventory 都可能漂移，恢复后须重新采集 live state。
- 除精确 `prod-sim` 外的 destructive action 仍需逐项明确授权。
- `prod-sim` 授权不等于 AC-10 已通过；当前不得删除。
- final cutover、应用 verification PR/CI、平台后续步骤与所有未执行 live Gate 保持
  `BLOCKED/NOT RUN`。
