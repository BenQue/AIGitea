---
issue: 316
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/316
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
  - ci
depends_on:
  - 313
status: pending
branch: change/316-service-pat-rotation
created: 2026-10-02
updated: 2026-10-03
---

# #316 证据记录

## 基线与范围

- 本票固定 base：5c2cd726c9aeaee9d17541d8feb049e33881bbac；T01 仅治理文档，本地 commit SHA 由会话 handoff 与 Issue 回执记录，避免文档自引用 SHA。T01 当时尚未实施 runtime；T02 当前实现与证据见下节。
- #313 PR #315 merge：480d1d262c3e915f546049ede3f34ad7d3362f50；已用 broker fresh fetch 与 local ancestry 验证在 origin/main。
- 独立 worktree：/private/tmp/issue-316-service-pat-rotation；branch：change/316-service-pat-rotation。
- Owner session：01a0fc7c-3835-7322-874e-c910518c5746；claim result=created。
- 用户两次“确认”最后明确承接“两台 broker 重装”提问；此前只使用该安装授权；随后用户明确确认完整 spec/plan 和新增撤销后台方案，本轮 T01 获准执行。fresh turn 后可在合同内实施 runtime；PR/后续安装/live Secret 仍未授权。
- 本记录负责 AC-1 至 AC-7 及前置证据；前置 PASS 不等于这些 AC 全部达成。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| typed issue.read 316/313、pull.read 315 | PASS | #316 open；#313 closed/completed；#315 merged；closed/completed 不证明 installed/live |
| typed git.fetch.main + git merge-base --is-ancestor | PASS | origin/main=5c2cd726...，315 merge=480d1d262... 是其 ancestor |
| 安装前两台 public 文件摘要 | GAP（已修复） | manifest、governance contract、bootstrap 三个文件两台字节相同且均旧；Mac scopes 只有 write:repository |
| Mac sudo -n bash installer | BLOCKED | sudo: a password is required；未安装 |
| gitea-ci sudo -n bash installer | PASS | source commit 5c2cd72 (level with origin/main)，source operations=36，installed candidate |
| Mac 原生管理员授权窗口执行同一 installer | PASS（独立 pin 读回补足） | installed candidate；elevated installer 自带 source commit 输出 unknown (not a git checkout; staleness unchecked)，不能拿这行证明 provenance；其前后普通用户 HEAD/origin/main 均为同一 exact SHA 且 clean，随后逐文件与 exact Git object 比较补证 |
| 两台全部 installer targets 对 pinned 5c2cd726... 比较 | PASS | Mac 22/22、gitea-ci 22/22，mismatch_count=0；同时验证 0644/0755、root owner；legacy helper absent；两台 scopes=[write:repository,read:user] |
| 两台 previous backups | PASS | Mac 与 gitea-ci 三个本次变化文件的 .previous SHA-256 均匹配安装前摘要 |
| installed Gitea --version、admin user --help | PASS（能力元数据） | version=1.26.4；CLI 无 revoke token 子命令；仅查看公开 help/version，未指定 config、未读 DB/凭据或查询 API 对象 |
| Context7 + v1.26.4 上游 router/model 复核 | PASS（文档分析） | /api/v1/token 不在该 tag router；exact token model 有 GetAccessTokenBySHA / DeleteAccessTokenByID(ID,UID)；不是 live 撤销能力验证 |
| 四份本票合同检查 | PASS | check-change-documents: changes=145 pass=2 gap=0；resolve-documents 316 读回四个 exact basename |
| typed issue.labels.set 316 lifecycle=approved | PASS | 用户明确合同/启动确认后执行；读回 after=[approved,complexity/complex,type/security]；不传递 PR、安装或 live Secret 授权 |
| 分类 --verify 316 | PASS | T01 治理应用后 real read-back result=projected，change_type=security，complexity=complex |
| T01 03/06 治理合同应用与 diff review | PASS | 03 加入 scope 变化必须轮换、operator 权限及治理阶段边界；06 增轮换列与失败恢复合同；没有修改 runtime、shell、CI、AGENTS 或 CLAUDE |
| T01 staged scope + git diff --cached --check | PASS | staged 文件集合与明确授权的六份 Markdown 精确相等；无 whitespace error；本地 commit 后的 SHA 与 clean 状态在独立 Issue 回执记录 |
| T03 transaction/typed runtime、Python/bash/smoke、PR CI | NOT RUN | T02 helper 本地实现/Go 验证见下节；其余实现与最终硬门未执行 |
| #316 helper 安装 / operator grant / PAT 轮换 / audit / no-op 演练 | NOT RUN | 独立 live/Secret 授权尚不存在；scope 修复代码安装不证明真实 PAT 已改变 |

## T02 本地实现与隔离验证（2026-10-02 fresh turn）

已重新读取本票 AGENTS、README、03/06、批准的 spec/plan，再进入 T02。新增内容仅在 `codex/tools/gitea-pat-helper/`，没有执行安装或读取现场 config/DB/Secret。

| Check | Result | Evidence |
|---|---|---|
| Go 1.26.3 官方工具链摘要 | PASS | 本票隔离临时目录；darwin-arm64 SHA-256=875cf54a15311eee2c99b9dd67c68c4a49351d489ab622bf2cfd28c8f2078d3c；最初下载得到重定向 HTML，摘要失败后未解包，跟随官方重定向重下载才通过；未全局安装 |
| 固定 Gitea module/model | PASS | code.gitea.io/gitea v1.26.4；module sum=h1:VDA00oYg16VrQf3sES0NuS/oiDLAIVng/7jKHsBMP/w=；token model SHA-256=dcf0e3fd325fe98e91d8a2e216aedbaf08fed20625748bbbdf03f090fc1728cd；go.mod/go.sum 固定，build.py 核验无替换、model bytes 与 go mod verify，并逐文件将实际 GOROOT 绑定至官方归档摘要 |
| helper 核心 suite 先红后绿 | PASS | 待实现桩时 TestExactRevokeAndFreshReadback（当时名为 CacheReadback）、Inspect、SecretErrors 三个测试 FAIL/NOT_IMPLEMENTED；实现后固定工具链 go test -mod=readonly -tags sqlite,sqlite_unlock_notify ./... PASS；临时 SQLite、上游 auth/user/db models，无现场 Secret |
| 失败/隔离负向矩阵 | PASS | 错账号、未知 token、admin、org、inactive、版本、ID/UID/name/project/kind、歧义 salted hash 全部零删除；其它 PAT 与其它账号保留；真实 SQLite trigger 删除失败回滚、driver error 输出固定错误码，synthetic canary 不泄露 |
| 请求与 manifest/build binding | PASS | 拒绝重复/未知字段、多文档、null、超长 stdin、任意 username/SQL；canonical 两份 manifest 四种身份可解析；未知 project/kind/无 routine binding 拒绝；module replacement/toolchain mismatch 拒绝 |
| Go race suite | PASS | 固定工具链 go test -mod=readonly -race -tags sqlite,sqlite_unlock_notify ./...；无 race 报告；不代表现场并发交易已验收 |
| Mac 本地固定 build + provenance | PASS（darwin/arm64） | build.py 重跑 suite 并构建，binary SHA-256=e07bcca33a21f9e2e4a9ef1cef118bcc35735d9f9d70979ce590accd3cbdaeb0；临时目录保存 source hashes、dirty 状态、Go build info；非 Linux release/installed 证据 |
| Mac binary 公开元数据与拒绝行为 | PASS | --version 返回 helper=1、model=1.26.4、toolchain=go1.26.3；普通运行先返回 HOST_UNSUPPORTED/exit 2，stderr 为空，未读取 config/DB/Secret |
| T02 双轴代码审查 | PASS（修复闭环） | Standards 无硬违反、1 项非阻塞进程级 Secret canary 建议留在 T04 Linux 验证；Spec 初查 1 项 P2：工具链摘要未绑定实际输入，已修复；复审无新 T02 缺陷；审查为源码证据，实际执行结果另列 |
| toolchain input 负向验证 | PASS | test_build.py 四项真实执行：正确归档/tree、同版本字符串但篡改 binary、错误归档、extra file/symlink；修复后的官方归档+实际 GOROOT+native build PASS；provenance 记录 archive SHA-256 与 extracted_tree_sha256 |
| Linux binary/CI、typed grant/交易工具、安装/live | NOT RUN | 留在 T03/T04/T05，当前不声称整体 Issue 已完成 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 本地隔离 shell/smoke 接入 PASS；组合完整 smoke FAIL | 已覆盖 rotate/no-op、撤旧失败、scope 不等、写入失败与 Secret canary；真实外部系统不在 fixture PASS 范围 |
| AC-2 | NOT RUN | 未授权且未执行真实 Secret 操作 |
| AC-3 | 文档与分类复核 PASS；范围补充已批准 | 03 已加入 scope 合同变化必须轮换、operator 权限和阶段边界；06 已加入轮换列、Secret/恢复合同；mapped documents/真实分类读回在 T01 复核，整体验收仍需 T04 |
| AC-4 | T02 本地隔离 DB suite 与阶段审查 PASS | fixed v1.26.4 helper 使用真实 models 覆盖精确删除/拒绝/脱敏；Linux release 与现场安装不在该 PASS 范围 |
| AC-5 | T03 本地隔离 PASS | 固定 store 交易、journal/锁/权限/owner、失败补偿和中断恢复；live NOT RUN |
| AC-6 | T03 源码/本地负向 PASS | 普通 typed caller、VM 公开 tuple/hash、缺/错 grant/capability 均拒绝；installed/live NOT RUN |
| AC-7 | local Linux/进程 PASS，组合 smoke FAIL，required CI NOT RUN | 已运行证据见 T04；新集成阻塞见下节，局部成功不证明整体验收/installed/live |

## 遗留风险与未完成项

两台 #313 installed 前置已解除，depends_on 仍保留 313，不能把批次集成排序写为产品依赖。新本地撤销 helper/operator 路线已获用户合同确认；现有 rollback 的假 self-revoke 不作真实证明。T01 已作治理 commit 并停止；T02 已完成；T03 fresh run 已完成源码、隔离测试与审查修复，证据见下节。PR 提交 manual、人合并、未来安装、grant provision、live PAT 轮换均有各自明确边界。只完成 source merge 而 AC-2 未验收时不声称 #316 已真正解决，不归档本聊天。


## T03 合同冲突历史（已由方案 A 解除）

- 新只读源码证据：`CredentialResolver`（broker.py:1010–1013）固定从 `mac_host.credential_root` 读取 PAT；`resolve` 的 routine 路径与 `host.access.audit` 都使用该消费位置。canonical manifest 固定 Mac store 为 `/Users/benque/Library/Application Support/AISoftPlatform/credentials`，VM bootstrap 则写 `/home/benque/.config/aisoft/credentials`。没有读取任何现场 Secret、marker、config 或 credential 文件。
- 已批准 spec:57 禁止 Secret 复制到 Mac，同时要求 transaction 文件在同一目标 store 文件系统。只轮换 VM 文件不能更新现有 Mac broker 消费的 PAT，故不能同时保证 AC-2。不能静默放宽 Secret 边界，或把 resolver 改成跨主机消费。
- 当时向用户提交两项具体提案：A 仅准许受控更新 manifest 固定 Mac canonical store，维持消费路径和同 store 交易；B 继续禁止 Secret 到 Mac，扩展为 VM-only broker custody/代理执行并重新规划全部受影响操作。当时提案尚未批准；后续用户已明确批准 A，见下节。
- T02 源码提交 `6767fffca52490c8a43f517ab3e9d04018bb6d54`；随后工具链绑定修复与状态/证据提交 `0ffe6bda169d70bd89f48fa527635aa079a23bff`。
- 当时 handoff：T02_COMPLETE / NEEDS_HUMAN_DECISION；T03 挂起直到上述合同决策。PR、安装、grant provision、live 轮换均未执行。新决定若修改治理合同，先独立应用并停止，再 fresh run 实施对应 runtime。
- typed issue.labels.set 已将本票从 approved 投影为 awaiting-triage，读回 after=[awaiting-triage,complexity/complex,type/security]；这是新合同冲突的等待状态，保留 T02 既有授权和已完成证据，不撤销或扩张 Secret 边界。

## T02A 方案 A 批准与独立治理应用（2026-10-02）

用户以“按建议继续”明确批准方案 A。仅固定 Mac canonical store 可接收轮换候选；同一 store/文件系统交易，固定 VM CLI/helper 内部受控管道，grant 绑定 store/helper，缺 ownership evidence 拒绝，既有 VM 副本不自动更新/清理。只修改 03/06 与四份 mapped Markdown；T02 helper 保持。当前 handoff 为 T02A_COMPLETE / T03_NEXT_FRESH_RUN；下一 fresh run 重读后可沿用本次启动批准实施 T03，无需再次询问启动确认。

| Check | Result | Evidence |
|---|---|---|
| T02A check-change-documents + git diff --check | PASS | changes=145 pass=2 gap=0；无 whitespace error；六份 Markdown 的 diff 已复核 |
| typed issue.labels.set 316 lifecycle=approved | PASS | before=[awaiting-triage,complexity/complex,type/security]；after=[approved,complexity/complex,type/security] |
| 分类 --verify 316 | PASS | action=verify、applied=false、result=projected、change_type=security、complexity=complex；仅标签与声明一致证据 |

本阶段文档检查、分类投影、staged scope、本地 commit SHA 与 clean 读回在本票 Issue 回执记录，避免文档自引用 commit SHA。没有修改 runtime、shell、CI、AGENTS、CLAUDE 或安装文件。T03、Python/bash/smoke、Linux 制品、PR CI、安装、grant provision、live PAT 轮换/audit/no-op 仍为 NOT RUN。AC-3 的治理文档部分已随 A 同步，T04 最终复核仍待执行；Mac 验收不得扩大为全部 VM 消费端验收。

## T03 fresh run：源码交易、typed grant 与隔离验证（2026-10-02）

起始 head 为 a4eef2aa242aecd46eb0850e091b37bbe81efbfc，沿用方案 A 启动批准，重读六份合同后实施本 frontier。无源码/安装 fallback，无现场 grant/marker/PAT/config 读取；没有安装、provision、签发/撤销真实 PAT、push、PR 或 merge。T03 本地 commit 在会话回执记录，避免文档自引用。

交易实现固定 Mac store 的 per-target lock、legacy ownership 等值、持久 journal、候选验证、exact helper 撤旧、401 证据、provenance 与最后原子发布；同请求经 active 身份/scope 复核后 no-op。撤旧结果不确定或候选丢失时保持隔离，不盲目重签。installer 只增加显式 Linux helper 制品 pin/readback，不生成 grant 或 capability。

两轴初审发现两个 P1：VM git endpoint 无法证明 Mac root operator 来源；非 TTY 普通文件可接收 Secret。新增隔离负例先红（2 failures）后绿。修复采用 Mac root-only grant 的随机 256-bit capability、VM grant 仅存 SHA-256 digest，每次私有请求在任何 subprocess 前 constant-time 验证；OperatorGrant 将 Secret 与交易 binding 分离，不进入 journal/provenance/receipt/argv/env。匿名管道按平台验证（Linux exact proc pipe inode；Darwin FIFO/dev/link），拒绝具名/unlinked FIFO与普通文件，写 Secret 前复核。它是窗口内 bearer capability，真实生成/provision 仍为 T05 独立授权。

| Check | Result | Evidence / boundary |
|---|---|---|
| T03 轮换 Python suite | PASS | 34 tests；transaction mutation counts、失败/恢复、no-op、锁/文件安全、grant strict schema、VM 缺/错/hash proof 零命令与匿名 pipe 负例；使用 synthetic PAT/capability |
| T03 shell black-box | PASS | test-rotate-gitea-service-account.sh；真实 operator process/文件系统，外部 Gitea/transport 为隔离 fixture；rotate/no-op/revoke/scope/write、公开 Secret canary、journal/provenance 无 capability |
| host-access Python 回归 | PASS | 192 tests，包路径 discover -t codex/runtime；临时 localhost 隔离测试 |
| shell 语法与 ShellCheck | PASS | 五份修改 shell 的 bash -n 与可用 ShellCheck；无修改 bootstrap/rollback marker 协议 |
| 完整 smoke | PASS（C locale，本地隔离） | LC_ALL=C bash codex/tests/smoke.sh；1012 tests OK，Codex platform static smoke checks passed，exit 0；新 shell suite 另跑 PASS，尚待 T04 接入 smoke |
| 双轴审查 | PASS（修复闭环） | Spec 与 Standards 复审均无残留阻塞；Standards 独立运行 34 tests PASS；trusted_read/trusted_digest 去重为非阻塞建议，本票未扩大修改 |
| Linux/CI/进程级 helper、installed/live | NOT RUN | T04/T05；Darwin 管道测试与模拟 Linux descriptor 规则不证明真实 VM transport PASS；新 shell suite 尚待 T04 接入 smoke |

smoke 首次沙盒路径因 localhost bind PermissionError 未完成；获授权的同一隔离测试在本地重试。默认 UTF-8 的既有 registry-preflight 测试触发 macOS Bash 3.2 fullwidth punctuation 解析错误，LC_ALL=C 独立该 suite PASS，不修改其它 Issue 源码。随后全量 smoke 发现新 fixture 裸 sibling import，已改为 tests.test_credential_rotation 后重跑。失败尝试仍保留，不能计为 PASS。

执行卡见 codex/tools/rotate-gitea-service-account.md；它说明后续 exact source/helper/grant/store/window/ownership 的 reviewable 边界，不授予安装或任何真实 Secret 操作。T04 frontier 尚待 CI/Linux/集成验证，AC-2 仍 NOT RUN，Issue 未完成。

## T04 source 与 PR 前隔离验证（2026-10-03，延续 2026-10-02 frontier）

起点 69bb0e914f30253888737b32cc8602a58c36b127，fresh 重读批准合同后仅实施 T04。新增步骤保持原 CI / verify (pull_request) job/context，不能把候选 workflow 写成真实 CI PASS。smoke 现已执行 rotate shell black-box、工具链四项负例及优化模式下载硬门；固定 native Linux build 单独在同一 CI job 中运行，未安装全局 Go/helper、未读取现场 Gitea config/DB/PAT/grant。

| Check | Result | Evidence / boundary |
|---|---|---|
| Issue 与分类只读读回 | PASS | #316 open，approved/complexity/complex/type/security；apply-classification --verify 316：projected，applied=false；无标签 mutation |
| 最终 local smoke | PASS（旧基线 C locale） | t04-smoke-final.log：1012 tests OK，exit 0；包括新 rotate shell、4 toolchain tests、优化模式 black-box；默认 UTF-8 组合验证另列，不混同 |
| bash -n / ShellCheck / Python compile | PASS | smoke.sh、两份 Linux helper shell、process Python；Go fixture经固定 gofmt |
| 固定 native Linux build/model/race | PASS（linux/arm64） | 官方 Go1.26.3 arm64 archive SHA-256 9d89a3ea57d141c2b22d70083f2c8459ba3890f2d9e818e7e933b75614936565；actual GOROOT tree 摘要绑定；build.py 重跑 model suite，race PASS，test-only exporter使用真实 models 生成临时 schema |
| 最终 Linux 候选制品 | PASS（测试候选，不能安装） | SHA-256 d63979d13012bea86b36dead301284e8928c45664c6a59346224b5f59c69f7a0；provenance source_commit=69bb0e914f30253888737b32cc8602a58c36b127，source_dirty=true；包含当前 staged Go source hashes，不是 merged-main clean release |
| 实际 helper 进程完整 DB/canary | PASS（local disposable container） | 无网络、只读 source/binary/model fixture；Go upstream schema/hash；真实 git fixture UID 的 inspect、wrong binding 零删除、真实 SQLite trigger error 脱敏、exact revoke、其它 PAT 保留、unknown token 与 unsafe config path 拒绝；Gitea --version 为明确 stub，无真实 server/HTTP/PAT |
| Linux rotation Python | PASS | 无网络容器的 34 tests；真实 Linux anonymous/named/unlinked FIFO descriptor 规则；补独立 fixture owner mock，不改生产身份闸门 |
| optimize 硬门先红后绿 | PASS | wrong checksum/traversal 在 PYTHONOPTIMIZE=1 下解包前拒绝，无 tar/制品；process harness优化模式拒绝 TEST_OPTIMIZATION_UNSUPPORTED；下载校验显式if/raise，runner Python-I |
| 双轴审查 | PASS（修复闭环） | Spec 无阻塞/scope creep；Standards P2 优化模式可跳 assert 已修复，复审无残留阻塞 |
| required CI | NOT RUN | 尚无 PR 提交批准/PR；CI workflow 只跑 basic actual-process canary + Go DB model/race，full-container DB/driver-error process 是独立 local 证据 |
| helper/operator installed、grant、live AC-2 | NOT RUN | 不继承 #313/#308 安装授权；测试容器内 fixture 用户/config/DB不是现场安装，未签发/撤销任何真实 PAT或清理任何消费端 |

临时测试镜像固定 python@sha256:e91fec3d1ac69f04e4eddcd29c327e630ce34658cf31075bfa7e8b0e052bafea，实际 Linux/arm64；测试容器 --rm，无现场卷。首轮 linked worktree metadata 缺只读 mount 导致 provenance 失败，已修正并重跑；首轮 DB fixture 的 PAT 长度/最小 schema 不完整，改为真实 upstream models 导出后 PASS，未放宽 helper。失败日志仍保留，不能计入 PASS。

Fresh typed git.fetch.main 读回 origin/main=70baa3588c0504e5d81facd99c63b74741967967，包含 #319 与 #288；当前 exact Issue branch 与之分叉（T04 commit 前 42 ahead-main / 5 ahead-Issue）。open PR只读读回没有本票 branch；未 push、建 PR 或 force。下一步进行只读组合树/默认locale验证；本票当前 frontier不授权修改其它Issue文件、改写history或处理平台publisher规则。

## T04 fresh-main 默认 locale 组合验证：FAIL / NEEDS_CONTRACT_EXTENSION

实现 head 为 `4643c3826ca6bcede5a5e81930debfcd8df0c9c8`。fresh main `70baa3588c0504e5d81facd99c63b74741967967` 与本票产生无冲突组合 tree `675692cda5a6fb778a460d683d84f755b132dc49`；仅在独立 lab 使用该 tree，未改变实际 Issue HEAD/index/branch，未 rebase 或创建 merge commit。

`LANG=LC_ALL=LC_CTYPE=C.UTF-8` 的 `bash codex/tests/smoke.sh` 退出 2，日志 `/private/tmp/issue-316-build/t04-fresh-main-default-smoke.log`：source `codex/install-host-access-broker.sh`、reason `installer-mapping-stale`、RESULT ERROR。这是有效源码集成失败，与旧基线 C locale PASS 分开；后续 suite 未执行，不能声称默认 locale 完整 smoke PASS。

闸门来自 #308。mapper 未覆盖本票新增 rotate 脚本、生成 source metadata 和可选 helper；仅刷新摘要会掩盖遗漏。两轴只读复审确认当前 #316 spec 没有明确列入共享 checker，且需要定义生成 metadata/可选制品的比较政策。具体 exact 文件、CLI 输入、验证、回滚和治理/fresh-run 边界见 [待确认提案](evidence/t04-installed-drift-extension-proposal.md)。该提案未生效，当前未修改 mapper 或 fixture，T04 blocked。独立 `--source-only` 同样返回 ERROR/exit 2，确认是 source mapping 问题；脱敏 readback 与日志摘要见 [集成阻塞回执](evidence/t04-fresh-main-integration-block.json)。

本票 branch 仍不是 fresh main 后代，`BASE_BRANCH_STALE` 仍是 Controller 发布前置条件；不能绕过它。required CI、PR 提交、helper/operator 安装、grant provision、live PAT 轮换及消费端副本处置仍 NOT RUN。PR 草稿当前为 BLOCKED_SOURCE_CANDIDATE，不能提交或当作 READY_FOR_REVIEW。

## T04A 已批准范围补充与独立治理应用（2026-10-03）

用户以“确认继续”批准具体补充提案。起点 head 为 `fdbc7e79a54a9c8584957a83427192d0d20a91fb`，branch `change/316-service-pat-rotation`；本步骤只应用本票 spec/plan/summary/verification、提案批准记录与脱敏批准回执。新授权为两个 exact 文件的 drift mapping/metadata/独立 provenance 与对应 fixtures；`--source-only` 不 stat/read/resolve 外部证据或目标；helper:null 不推断整体轮换不可用。批准回执见 [T04A](evidence/t04a-contract-extension-approval.json)。

T04A 不改运行时或 checker/fixture，不进行历史改写、push、PR、label、安装、grant 或真实 PAT 操作。当前组合 smoke 仍 FAIL（未修复、未重跑）；required CI、installed、live 保持 NOT RUN。文档与 staged scope 检查及最终 clean/commit 读回作为本 turn 回执，避免本文件自引用自己的 commit SHA。

当前 handoff：T04A_COMPLETE / T04B_NEXT_FRESH_RUN。下一 fresh run 重读已批准补充合同即可沿用本次确认实施 T04B，无需再次询问启动批准。T04A 必须本地提交后停止；T04B 不能在本 turn 进行。

T04A 已运行检查：check-change-documents PASS（changes=145、pass=2、gap=0）；git diff --check PASS；本地文档链接与批准回执结构检查 PASS。仅文档变更未重跑源码 suite，未运行的 T04B/CI/installed/live 不计为 PASS。
