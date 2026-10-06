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
status: pending
branch: change/340-appserver-preflight-read
created: 2026-10-06
updated: 2026-10-06
---

# #340 T01 治理证据与未执行事实

## 基线与范围

- 日期：2026-10-06（Asia/Tokyo）。准备阶段曾为 AWAITING_START_CONFIRMATION；
  实际本人确认后，本轮执行止于 T01_GOVERNANCE_STOP。
- T01 前 HEAD / fresh origin/main：c9b5ef4e74592cbc68d6bdc6219568a1d51b6853。
- owner：01a10e8e-9128-7fa2-97a8-6493ee84be08，local。
- worktree：/private/tmp/issue-340-appserver-preflight-read。
- branch：change/340-appserver-preflight-read。
- 本文按阶段保存事实：准备/T01 只修改治理合同并 STOP；后续 fresh T02–T05 已完成
  白名单 source/local。下面早期 NOT RUN/失败记录是当时快照，不覆盖后续冻结验证。
- 本记录保存 AC1–AC6 的 source/installed/live层级；不是部署报告。

## 合同准备阶段执行结果（批准前记录）

| Command / check | Result | Evidence |
|---|---|---|
| installed gitea.issue.read --number 340（sandbox） | BLOCKED | TRANSPORT_ERROR，执行路径不可达，不能推断Issue不存在 |
| 同请求 host retry + comments.read | PASS（只读） | OPEN；comments=0/[]；content_version=0；triage/needs-triage；Issue正文AC1–6 |
| installed git.fetch.main（sandbox→host同请求） | PASS（host只读） | remote=origin/project=aisoft-platform；随后origin/main完整SHA读回 |
| fresh gitea.protection.read（同请求host） | PASS（读回） | main push/force禁用；admin-only merge；CI / verify (pull_request) |
| installed gitea.pulls.read --state all | GAP（完整性） | 返回50条最新PR，#341至#245；本页无#340；不是完整namespace/full pagination证明 |
| installed git.fetch.change --branch change/340-appserver-preflight-read | BLOCKED | sandbox TRANSPORT_ERROR；host HOST_COMMAND_FAILED；不能解释为branch absent |
| 本地refs/history/docs/worktree/claim/调度台账 | PASS（本地归属） | 本地创建前无#340 tuple；root台账仅本session；创建后exactbranch与ownermarker一致 |
| git worktree add + claim-worktree | PASS（本地准备） | .git只读sandbox被阻断后，原命令host成功；未takeover；last_push_head=null |
| source/installed manifest只读投影 | PASS（限定观测） | 两者均SHA256 509bdffb34494cbf82ef016d96e519c6bc3a17034a68ea052a516121aca4a8b9；38 operations；fixed gitea-ci；无preflight |
| source/installed技能与private-access比较 | GAP（局部文档漂移） | installed issue-session-flow/private reference缺source #286 dependency说明；aisoft-platform SKILL.md一致；未安装/修改skills |
| Context7 OrbStack resolve + query / 官方docs / local CLI --help | PASS（文档读取） | /websites/orbstack_dev；https://docs.orbstack.dev/machines/commands；run/exec aliases；help未列no-start，不是现场no-autostart证明 |
| target no-autostart primitive可靠性 | GAP | 尚无可证明实现；spec强制无法证明则zero target execution/BLOCKED |
| resolve-documents / resolve-required-documents 340 | PASS（文档） | 四角色明确映射到真实 appserver-preflight-read-261006 basename；required_docs=[summary,spec,plan,verification] |
| check-change-documents --repo 本worktree | PASS（文档） | changes=157；change-documents与change-pr-url两项PASS，gap=0；不证明新接口实现 |
| Classification.from_yaml / front matter / Ticket graph 静态核对 | PASS（文档） | 两处判级一致，platform/complex/add；production四角色；五票据，first frontier=T01，均pending |
| 新文档 whitespace / scope核对 | PASS（修正后） | 初次no-index --check发现末尾多空行FAIL，已修正；四文件重验无diagnostics；tracked source diff=[] |
| source feature/runtime tests / full smoke | NOT RUN | 准备阶段未获启动批准；批准后仍留给 fresh run，本轮 T01 只验证文档 |
| final-head required CI / PR / push | NOT RUN | 无 push/唯一最终PR授权 |
| 正式Mac/gitea-ci broker/AppServer helper安装及真实restore | NOT RUN | 无独立安装授权；manifest同hash不等于整个installed面验收 |
| operator创建/组/权限/SSH/sudo/Docker socket/PG授权 | NOT RUN | 固定候选aisoft-preflight可用性未知；零grant/provision |
| AppServer内部预检/live fresh task | NOT RUN | 未调用目标；2026-10-05 running/questing/arm64仅来源交接历史，未在本轮重验 |
| target/保留对象完整before/after / #333消费现场回执 | NOT RUN | 没有本轮liveinventory，历史清理不能代替 |
| deploy/VM lifecycle/Secret/DB/service/container mutation/UAT | NOT RUN | 不在本轮批准内 |

自身证据存放本 Issue evidence/；完整开发启动卡存放本会话visualization目录。
其它owner的worktree/台账/heartbeat均只读，本轮未恢复总调度。

准备阶段新文档尚未git add；普通git diff --check不包含untracked文件。
当时对四个新文档分别执行git diff --no-index --check /dev/null <exact-file>，
以没有whitespace diagnostics为依据；no-index对新增差异本身可返回1，不能误报失败。

## T01 治理应用与本地验证（本人确认后）

批准原文、批准前四文件/确认卡 SHA256 与 exact owner/tuple 绑定见
[approval receipt](evidence/t01-approval-readback.json)；原卡保持原字节。
本轮 fresh Issue/comments/main 读回见 [fresh readback](evidence/t01-fresh-readback.json)。
Issue 仍 OPEN/content_version=0/comments=0，live 仍只有 triage/needs-triage；
本轮只记录本地 approved，没有投影 live 标签或运行 Controller。

| Command / check | Result | Evidence |
|---|---|---|
| 本人确认与批准前 hash/owner/branch/HEAD 核对 | PASS | 直接本人确认 #340/exact branch/manual；四文件与原卡 hash 全匹配；owner 与 last_push_head=null；T01 前 HEAD/origin/main 均为 c9b5ef4e74592cbc68d6bdc6219568a1d51b6853 |
| installed Issue/comments/main 同请求 sandbox→host 读回 | PASS（host只读） | sandbox TRANSPORT_ERROR 后，同 typed 请求 host 成功；Issue/comments 无漂移，main 未前进 |
| 06 新增固定应用目标只读预检治理合同 | PASS（文档应用） | 仅新增 #340 小节：接口/目标/身份/字段/限额、no-autostart fail closed、Secret/零写边界、分层证据与独立安装授权；未修改 runtime/manifest/helper |
| resolve-documents / resolve-required-documents 340 | PASS | 四角色 basename/目录/branch 对齐；required_docs=[summary,spec,plan,verification] |
| check-change-documents --repo 本worktree | PASS | changes=157、pass=2、gap=0；change-documents 与 change-pr-url 均通过；只证明文档合同 |
| Classification.from_yaml / parse_front_matter / Ticket graph | PASS | 四文件判级一致、platform/complex/add；summary/spec/plan 本地 approved，verification pending；T01 completed，其余 pending，first frontier=T02 |
| JSON evidence、tracked/untracked scope 与 whitespace | PASS | 仅 06 与本 Issue 文档/证据；git diff --check 与逐文件 no-index --check 无 diagnostics；新增差异 rc=1 不当作测试失败 |
| staged scope/whitespace、原子本地 commit 和最终 clean readback | 提交后回执记录 | 提交前再次核对 staged allowlist；完整 SHA 与最终 staged check/clean 状态记录在本会话 visualization 的 T01 提交后 STOP 回执，避免自引用 |
| runtime/fixture/full smoke、CI、push/PR、正式安装、live、权限或部署 | NOT RUN | T01 治理隔离；本轮本地 commit 后 STOP，后续源码必须 fresh run，现场层与唯一最终 PR 仍需另确认 |

静态核对脚本首次因 PyYAML 不存在报 ModuleNotFoundError，随后改用仓库现有
parse_front_matter 并通过；未安装依赖。范围脚本首次将 Git 的中文路径 quoting 当成差异，
改用 -z 分隔后通过；未修改 Git 配置。两次脚本失败均未作为 PASS 或 feature 证据。
最终文档验证命令与输出见 [T01 document checks](evidence/t01-document-checks.json)。

本轮治理回滚仅通过本 owner 的追加 revert commit；没有向 AppServer/gitea-ci 内部执行 helper，
无目标写入或主机回滚。STOP 后不得在本 implementation run 接着执行 T02。

## Fresh T02 源码切片

fresh 起点仍为原 T01 commit；owner/branch/worktree、实际 Issue/comments 与 main 漂移见
[fresh T02 readback](evidence/fresh-t02-start-readback.json)。main 仅新增 #339 文档，没有 runtime
冲突；本会话未重写 T01 历史，也未静默变更批准前 pin。

- source operation/manifest 新增固定 localwms/localwms-local-test→AppServer；原项目、身份、ACL、
  credential route 与旧操作参数不变；旧 38-operation manifest 仍可读。
- 新 CLI 严格拒绝重复/外来 flags，拒绝不回显 caller values；broker 在任何 control/credential
  访问之前拒绝未知 target、跨项目及缺/增参数。typed runner 限额读 stdout 并验证固定拒绝回执。
- control 只允许 orb list --format json，按 bytes/rows 限额解析；没有任何 target executor。
  running、running→stopped 竞态仍返回 TARGET_EXECUTION_NO_START_UNPROVEN/BLOCKED、execution=0。
- 专用测试 12 项 PASS；既有 test_host_access.py 194 项 PASS；test-host-access-broker.sh PASS，
  其 installer 只使用临时 fake root；bash -n 与 ShellCheck PASS。
- 完整 smoke 的 sandbox 首次在 fixture 127.0.0.1 bind 被拒，FAIL（执行权限）；
  相同命令 host 路径复验在进行，尚无最终 PASS。最终 T05 必须冻结源码后重跑并绑定 tested bytes。
- live classification 写入被 automatic approval review 拒绝；原因：原批准仅 source/local，
  未含 live 标签。该写入未执行、未绕路重试，lifecycle approved/Controller 为 NOT RUN。
  source/local 工作仍按原直接本人批准完成；最终 PR readiness 为 BLOCKED。

T02 完成的是安全拒绝与 source fixture 切片，不是 no-autostart primitive/目标执行可用性证明。
正式安装、权限与 live 层均 NOT RUN，无法据此解除消费者 #333 的现场前置。

## Fresh T03 collector

单文件 stdlib helper 按固定路径/字段采集 identity/OS/CPU/RAM/filesystems、Node/npm/PG18、
TCP/UDP sockets、六 unit、exact users/groups 与八个目录 metadata。npm 只读 package.json version；
PG 实例/角色仍 PG_READ_ROUTE_UNAUTHORIZED/BLOCKED，不连接或读取凭据。

- native 内容/版本探针用 anchored openat + O_NOFOLLOW；每级可信 root owner/mode、regular ELF
  校验后以 opened fd 执行，并保留真实 argv[0]，避免路径替换及 PostgreSQL 版本名错判。
- 目录仅 no-follow metadata；os-release 仅允许固定 /usr/lib/os-release alias；没有读取未知
  symlink target、应用配置、归档正文或 source profiles。uid/gid/mode/字段严格投影。
- subprocess 双 pipe 在读取时限额、进程组超时取消；probe 5s/request 30s；helper 入口另有
  Linux 30s alarm。缺 binary/path 与权限据实 GAP/BLOCKED，固定路径不动态扩大。
- 25 个专用 source/local 测试 PASS：字段投影、Secret sentinel、max/max+1、root/mode拒绝、
  real temporary filesystem 的 symlink escape/opened-inode 替换、fixed vectors、CLI拒绝与超时。
  root UID 在 temporary fixture 模拟；不是现场 root/operator/权限证明。
- T02 host smoke 复验已经运行到 1127 项，但遇到正在添加的 T03 red test（helper 尚未创建）
  FileNotFoundError，FAIL；该测试在 helper 实现后已 green。此中途结果不作为冻结源码验证。
  T05 在完成实现/评审修复后重跑完整 smoke，正式安装/live 仍 NOT RUN。

T03 不增加任何 VM executor。真实 no-autostart/operator/helper 与最终 PR label/base 门仍待证。

## Fresh T04 Docker/PG/零写 fixture

- Docker 最小投影仅 version/api version/platform/storage driver、container name/state/ports/named
  volume names；Command/Env/labels 与 bind source/destination 均不输出、不持久化。
  仅三个固定 GET 数据源 /version、/info、/containers/json?all=1&limit=129 的隔离 fixture，
  128/129、64KiB、权限拒绝、异常脱敏和零 CLI/fallback 均验证。
- Native 仅核对固定 AppServer 内 socket metadata，没有 connect/HTTP 请求能力。
  Docker 官方 [dockerd](https://docs.docker.com/reference/cli/dockerd/) 说明支持 systemd socket
  activation；仅 socket 存在/owner/mode 不能证明不会启动 daemon。安全默认是
  DOCKER_NO_START_UNPROVEN/BLOCKED、zero socket connects，而非“只有 GET 所以不会启动”。
  这是 no-Engine-start 合同下的技术 GAP；未扩展六 unit/文件白名单或新建权限/服务通道。
- PostgreSQL 实例/角色默认 PG_READ_ROUTE_UNAUTHORIZED/BLOCKED、zero DB connections；
  既有 PG18 --version 只执行 opened trusted ELF，既有 arch/runtime 均按观察报告。
- 30 个专用测试 PASS；包含 timeout 取消 descendants，临时 delayed-write marker 未创建；
  Native socket metadata 即使模拟匹配也不调用 socket.connect；native fixtures 的 UID/mode
  仅模拟，不构成 installed/operator/whole-machine before/after 证明。

AC1/AC3 的 source fixture 可以继续完成；AC2 的真实 running target/no-autostart 与 Docker
实际只读通道仍 GAP，AC4–AC6 installed/live 为 NOT RUN。不能将六项整体标 PASS。

## Fresh T05 冻结验证与交接

冻结 source HEAD：`83fdd12dc93b79442aae9c0763c7e92e221344d8`，
tree：`67f98c6a654a5559122094d6982f8d5aeed9cf51`。测试前后九个新增/修改 source、fixture 文件
SHA256 全一致；正式安装/target/live 为 NOT RUN。T05 后续 commit 只改本 Issue 文档/证据，
提交后 HEAD/tree/clean/owner 回执在本会话 visualization 的 `T05-source-local-stop-state.json`，
不在 commit 内写自引用 SHA。

| 实际执行 | 结论 | 限定证据 |
|---|---|---|
| 双轴 code-review（T01…e2250d8）+ red→green 修复 | PASS（修复后） | Standards 2 项/最严重 P2；Spec 2 项/最严重 P1；两轴的发现对应同两处缺陷，均修复于冻结 SHA |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p test_application_preflight.py -q` | PASS | 33 项；strict args、错位 parser 脱敏、缺 service GAP、identity/limits parity、Secret、路径替换/限额/竞态/取消 |
| 相同 discovery 的 `test_host_access.py` | PASS | 194 项旧行为回归；预期旧 CLI 拒绝测试的 argparse 输出不是新 route 输出 |
| `PYTHONDONTWRITEBYTECODE=1 LC_ALL=C bash codex/tests/smoke.sh`（host，本地 fixture） | PASS | exit 0；runtime unittest 1147 项/97.292s；最终 Codex platform static smoke checks passed |
| smoke 包含 `test-host-access-broker.sh` / `test-install-host-access-broker.sh` | PASS（fake roots） | 禁止把 fake installer PASS 解释为正式安装；本轮没有新增 installer 行为 |
| 附加精确 fake-root module/manifest 比较 | PASS | 9 个 package 文件字节一致；新增 application_preflight.py 已复制；没有自动安装 AppServer helper、没有 token/.env |
| smoke 的 shell syntax / ShellCheck | PASS | 涵盖修改的 test-host-access-broker.sh；可用 ShellCheck 已执行 |
| mapped docs / scope / JSON / whitespace / owner | PASS | 四角色 resolver；changes=157/pass=2/gap=0；五票据 completed；staged/final clean 另由提交后回执读回；无 AGENTS/skills/controller/CI/installer 或应用变更 |

完整 machine-readable 记录见 [source validation](evidence/t05-source-validation.json)。
附加范围核对脚本初次将现有 parse_front_matter 的 Issue 字符串与 int 比较而 FAIL，
按真实 parser 合同改为 exact string 340 后 PASS；这是核对脚本错误，没有修改 parser 或放宽验证。
定位票据 parser 的首次文件搜索引用不存在的 tickets.py，随后按真实 controller.py 查到
纯文档解析函数；没有执行 Controller 或提供 synthetic approved 标签。
只持久化白名单输出的 [source fixture receipt](evidence/t05-sanitized-fixture.json) 是
SOURCE_FIXTURE：36 items、37 个模拟调用，actual target execution=0，fingerprint 为明确标注的
模拟值；真实 helper 文件 SHA256 单独绑定。它不是 #333 的现场解阻塞证据。

### Standards

固定 HEAD 的 `cli.py:92–119` 可在合法 flag 错位时由 argparse 回显请求值，违反
06 的稳定/脱敏错误合同；`application-target-preflight.py:498–508` 将 not-found service
包装为 PASS，违反 06 的缺项 GAP 合同。两项均 P2，当前补丁已修复；CLI 修复由 reviewer
独立复测。未提出额外 smell 改造；独立 stdlib helper 与 host 的重复 bounded reader/limits
来自单文件合同，增加 parity 测试保持一致，没有为了抽象扩大依赖。

### Spec

固定 HEAD 的 CLI 回显违反 spec“不能输出 raw 请求值或任意错误正文”（P1）；
not-found service PASS 违反“缺 binary/service/metadata 明确 GAP/BLOCKED”（P2）。
两条 red 测试分别复现 SystemExit(2)/sentinel 和 expected GAP/observed PASS；
修复后统一 ARGUMENT_MISMATCH 且 loader 零调用，service 为 MISSING/GAP。
未发现 scope creep，两个 reviewer 均核查当前修复；VM/Docker 安全拒绝符合已批 fail-closed 合同。

Standards：2 项/最高 P2；Spec：2 项/最高 P1；两轴各自保留，发现已全部修复。

### Source helper 与未来安装清单（未批准、未执行）

helper：`codex/tools/application-target-preflight.py`，29508 bytes，SHA256
`75f3a622b2115769c0f4f80f859aae60473abdb9778bafeac8e5d400b1f2ab4c`，
version `application-target-preflight/v1`。未来目标 `/usr/local/libexec/aisoft/application-target-preflight`，
root UID 0、0755、可信且不可 group/other 写的 ancestors；AppServer 只单独安装该文件，
不运行完整平台 installer。正式 merged SHA、operator/既有权限、VM no-start transport、
Docker no-start 条件、exact 必需主机集合与真实 restore 仍未绑定。

[未来文件清单](evidence/t05-future-installation-inventory.json) 列出 26 个 broker source 文件的
destination/mode/SHA256 和 installer 派生 metadata 的单独约束；没有凭据。
它是 source 准备清单，不能直接执行。正式卡必须在 manual merge 后固定 merged SHA，
按每个获准 host 保存旧字节/mode/owner/缺项、验证实际 restore、no-op 与 installed readback；
未获卡批准之前不安装，不用 source revert 代替现场恢复。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1 | PASS（source/local） | strict manifest/CLI/broker/runner、正反 kwargs、拒绝先于 IO、旧路由与 38-operation 兼容回归；33+194 专用/旧测试及 full smoke |
| AC2 | GAP（真实 running/no-start） | stopped/missing/race fixture PASS、零目标命令；running 也明确 BLOCKED，尚无可靠 no-autostart execution primitive，未实际调用 helper |
| AC3 | PASS（source fixture）；native Docker read GAP | 字段/trust/Secret/bounds/timeout/缺项/旧行为 fixture；native Docker 仅 metadata 后 DOCKER_NO_START_UNPROVEN/BLOCKED、零 connect；PG 零连接 |
| AC4 | NOT RUN（正式安装） | fake-root 复制/字节 PASS 和 future 清单仅 source 准备；正式 merged source 安装/实际 restore 未授权 |
| AC5 | NOT RUN（live） | 无 installed/operator/no-start ready 证据，没有 AppServer target 调用 |
| AC6 | NOT RUN（现场交接）；source fixture PASS | 输出无 Secret 模拟回执；整个 VM/保留对象 before/after 与 #333 live 消费未取得，不宣称消费者解阻塞 |

## 需要本人处理的下一步

source/local 已完成，当前停在 `BLOCKED_EXTERNAL_GATES`，没有运行 Controller，
没有 `AWAITING_PR_CONFIRMATION` 或唯一 PR。当前只需要处理发表前的元数据/本地基线，
不需要你启停 VM、授予 operator 权限或安装 helper。

在本 #340 会话回复下面一句即可，一次覆盖两个具体的受控步骤：

> 确认 AISoftPlatform #340（change/340-appserver-preflight-read，manual）仅批准 existing typed broker 投影 type/platform、complexity/complex、approved 并读回；另批准本 owner 将未 push 的本地分支 rebase 到 96ba8a17baad8e9854d4e8d0397d4162b8067b09，先以 refs/aisoft/recovery/340/pre-main-integration 保留当前 HEAD 和原 T01，核对 source bytes 不变；不批准 push/PR、merge、安装、权限、Secret 或部署，唯一最终 PR 另确认。

确认后的最多三个动作：

1. fresh 读取 Issue/comments/main；main 必须仍为上述 exact SHA，漂移则不套用旧批准。
   通过 existing installed typed broker 投影 classification，再 lifecycle approved，保留其它标签，读回验证。
2. 在 exact owner worktree 先将 recovery ref 固定到提交后最终 HEAD，再 local rebase exact main。
   不写 main、不 force-push；保留原 T01 可恢复性；出现 conflict/scope 或 source 字节变化即停止，
   必要时 abort 回原分支，不能静默修改本次受测 source。
3. 重新核对全部 frozen source bytes、owner、docs/base 门及 remote namespace 完整性；
   全部门可证明时才制作唯一 final manual PR 确认项。完整远端 namespace 仍 GAP，
   不用当前 50 行或 HOST_COMMAND_FAILED 伪装不存在，也不换入口绕开 broker。

成功后 owner 回报 live projected 实际读回、recovery ref、rebase 后 HEAD/base/source-hash parity；
然后继续最终 PR 候选核对。PR 发表本身仍需要单独确认。若完整 namespace 仍无法证明，
输出其具体最小补证动作，不把 #327/#336 机械挂成产品硬依赖。

自动审批审查已拒绝 `gitea.issue.labels.classify` 的 live 写入：原实际批准仅 source/local。
命令未执行、未间接重试；这就是需增加 exact live 元数据授权的原因，不是再次询问启动。
本地 rebase 会重写本分支 commit SHA；所读
[aisoft-matt-workflow SKILL.md](/Users/benque/.agents/skills/aisoft-matt-workflow/SKILL.md)
明确写“Never deploy, rewrite history, force-push, or silently switch to a different tracker or repository.”
它并非要求常规确认，而是禁止 history rewrite；上述本人明确批准才可覆盖该规则，
例外只限未 push 的本 owner 分支并保存恢复引用，不延伸到他人/受保护 main/远端历史。

VM no-start 和 native Docker 通道的当前具体处置已落实为安全拒绝、零执行/零连接。
本 source 候选保留 AC2/native Docker GAP；不要求人停机试错、放宽权限或批准未证明的通道。
若未来需要 positive target observation，必须先给出新固定 primitive/最小通道的可审查设计与证明，
再按相同 Issue 的独立安装/权限/live 卡处理，不能由本次元数据/rebase 确认替代。

## 遗留风险与未完成项

1. 完整远端#340命名空间证据GAP：无已发现冲突；不得将HOST_COMMAND_FAILED当不存在。
   已再次核对本地唯一 owner/tuple；远端完整性未通过，发现 actual 冲突即 STOP。
2. 现有orb help无no-start参数：running前读不能证明竞态后不自启。
   默认BLOCKED，不能把fixture正向模拟替代真实execution primitive证明。
3. operator/helper可用性、Docker/PG获准访问是live条件；未经精确权限卡不provision或fallback。
   PG角色/旧归档/未知datadir不能从固定路径猜测完整性。
4. 原实际本人启动批准已由 T01 STOP 与 fresh T02–T05 source/local 完成；live 分类投影仍未执行。
   fresh main 96ba8a17… 非当前 HEAD ancestor；broker.py:3378–3392 预测 BASE_BRANCH_STALE，
   merge commit 也被拒绝。未调用 publish 以实测该写入硬门，没有 rebase/merge 或历史重写。
5. source PR/CI后仍须将AC4–AC6未执行事实保留，source合并不等于通道installed/live ready。
   后续唯一PR确认卡必须明确source与现场边界，不能宣称六条AC整体PASS或消费者已解阻塞。
