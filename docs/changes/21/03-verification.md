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
status: verification-in-progress
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
Gate B 结束时 AppServer candidate 离线，旧 runtime/8091 保持健康；Issue #13 保持 open。用户
随后单独授权 Gate C；重新 fetch 并核对 exact SHA、Issue 标签、两端身份/runtime/DB、NGINX
symlink 与回滚路径后，旧 writer/8091 已可逆停止，停写后的 final SQLite backup 已逐跳校验并
激活到 AppServer。exact current/唯一 PID/cwd、direct/macOS 外部 health、DB integrity、旧端
持续停写及无关服务检查全部 PASS。用户随后明确把本应用全部不需要、过时对象纳入 Gate D
整体授权，无需逐对象再次等待批准；删除前仍完成精确对象、依赖、引用、唯一数据与可重建性
盘点。`gitea-ci` 旧 PM2 home/unit/vhost/runtime、source snapshots、两端冗余传输副本和三份
Gate B rollback 已清理，AppServer exact runtime、权威 artifact 与最新 Gate C recovery baseline
保留。删除后 absent、single-writer、外部 health、DB integrity 及无关服务全部 PASS。应用 final
verification PR #15 final head `dbe483d9c8991b365957610961ee18cca28f0b34`、正文含
`Closes #13`；required Actions run/job #344 successful in 50s。用户随后人工合并，live API 与
`origin/main` 均读回 merge SHA `480dd7d0b55eebb0b12d60e23261a64b60d9ce7e`，Issue #13 已关闭，
第 6 步完成。平台随后按顺序进入第 7 步：保留 SFMDigitalBoard 脏 main checkout，在独立
`change/86` 实施 process-group cleanup 与 current-run DB finalizer。应用本地 bash-n、ShellCheck、
platform suite、148 files/949 tests 与 production build 全部 PASS；最终 PR #87 head
`58d8df7b400181ea05ed9578b487ddad61b4422c`、正文含 `Closes #86`，required Actions run/job #346
在 Node 22 上 successful in 1m43s。Issue #86 已从 `approved` 切换为 `pr-open`，PR open/mergeable，
但尚未由人合并；live 3212 process stop 与 15 个历史 DB 删除仍为独立 Gate，均未执行。后续步骤
与 `prod-sim` 删除也仍未执行；本结论不表示部署或 live cleanup，也不把任何既有 Gate D 授权
扩大到 SFMDigitalBoard、其它应用或任何 VM。

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
- `rsdesign-new` final verification PR：
  `http://gitea-ci.orb.local:3000/admin/rsdesign-new/pulls/15`
  - final head：`dbe483d9c8991b365957610961ee18cca28f0b34`
  - base：`3323ab214b4222733715cacc536905392c042b60`
  - 正文含 `Closes #13`；required Actions run/job #344，
    `CI / test (pull_request)`，PASS in 50s
  - state：人工 merged at `2026-08-03T11:30:23+08:00`
  - merge SHA：`480dd7d0b55eebb0b12d60e23261a64b60d9ce7e`
  - live Issue #13：closed；final head 为 `origin/main` 祖先
- SFMDigitalBoard code PR：
  `http://gitea-ci.orb.local:3000/admin/SFMDigitalBoard/pulls/87`
  - 正式 repo：`/Users/benque/Projects/SFMDigitalBoard`；脏 main checkout 原样保留，实施 worktree
    为 `/private/tmp/sfm-change-86`
  - baseline/base：`d9d3b994dfa94421ccb12b51c01db5336eb61e7a`
  - final head：`58d8df7b400181ea05ed9578b487ddad61b4422c`
  - commits：`85bcad3`（合同文档）、`07f4a32`（实现/测试）、`58d8df7`（本地验证证据）
  - PR open、非 draft、mergeable；正文含 `Closes #86`
  - required CI：Actions run/job #346，`CI / verify (pull_request)`，PASS in 1m43s
  - live Issue #86：open，标签 `pr-open`；尚未人工合并
  - live 3212/PID `2487` 与 15 个历史 runner DB：未停止、未删除
- 实时 Issue #21：open；标签精确包含 `type/platform`、`complexity/complex`、`approved`
- `gitea-ci`：hostname `gitea-ci`，machine ID
  `c7a9c69b3f604cc4b4c37123ab93e472`，Ubuntu 26.04 ARM64，running
  - `jq` 存在；guard/schema/catalog checksum 与 platform candidate 一致；profile
    `root:gitea-runner` mode 640、role=`scm-ci`
  - runner 身份下两次 package allow、artifact publish allow、application start deny/20
  - merge SHA artifact 存在且 checksum/tar safety/关键文件 PASS
  - Gate C pre-state：legacy `3100`/`8091` 均健康；old PID `219460` cwd 指向
    `49033a12.../app`，source SQLite SHA-256 `095c59...eeeb`、quick_check=ok
  - Gate C post-state：old PM2 entry 保留为 stopped，`3100`/`8091` absent；原 vhost file
    checksum 不变，enabled symlink 可逆保留为 sites-available 下的 disabled symlink
  - Gate D post-state：旧 `/opt/rsdesign-test`、`/opt/act-runner/.pm2`、unit/vhost 与 source
    snapshots 均 absent；unit readback `not-found/inactive`，3100/8091 仍 absent
- AppServer：hostname `AppServer`，machine ID
  `149f0a0e2e1a4c1982289abeb01145d5`，running
  - 新增 `jq 1.8.1`、`libjq1`、`libonig5`，0 upgrade/0 remove；profile
    `root:benque` mode 640、role=`appserver-test`
  - `/opt/incoming`、`/opt/rsdesign-test`、无 Secret `.env`、stable scripts、exact
    artifact、mode 600 target SQLite、release 与 rollback backup 已建立
  - Gate B end-state：`current`、同名 PM2、`3100`/`8091` 均为空
  - Gate C post-state：`current`/release marker/唯一 PID `278336` cwd 均为
    `3323ab214b4222733715cacc536905392c042b60`；3100 direct 与
    `http://AppServer.orb.local:3100/api/health` external 均为 `status=ok`；8091 absent
  - final target SQLite 为 `benque:benque` mode 600、SHA-256 `f4e576...57d7`、
    quick_check=ok；Gate C rollback manifest 为 `20260803T022232Z-...-277996`
  - Gate D post-state：冗余 incoming transfer files 与三份 Gate B backup absent；只保留上述
    Gate C manifest，mode 700，`db.before` checksum/integrity PASS；active runtime/DB 不变
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
| `bash codex/tests/smoke.sh` | PASS | 实现后、文档后、blocker、跨仓库 handoff、merge evidence、Gate B/C/D 与 SFM PR/CI evidence 记录后运行；累计十一次均为 105 项 Python tests 及全部 shell/static smoke 通过，最后一次覆盖 PR #87 required CI 与 live Gate 未执行边界 |
| documentation state review | PASS | README、01/02/06/07/09/12 与 onboarding 已区分 current `scm-ci`、AppServer roles、legacy runtime 和待 Gate 清理；未修改本次运行遵循的 `AGENTS.md` |
| `gitea-ci` baseline inventory | PASS（第 1 步只读） | Gitea/runner/Verdaccio/Mailpit/PostgreSQL/Redis/Nginx/legacy app listeners、systemd/timers、DB 脱敏元数据、artifact/目录引用和 health 已盘点；不等同于第 10 步两轮 pre-delete inventory |
| `rsdesign-new` contract conflict resolution | PASS | 用户确认 #21 优先；live #13 title/body 已改为 AppServer migration；`change/13` 用 additive commits 删除旧 auto-restore source，历史未改写 |
| `rsdesign-new` prerequisite candidate/tests | PASS | build-only workflow、旧入口 deny、AppServer prepare/activate/validator/rollback 与 7 focused tests；fresh SQLite 后 70 files/326 tests、Next build、bash-n、ShellCheck 均 PASS |
| `rsdesign-new` prerequisite PR/CI | PASS | PR #14 exact head `71452d5...` required CI run/job #340 PASS；人工 merge SHA 为 `3323ab2...`，Issue #13 保持 open |
| live host-role prerequisite | PASS | 用户明确授权；`gitea-ci` 与 AppServer guard/profile identity/owner/mode/checksum/allow/deny 全部 PASS；未创建 Secret、service 或 timer |
| merge SHA build-only workflow | PASS after expected fail-closed | run/job #341 首次 FAIL in 2s；安装受保护 `scm-ci` prerequisite 后只重跑同一 job，commit status `success`、`Successful in 40s`；exact artifact checksum/tar safety PASS |
| Gate B artifact/SQLite transfer | PASS | Python SQLite backup API，不读取业务表；source/snapshot/target metadata、SHA-256、mode 与 quick_check PASS；artifact 通过 mode 700 Mac staging，每跳 checksum 一致 |
| Gate B prepare/readiness/rollback | PASS | prepare `created`/`already-present`；两次 exact SHA/PID cwd/direct health成功；bounded loopback health failure rc=1 后自动 rollback；两次显式 rollback；最终 candidate 离线、DB checksum/integrity 恢复 |
| Gate C CLI/docs/local-help review | PASS | Context7 OrbStack、NGINX 与 PM2 官方文档确认 named-machine、`nginx -t`/graceful reload、named stop/restart semantics；本机 OrbStack 2.2.1 与 live NGINX 1.28.3/PM2 help 复核。未使用 `nginx -T`，未读取 PM2 environment |
| `rsdesign-new` old shutdown/final cutover | PASS Gate C | 用户独立授权且 Issue #21 标签再次精确读回；只停止 `/opt/act-runner/.pm2` 的 `rsdesign-new`，保留 stopped entry。8091 enabled symlink 可逆移动、vhost file SHA-256 `8e9a65...e789` 不变，`nginx -t`/reload PASS；old 3100/8091 与外部入口均 absent |
| Gate C final SQLite/transfer | PASS | writer 停止后 source checksum/integrity 不变；SQLite backup API 生成 mode 600 final snapshot，SHA-256 `f4e576...57d7`、quick_check=ok；source → mode 700 Mac staging → AppServer incoming/target 每跳 checksum/mode/integrity PASS，未读业务表 |
| Gate C AppServer activation/external health | PASS | stable script 返回 `ACTIVATE_OK`；rollback manifest `20260803T022232Z-...-277996`/`db.before` 完整。`APP_VALIDATION_OK`，exact current/marker/唯一 PID `278336` cwd 一致；direct 与 macOS external 3100 均 `status=ok`，target DB mode 600/integrity PASS |
| Gate C cross-host/unrelated post-check | PASS | single writer：old pid=0/3100/8091 absent，AppServer only 3100；Gitea health、runner、AppServer 既有 listener 与 3202 health 不受影响。old DB/release/vhost/process entry、两端 snapshots/artifacts/releases 与 4 个 rollback dirs 全部保留；Gate D/delete/VM operation NOT RUN |
| Gate C delayed stability readback | PASS | `2026-08-03T10:29+08:00` 再次 `APP_VALIDATION_OK`，PID 仍为 `278336`，external health/target DB integrity PASS，`pm2-benque.service` active/enabled；old pid=0、3100/8091 absent、source DB checksum 不变，Gitea/runner/3202 health 均 PASS |
| `rsdesign-new` Gate D authorization/docs review | PASS | 用户整体授权本应用全部过时对象 cleanup，无需逐对象再次等待；范围不含其它应用、生产或 VM。Context7 systemd/PM2/NGINX/OrbStack 官方文档与本机 OrbStack 2.2.1、systemd 259、PM2、NGINX 1.28.3 help 复核，使用 exact-name/path 命令 |
| Gate D pre-delete inventory/rebuild proof | PASS | 旧 runtime 4,640,403,456 bytes/8 releases；source/target SQLite size、checksum、quick_check 与 zero-file storage 盘点完成，无唯一附件；安全 `/proc` cwd/fd scan 无旧路径引用。旧 PM2 home 仅 stopped `rsdesign-new`，unit disabled/inactive 且无 reverse dependency，vhost 仅 disabled link；exact artifact/current release 与 Gate C recovery baseline 可重建/恢复，未读取业务表、`.env`、PM2 environment 或 Secret |
| Gate D exact cleanup | PASS | named PM2 delete/save/kill 后精确删除旧 PM2 home；精确删除 unit 并 daemon-reload、精确删除 disabled vhost symlink/file且 `nginx -t`/reload PASS；精确删除旧 runtime/source snapshots、Mac staging、AppServer redundant incoming files及三份 Gate B backups。保留 `/opt/incoming` 目录、AppServer active target、唯一 Gate C recovery baseline和权威 artifact |
| Gate D post-delete/cross-service checks | PASS | 所有已授权对象 absent，unit `not-found/inactive`，旧 3100/8091 absent；AppServer validator、PID `278336` exact cwd、external 3100 health、target DB mode/checksum/quick_check PASS；Gitea、runner、Verdaccio、Mailpit、PostgreSQL、NGINX 与 AppServer 3202 health PASS。未触碰 SFM 3212、MyApp 8090、其它平台对象或任何 VM |
| application post-Gate D repository verification | PASS | 应用四份 shell `bash -n`/ShellCheck、focused 1 file/7 tests、fresh temporary SQLite migration、full 70 files/326 tests、Next.js 14.2.35 production build与 diff/scope review 均 PASS；首次 sandbox Vitest invocation 在收集前因 worktree 写权限 `EPERM`，同一命令在 host context PASS，记为 `SANDBOX_PATH_BLOCKED` |
| application final verification PR #15 | PASS human merge | final head `dbe483d...` required run/job #344 completed/success in 50s；用户人工合并为 `480dd7d...`，Issue #13 closed，final head ancestry PASS；未自动合并 |
| SFM smoke cleanup candidate | PASS / human merge pending | 正式 Issue #86/change/86/PR #87；success/failure/TERM/INT process-group、bounded KILL、unrelated control、exact DB/fail-closed 与两个 always-finalizer 回归均 PASS；bash-n/ShellCheck、platform suite、148 files/949 tests、build、required Node 22 run/job #346 全部 PASS。PR open/mergeable，未自动合并 |
| SFM live 3212/history DB Gate | NOT RUN | PID `2487`、3212 listener 与 15 个历史 DB 均原样保留；必须等 PR #87 人工合并后重新读取 PID/cgroup/cwd/FD，再独立授权执行 |
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
| AC-5 | PASS complete | prerequisite/final PR CI与人工 merge、exact artifact/readiness/rollback、Gate C/D 与 post-check 全部 PASS；final merge SHA `480dd7d...`、Issue #13 closed，旧 writer/8091 absent，AppServer exact current/唯一 PID/cwd、direct/external health 与 recovery baseline 均已验证 |
| AC-6 | BLOCKED human merge/live Gate | Issue #86/change/86/PR #87 与 required Node 22 CI 已 PASS；尚待人工 merge，随后才能重新盘点并申请 live 3212/历史 DB Gate |
| AC-7 | NOT RUN | 未进入 MyApp inventory/backup/restore 与删除 Gate |
| AC-8 | NOT RUN | 已有第 1 步 baseline，但尚无收口前后成对验证 |
| AC-9 | NOT RUN | retention tool/dry-run 与 Redis/Nginx predicate 尚未实施 |
| AC-10 | NOT RUN | 尚未执行两轮 pre-delete inventory 与完整 dependency/unique-data/rebuild Gate |
| AC-11 | NOT RUN | 未执行任何 VM 删除；`gitea-ci`、AppServer 和其它 VM 均未删除 |
| AC-12 | PASS | post-Gate D 应用与 SFM candidate bash-n/ShellCheck/定向/full/build、SFM Node 22 required CI 与平台 bash-n/ShellCheck/定向 tests/完整 smoke 全部通过；live allow/deny/幂等、故意 health failure rollback、process-tree cancellation 与 Gate C/D post-state checks 均通过 |
| AC-13 | BLOCKED later steps | 本文件已记录 rsdesign 最终 merge SHA与 SFM PR #87 final head/CI；SFM 人工 merge/live Gate、MyApp/retention/VM live Gates、platform final head/CI/PR 尚不存在 |
| AC-14 | PASS（截至阻塞点） | prerequisite PR 已由人合并；Gate B prerequisite/readiness、Gate C 及本应用整体 Gate D 均有明确授权。Gate D 只清理盘点后的 `rsdesign-new` 过时对象并保留权威 artifact/active target/latest recovery；未执行其它应用 Gate、平台 retention apply、生产或任何 VM 操作，未自动合并 |

## 重复部署/执行

- host-role guard allow：PASS，两次输出一致。
- host-role guard deny：PASS，禁止的 application start 在 mutation 前返回 denied，mutation
  marker 不存在。
- installer：PASS，两次执行结果一致。
- live prepare：PASS，首次 created、重复 already-present，均未启动 PM2。
- live readiness：两次成功；每次随后显式 rollback，最终 current/PM2/listener 为空。
- live Gate C：一次 final cutover PASS；exact-SHA single writer、direct/external health 与新
  rollback manifest 均通过，故未执行不必要的 final rollback。
- 应用 Gate D：一次 exact cleanup PASS；删除后以 absent、unit `not-found`、listener、PID/cwd、
  DB checksum/quick_check、external health 与无关服务检查替代重复 destructive action。
- SFM candidate：success、health failure、TERM 与 INT 四类 fixture 均重复验证精确 group 清理；
  current-run DB helper 对 `ci`/`deploy` 删除 test-owned exact path，对 wrong URL/run ID/kind 均
  fail closed。未对 live PID 或历史 DB 重复/试探 destructive action。
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
- 应用 Gate C rollback readiness：新 manifest/`db.before` checksum/integrity PASS；final
  validation 未失败，未触发回切，old runtime/entry 恢复对象仍完整保留。
- SFM smoke 旧实现红灯：success 后 test TCP child 仍存活；测试 trap 仅按精确 fixture PID 回收。
  修复后故意 health failure、TERM=143、INT=130 与 ignore-TERM→bounded KILL 全部 PASS，unrelated
  control process 存活。首次 sandbox listener 因 `EPERM` 未建立，同一命令在 host context 得到
  真实红/绿结果，记为 `SANDBOX_PATH_BLOCKED`。
- `prod-sim` identity/引用不满足：NOT RUN；预期停止删除。
- `prod-sim` 删除后整机原地 rollback：不可能；恢复路径只能依据版本化最小基线重新创建。

## 操作与授权账本

| Object/action | Authorization | Result |
|---|---|---|
| host-role repository implementation/tests/docs | Issue #21 `approved` 合同内 | PASS |
| `rsdesign-new` contract/candidate/PR | 用户已确认合同优先级；应用 Issue/branch/PR 内实施 | PASS，PR #14/#15 required CI 与人工 merge 全部通过；final merge `480dd7d...`，Issue #13 closed |
| `rsdesign-new` host prerequisites/readiness | 用户明确授权 Gate B prerequisite 与 Gate B | PASS，结束时 AppServer candidate 离线、旧 runtime 健康 |
| `rsdesign-new` final cutover | 用户明确授权 Gate C；不含 cleanup/delete | PASS，AppServer exact candidate online，旧 writer/8091 stopped/disabled，可恢复对象全部保留 |
| `rsdesign-new` exact legacy cleanup | 用户明确整体授权本应用过时对象，无需逐对象再次等待；不扩大到其它应用/VM | PASS，pre-delete ledger、exact cleanup 与 post-check 完成 |
| `rsdesign-new` authoritative artifact/active target/latest recovery | Gate D 明确保留边界 | PASS，均保留且 checksum/integrity/health 可读 |
| SFM repository implementation/PR | Issue #86 `approved` 合同内；repo change/PR 独立治理 | PASS，PR #87 final head required CI 通过；保持 open，未自动合并 |
| SFM process stop/history DB delete | 仍需 PR #87 人工 merge 后重新盘点与独立 live Gate | NOT RUN |
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

第 6 步全部 blocker 已解除并以 merge SHA `480dd7d...` 收口。第 7 步 repository candidate 与
required CI 已完成：SFMDigitalBoard PR #87 final head `58d8df7...` 为 open/mergeable，run/job #346
PASS。当前 blocker 是人工合并 PR #87；不得自动合并。合并后须先重新读取 live 3212 PID/cgroup/
cwd/FD 与历史 DB，再取得独立 live Gate 才能终止或删除；不得把 `rsdesign-new` Gate D 授权扩展
过来，也不得提前进入第 8 步。

## 遗留风险与未完成项

- `rsdesign-new` 第 6 步已以 final PR #15 CI、人工 merge SHA `480dd7d...` 与 Issue #13 closed
  完整收口；旧 host cleanup 不可原地撤销的恢复边界保持不变。
- 旧 host runtime/DB/entry 已清理，不能原地回切；恢复依赖已合并 exact SHA/权威 artifact 与
  AppServer 当前 target/latest Gate C recovery baseline。cleanup 本身不可原地撤销。
- `/opt/artifacts` 保留原状；历史 artifact retention 仍属于平台第 9 步 predicate/dry-run/Gate，
  不能把应用 Gate D 授权用于提前清理。
- 任何 planning/baseline inventory 都可能漂移，恢复后须重新采集 live state。
- 除已完成的 `rsdesign-new` Gate D 与精确 `prod-sim` 条件授权外，其它 destructive action 仍需
  对应应用/平台 Gate 明确授权。
- `prod-sim` 授权不等于 AC-10 已通过；当前不得删除。
- SFMDigitalBoard 第 7 步 repo candidate/PR/required CI 已 PASS；人工 merge 与 live Gate 保持
  `BLOCKED/NOT RUN`。平台后续步骤与所有未执行 live Gate 仍为 `NOT RUN`；candidate CI 不等于
  部署、live cleanup 或平台清理完成。
