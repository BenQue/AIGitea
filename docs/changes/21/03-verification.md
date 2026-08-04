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
status: pr-ready
branch: change/21
pr_url:
created: 2026-08-02
updated: 2026-08-04
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
在 Node 22 上 successful in 1m43s。用户随后人工合并为
`579282df2c765df706c26d68850198ea306f4f57`；merge SHA 的 CI #347 与 AppServer deploy #348
分别 successful in 1m41s/2m1s。AppServer `current`、3202 PID cwd 均为 merge SHA，外部
health/database 为 ok，Issue #86 closed + `deployed`。合并后的 current-run DB finalizer 已证明
`ci-347`/`deploy-348` absent。用户随后对本应用独立 live Gate 明确回复“授权清理”。mutation 前
fail-closed 复核确认唯一 listener PID `2487`、PGID `2464`、组内仅该 PID、deleted cwd/log/DB、
cgroup、UID/GID、零连接以及 15 个无人打开且可重建的历史 DB 全部匹配。精确进程组收到 `TERM`
后在第 2 次检查前退出，未使用 `KILL`；随后只删除 15 个列明路径。PID/PGID/3212、旧 FD 与全部
SFM run DB 均 absent，Gitea/runner、AppServer exact current/3202/数据库 health 及三台 VM 状态
全部 PASS。第 7 步完成。后续步骤与 `prod-sim` 删除仍未执行；本 Gate 授权不扩大到 MyApp、
其它平台对象、服务、目录、数据库或任何 VM。按顺序进入第 8 步后，MyApp Notes 正式 repo
`admin/myapp`、current/release SHA、8090 vhost、runtime、`app_test` DB、7 个专属 artifact、
引用和连接 inventory 已完成。root-only recovery bundle
`/opt/cleanup-backups/issue-21/myapp/20260803T144609Z` 的 custom DB restore、current artifact
完整文件/符号链接 restore 和 vhost backup 均 PASS。`/opt/app-test/.env` 只记录脱敏元数据，未读、
未复制。用户随后明确“授权同意”精确 MyApp live Gate，并接受该 Secret 随 runtime 不可恢复。
mutation 前所有 identity/checksum/连接/引用再次匹配；两个 vhost path 删除后 `nginx -t` 与
graceful reload PASS，8090 absent。只 drop `app_test` database 并保留同名 role；精确删除
`/opt/app-test` 与 7 个账本 artifact。所有 target absent、recovery bundle 完整、Gitea/runner/
Nginx/PostgreSQL/Redis/Verdaccio/Mailpit/AppServer 两应用及三台 VM 的 paired checks 全部 PASS。
第 8 步 MyApp 部分完成；随后进入 Redis/Nginx predicate。
随后按计划执行 Redis/Nginx metadata-only predicate。Redis 8.0.5 仅 loopback 6379，16 个 DB
全部 0 key、SCAN=0、probe 后零 established connection、AOF disabled、RDB 88 bytes；Gitea、
Verdaccio、HSDB、active units 与正式应用 runtime 无 live consumer。已退役 MyApp repo 仅剩未使用
`ioredis` package declaration，SFM 命中仅为历史设计 HTML。root-only Redis recovery bundle
`/opt/cleanup-backups/issue-21/redis/20260803T151307Z` 已保存 config、空 RDB 与两个 exact arm64
`.deb`，RDB/package/checksum 验证 PASS。APT purge dry-run 只移除 `redis-server`/`redis-tools`，不
autoremove。Nginx 因 `12` 分册明确分配平台 Gitea proxy 批准职责，predicate 结果为 KEEP；Redis
随后获用户独立 live Gate 授权。完整 mutation precheck 再次证明 zero-key/connection/reference、
exact package/directory identity、recovery 与 purge simulation PASS；先仅
`systemctl disable --now redis-server.service`，6379 即 absent。首次 purge 在取得 dpkg lock 前
fail closed，锁随后自然释放，未 kill 进程或删除锁。官方 `redis-tools` postrm（与 recovery
`.deb` SHA 一致）会删除 Redis user、config/data/log；用户随后明确“直接清除，未来需要再安装”，
授权这一标准 package purge 范围。最终再次按 exact 包、config/data/log、empty RDB、recovery/cache、
lock 与 shared-service predicate 通过后，只 purge `redis-server`/`redis-tools`，没有运行
`autoremove`。Redis package/unit/user/group、`/etc/redis`、`/var/lib/redis`、`/var/log/redis` 和
6379 全部 absent；`libjemalloc2`/`liblzf1`、APT cache、root-only recovery、Gitea/runner/Nginx/
PostgreSQL/Verdaccio/Mailpit、AppServer 两应用及三台 VM 均保持健康。

第 9 步已实现 `codex/tools/artifact-retention-dry-run.sh`：它只接受 versioned policy 与
reference ledger，要求项目 allowlist、完整 40-hex SHA、重新计算的 `.sha256`、每项目声明的
current/rollback/workflow/test-attestation/production-manifest 引用、最低保留数量与期限；没有
`--apply` 或删除代码路径。policy 或引用不完整、未知项目/非 SHA 名称、缺 checksum 或 checksum
不符均为 `BLOCKED`。定向 fixture 覆盖 protected reference、unreferenced candidate、checksum
mismatch、incomplete references、unknown artifact 和 audit ledger。真实 `gitea-ci:/opt/artifacts`
metadata-only inventory 得到 10 个 `rsdesign-new-<40-hex>.tar.gz`（2026-07-10 至
2026-08-03，165,610,799–168,904,979 bytes）；没有 `.sha256` sidecar。使用临时的仅阻断
diagnostic policy（9/36500，仅为避免未批准策略产生 candidate）和空 reference ledger 执行真实
dry-run：10 个均 `BLOCKED missing-checksum`，`candidates=0 keep=0 blocked=10`。审计 ledger
为 14 行、SHA-256 `7b0dd06c5bb417d417539ddb2e46691cc8d9daeb9842df79ca79ec3ab530bab5`，临时输入与
ledger 由 EXIT trap 精确移除；`/opt/artifacts` 没有被改写或删除。正式项目 allowlist、最小保留
数量/期限和可验证的全量引用来源尚未获定义，因此 retention apply 保持 BLOCKED，不能根据文件名
或 mtime 推断删除。

2026-08-04 按用户的条件决策重新采集容量与健康证据：上述 10 个文件合计
1,685,669,209 bytes（1.570 GiB）；其所在文件系统为 302,096,367,616 bytes，总可用
202,563,907,584 bytes（188.65 GiB），制品仅占文件系统约 0.56%，文件系统使用率 33%。因此
不构成大量存储占用，用户选择完成验证并提交 PR，而不是进入清理分析。AC-9 以
“fail-closed dry-run + 小容量安全保留”完成；现有文件、内容与 `/opt/artifacts` 均未修改。
未来若要删除，仍必须补齐正式 policy/reference/checksum 并重新取得独立 apply Gate。

## 环境与版本

- Planning baseline：`48d47f7edd4cc9190f80886260b974477fc20236`
- Source baseline：`origin/main@b806317cc87a58049719fff103af2c9d7c14ed56`
- 2026-08-03 恢复时平台 `origin/main` readback：
  `7021224118a9d6b0bbb9e9cdd6ea5d4cbbb791bc`
- 2026-08-04 final integration `origin/main`：
  `63f571ac74cccd885b696e4efaab922c79cadeee`（包含已合并 Issue #22/#23）
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
  - PR 创建时 open、非 draft、mergeable；正文含 `Closes #86`；未自动合并
  - required CI：Actions run/job #346，`CI / verify (pull_request)`，PASS in 1m43s
  - state：人工 merged at `2026-08-03T22:16:23+08:00`
  - merge SHA：`579282df2c765df706c26d68850198ea306f4f57`；final head ancestry PASS
  - merge SHA status：CI run/job #347 PASS in 1m41s；AppServer deploy run/job #348 PASS in 2m1s
  - live Issue #86：closed，标签 `deployed`
  - AppServer：`current` 与 PID `287949` cwd 均为 merge SHA；3202 health/database ok；shared DB
    owner `benque:benque`、mode 640、368,640 bytes，未读业务表或 Secret
  - live Gate post-state：PID `2487`、PGID `2464`、3212 listener、旧 deleted FD 与 15 个历史
    runner DB 均 absent；`TERM` 成功，未使用 `KILL`
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
- MyApp Notes pre-Gate：正式 repo `admin/myapp`，`main`/current release
  `3424b0666b34bcf94609248abfc0306ee0b9b051`；release `5d8fc9a...`、`a83a794...` 均为其
  可达祖先。8090 static root direct/external 200，API 502，8080 backend absent；runtime
  813,123,755 bytes、15,598 files、无 process cwd/FD reference；`app_test` owner 同名，约
  8 MB、零其它连接。7 个专属 artifact 共 689,821,060 bytes、零打开引用。
- MyApp recovery bundle：`/opt/cleanup-backups/issue-21/myapp/20260803T144609Z`，
  `root:root` mode 700；内部 dump/artifact/vhost/inventory/manifests 均 mode 600。DB dump
  SHA-256 `9337d9351d2f2ab7c92a2847de7abbf612aa601d781c2b22102e7d81339407ee`；current
  artifact backup SHA-256 `799ab6b740a19eef379264d95fa116e33f19347b2cd2812c21c5fdfdd74d407d`；
  vhost SHA-256 `675b1dd4e82c60e20a4bc323b263ea3b7b6689779372224333f9eed6be6e5d21`。
- MyApp live Gate post-state：两个 `app-test` vhost path、8090、`/opt/app-test`、database
  `app_test` 与 7 个 `/opt/artifacts/app-*.tar.gz` 精确账本对象均 absent；role `app_test` 和上述
  recovery bundle 保留。未使用 DB `--force`、artifact glob、全局 Nginx stop/remove 或任何 VM
  命令；用户已明确接受 `.env` 内容无恢复路径。
- Redis pre-Gate：version 8.0.5，PID 257，cgroup `redis-server.service`，只监听
  `127.0.0.1/[::1]:6379`；DB0–15 均 0 key、SCAN=0、零 established connection、AOF disabled，
  `/var/lib/redis/dump.rdb` 88 bytes。package `redis-server`/`redis-tools` 均为
  `5:8.0.5-1` arm64；purge simulation 为 0 upgrade/0 install/2 remove，不含 autoremove。
- Redis recovery bundle：`/opt/cleanup-backups/issue-21/redis/20260803T151307Z`，root mode 700；
  `redis.conf`、empty `dump.rdb`、两个 cached `.deb` 与 inventory 均 mode 600。config/RDB SHA-256
  分别为 `68ff69f4b44ebce67227ff4bd1aa5a38f1e9c155d13948183b0453e4354a89f4`、
  `f226c4390bb2fb17cba709035316c34e44defd3a8ee8bf0822bf2e99617e63a9`；server/tools `.deb`
  分别为 `e2116ed87d02728956ec3509522dd2c7037490a6d4f97e7af5e3e78e307a3a95`、
  `f6a4a67b649583a6d90a58e23e047586b89400cfc2d22ea964617453d2049f20`。
- Redis live Gate result：`redis-server`/`redis-tools` packages、service unit、Redis user/group、
  `/etc/redis`、`/var/lib/redis`、`/var/log/redis` 与 6379 listener/connection 全部 absent。
  graceful stop 曾将 live empty RDB 重写为 SHA-256
  `4ad87cecc0c865481e875dcc482a81a7c7016042e4acb2a8951186a4c0dbbc23`；`redis-check-rdb` 证明
  checksum OK、0 keys/0 expires，recovery 中原 empty RDB hash 不变。
- `/var/lib/dpkg/info/redis-tools.postrm` 为 root-owned mode 755、SHA-256
  `201e00280722f1558e8c12b282e2f6d83e0a2d42cea45ad400f875ffd9df1566`，与 recovery `.deb`
  内 postrm 一致；其 purge branch 删除 Redis user 与 `/var/log/redis`。用户随后明确接受直接
  清除；重盘点后的 log 目录仅含 4 个 Redis log、零 open refs，package purge 后目录与 user/group
  均 absent。APT cache 与 recovery bundle checksum 保持不变。

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
| `bash codex/tests/smoke.sh` | PASS | 历史十九次均为 105 项 Python tests 及全部 shell/static smoke 通过；2026-08-04 集成 latest main 的 Docker release/architecture 后最终运行 166 项 Python tests 及全部 shell/static smoke 通过，同时覆盖 retention safe-retain 与 prod-sim final evidence |
| latest-main integration | PASS | `change/21@c4b13fd...` 合并 `origin/main@63f571ac...`；手工整合 README、Linux host-role/Docker-first 文档和 smoke 聚合入口，保留 Issue #21/#22/#23 合同；无冲突标记，`git diff --check` PASS |
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
| SFM smoke cleanup candidate/merge/deploy | PASS human merge | 正式 Issue #86/change/86/PR #87；success/failure/TERM/INT process-group、bounded KILL、unrelated control、exact DB/fail-closed 与两个 always-finalizer 回归均 PASS；bash-n/ShellCheck、platform suite、148 files/949 tests、build、required Node 22 #346 全部 PASS。用户人工 merge `579282d...`；main CI #347、deploy #348 PASS，Issue closed+deployed，AppServer exact current/PID cwd/3202 health PASS；未自动合并 |
| SFM current-run finalizer live proof | PASS | active deploy 时只读观察到 `deploy-348.db`；job 终态后 `ci-347`/`deploy-348` 均 absent，历史清单精确回到 15 个，证明 merged `if: always()` finalizer 生效 |
| SFM live 3212/history DB Gate | PASS | 用户明确授权本应用 live cleanup。第一次 mutation precheck 因过窄的 cwd 名称谓词 fail closed，零 signal/delete；以实时完整路径 `/opt/act-runner/.cache/act/f08f8d2d361cee6d/hostexecutor/sfm-board (deleted)` 重新核对后，host/machine ID、唯一 PID `2487`/PGID `2464`/组成员、PPID=1、UID/GID 999/986、cgroup、Node exe、deleted log/ci-87 DB、零连接、15 个精确 DB（4,546,560 bytes、无人打开）及 runner/Gitea 全部 PASS。仅向 `-2464` 发送 `TERM`，第 2 次检查前组已退出，`KILL` 未使用；只以 15 个精确路径执行非递归删除 |
| SFM live Gate post-state/unrelated checks | PASS | PID `2487`、PGID `2464`、3212、旧 deleted FD、15 个精确路径及其它 SFM run DB 均 absent；runner/Gitea active、Gitea health PASS。AppServer `current` 仍为 merge SHA，3202 仍为 PID `287949`，实际共享 DB `/opt/sfm-board/shared/db/sfm-board.db` 为 368,640 bytes、`benque:benque`、mode 640，外部 health/database ok。AppServer、gitea-ci、prod-sim 均仍 running；未操作任何 VM |
| MyApp formal repo/release inventory | PASS | 只读 mirror 确认正式 repo `admin/myapp`、main=current `3424b066...`，另两个 release SHA 均为 main 可达祖先；repo 无 `AGENTS.md`。main workflow 只按 exact SHA 生成/消费 `/opt/artifacts/app-${SHA}.tar.gz`，无 `badrollback*` 引用；未修改应用 repo |
| MyApp live runtime/vhost/DB inventory | PASS pre-Gate | 8090 为 root 200/API 502 的 Nginx vhost，8080 absent；vhost 仅 `app-test` 文件+enabled symlink。`/opt/app-test` 3 releases、current exact SHA，15,598 files/813,123,755 bytes、零 cwd/FD 引用。`app_test` owner 同名、backup 时 8,058,559 bytes、零其它连接；Gitea/runner/Nginx/PostgreSQL active |
| MyApp database recovery proof | PASS | PostgreSQL 18.4 custom dump 8,094 bytes/25 archive entries（含 2 个 TABLE DATA、1 个 SEQUENCE SET），mode 600。首次让 `postgres` 直接打开 root-only archive 因权限 fail closed，EXIT trap 删除测试 DB；随后由 root 打开同一 dump 并通过 stdin、`--exit-on-error --single-transaction` 恢复到 template0 临时 DB，catalog shape/extensions 一致，临时 DB 精确删除，原 `app_test` 未改 |
| MyApp runtime/vhost recovery proof | PASS | current artifact 98,542,215 bytes，无 absolute/`..`/`.env` entry；root-only scratch 恢复 5,199 files/5 symlinks，完整 SHA/symlink manifest 与 current release 一致，scratch 已删除。current artifact 与 vhost 的 mode-600 副本、manifest 和脱敏 inventory 已保留 |
| MyApp exact live cleanup | PASS | 用户明确授权并接受 `.env` 未备份的不可恢复边界。mutation precheck identity/recovery checksum/vhost/runtime/DB/artifact/zero-ref 全匹配；两个 vhost path 精确删除，`nginx -t` + graceful reload 后 8090 absent。无 `--force` 精确 drop `app_test`、保留 role；精确递归删除 `/opt/app-test`；以 7 个列明 path 非 glob 删除 artifacts |
| MyApp post-state/cross-service checks | PASS | 全部 exact targets 与 deleted cwd/FD absent，mode-700 recovery bundle 及 3 个核心 checksum不变；Gitea/runner/Nginx/PostgreSQL/Redis active，Gitea health、Nginx default、Verdaccio、Mailpit、rsdesign 3100、SFM 3202 均与 pre-state 一致；AppServer、gitea-ci、prod-sim running |
| Redis consumer/data predicate | PASS pre-Gate | Context7 Redis docs + redis-cli 8.0.5 help；INFO keyspace 无 DB entry，DB0–15 DBSIZE=0、SCAN=0、probe 后 6379 established=0、AOF=0、RDB 88 bytes。Gitea config、Verdaccio config、HSDB code/Secret-ref boolean、active units均无 Redis ref；rsdesign/SFM runtime 无 ref。MyApp main 仅未使用 `ioredis` dependency，live runtime 已退役且 loopback Redis 不可由 AppServer 消费 |
| Redis recovery/purge dry-run | PASS | config 无 active Secret/include；exact config/RDB 与 cached Redis 8.0.5 arm64 `.deb` 已复制到 root-only bundle，`redis-check-rdb`、`dpkg-deb` metadata/checksum PASS。`apt-get -s purge redis-server redis-tools` 只计划移除 2 packages；`libjemalloc2`/`liblzf1` 仅提示可 autoremove，明确不执行 |
| Redis live stop/purge/config+data/log/user removal | PASS | 用户最终明确授权直接清除 Redis。完整 precheck、empty RDB offline check、exact postrm/package/cache/recovery/lock/shared-service predicates 全部通过；只 `apt-get purge -y redis-server redis-tools`，0 upgrade/0 install/2 remove，未运行 autoremove。packages/unit/user/group、config/data/log dirs、6379 listener/connections 全 absent；`libjemalloc2`/`liblzf1`、APT cache 与 recovery checksum均保留，Gitea/runner/Nginx/PostgreSQL/Mailpit及两套 AppServer health PASS |
| Nginx predicate | PASS KEEP | MyApp vhost 删除后只剩 Ubuntu default static vhost/port 80；但 versioned `12-Linux-GitHub-Gitea-双服务器自动部署方案.md` 明确把平台 Nginx proxy 分配为 Gitea 批准职责。按 AC-9 shared-reference predicate 保留 Nginx service/package/config，不申请 stop/remove |
| artifact retention implementation/dry-run | PASS dry-run / BLOCKED apply | tool/examples/fixture/smoke 已通过；真实 10 个 legacy artifact 均缺 `.sha256` sidecar，`candidates=0 keep=0 blocked=10`，正式 policy/reference ledger 未定义，未删除制品 |
| artifact capacity decision | PASS keep | 10 个文件合计 1,685,669,209 bytes（1.570 GiB），仅约占 302,096,367,616-byte 文件系统的 0.56%；可用 202,563,907,584 bytes（188.65 GiB）、使用率 33%。按用户条件决定不清理，并在 Gitea/Nginx/runner/PostgreSQL/Mailpit/Verdaccio health PASS 后进入最终验证 |
| `prod-sim` pre-delete two-round inventory | PASS with direct owner disposition | 两次 `orb list`/`orb info` exact name+ID 一致；盘点显示 active Nginx/Redis/PostgreSQL、`app_prod`、release/incoming/backup assets。用户随后明确确认这是无实际功能的原型并授权其全部当前资产永久丢弃；这不是“资产不存在”的断言，而是所有者对不可恢复丢失的直接 disposition |
| `prod-sim` delete/post-check | PASS | 只执行 `orb delete --force prod-sim`；post `orb list` 仅含 AppServer/gitea-ci running，`orb info prod-sim` rc=1 `machine not found`，DNS rc=127、8090 HTTP rc=6，gitea-ci 与 AppServer paired health PASS |
| AISoftPlatform final PR CI | NOT RUN | 平台 final PR 尚未创建；`change/21` branch push 只保存候选与 blocker 证据，不能用应用 prerequisite PR 或 branch push 替代 final acceptance |

## MyApp live Gate 精确对象账本（已授权并执行）

| Exact object | Pre-Gate evidence | Result / 恢复边界 |
|---|---|---|
| `/etc/nginx/sites-enabled/app-test` | symlink → `/etc/nginx/sites-available/app-test`；8090 static 200/API 502 | **PASS removed**；`nginx -t`/reload PASS，Nginx 保持 active |
| `/etc/nginx/sites-available/app-test` | root-owned mode 644，SHA-256 `675b1dd4e82c60e20a4bc323b263ea3b7b6689779372224333f9eed6be6e5d21` | **PASS removed**；mode-600 exact backup 保留 |
| `/opt/app-test` | 813,123,755 bytes、15,598 files、3 个 repo-reachable releases、零 process refs | **PASS removed**；用户明确接受 `.env` 内容无恢复，非 Secret runtime 可由 backup artifact 重建 |
| PostgreSQL DB `app_test` | owner=`app_test`、约 8 MB、零其它连接；custom dump checksum `9337d935...` 已在 template0 临时库真实恢复 | **PASS dropped without force**；同名 role、root-only dump、其它 DB 保留 |
| `/opt/artifacts/app-a83a794280a2a1392763919f43d75f0bcec83ed1.tar.gz` | 98,553,988 bytes；SHA-256 `071dee1c76dcc62fb10c9f10de4c8536aa4df47f898d0b1ef53ebc4e41f717a5`；commit reachable、零打开引用 | **PASS exact path removed** |
| `/opt/artifacts/app-5d8fc9a44f4c69702928c72f6b3136076c9c4f66.tar.gz` | 98,538,225 bytes；SHA-256 `d43a795038f622e4833dd1c9cde7d200272c875f246d1e077441da6304f8163d`；commit reachable、零打开引用 | **PASS exact path removed** |
| `/opt/artifacts/app-3424b0666b34bcf94609248abfc0306ee0b9b051.tar.gz` | 98,542,215 bytes；SHA-256 `799ab6b740a19eef379264d95fa116e33f19347b2cd2812c21c5fdfdd74d407d`；main/current、零打开引用 | **PASS exact path removed**；checksum-identical recovery copy 保留 |
| `/opt/artifacts/app-badrollbacktest.tar.gz` | 98,547,885 bytes；SHA-256 `5d17e10a4a9825c68c24d66ae874ac807beb6f8213f2dde65deeaf144e60879f`；main 无引用、零打开引用 | **PASS exact path removed** |
| `/opt/artifacts/app-badrollbacktest2.tar.gz` | 98,547,995 bytes；SHA-256 `db7198d2be49e7136e2e1711175b370c99cf85b389289b0ec4f9307ba1e451e5`；main 无引用、零打开引用 | **PASS exact path removed** |
| `/opt/artifacts/app-badrollbacktest3.tar.gz` | 98,546,161 bytes；SHA-256 `ae5c7c1a545edc6e8aecc5a2fc516350335b98a60d7548d102d027e250875e47`；main 无引用、零打开引用 | **PASS exact path removed** |
| `/opt/artifacts/app-badrollbackfinal.tar.gz` | 98,544,591 bytes；SHA-256 `e8f8624ac3a7e4573829502cb1a08e12ae786111fdf1646c0b456e2ea670889e`；main 无引用、零打开引用 | **PASS exact path removed** |
| `/opt/cleanup-backups/issue-21/myapp/20260803T144609Z` | root-owned mode 700；DB/artifact/vhost/inventory/manifests 均 mode 600 | **PASS kept**；3 个核心 checksum post-state 不变 |
| Nginx service/default vhost、Redis、PostgreSQL roles/其它 DB、其它 artifacts、其它 runtime/VM | 非 MyApp Gate 对象或共享对象 | **PASS kept / not mutated** |

## Redis live Gate 精确对象账本（已授权并执行）

| Exact object | Pre-Gate evidence | Current result / 恢复边界 |
|---|---|---|
| `redis-server.service` / loopback 6379 | active/enabled，PID 257；0 key、0 post-probe connection、无 live consumer | **PASS absent**；先 exact disabled/stopped，package purge 后 unit `not-found`、6379/source+destination connections均 absent；未 stop 其它 service |
| packages `redis-server`、`redis-tools` | exact `5:8.0.5-1` arm64；APT simulation 只移除这 2 个 | **PASS purged**；用户确认直接清除，only two packages removed，未执行 `autoremove` |
| `/etc/redis` | 唯一文件 `redis.conf`；config root hash 已保存，无 active Secret/include | **PASS absent**；official postrm purge 清除，mode-600 config recovery 保留 |
| `/var/lib/redis` | 唯一文件为 88-byte empty RDB，DB0–15 均 0 key | **PASS absent**；stop 后 RDB offline check=0 keys/0 expires；原 empty RDB recovery 保留 |
| `/var/log/redis` | 重盘点为 4 个 Redis log，零 open refs；内容未读 | **PASS absent**；用户明确接受 package postrm direct cleanup |
| `/opt/cleanup-backups/issue-21/redis/20260803T151307Z` | root mode 700；config/RDB/two `.deb`/inventory 均 mode 600 | **PASS kept**；四个核心 checksum 不变 |
| Redis user/group | `redis:101:104`、zero application/connection/reference | **PASS absent**；official postrm cleanup，用户明确接受 direct removal |
| APT cache、`libjemalloc2`/`liblzf1`、Nginx、Gitea/runner/Verdaccio/Mailpit/PostgreSQL/Node/HSDB、应用 runtime/artifacts、VM | 明确保留或非 Redis Gate 对象 | **PASS kept / not mutated** |

## Artifact retention dry-run 账本（第 9 步）

| Object / contract | Evidence | Result |
|---|---|---|
| `codex/tools/artifact-retention-dry-run.sh` | versioned policy/reference JSON，fixed project prefix/suffix + full SHA parser，recomputed SHA-256，reference-kind completeness，optional audit ledger | **PASS implemented**；只输出 `KEEP`/`CANDIDATE`/`BLOCKED`，无 `--apply` 或删除路径 |
| `codex/config/artifact-retention-{policy,references}.example.json` | 无 Secret 的 policy/reference schema examples | **PASS**；必须显式填写项目、最低数量/期限和每类引用 |
| fixture and smoke integration | `bash -n`、ShellCheck、`bash codex/tests/test-artifact-retention-dry-run.sh` | **PASS**；protected/candidate/checksum/reference/unknown/audit cases 均覆盖 |
| `gitea-ci:/opt/artifacts` | 10 个 `rsdesign-new-<40-hex>.tar.gz`，无 `.sha256` sidecar；metadata-only inventory | **BLOCKED**；checksum predicate 不满足，未读 artifact 内容，未删除任何制品 |
| live diagnostic dry-run audit | 10 × `missing-checksum`；`summary candidates=0 keep=0 blocked=10`；14-line ledger hash `7b0dd06c...530bab5` | **PASS dry-run / BLOCKED apply**；临时 input/ledger 已精确清理，正式 retention policy/references 未被臆造 |

## Acceptance criteria 结果

| Acceptance criterion | Result | Evidence |
|---|---|---|
| AC-1 | PASS | schema、catalog、example 与正反 fixtures 已实现；缺字段、未知 role/capability 均 fail closed |
| AC-2 | PASS | 单一 guard 在 mutation 前按固定 capability 判定；`scm-ci` 的 application start/deploy、业务 DB 与长驻 smoke 被拒绝 |
| AC-3 | PASS | production profile/identity 路径固定；owner/mode/parent/hostname/machine ID 检查完整；调用方无 profile/identity override；输出脱敏测试通过 |
| AC-4 | PASS | 指定平台文档与 onboarding 已明确 SCM/CI 与 AppServer 分离，并把同机 runtime 标为 legacy/pending Gate |
| AC-5 | PASS complete | prerequisite/final PR CI与人工 merge、exact artifact/readiness/rollback、Gate C/D 与 post-check 全部 PASS；final merge SHA `480dd7d...`、Issue #13 closed，旧 writer/8091 absent，AppServer exact current/唯一 PID/cwd、direct/external health 与 recovery baseline 均已验证 |
| AC-6 | PASS complete | Issue #86/change/86/PR #87、required CI、人工 merge、main CI/deploy、current-run finalizer 与 live dependency/rebuild checks 均 PASS；独立授权后精确 `TERM` PGID `2464`（无需 `KILL`）并删除 15 个历史 DB，success/failure/TERM/INT fixtures、current-run finalizer及 live post-state 均无进程/端口/DB/cwd 残留 |
| AC-7 | PASS complete | 正式 repo/current ancestry、vhost/runtime/DB/artifact inventory、零连接/引用和 root-only per-object recovery proof 全部 PASS；独立授权后 exact cleanup 与 post-state PASS。`.env` 未读/未备份的不可恢复边界由用户明确接受 |
| AC-8 | PASS paired checks | MyApp mutation 前后 Gitea/API+DB、act_runner、Verdaccio、Mailpit、`/opt/node22`、`/opt/hsdb-ci`、`hsdb_ci`、Nginx default、Redis、AppServer rsdesign/SFM 与 VM 状态均成对通过；保留 artifacts/recovery bundle checksum 不变 |
| AC-9 | PASS safe retain | Redis zero-data/connection/reference、recovery、exact purge 与 post-state PASS；Nginx predicate=KEEP。retention tool/fixtures/audit 与真实 dry-run PASS；10 个 legacy artifact 因 missing checksum fail-closed。容量仅 1.570 GiB、约占文件系统 0.56%，可用 188.65 GiB，按用户条件决定安全保留，无 candidate、未 apply；未来删除仍需正式 policy/reference/checksum 与独立 Gate |
| AC-10 | PASS with direct owner disposition | 两轮 `orb list`/`orb info` 精确 name/ID、guest OS/architecture/resources/mount/listener/timer/data metadata、repository reference scan 均完成。live assets 仍存在，但用户明确确认无实际功能并授权永久丢弃；最小可重建基线仅保留 OS=`Ubuntu 26.04 resolute`、ARM64、disk=3,875,823,616 bytes、10 CPU、16,820,465,664-byte memory、machine ID、runtime/data metadata，未读取 `.env` 或业务数据 |
| AC-11 | PASS | 唯一 destructive command 为 `orb delete --force prod-sim`。删除后 `orb list` 无该 VM、`orb info` 明确失败、DNS/8090 connection 失败；AppServer 与 gitea-ci 仍 running，Gitea/runner/Nginx/PostgreSQL/Mailpit/Verdaccio 与 3100/3202 health 全部 PASS |
| AC-12 | PASS | post-Gate D 应用与 SFM candidate bash-n/ShellCheck/定向/full/build、SFM Node 22 required CI 与平台 bash-n/ShellCheck/定向 tests/完整 smoke 全部通过；live allow/deny/幂等、故意 health failure rollback、process-tree cancellation 与 Gate C/D post-state checks 均通过 |
| AC-13 | PASS PR-ready evidence | 本文件已记录 rsdesign/SFM/MyApp/Redis、retention safe-retain 与 prod-sim final Gate；platform final PR/CI 将在本分支最终验证与 push 后记录，不把未运行的远端 CI 写成 PASS |
| AC-14 | PASS（截至当前步骤） | prerequisite PR 已由人合并；Gate B prerequisite/readiness、Gate C、rsdesign Gate D、SFM、MyApp、Redis 与 exact prod-sim delete 均有明确授权。用户的 prod-sim 直接 disposition 只覆盖该 VM 及其内部资产；未扩大到 retention、生产、gitea-ci、AppServer 或其它 VM，未自动合并 |

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
  fail closed。merge 后 #347/#348 current-run DB 均 absent。live Gate 只执行一次：`TERM` 后第 2 次
  bounded 检查已无 PGID，因此未发送 `KILL`；15 个精确历史路径只删除一次，随后以 absent 读回。
- MyApp live Gate 只执行一次：vhost remove/test/reload、无 force database drop、exact runtime
  recursive delete 与 7-path artifact delete 均一次成功；以 absent、paired health 和 recovery
  checksum 读回替代重复 destructive action。
- Redis live Gate 的完整 precheck 重跑后仅执行一次 service disable/stop；首次 purge 在 dpkg lock
  前退出，随后在用户明确 direct cleanup 后以新一轮 exact precheck 执行一次 package purge。以
  package/unit/user/group/config/data/log/6379 absent 与 kept cache/recovery/dependency hashes 读回，
  不重复 purge 或运行 `autoremove`。
- `gitea-ci` inventory：第 1 步 baseline PASS；第 9 步 live dry-run 在 host execution path PASS，
  10 个 artifact 因 missing checksum BLOCKED。
- `prod-sim`：两轮 pre-delete inventory 已记录 active runtime/data evidence；用户随后直接确认
  原型无实际功能并允许永久丢失，因此执行一次且仅一次 `orb delete --force prod-sim`。post list/info、
  DNS/8090 connection 与另外两台 VM health 均已读回，未进行重复 destructive action。

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
- Redis purge concurrent lock：PASS expected fail closed；service stop 已完成，但 APT 在删除前退出，
  lock 自然释放。official postrm contract conflict：PASS expected fail closed；用户随后明确授权直接
  清除 Redis 后，完整新 precheck 与 standard package purge PASS。
- Redis final purge precheck 首次发现停机后 logrotate 将 3 个历史 log 重排为 4 个 Redis-only log；
  zero open-ref metadata 重盘点后重跑。一次 post-check `ss` 因嵌套引号误解析，零 mutation；无
  嵌套引号的 listener/source/destination recheck 均为空。
- `prod-sim` identity 精确匹配但依赖/唯一数据/重建性不满足：PASS expected block；未发送任何
  delete/stop/restart 命令。
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
| SFM repository implementation/PR/deploy | Issue #86 `approved` 合同内；repo change/PR 独立治理 | PASS，PR #87 final head CI、人工 merge SHA、main CI/deploy、Issue closed+deployed 与 exact AppServer current/health 均已读回；未自动合并 |
| SFM process stop/history DB delete | 用户在精确范围说明后明确“授权清理”；不扩大到其它对象 | PASS，PGID `2464` TERM-only 退出，15 个精确历史 run DB 删除，post-state 与无关服务/VM 检查通过 |
| MyApp inventory/DB+runtime+vhost recovery | Issue #21 approved 合同内的非破坏性 pre-Gate | PASS，root-only recovery bundle 已保存并真实恢复验证；原 runtime/vhost/DB/artifact 未改 |
| MyApp vhost/runtime/DB/7 artifacts | 用户明确“授权同意”，并接受 `.env` 不可恢复丢弃；不扩大到 Redis/global Nginx/其它对象 | PASS，exact cleanup、recovery keep 与 paired post-state 全部通过 |
| Redis/Nginx predicate + recovery | Issue #21 approved 合同内的只读/非破坏性 pre-Gate | PASS，Redis removal candidate、Nginx KEEP；root-only Redis rollback bundle 与 purge dry-run 完成 |
| Redis stop/purge/config+data/log/user | 用户明确“Redis目前没有应用使用，请直接清除。以后有需要再安装” | PASS：仅 purge `redis-server`/`redis-tools`；postrm 清除 Redis user/config/data/log，保留 APT cache、recovery、`libjemalloc2`/`liblzf1`与其它服务/VM |
| Nginx stop/remove | approved Gitea proxy responsibility blocks removal | KEEP / NOT AUTHORIZED |
| artifact retention tool and live dry-run | Issue #21 approved 合同内的 non-destructive implementation/dry-run | PASS；临时 diagnostic inputs only，10 个 missing checksum blocked，`/opt/artifacts` 未变 |
| artifact retention apply | 容量证据显示不构成压力，用户按条件选择完成验证/PR；未来删除仍须正式 policy/reference/checksum 与独立 human Gate | NOT NEEDED / NOT RUN；10 个文件安全保留 |
| `prod-sim` two-round inventory | Issue #21 approved 合同内的只读 Gate；随后用户明确确认无实际功能且全部内部资产可永久丢弃 | PASS with direct owner disposition；active Nginx/Redis/PostgreSQL、`app_prod`、release/incoming/backup assets 与 legacy deploy references 已记录但不迁移 |
| exact `prod-sim` delete | 用户明确“可以删除”，仅覆盖该 VM | PASS；仅 `orb delete --force prod-sim`，未用 `--all`，未操作 gitea-ci/AppServer/其它 VM |
| any other VM delete or `--all` | 未授权且明确禁止 | NOT RUN |

## 观察偏差与副作用核对

- sandbox 内首次 `orb list` 因无法连接 OrbStack backend 超时；在 host context 的只读调用
  成功。前一次超时只记为 `SANDBOX_PATH_BLOCKED`，未把它当作 VM 状态。
- 一次 PM2 只读盘点误用了 `/home/gitea-runner/.pm2`；PM2 尝试创建目录/daemon，但均因权限
  不足失败。后检查未产生目录或 daemon，未停止、启动或更改现有进程。
- `orb pull` 对绝对 `/opt/artifacts/...` source 返回 source-relative path error，未复制任何文件；
  随后按官方文档改用 `/mnt/mac` mode 700 staging，source/Mac/target checksum 一致。
- SFM live Gate 第一次 mutation precheck 将 cwd 错误限定为包含 `SFMDigitalBoard`，而实时路径
  使用 `hostexecutor/sfm-board (deleted)`；命令在发送 signal/delete 前 fail closed。改为完整实时
  路径后全部条件通过。post-check 首次把共享 DB 元数据路径写成不存在的
  `/opt/sfm-board/shared/sfm-board.db`，只读 `stat` 失败；实际路径
  `/opt/sfm-board/shared/db/sfm-board.db` 随后以 metadata-only 检查通过，health 全程为 ok。
- MyApp DB restore 首次以 `postgres` 直接打开 root-only mode-600 dump，因目录权限返回
  permission denied；EXIT trap 精确删除临时 DB，原 DB 未改。复核临时 DB absent 后，改由 root
  打开同一 dump 并通过 stdin 交给 `pg_restore`，完整恢复、catalog comparison 与 cleanup PASS。
- PostgreSQL 本机 help 首次 grep 以 `--format...` 开头的 pattern 未加 `--`，被误解析为 grep
  option；只读命令零 mutation。加 `grep -E --` 后复核 18.4 选项通过。
- Redis mutation precheck 首次把 `/proc/257/exe` 过窄限定为 `/usr/bin/redis-server`；Ubuntu 包中
  该入口实际为由 `redis-server` 包拥有、指向 `redis-check-rdb` 的 symlink，目标由同版本
  `redis-tools` 拥有。`dpkg -V` 与 recovery `.deb` 内容一致后从头重跑 precheck PASS。
- Redis service exact disable/stop 后，首次 `apt-get purge` 因 PID `1352821` 的 concurrent APT
  lock 在取得 lock 前退出；未删除 package/dir。该进程和 lock 随后自然消失，未 kill 或删锁。
  graceful stop 重写 88-byte empty RDB；新 hash 经 offline check 证明 0 keys/0 expires，原 recovery
  hash 不变。
- partial resume 在 mutation 前识别 official `redis-tools` postrm 会 `userdel redis` 并
  `rm -rf /var/lib/redis /var/log/redis /etc/redis`。初始合同范围不足时未修改 dpkg maintainer
  script、未 purge、未删除任何目录；用户随后明确授权 direct cleanup 后才执行标准 purge。
- 第 9 步首次 sandbox `orb -m gitea-ci` read-only inventory 超时；改在 host execution path
  成功，故只记 `SANDBOX_PATH_BLOCKED`，不把超时当作 VM 状态。live dry-run 的临时 policy 将
  `minimum_retained=9`、`minimum_age_days=36500` 仅用于证明缺 checksum 时无 candidate；它不是
  正式 retention policy，未写入 `/opt/artifacts` 或任何 production 配置。

## 当前 blocker 与恢复条件

第 6 步已以 merge SHA `480dd7d...` 收口。第 7 步也已完整收口：PR #87 merge SHA
`579282d...`、Issue closed+deployed、AppServer exact current/3202 health、current-run finalizer、
独立授权的 live PGID/历史 DB cleanup 与 post-state 全部 PASS。第 8 步 MyApp Notes inventory、
数据库/目录/vhost recovery proof、独立 live Gate 与 paired post-state 也已完成。Redis/Nginx
predicate 随后完成：Nginx 因批准的 Gitea proxy role 为 KEEP；Redis 满足 remove predicate 且
recovery/dry-run PASS。用户随后明确授权 direct cleanup；Redis package/unit/user/group/config/data/
log/6379 的 final post-state 全部 PASS，shared services、两套 AppServer health、VM 和 recovery/
APT cache/依赖均保持。第 9 步 implementation 与真实 dry-run 已完成；all 10 legacy artifacts
因缺 `.sha256` sidecar fail closed。2026-08-04 容量复核确认它们合计 1.570 GiB、仅约占文件系统
0.56%，且仍有 188.65 GiB 可用；按用户条件决策安全保留并完成验证，retention apply 不再是本
Change 的完成条件。第 10 步随后已完成两轮只读 inventory：`orb list` 与 `orb info prod-sim` 两次均精确
回读 name=`prod-sim`、ID=`01KX3FFXSJVYPDHZVY4MZB7CQZ`、Ubuntu resolute/ARM64、running、
disk_size=3,875,823,616 bytes。guest machine-id 固定为 `531d0ec7d550406bb193b31b18ea27c6`，但
Nginx/Redis/PostgreSQL 均 active，80/8090/6379/5432 均监听；8090 root 指向
`/opt/app-prod/current/frontend`。`app_prod` 数据库为 7,984,831 bytes，`/opt/app-prod` 有 current
与 6 release，`/opt/incoming` 有 6 个 98 MB 级 artifact，`/opt/db-backups` 有 7 个 SQL backup。
仓库扫描还找到该 VM 的 legacy deploy/SSH/document references。用户随后直接确认该系统没有实际功能、
允许当前全部原型资产永久丢弃；以该所有者 disposition 覆盖“需迁移/保留”的风险判断后，最终 preflight
再次匹配 exact name/ID 并显示 gitea-ci/AppServer healthy。随后仅执行
`orb delete --force prod-sim`。post-state 中该 VM 不在 `orb list`，`orb info prod-sim` 返回
`machine not found`，DNS/8090 connection 失败；gitea-ci 与 AppServer paired health 仍 PASS。
第 11 步完成。当前无 destructive 或外部合同 blocker；完成 latest-main 集成、本地最终测试和
branch push 后可创建最终 PR，远端 CI 仍须按实际结果记录。

## 遗留风险与未完成项

- `rsdesign-new` 第 6 步已以 final PR #15 CI、人工 merge SHA `480dd7d...` 与 Issue #13 closed
  完整收口；旧 host cleanup 不可原地撤销的恢复边界保持不变。
- 旧 host runtime/DB/entry 已清理，不能原地回切；恢复依赖已合并 exact SHA/权威 artifact 与
  AppServer 当前 target/latest Gate C recovery baseline。cleanup 本身不可原地撤销。
- `/opt/artifacts` 保留原状；第 9 步 tool/dry-run 已证明所有 10 个 legacy rsdesign artifacts
  缺 checksum。它们合计仅 1.570 GiB、约占文件系统 0.56%，按用户条件决定安全保留；未来若容量
  或保留要求变化，仍须定义正式 allowlist/count/period/reference ledger、补齐可信 checksum 并
  取得独立 Gate 后才能申请 apply，不能把应用 Gate D 或 Redis 授权用于制品清理。
- 任何 planning/baseline inventory 都可能漂移，恢复后须重新采集 live state。
- 除已完成的 `rsdesign-new` Gate D 与精确 `prod-sim` 条件授权外，其它 destructive action 仍需
  对应应用/平台 Gate 明确授权。
- SFMDigitalBoard 第 7 步 repo/PR/CI/人工 merge/AppServer deploy、live Gate 与 post-state 已
  PASS；其 cleanup 授权未扩展到其它对象。MyApp、Redis、retention safe-retain 与 `prod-sim`
  各自依合同和独立授权完成，不能互相替代证据。
- MyApp recovery bundle 保留 DB/current artifact/vhost 与验证 manifests，但按 no-Secret 合同不
  包含已删除 `/opt/app-test/.env` 的内容；用户已明确接受其不可恢复。正式 repo/current artifact
  可重建非 Secret runtime，DB dump 已真实恢复验证。
- Redis 已清除；可由保留的 exact cached `.deb` 与 root-only recovery bundle 在未来按需重新安装。
  `libjemalloc2`/`liblzf1`、APT cache、其它 shared services、应用 runtime/artifacts 与 VM 未变。
  Nginx 必须按批准的 Gitea proxy contract 保留。
- `prod-sim` 已按用户直接 disposition 删除，不能原地 rollback；只保留已记录的 OS/architecture/
  resource/runtime metadata 作为最小重建线索。它不证明已迁移应用或恢复任何数据。
