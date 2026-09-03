# 公司两 VM 确定性交付 operator runbook

> 状态：仓库交付物，未在公司执行。本 runbook 不证明公司安装、备份、恢复、CI 或生产部署成功。

本册随 operator `1.3.0` 生效：`company-delivery-inventory/v3` 与 `company-delivery-gitea-transition/v2`
合同不变；compatibility matrix 与 `scm-ci` sync timer unit 名改由项目数据声明——matrix 由项目仓保存并在
Stage 00 前由 `build-bundle --compatibility-matrix` 传入，handoff manifest 的 `compatibility.sync_timer_unit`
是 Stage 10/20 唯一的 timer 名来源。旧 `1.0.1`/`1.1.0`/`1.1.1`/`1.2.0` Stage 00 与既有 Stage 10 只保留为历史
evidence，不能投影为 `1.3.0` Stage 00/10 `PASS`；要进入本册 Stage 10，必须用同一 exact source
重新生成、校验并批准 `1.3.0` handoff。`appserver-prod` Stage 10 保持 `NOT RUN`，直到获得独立人工批准。

## 1. 不变量与人工闸门

本流程只有两台公司 Linux VM：`gitea-ci`（role=`scm-ci`）和 `appserver`
（role=`appserver-prod`）。非生产 role=`appserver-test` 继续由本地 OrbStack DockerLab
承担，不新增第三台公司 VM。

任何时刻只有一个 stage 处于已批准且可执行状态。人必须先在公司批准系统中记录以下不可变 tuple，才可在
指定 host 上手工启动该阶段：本次交付的 Issue/Change 编号、stage、operator version、full source Git SHA、full
release SHA（不适用时为 null）、scope、role、批准引用、批准时间和失效时间。批准不得使用 wildcard，
不得自动继承到下一 stage，也不得授权任意 shell、任意 host 或任意 target。

共同规则：

1. 每阶段开始时，操作人逐字比对 approval tuple、上一阶段 evidence、bundle identity 和当前 role；任一不符
   即写 `BLOCKED`，不运行本阶段。
2. 每阶段结束后先停止，再由另一位 reviewer 审核 strict evidence；只有完整 `PASS` 才能申请下一 stage。
   `FAIL`、`BLOCKED` 或 `NOT RUN` 都不能前推。
3. Secret 只由公司 secret store 或 root-owned mode `0400/0600` 文件在未来已批准阶段消费；不得进入
   bundle、argv、stdout/stderr、日志摘录、inventory 或回流 evidence。不得记录原始主机名/IP、用户名、
   token、认证 header、connection string、key 或配置内容。
4. evidence outcome 只允许 `PASS`、`FAIL`、`BLOCKED`、`NOT RUN`。`observed`、`changed`、`verified`、
   `pending` 必须分开；未运行不得写入 `changed`，local/fake 不能投影为 company/live。
5. company Gitea 是公司部署权威；私有 GitHub 只运输 source provenance 或 approved bundle。公司重新创建
   PR、运行 CI/verification 并由人合并；不得继承 GitHub 或本地 PR 的审批结论。
6. `scm-ci` 只能做 SCM/CI/Registry/cache、artifact-only verification 和受控编排，不得运行应用
   runtime 或业务 DB。`appserver-prod` 只承载应用/PostgreSQL/Nginx/fixed target，不得安装 Gitea、
   通用 Runner、源码 builder 或 AI。
7. exact `docker-release/v2` bytes 是信任根；不同 bytes 不得继承本地测试结论。公司要求内网重建且无隔离
   测试环境时固定 `BLOCKED`。
8. 安装与首次验收期间，sync timer、Actions auto deploy 与 production gate 均为 `disabled/inactive`；
   任一启用都需要未来独立批准。
9. 本地 handoff builder 对 operator、manifest、Compose 与其它非 archive payload 执行 no-secret 检查；已通过
   `docker-release/v2` identity/checksum/outer graph 校验的 `images.tar` 作为 opaque immutable payload 搬运，
   不做 image 内部 Secret 审计。bundle PASS 只证明 exact bytes 与运输完整性；公司真实 Secret 与授权由人
   在内网处理。
10. `greenfield-isolated-install` 只能建立完全独立的新 namespace。legacy Docker Gitea 的 container、image、
    volume、network、database、configuration、port、repository 与 service lifecycle 全部在 mutation denylist；
    greenfield collector 不探测 legacy Docker/HTTP，legacy observation 固定为 `NOT RUN`。任何 legacy 读取或
    mutation 都必须停止并另建 Change。

### Evidence 文件与回流

- 每个 stage 从 `templates/evidence.<outcome>.example.json` 复制到新的 mode `0600` 文件；模板仅表示结构，
  不能直接作为证据。
- `scope` 必须精确为 `local-fake`、`company-scm-ci`、`company-appserver-prod` 或
  `company-cross-host`；一个文件只对应一个 stage 和一次批准。
- stage/scope 固定矩阵为：Stage 00=`local-fake|company-scm-ci`；Stage 10=`company-scm-ci|company-appserver-prod`；
  Stage 20=`company-cross-host`；Stage 30/40=`company-scm-ci|company-appserver-prod|company-cross-host`；
  Stage 50–80=`company-scm-ci`；Stage 90/100=`company-appserver-prod`；Stage 110=
  `company-scm-ci|company-appserver-prod|company-cross-host`。其余组合一律拒绝，尤其禁止把 Stage 100 写成
  `local-fake`。
- `PASS` 只允许已完成的 `PASS` facts 且 `pending=[]`；`FAIL` 必须有已完成的 `FAIL` fact，且 pending 如存在
  只能记录尚待独立批准的 `BLOCKED/NOT RUN` 处置；
  `BLOCKED` 必须至少有一个 pending `BLOCKED` fact；`NOT RUN` 只能含 pending `NOT RUN` facts，且
  `observed/changed/verified` 为空。`changed` 中的事实只能是 `PASS`。
- artifacts 仅引用脱敏 JSON/checksum/receipt 的相对路径。原始 logs、backup bytes、Secret files 与 host
  addresses 不进入回流包。
- 回流前运行 `operator/bin/aisoft-company-delivery verify-evidence --input <evidence-json>`，再对允许文件生成
  新的排序 `SHA256SUMS`。验证失败则 outcome 为 `BLOCKED`，禁止手工修改 validator 输出后继续。

## Stage 00 — archive、handoff 与 exact release 校验

| 字段 | 合同 |
|---|---|
| 前置输入 | 已批准的 archive basename、相邻 `.sha256`、operator version、full source SHA、full release SHA、transport 和空的 mode `0700` staging directory；本地 fake 与公司 scope 必须分开。 |
| 人工批准记录 | 只批准 Stage 00 和一个 archive checksum；不授权 network、Docker、target profile、Secret、service 或 deploy。 |
| 执行位置 / role | 开发侧只可用 `local-fake`；未来公司 handoff 在 `gitea-ci` / `scm-ci` 的批准 staging directory。 |
| 允许动作 | 先以 `sha256sum --check <archive>.sha256` 校验 archive；固定 `umask 077` 后解包到新目录；禁止 symlink/绝对/上跳 member；随后运行 `operator/bin/aisoft-company-delivery verify-handoff --manifest <bundle>/handoff-manifest.json --bundle-root <bundle>`。占位符必须由批准 tuple 替换。 |
| 预期输出 | archive checksum PASS；validator 只输出 contract/release identity、`ok=true`、`docker_calls=0`、`target_facts=NOT_READ`；`SHA256SUMS` 覆盖全部 payload 与 handoff manifest。 |
| PASS | archive、source/release/compatibility、逐文件 SHA256、mode、path 和 `docker-release/v2` artifact-only contract 全部一致。 |
| FAIL | 已执行只读校验，但 checksum、schema、release graph 或 compatibility 明确不一致；记录固定错误 code，不回显输入内容。 |
| BLOCKED / 停止点 | short SHA、不同 bytes、unknown architecture/image store、unsafe path/mode/symlink、非 archive payload 的 `SENSITIVE_CONTENT`、缺文件或任何 Docker/target 访问迹象；scanner 只允许 fixed code/message，不得回显值；立即停止，不搬运到 AppServer。`images.tar` 内部内容不属于本 gate 的扫描面。 |
| Evidence | 一个 Stage 00 evidence JSON、archive sidecar checksum、脱敏 validator receipt；archive 本体不回流开发侧。 |
| 回滚边界 | 仅删除本阶段新建的 staging copy，保留原始只读介质；不得触碰 Gitea、Registry、service、DB 或 target。 |

## Stage 10 — 两台 VM 的只读脱敏 inventory

| 字段 | 合同 |
|---|---|
| 前置输入 | 同一 exact source 的 operator `1.3.0` Stage 00 PASS、两份彼此独立的批准记录、目标 role，以及预先创建的 mode `0700` evidence directory。旧 1.0.1/1.1.0/1.1.1/1.2.0 Stage 00 或既有 Stage 10 evidence 不满足该前置。 |
| 人工批准记录 | 分别批准 `gitea-ci/scm-ci` 和 `appserver/appserver-prod` 的 collector；不批准 package install、network discovery、config read、service change 或 restart。 |
| 执行位置 / role | 在两台公司 VM 上由人分别运行；collector 的 `--role` 必须与批准记录一致。 |
| 允许动作 | `operator/bin/aisoft-company-delivery collect-inventory --role scm-ci --mode preflight --output <new-json> --handoff-manifest <bundle>/handoff-manifest.json`（sync timer unit 名只从 Stage 00 已验证的 handoff 读取，collector 会重新校验整个 bundle；不手工输入 unit 名），或在 AppServer 运行 `operator/bin/aisoft-company-delivery collect-inventory --role appserver-prod --output <new-json>`（不接受 `--handoff-manifest`）。`scm-ci` 只增加候选 `127.0.0.1:8888`/`127.0.0.1:55432`、固定 path 与新 unit 状态 probe；禁止 legacy port 参数、`docker ps/inspect`、legacy HTTP/API、env/config/log/raw output。 |
| 预期输出 | 两个 mode `0600` strict inventory v3 JSON；`scm-ci` mode=`preflight` 且 candidate health=`NOT RUN`，`appserver-prod` mode/scm=`null`。SCM 对象只有 `probe_profile`、`candidate` 与 `automation`；不包含任何 legacy 字段。 |
| PASS | 两个 role 均通过 `verify-inventory`；候选 `127.0.0.1:8888`/`127.0.0.1:55432` 均 free、固定 resources absent/expected-empty；`aisoft-gitea.service` 必须为 `not-found/not-found`，PostgreSQL 候选 unit 只允许 `not-found/not-found` 或已安装但安全停用的 `disabled/inactive`；自动化入口均为 disabled/NOT RUN。任一 unknown、collision、ambiguous 或 raw/sensitive output 都不能 PASS。legacy 状态不参与结论。 |
| FAIL | 已运行固定 probe 且明确得到不兼容版本、错误 architecture 或角色冲突；不保存 raw stdout/stderr。 |
| BLOCKED / 停止点 | 除上述双重确认的待安装工具外，probe 缺失/不可解析、command 与 unit 状态冲突、Secret-like output、unknown host fact、目录/mode 不安全或发现跨 role 服务；不得为补齐结论读取 legacy 状态或“补猜” inventory。 |
| Evidence | 每台 VM 一个 inventory JSON + 一个 Stage 10 evidence JSON；只回流 fingerprint、enum、semver、数值和固定 reason。 |
| 回滚边界 | 只读，无 live rollback；仅移除本阶段新建的 evidence copy。任何系统状态变化都视为越界并停止。 |

## Stage 20 — Gitea greenfield isolated install 决策

| 字段 | 合同 |
|---|---|
| 前置输入 | 两份 mode `0600` Stage 10 inventory v3 PASS 及其 SHA-256；`scm-ci` 为 preflight，`appserver-prod` mode/scm 为 null；已验证的 operator 1.3.0 `handoff-manifest.json`（含 `compatibility.sync_timer_unit`）、完整 PostgreSQL OS package-set SHA-256 manifest、public-name fingerprint、固定 target tuple 与 reviewer decision ID 已准备。package manifest 必须是非空、ASCII、按 artifact path 排序且路径唯一的清单，每行精确为 `<64-lowercase-hex><two-spaces><safe-relative-artifact-path>`。 |
| 人工批准记录 | 只批准一个 decision enum：`greenfield-isolated-install` 或 `BLOCKED`；本阶段不授权安装、停止服务、写数据、备份、恢复、迁移或 legacy observation。 |
| 执行位置 / role | company cross-host review；技术事实来自 `gitea-ci/scm-ci`，AppServer 只确认无 Gitea/Runner 角色漂移。 |
| 允许动作 | 复制 transition example 到新的 mode `0600` receipt，填入批准事实后运行 `operator/bin/aisoft-company-delivery verify-gitea-transition --input <transition-json> --scm-inventory <scm-json> --appserver-inventory <appserver-json> --handoff-manifest <bundle>/handoff-manifest.json --postgresql-package-manifest <package-set-sha256-manifest>`；不得执行安装/升级命令。 |
| 预期输出 | 一个 strict transition v2 receipt：checksum 绑定并实际读回 operator 1.3.0 handoff/source SHA、handoff 声明的 sync timer unit（必须与 `scm-ci` inventory 记录的 timer 实例一致）、PostgreSQL OS package-set manifest、two inventories、public-name fingerprint、固定 target、automation、candidate isolation、精确 stage map 与 reviewer decision；不含 legacy 字段，CLI 仅回显 sanitized decision/outcome。 |
| PASS | `greenfield-isolated-install` 只允许 Stage 00/10/20 PASS 且 Stage 30/40/50 为 `NOT RUN`，Stage 50 prerequisite=`candidate-post-install-health`。validator PASS 仍不是安装批准。controlled upgrade 不属于本合同，必须另建 Change。 |
| FAIL | 已知事实证明两条路径都与容量、兼容性或隔离要求冲突。 |
| BLOCKED / 停止点 | 任一 candidate port/path/unit/identity、package provenance、checksum binding 或 rollback namespace 不明确；禁止用 side-by-side 绕过 candidate 冲突，也禁止读取 legacy 来替代 candidate 证明。 |
| Evidence | Stage 20 evidence JSON、两份 inventory checksum、decision receipt checksum；不含 config/database 内容。 |
| 回滚边界 | 纯决策，无 live rollback；废弃 decision receipt 后重新批准 Stage 20，不能在原记录上静默改选。 |

| 条件 | 唯一允许结论 |
|---|---|
| 新 user/group/unit/path/DB/port 全部独立、无 collision；所有自动化与切流入口禁用；legacy observation=`NOT RUN` | `greenfield-isolated-install` |
| candidate identity/path/port/storage/rollback 未知，或拟覆盖任一既有 namespace | `BLOCKED` |
| 要求升级、检查、迁移或退役 legacy | `BLOCKED`；另建独立 Change |
| 公司要求内网重建且无隔离测试环境 | `BLOCKED`；不同 bytes 不得继承本地测试结论 |

## Stage 30 — legacy backup（本合同不适用）

| 字段 | 合同 |
|---|---|
| 前置输入 | transition v2 已验证且 Stage 30 精确为 `NOT RUN`。 |
| 人工批准记录 | 本合同不接受 Stage 30 批准；legacy backup/upgrade/phase-out 必须另建 Change。 |
| 执行位置 / role | 无执行位置。 |
| 允许动作 | 无；不得读取、备份或验证 legacy。 |
| 预期输出 | transition 固定 stage map 中的 `NOT RUN`，不创建独立 evidence。 |
| PASS | 不适用；禁止把未运行投影为 PASS。 |
| FAIL | 不适用；如果已发生 legacy 操作则属于越界，停止并人工接管。 |
| BLOCKED / 停止点 | 任一流程要求 legacy backup、health、version、baseline 或 storage fact 时停止并另建 Change。 |
| Evidence | 仅 transition v2 中的 Stage 30=`NOT RUN`。 |
| 回滚边界 | 没有 live mutation；不得创建或删除任何 legacy backup。 |

## Stage 40 — legacy restore drill（本合同不适用）

| 字段 | 合同 |
|---|---|
| 前置输入 | transition v2 已验证且 Stage 40 精确为 `NOT RUN`。 |
| 人工批准记录 | 本合同不接受 Stage 40 批准；legacy restore/reconciliation 必须另建 Change。 |
| 执行位置 / role | 无执行位置。 |
| 允许动作 | 无；不得建立 restore target 或读取 legacy backup identity。 |
| 预期输出 | transition 固定 stage map 中的 `NOT RUN`，不创建独立 evidence。 |
| PASS | 不适用；禁止把未运行投影为 PASS。 |
| FAIL | 不适用；如果已发生 restore 操作则属于越界，停止并人工接管。 |
| BLOCKED / 停止点 | 任一流程要求 legacy restore、对象对账或 pre/post equality 时停止并另建 Change。 |
| Evidence | 仅 transition v2 中的 Stage 40=`NOT RUN`。 |
| 回滚边界 | 没有 live mutation；不得创建、修改或删除任何 restore namespace。 |

## Stage 50 — Gitea greenfield isolated install

| 字段 | 合同 |
|---|---|
| 前置输入 | 已验证的 Stage 20 transition v2（00/10/20 PASS，30/40/50 `NOT RUN`）、preflight candidate inventory v3、固定 target、exact bytes/checksums、maintenance window 与仅新 namespace 的回退步骤。 |
| 人工批准记录 | 未来独立 live mutation，只批准选定路径和 exact version/checksum；不授权 DNS/TLS 切换、repo import、timer、Actions auto deploy 或 production gate。 |
| 执行位置 / role | 仅 `gitea-ci/scm-ci`；`appserver-prod` 不执行 Gitea 变更。 |
| 允许动作 | 只按批准 tuple 建立 `aisoft-gitea` user/group、新 `aisoft-gitea.service`、`postgresql@18-aisoft-gitea.service`、固定 paths 与 loopback ports；校验 Gitea 1.26.4 和 PostgreSQL 18.4 provenance 后运行新实例最小本机 health/version/storage readback，再用 `collect-inventory --role scm-ci --mode post-install --output <post-json> --handoff-manifest <bundle>/handoff-manifest.json` 验证 candidate。不得运行 legacy Docker/HTTP probe、修改 legacy resources 或在同一次批准中改变路径。 |
| 预期输出 | exact installed version/checksum、chosen path、new namespace health/data/service receipt及 post-install inventory v3。SSH、Runner、sync timer、Actions auto deploy、production gate 均 disabled/inactive，DNS/TLS、reverse proxy、repository import 与 legacy observation 仍 `NOT RUN`。 |
| PASS | 新实例固定 identity/health 与 candidate post-install inventory v3 均 PASS，Stage 30/40 仍 `NOT RUN`；不能暗示 traffic cutover、repository migration 或 legacy health。 |
| FAIL | install/upgrade 已执行但 health、登录、对象 identity 或 service state 不符。 |
| BLOCKED / 停止点 | binary checksum、migration step、rollback snapshot、端口/路径或自动化禁用状态不明确；禁止切 DNS/TLS 或导入正式仓库。 |
| Evidence | Stage 50 evidence JSON + version/checksum/health/disabled-state 脱敏 receipt；不含 `app.ini`、keys、cookies 或日志原文。 |
| 回滚边界 | 只停止/隔离 `aisoft-gitea.service`、`postgresql@18-aisoft-gitea.service` 和新 `aisoft-gitea` namespace；禁止停止、重启、修改、删除或探测 legacy Docker container/image/volume/network/database/config/port/repository。不得自动 restore AppServer DB。 |

## Stage 60 — company Gitea bootstrap、保护与 company PR

| 字段 | 合同 |
|---|---|
| 前置输入 | Stage 50 PASS、GitHub allowlisted full SHA、approved source bundle、company repo owner/name、权限矩阵、required CI context 名称和 protected-main policy。 |
| 人工批准记录 | 未来独立 live mutation，只批准一个 repo/bootstrap SHA 与保护策略；不批准 merge、force push、auto deploy 或 production access。 |
| 执行位置 / role | 仅 `gitea-ci/scm-ci`；company Gitea 成为部署权威。 |
| 允许动作 | 建立/核对 company repo；从 approved source provenance 导入 immutable full SHA；立即保护 `main`；创建 company-side change branch/Issue/PR；配置 required CI，但由人保留 merge 权。 |
| 预期输出 | GitHub source SHA、company baseline SHA、branch head、repo protection、required context、PR number/body 和权限负向 readback。 |
| PASS | SHA ancestry/identity 一致；`main` 禁止 direct/force push；唯一 company PR 存在且未合并；required CI 已配置并绑定该 PR。 |
| FAIL | 已执行 bootstrap，但 SHA、protection、context 或权限 readback 与批准合同不符。 |
| BLOCKED / 停止点 | 只能得到短 SHA/tag、历史不相交、repo/branch/PR 重复、protected main 或 required CI 无法读回；不得把 GitHub/local PR 状态当 company approval。 |
| Evidence | Stage 60 evidence JSON + repo/branch/PR/protection/status 的脱敏 JSON/checksum；不回流 token、URL credential 或 host address。 |
| 回滚边界 | 只撤销本 stage 新建且未被消费的 bootstrap objects；不删除历史 repo，不重写 `main`，不合并 PR。冲突时人工决定。 |

## Stage 70 — one-shot inbound、Runner 与 Registry 正负验收

| 字段 | 合同 |
|---|---|
| 前置输入 | Stage 60 PASS、allowlisted sync profile 名称、company PR、disposable CI fixture、Registry test namespace、immutable digest 和权限负向矩阵。 |
| 人工批准记录 | 未来独立 live mutation，只批准一次 one-shot reconcile、一个 disposable Runner job 和一个 Registry fixture；不批准 timer enable、auto deploy 或 production credentials。 |
| 执行位置 / role | 仅 `gitea-ci/scm-ci`；不得在 `appserver-prod` 安装或运行 Runner。 |
| 允许动作 | 由人执行 `sync/inbound-sync.sh reconcile <allowlisted-profile>`；以同一 source SHA 再运行一次验证幂等；运行 disposable PR CI；以 digest 做 Registry publish/pull，并验证同 identity no-op 与不同 bytes 覆盖拒绝。 |
| 预期输出 | one-shot source/company SHA、唯一 sync PR、同 SHA no-op、Runner job identity、Registry digest/immutable conflict 和拒绝权限 receipts。 |
| PASS | one-shot 与重复调用不覆盖 `main`；Runner 可完成 disposable CI；Registry digest identity 一致；普通 Runner 无 production SSH、sudo、业务 DB 或任意 shell 权限。 |
| FAIL | 已执行验收但发生 SHA drift、重复 active PR、mutable overwrite、Runner 越权或 cleanup 不完整。 |
| BLOCKED / 停止点 | profile/credential 文件保护不合格、source history rewrite、CI 非 disposable、Registry 只提供 tag、无法做权限负向测试；timer 与 auto deploy 继续禁用。 |
| Evidence | Stage 70 evidence JSON + source/PR/job/digest/negative-check receipts；只记录 identity/status，不回流 credential 或 raw logs。 |
| 回滚边界 | 删除且仅删除 disposable job/artifact/Registry fixture；保留审计记录。不得删正式 repo、改 `main` 或启动 AppServer。 |

## Stage 80 — `scm-ci` artifact-only verification

| 字段 | 合同 |
|---|---|
| 前置输入 | Stage 70 PASS、Stage 00 同一 handoff identity、company-side exact release directory、full release SHA 与 compatibility checksum。 |
| 人工批准记录 | 只批准 `verify-artifact`；不提供 target profile、Secret、Docker endpoint 或 production action grant。 |
| 执行位置 / role | 仅 `gitea-ci/scm-ci`。 |
| 允许动作 | `operator/dependencies/docker-release/bin/aisoft-docker-release verify-artifact --release-root <absolute-release-root> --release-id <full-sha>`；随后重新运行 handoff validator。 |
| 预期输出 | `docker-release/v2` conformance PASS，`docker_calls=0`、`target_facts=NOT_READ`，release/manifest/archive/inventory/architecture/Compose checksums 与 Stage 00 相同。 |
| PASS | 所有 exact bytes 与 full identities 一致，artifact-only validator 不读取 target facts，不 build、不 pull/load、不 deploy。 |
| FAIL | 已运行只读校验且任一 checksum/identity/contract 明确不一致。 |
| BLOCKED / 停止点 | 不同 bytes、重建产物、mutable-only tag、target/profile/Secret 依赖、Docker mutation 或 unknown architecture/store；不得搬到 AppServer。 |
| Evidence | Stage 80 evidence JSON + artifact-only sanitized receipt + release/handoff checksum references。 |
| 回滚边界 | 只移除本阶段新建的 staging copy；Registry、Docker、service、DB 和 AppServer 不变。 |

## Stage 90 — `appserver-prod` read-only target readiness

| 字段 | 合同 |
|---|---|
| 前置输入 | Stage 80 PASS、Stage 40 backup/restore PASS、exact bundle 已离线搬运、root-owned protected target profile、fixed target ID `<fixed-target-id>`（由项目 target profile 声明）与完整 action grant review。 |
| 人工批准记录 | 未来独立只读批准，只绑定 action=`verify-target`、target ID、profile checksum 和 full release SHA；不授权 stage/migrate/activate/rollback。 |
| 执行位置 / role | 仅 `appserver/appserver-prod`；普通 Runner 不接触此 host。 |
| 允许动作 | 经人工批准后调用 `aisoft-docker-release-gate verify-target <fixed-target-id> <full-sha>`；gate 从 root-owned grant 解析固定 profile/audit path，调用方不能传 shell、Docker argv 或任意路径。 |
| 预期输出 | hostname/role、Engine/Compose、`linux/amd64`、containerd store、disk、profile/architecture/Compose compatibility 的 sanitized readiness receipt；无 container/DB mutation。 |
| PASS | fixed target、role、profile、release、compatibility、backup identity 全部匹配，read-only readiness 通过。 |
| FAIL | 已运行只读 gate，得到明确 incompatibility 或 target mismatch。 |
| BLOCKED / 停止点 | grant/profile mode/owner 不安全、unknown store/version、release bytes drift、backup/restore 不完整、需要普通 Runner/SSH/sudo/DB；不得创建 mutation grant。 |
| Evidence | Stage 90 evidence JSON + fixed gate started/completed audit identity与 sanitized readiness receipt；不回流 profile/env 内容。 |
| 回滚边界 | 只读，无 live rollback；撤销本次 verify-target grant 必须由人按公司权限流程处理，不自动创建下一 grant。 |

## Stage 100 — fixed production action、验证与独立回滚

| 字段 | 合同 |
|---|---|
| 前置输入 | Stage 90 PASS、company PR 已由人合并且 exact merge SHA 等于 release identity、maintenance window、previous release、migration plan、health gate、application rollback 与独立 DB restore decision 已批准。 |
| 人工批准记录 | 未来 production mutation；一次批准只允许一个 `<action>`，不得批准 wildcard 或整个序列。每个 `stage`、`migrate`、`activate`、`status`、`rollback` 之间都要停下审核再申请。 |
| 执行位置 / role | 仅 `appserver/appserver-prod`，通过 root-owned fixed action gate；`scm-ci` 只编排批准，不执行 target 命令。 |
| 允许动作 | 固定调用形态为 `aisoft-docker-release-gate <action> <fixed-target-id> <full-sha>`；`<action>` 只可取批准记录中的一个固定值。不得使用 generic deploy shell、任意 profile、Compose override、SSH command 或数据库命令。 |
| 预期输出 | 每个 action 独立的 started/completed audit、staging/migration/activation/health/status receipt、current/previous full SHA 与 exact image identity。 |
| PASS | 当前 action 的固定输入、pre/post state 与 health 全部满足；同 SHA 重复 action 只按既有 contract no-op，之后停止等待下一批准。 |
| FAIL | 已执行当前 action，但 migration、activation、identity、health 或 rollback 失败；立即停止，不自动继续下一 action。 |
| BLOCKED / 停止点 | company PR 未人工合并、SHA/bytes/profile/target/grant 不匹配、migration 状态不确定、缺 previous release 或会触发 DB restore；不运行命令。 |
| Evidence | 每个 action 一个独立 Stage 100 evidence JSON + fixed gate audit/checksum；禁止合并多次批准或回填未运行 action。 |
| 回滚边界 | application rollback 只切回 recorded previous release，不自动 restore PostgreSQL。DB restore 是新的破坏性人工决策；没有该批准时保持 `NOT RUN/BLOCKED`。 |

## Stage 110 — evidence 脱敏、对账、回流与关闭

| 字段 | 合同 |
|---|---|
| 前置输入 | 所有实际运行 stage 的 strict evidence、允许 artifacts、对应 approval references 和 cleanup/rollback receipts；未运行 stage 清单。 |
| 人工批准记录 | 只批准脱敏、校验和归档/离线回流；不授权重跑、修复 live 状态、启用 timer/gate、部署或删除 source evidence。 |
| 执行位置 / role | 两台公司 VM 各自在本地生成最小包；由人离线汇总为 company-cross-host evidence bundle。 |
| 允许动作 | 逐文件 schema validation、allowlist、Secret/hostname/address/raw-log review、mode `0600`、排序 checksum；只复制批准的 sanitized JSON/checksum/receipt。 |
| 预期输出 | versioned evidence bundle、full source/release SHA、stage/outcome matrix、artifact checksums 和 reviewer decision；公司侧 Stage 10–110：`NOT RUN` 项仍明确保留。 |
| PASS | 每个实际 stage 均能映射到唯一 approval/evidence/checksum，所有未运行/失败/阻塞项如实保留，无敏感或 live data bytes。 |
| FAIL | 已执行归档检查但 schema/checksum/allowlist/脱敏任一不通过；不传输不合格包。 |
| BLOCKED / 停止点 | 缺 approval/evidence、scope 投影、原始日志或 Secret 可能泄漏、状态被补写为 PASS；保持公司侧原件不动并人工处理。 |
| Evidence | Stage 110 evidence JSON + 最终 evidence `SHA256SUMS` + stage matrix；Git/PR/CI/local test 不能替代 company/live evidence。 |
| 回滚边界 | 归档只复制，不删除公司原件；若回流包错误，只撤销/隔离该副本并重新走 Stage 110 批准。 |

## 2. 当前状态与强制 NOT RUN

历史证据：Issue #120 建立了本 runbook；Issue #124 另行批准以 repo-external exact pilot release 运行本地只读
deterministic handoff regression（pilot 叙事见 `archive/company-delivery-pilot-历史-20260903.md`）。该 pre-Stage 00
local exact-release regression 已 PASS，但不生成 Stage evidence，也不是公司侧 handoff、安装或部署；正式搬运包
仍须从 protected `main` exact SHA 重新生成。采用本 runbook 的项目，其公司 Stage 00–110 进度由项目仓记录；
本仓库对任何项目均为 `NOT RUN`。

以下事项不得因 source commit、merged PR、local tests 或 future company PR/CI 而写成 PASS：两台 VM
inventory、Gitea install/upgrade、backup/isolated restore、GitHub inbound、company bootstrap、Runner、
Registry/cache、公司侧 `docker-release/v2` handoff、AppServer readiness、PostgreSQL migration/restore、Nginx、
application deploy/health/rollback、service/timer enable/restart、DNS/TLS/firewall 和 production。
