---
issue: 340
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/340
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/340-appserver-preflight-read
created: 2026-10-06
updated: 2026-10-06
---

# #340 固定 AppServer 只读预检合同

本文件为实际本人已批准的生产阶段 complex 合同。本轮仅 T01 治理应用/本地提交后 STOP；
后续 fresh run 可继续白名单源码实施、本地 fixture/测试、修复和 commit，未授权现场 mutation。
事实基线和归属见映射 summary；本文不使用历史清理记录证明当前 VM 状态。

## 目标与原因

补齐 LocalWMS #333 AC2/AC5 所需的固定 AppServer 无 Secret 预检。
一个 typed operation，只读、可搜索、受限、fail closed；不负责选择或改变交付架构。

## 接口、数据与兼容性影响

- operation：application.target.preflight.read；mutating=false；arguments 精确为 [target]。
- caller：仅 --project localwms --target localwms-local-test。target 必须为单一 strict string，
  大小写和完整字符精确匹配；缺失/多传/null/列表/跨项目/未知 target 在任何目标执行前拒绝。
- 建议固定 manifest 区块 application_targets，唯一一行：
  project_id=localwms、target_id=localwms-local-test、machine=AppServer、
  operator=aisoft-preflight、helper=/usr/local/libexec/aisoft/application-target-preflight、
  helper_version=application-target-preflight/v1。
  必须 strict keys、唯一 pair、精确 machine/operator/helper，不能加载 caller 提供的 manifest。
- 该操作使用独立 application-preflight route，不解析或使用 Gitea PAT；
  Gitea project agent 不授权 VM operator/SSH/sudo/DB/Docker 权限。
  不得更改原 host-operator、mac_host.orbstack_machine=gitea-ci 或任何既有 operation 参数集合。
- CLI/HostAccessBroker typed kwargs/runner/contract/config 只增加 target 通路。
  所有旧操作透传 target=None 时的形状和语义保持；新 route 不允许改变项目 ACL。
- source helper 为单一一次性、无 caller 参数的 Python/stdlib collector，
  路径和字段编译固定并与 manifest 合同做 parity 测试；不另建 daemon 或通用 helper。
  AppServer helper 正式安装不是现有 Mac/gitea-ci installer 的自动副作用。

## 目标执行闸门

1. 先完成 strict project/operation/exact argument/schema gate；拒绝时 target runner/helper
   与 credential resolver 的调用次数均为零。不能输出 raw 请求值或任意错误正文。
2. 只读控制面绑定精确 AppServer，并确认已 running；停止/缺失/重名/无法读回均 BLOCKED，
   不执行 target helper。禁止 start/restart/create，也不把另一 VM 的结果填入目标回执。
3. running 预读不足以证明零自启。必须有不会自动启动停止 VM 的执行 primitive 的证据，
   包含“running 预读后、执行前停机”的 fixture。没有此证据返回
   TARGET_EXECUTION_NO_START_UNPROVEN / BLOCKED，target execution=0。
   当前 orb run/exec help 没有 --no-start，本合同不宣称该 primitive 已可用。
   source 实现可研究/验证固定 primitive；禁止以 raw orb/SSH/root/sudo 现场试错或
   新建常驻监听服务替代。若需要新增通道/权限，先输出最小具体差异，STOP。
4. helper 必须绑定受信任版本/固定路径和实际 operator；不存在或 owner/mode/祖先路径
   不可信时拒绝。不得通过 PATH、shell profile、ORBENV、用户 config 或环境变量覆盖探针。
5. 不使用 shell=True、登录 shell、任意 command/URL/path、credentialpath、port-range、
   sudo command、动态发现执行文件、容器 exec 或 PM2 CLI。
6. 用 monotonic deadline、stream bounded read 和取消机制控制全部子进程。
   stdout/stderr 先限制 bytes 再解析，raw stderr/日志从不直接返回，错误用稳定 reason。
   response/helper schema 与身份/version 不符一律失败，不用宽 schema 接受未知字段。

## 固定字段与路径

下面路径是本 spec 已批准的只读 allowlist，不可由 caller 扩展。
存在性/值当前均未 live 读取；部署兼容性由 LocalWMS 自身 lock/runner 决定。

| 分类 | 固定输入与允许输出 | 明确限制 |
|---|---|---|
| 身份/OS | hostname、/etc/machine-id；/etc/os-release，仅 ID/VERSION_ID/VERSION/VERSION_CODENAME；architecture | os-release 合法 symlink 只允许精确 /usr/lib/os-release；值有类型/长度上限 |
| CPU/RAM | CPU count；/proc/meminfo 的 MemTotal/MemAvailable | 不返回完整 proc 内容或进程 argv |
| filesystem | /、/opt、/var/lib/postgresql/18/main 的 statvfs | PG 路径只对已存在、可安全访问的 fixed path 读取，不猜配置/自找 datadir；缺失/拒绝逐项 GAP/BLOCKED |
| Node | /opt/node24.18.0/bin/node 的存在性、numeric uid/gid/mode/type、可信版本 | 不加载 profile；可信 binary 才可固定 --version，拒绝 user writable/未知 symlink 目标 |
| npm | /opt/node24.18.0/bin/npm metadata；固定 /opt/node24.18.0/lib/node_modules/npm/package.json 仅 version | 不运行 npm CLI，不读 .npmrc、不建缓存；symlink 只报告 metadata 或验证精确受信任目标 |
| PG18 binaries | /usr/lib/postgresql/18/bin/{postgres,psql,pg_dump,pg_restore} 存在/mode/owner/可信 --version | 不运行 server/initdb/连接或读 PG config/应用 Secret |
| sockets | 固定 TCP/UDP listening address/port、可获准的 pid/comm | 不含 argv、Environment、cwd、完整 Unix socket path；权限不足不能补 sudo |
| services | nginx.service、postgresql.service、postgresql@18-main.service、pm2-benque.service、localwms-api.service、localwms-worker.service | 只 LoadState/ActiveState/MainPID；无 Environment/ExecStart/日志；pm2-benque 是固定候选名，不能动态枚举或初始化 PM2 |
| 用户/组 | exact localwms 与 aisoft-preflight 的存在性、numeric uid/gid/有限组名 | 不读 shadow/passwd 全文，不输出 home、登录配置或添加用户/组 |
| 目录 | /etc/localwms、/opt/localwms、其 current/releases/state/backups；/opt/retired-app-data-20260913、/etc/nginx/sites-retired-20260913 | 仅 lstat/numeric owner/mode/type/symlink metadata；后两项是历史归档候选，当前存在性未验证，不列目录、不读配置/归档正文 |
| Docker | 仅 AppServer 现存 /var/run/docker.sock：version/platform/store，bounded container name/state/ports/named-volume name | 固定 read-only requests；无 Env、Command/argv、labels、host mount source/destination、inspect/logs；不读 Mac context，不用 DockerLab 代替 |
| PG 实例/角色 | 实例身份/角色能力的独立状态槽位 | 当前 binding 没有已获准非 Secret DB read route：默认 PG_READ_ROUTE_UNAUTHORIZED/BLOCKED，零连接；不借 postgres/root，不读 .pgpass、连接串或业务数据 |

/opt/retired-app-data-20260913 与 /etc/nginx/sites-retired-20260913 来自历史保留边界，
只用作精确 metadata 候选，均未在本轮现场验证；它们不是“LocalWMS 所有归档”的证明。
未绑定其它旧归档路径则 archive_inventory_complete=false/GAP。
未知现存 PG datadir、PM2 owner/unit 不动态猜测，不从固定候选路径推断完整实例清单。

安全 lstat/symlink 拒绝必须发生在内容读取/执行前；固定 metadata 内容与未知配置内容分开。
不得仅用 exists 然后跟随任意 symlink。文件读/版本执行要求同一次可信校验依据、
固定祖先路径和 owner/mode，fixture 覆盖路径替换/逃逸；无法可靠保证时按项 BLOCKED。

Docker daemon/socket/operator 权限未证实时按项 BLOCKED。
本操作没有 provision 能力，不加入 docker group、不 chmod/chown socket，不 pull/build/up/down/prune。
只有已存在、单独确认的 socket 访问才进入 fixed GET collector；传输原始响应不持久化，
最小投影是唯一输出，body/row 达界限后标记不完整。CLI 配置或 broad inspect 不能作为捷径。

## 输出与限制

建议 output contract=application-target-preflight/v1；各 item：
status、reason、observed value（仅白名单）、complete、observed_at。
顶层：UTC/JST、project/target/machine、actual operator、helper_version/source fingerprint、
limits、duration、各 item 与 transport/保留证据边界。不得把预检观察 PASS 解释成可部署。

| 资源 | 固定上限 |
|---|---|
| 全请求 / 单一探针 | 30s / 5s；超时即取消，不后台继续 |
| 控制面响应 / helper 响应 / 单项文件读取 | 64KiB / 256KiB / 64KiB |
| 机器枚举 / sockets / containers | 64 / 256 / 128；读取 max+1 判溢出 |
| unit / 用户组 / directory metadata | 6 units / 32 groups / 16 paths |
| 单一文本值 | 256 bytes；容器名/组名等另限制字符集 |

枚举溢出：GAP + LIMIT_EXCEEDED + complete=false，不把截断部分标 complete=true；
超时：BLOCKED + PROBE_TIMEOUT；无法读权限：BLOCKED；已确定缺项：GAP；
目标/schema/trust mismatch：FAIL，拒绝执行；未尝试项：NOT RUN。
已观测值不满足应用 runtime lock，不静默修改目标或版本，也不放宽 LocalWMS 目标闸门。

“零写”证明精确限定 helper 发出的调用/文件访问，不声称 OS audit/atime 或
全 VM 对象不变。fixture 保存命令/文件访问 spy 与 Secret sentinel；现场完整 before/after
无法取得时保留 NOT RUN。禁止为证明零写而创建现场测试对象或停 VM。

## Acceptance criteria

- [ ] AC1：config/schema/CLI/broker/runner exact kwargs 与正反测试一致；
  缺/增参数、未知 target、非 localwms、大小写变体、跨项目、shell/path/URL/credentialpath/
  port-range/sudo 均在目标执行前 fail closed；旧 Gitea route 行为不变。
- [ ] AC2：stopped/missing target 与 read→execution race fixture 返回 BLOCKED，零 start/exec；
  running 只能调用已证明 no-autostart 的固定只读 helper，零 lifecycle/host/DB/container write。
- [ ] AC3：全部字段白名单、禁止 Env/argv/Secret、safe metadata、bounds/timeouts/overflow、
  Docker target/socket/permissions、PG 无凭据通路与旧操作回归都有 fixture。
  缺 binary/service/metadata 明确 GAP/BLOCKED；禁止隐藏错误造 PASS。
- [ ] AC4：source/唯一 manual PR 后，只有独立 exact merged source 安装卡获批才执行
  必要 Mac/gitea-ci broker 安装与 AppServer helper 精确安装、真实恢复、版本/bytes/mode/owner
  读回；operator/权限卡另批，不复制/变更 Secret。未批准/未执行为 NOT RUN。
- [ ] AC5：安装/权限/执行 primitive 获准且 ready 后，由 fresh localwms task 经 installed
  typed operation 读取实际 AppServer 目标/OS/runtime/资源/端口；无现场反向试错。
  尚不能读取的 item 保留真实 GAP/BLOCKED，不能伪造整体 PASS。
- [ ] AC6：生成 #333 可直接消费的无 Secret evidence/receipt，身份/时间/版本/limits齐全。
  AppServer/gitea-ci/既有容器卷服务保留按实际 before/after 证据呈现；缺完整读回保持 NOT RUN。
  source 回执不能当作 installed/live 或消费者解除阻塞证据。

## 允许修改范围及既有合同依据

以下源码 allowlist 已获本人启动批准；本轮仅 T01 的 06、本 Issue 四份合同与自己的证据，
其余路径必须后续 fresh run 重新读取后实施。

| 路径 | 修改边界 / 当前依据 |
|---|---|
| 06-运维手册与踩坑集.md | 仅 T01 应用 #340 固定 target、安全拒绝、层级与安装边界；AGENTS 治理独立步骤规则、06 §1.0、Issue AC1–AC6 |
| codex/config/host-access-broker.json | 仅添加 operation/application_targets/独立 route；保持所有旧字段和项目声明；Issue 最小方案、AC1、AC3 |
| codex/runtime/aisoft_host_access/contract.py | strict target/schema/route validation；现有 exact-key 合同、AC1 |
| codex/runtime/aisoft_host_access/cli.py | 仅新增 --target optional typed scalar，不改旧参数语义；06 精确参数集合、AC1 |
| codex/runtime/aisoft_host_access/broker.py | 在 credential/target execution 前拒绝，派发唯一 readonly operation；AC1/AC2 |
| codex/runtime/aisoft_host_access/runner.py | 固定 application preflight adapter，不新增 controller 行为；AC1 |
| codex/runtime/aisoft_host_access/application_preflight.py | 新增固定 transport gate、bounded reply/schema，host 不取 Gitea credential；AC1–AC3 |
| codex/tools/application-target-preflight.py | 单个 fixed one-shot collector，仅本 spec 字段/路径；AC2/AC3、未来 AC4 helper 制品 |
| codex/runtime/tests/test_application_preflight.py | 新建隔离正反 fixture/Secret/零写/竞态/超限/回归；AC1–AC3 |
| codex/runtime/tests/test_host_access.py | 仅新 operation/schema/args 与旧行为回归相关断言；AC1/AC3 |
| codex/tests/test-host-access-broker.sh | 仅 operation 数/target 合同及禁止参数断言，保留旧硬门；AC1/AC3 |
| 本 Issue 映射的 summary/spec/plan/verification 与 evidence/ | 分类、合同、票据、真实证据与手工 PR 卡；03 文档合同、AC1–AC6 |

不修改 AGENTS.md/CLAUDE.md、global skills、Agent/provider/controller、.gitea/workflows、
gitea-governance.json、host-role、credential catalog、installer、其它项目或其它 Issue。
现有 installer 自动复制 Python package 与 manifest；无需为此改其执行/权限合同。
AppServer 的独立 helper 安装卡由其固定 source 文件单独列清单，不运行完整平台安装器
往 AppServer 安装其它管理组件。若实现证明必须改 installer/CI 等白名单外文件，STOP，
先提供具体必要差异并更新本人确认的合同；不能把“测试需要”作为扩大治理范围的授权。

## 治理 STOP 与 fresh run

T01 独立受控步骤只修改 06 的治理合同和 #340 文档，验证、提交后立即 STOP。
T01 不修改运行中 AGENTS，也不改 manifest/CLI/runtime/helper/tests/install/CI。
后续 fresh run 重新读取 AGENTS、skills、T01 commit、exact owner/tuple 和 latest Issue/comments，
才实施 T02 及之后源码；同一范围的本人启动授权持续，不新增例行确认。
本轮 T01 应用 06 与自身文档，完成本地提交后 STOP；提交 SHA 以提交后的 STOP 回执为准。
本 Issue 同一 branch 最终只建一个 PR，不另造治理 PR 或子 Issue。

## 风险与回滚约束

源码失败在本人 worktree 追加 revert/recovery commit，不重写他人或受保护 main，
保留失败证据和唯一 tuple。没有真实 mutation，不运行主机 rollback 命令。

未来安装按单独卡固定 merged SHA/helper bytes、文件权限和可信源、目标/operator/window、
snapshot/restore/no-op/installed readback；operator 另批最小权限、恢复方式和成功/失败条件。
任何 installer exit 0、源码/CI PASS 均不能替代现场字节或安全读回。
缺权限不做宽权 fallback，超限不放宽 limits，无可靠 no-start primitive 时不调用目标。

## 非目标

LocalWMS 源码/ADR/lock、OS 更换/升级/降级、新 LTS VM、VM lifecycle、安装软件、
用户/组/ACL/sudo/SSH/credential provision、服务/代理/PM2/Docker/DB写入、真实部署/UAT均不在本次。

## 未决问题

无待选择的产品方向：default fail closed。no-autostart transport 的具体实现证明和 operator
现存能力是技术待证项，不能标为已解决，也不能为了它们给源合同添加机械 hard dependency。
如固定 transport 无法实现，输出精确技术证据和最小替代合同后 STOP；未授权额外服务/SSH路径。
