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
status: approved
branch: change/316-service-pat-rotation
created: 2026-10-02
updated: 2026-10-03
---

# 服务账号 PAT 显式轮换合同（已批准）

## 目标与原因

让负责人用一条可审计操作轮换 manifest 已管理的非 site-admin 服务账号 PAT，失败能明确恢复，Secret 不进入聊天、argv、用户可见 stdout/stderr、CI 日志、仓库或审计回执。内部受控 Secret 管道须与回执输出分离，不能返回给 Agent 或工具结果。首次现场目标固定为 `newemaint-routine-merger`；若负责人已另行完成轮换，按 Issue 正文另行明确专用测试对象后再验收。

#313 的合并与两台重装已完成，不新增其它产品依赖。#313 AC-1 的 live 凭据复验仍不能由安装证据推断为通过。用户于 2026-10-02 在本票聊天明确确认这份完整 spec/plan 与新增撤销后台方案。本次合同批准授权按阶段实施源码，不授权 PR 提交、后续安装或 live Secret 轮换。此前两台重装授权只覆盖 #313 安装前置。

## 版本与撤销后台决策

已安装 Gitea 是 `1.26.4`；其 `admin user --help` 仅有创建、列表、改密码、删账号、生成 PAT、密码策略操作。Context7 未找到版本限定的 self-revoke 文档；随后核对固定版本上游源码：[v1.26.4 API router](https://raw.githubusercontent.com/go-gitea/gitea/v1.26.4/routers/api/v1/api.go) 没有 `/token` 自撤销路由，用户 tokens 管理需要 Basic/reverse-proxy authentication。现有 rollback 的假接口不能成为新工具的真实能力证明。

**本合同已批准的明确方案**：增加固定 `Gitea v1.26.4` token-model 的本地 Go helper，由已有 Gitea service user 的受控 operator 路径运行，不升级/重建 Gitea server，不新增服务账号密码、不使用 admin HTTP 凭据 fallback、不写任意 SQL。helper 仅接受 manifest 派生目标与受保护 stdin 中的 PAT，使用 [固定版本 token model](https://raw.githubusercontent.com/go-gitea/gitea/v1.26.4/models/auth/access_token.go) 定位 exact token，校验 UID 与精确服务账号匹配，再按 ID+UID 删除并读回不存在。任何上游 error 都转为固定错误码，禁止直接输出可能携带 token 的 Error()。

这是新增本地数据库撤销能力和 Go 制品的安全决策，已被本合同的用户启动确认明确接受。server 版本不等于已测试版本、目标/marker 不相符、权限不足、DB helper 无法证实 exact token 或出现歧义均在 mutation 前拒绝。使用上游受支持的 model 不代表 live 已验证。

## 用户故事与外部行为

1. 负责人能声明精确目标和授权 Issue；账号、scope、credential 路径由 canonical manifests 派生。
2. scope 合同更新后，负责人能更换旧 PAT 并恢复对应 broker 身份，保持账号、协作者与分支保护不变。
3. 重复同一请求返回经验证的 no-op，不重复签发、撤销或写入。
4. operator 能在失败/中断后恢复同一交易，不盲目创建第二个 PAT。
5. Agent 只能取得脱敏状态和验收回执，不能取得 token 或通用数据库/管理员权限。
6. 其它未指定身份、其它仓库、未授权生产系统不受轮换触及。

## 接口、数据与兼容性影响

- 增加独立 `rotate-gitea-service-account` operator 工具；既有 bootstrap 的 create/no-op 语义保持，不能自动触发 rotate。
- Agent 对 live 的入口是新增 operator-only typed broker operation `gitea.credential.rotate`。参数使用明确字段：授权 Issue、已合并 source SHA、manifest project id、token kind；不接受 username、owner/repo、URL、SQL、token、任意文件路径或 shell。
- operator identity/grant 独立于 project agent、manager PAT、routine merger。grant 必须由负责人另行安装到 operator-only 受保护位置，绑定本次授权 Issue、已合并源码 SHA、exact project/token kind、manifest 固定 Mac canonical store、VM exact helper 与有效期；普通调用方不能通过环境变量自行生成授权或选择 store/helper。缺 grant 返回零 mutation 的稳定拒绝，不提供宽权限 fallback。
- 先支持 manifest 已声明的 manager audit/mutation、project-agent、routine-merge-agent 非 site-admin 身份；未知 project、token kind、账号、缺少 creation ownership evidence 或身份已变成 admin 一律拒绝。
- routine scope 当前精确集合是 `read:user` + `write:repository`；其他身份也从自己的 manifest policy 派生，不使用 `all`。
- legacy account/token/password-policy marker 原内容保持，新增 rotation sidecar 保存非 Secret provenance：授权 Issue、时间、exact source SHA、目标、scope 集合、交易状态。不能破坏 bootstrap/rollback 原有 marker 等值闸门。
- transaction/journal/候选/旧凭据均在 manifest 固定 Mac canonical store 同一受保护文件系统：目录 0700、文件 0600（已声明允许只读 store 的路径须以原政策为准）、正确 owner、拒绝 symlink 和目录逃逸。仅允许该 canonical store 接收轮换候选；禁止写入工作树、普通 `/tmp`、其它 Mac 位置或另一个 provider。
- Go helper 源码/依赖固定 Gitea v1.26.4，构建工具链固定并记录摘要；CI 验证精确 model 版本、隔离 DB 测试与制品 provenance。helper 的文件安装、operator grant provision 和 live 使用各需独立授权。

## 凭据消费位置与 Secret transport（方案 A，已批准）

现有 `CredentialResolver` 与 typed audit 从 `mac_host.credential_root` 消费 PAT。用户于 2026-10-02 以“按建议继续”批准方案 A：替换原先绝对禁止 Secret 到 Mac 的限制，仅允许受控更新 manifest 固定的 `/Users/benque/Library/Application Support/AISoftPlatform/credentials`。各目标文件相对路径仍由 canonical manifests 派生；保持现有消费位置，不扩展为 VM-only custody/代理执行。

交易 journal、旧凭据隔离区、候选与最终 canonical 发布均在上述 Mac store 的同一受保护文件系统，owner 必须符合 manifest 的 `benque` 归属。Gitea CLI 与固定 model helper 仍在固定 VM、以现有 `git` service user 执行；PAT 仅经内部受控 stdin/pipe 传递。CLI 的 Secret 数据管道不得接入用户可见 stdout/stderr、Agent/tool 返回、日志或审计；候选不得落入 VM 普通临时目录。ownership markers 缺失或不符时拒绝，不补建归属证明。调用方不能用 env/path/URL 指定 store、helper 或 transport，也不能自行签发 operator grant。

本次是单-store 发布，既有 `/home/benque/.config/aisoft/credentials` 副本不自动更新或清理。旧 PAT 撤销后这些旧副本不可继续使用；需要消费它们的 runtime 须在各自明确授权下处理并形成单独回执。Mac typed audit PASS 不代表所有消费端通过。源码批准不授权 helper 安装、grant provision 或 live Secret 操作。

## 状态机与恢复

选择“先验证受保护候选，再撤旧，最后发布 canonical 新凭据”。不使用现有 routine pilot rollback 作为轮换步骤，因为它要求禁用整个 pilot 并撤除权限，范围超出 PAT 轮换。

1. Preflight：验证已合并源码、授权 grant 对 Mac store/VM exact helper 的绑定、目标 tuple、账号 non-admin、owned marker、路径权限、helper/version/capability 与交易锁。未通过不签发、不撤销、不写 credential。
2. 隔离：建立持久 journal，把旧 canonical credential 原子移入同目录的受保护交易区。canonical 路径缺失期间 broker 自然 fail closed；同时只允许一个该目标交易。
3. Candidate：固定 VM 的已有 Gitea CLI 按当前精确 scope 生成候选，经内部受控管道保存到 Mac store 的受保护交易文件；验证 exact identity、non-admin、scope 集合。旧 PAT 可因 #313 缺 `read:user` 而不能调用 `/user`，它的归属须由本地 exact-token model 与 creation marker 证实，不能以 403 假定失效。
4. Revoke：helper 只撤销已证明归属的旧 PAT；以 model 的 exact ID+UID 不存在与旧 PAT 新请求拒绝（401）双重验证。不能只凭 DELETE 返回码判成功。
5. Commit：先持久保存兼容的 rotation provenance，再最后原子发布候选为 manifest 固定 Mac canonical credential，并只读验证新身份/scope。提交成功后移除该交易区内旧 Secret 与候选残留，保存非 Secret receipt；不触及既有 VM 副本。
6. Retry：读取并校验 journal 后恢复已有交易。旧 token 已撤销而发布失败时只重试已验证候选的发布；不得复活旧 PAT，不再次生成。已完成 marker 与 active 身份/scope 均匹配时 no-op；显式新轮换必须另有对应授权，不能凭 `--force` 绕过授权。

失败约束：撤旧前可撤销已创建候选并恢复仍有效、符合当前 manifest 的旧凭据；候选补偿失败、旧凭据不符当前 scope、撤销结果不确定时保留 journal 并保持 canonical 隔离。撤旧后无法恢复原 PAT，只能用保留候选完成恢复或由负责人决定下一次修复。所有未完成状态均不能报告 rotated/no-op。

## Acceptance criteria

- [ ] **AC-1（Issue AC-1）** shell black-box 套件在 smoke 中覆盖成功、旧 PAT 撤销失败、scope 读回不等、credential 写入失败，先红后绿。断言 external mutation 数、canonical 可用性、精确目标及重复执行零 mutation，而非只比字符串。
- [ ] **AC-2（Issue AC-2）** 在独立 live/Secret 授权下对 `newemaint-routine-merger` 真实轮换一次；Mac project=newemaint 的 typed audit 返回非 BLOCKED，第二次同请求 no-op，旧 PAT 为 401、新 scope 精确相等。既有 VM 副本及其消费端另行记录，不能由 Mac audit 推断通过。若已被负责人手工轮换，必须先记录并明确 dedicated test target，不能自动创建账号。缺授权为 NOT RUN，Issue 保持未完成。
- [ ] **AC-3（Issue AC-3）** 06 凭据清单增加轮换列，03 写明 scope 合同变更必须轮换；四份 mapped documents 检查通过，classification --verify 316 读回 projected。
- [ ] **AC-4** helper 在独立临时数据库中覆盖 exact token/UID 删除、wrong-user/unknown token/admin/version mismatch 零 mutation，以及上游错误含 Secret 时输出仍脱敏；同一账号其它 PAT 与其它账号完整保留。未经真实 helper 集成验证的 mock 不能作为 backend PASS。
- [ ] **AC-5** journal/lock/marker 兼容和中断恢复验证：撤旧前失败、撤旧后写入失败、完成后重试、同目标并发、不同目标隔离、symlink/权限/owner 拒绝；证明交易位于固定 Mac store 同一文件系统、VM 副本未自动更新或清理。不得恢复已经撤销的旧 PAT。
- [ ] **AC-6** typed operator surface 对缺授权、过期、wrong Issue/source/target/kind/identity/store/helper、env/path/URL override、未知 schema、provider/project-agent 普通调用均零 Secret mutation；不扩大 existing operations、ordinary Git、merge allowlist、sudoers 或 provider 权限。
- [ ] **AC-7** Go model/制品 provenance、对应 Python suites、bash -n、可用 ShellCheck、完整 smoke、required CI 真实通过；source/local/CI/installed/live 证据分别记录。Secret canary 在用户可见 stdout/stderr/argv/audit/文件清单中都不得出现；内部管道不得 echo 或返回 Secret，固定 Mac 保护区以外（含 VM 普通临时目录）不得产生候选 Secret 文件。

## 治理文件授权与阶段边界

用户已确认本合同，允许 T01 **仅**修改 03/06 中上述轮换与权限/恢复合同、mapped docs 并作本地原子 commit，然后停止该 turn。当前运行的 AGENTS.md、CLAUDE.md 不修改。

T01 已完成，后续 fresh turn 已完成 T02。用户本次批准方案 A，授权 T02A **仅**修订 03/06 与四份 mapped Markdown，文档检查、本地原子 commit 后停止本 turn；不修改 helper、runtime、shell、CI、AGENTS 或 CLAUDE。下一 fresh run 重新读取修订后的治理合同即可沿用本次启动批准实施 T03，无需再次询问启动确认。

只有后续 fresh turn 重新读取这些合同后才能执行 T02 起的 runtime。明确授权源码 touch points：rotate/operator helper 与固定依赖/构建定义；host-access broker contract/dispatch/runner/CLI 与 canonical access manifest 的 operator-only typed surface；broker installer 对 helper 的版本化安装；对应 Go/Python/bash 测试；smoke 与 `.gitea/workflows/ci.yml` 的固定 helper 构建/隔离验证。该 source 范围不授予 live grant provision、sudoers 更改或实际凭据轮换。

## 测试方式

最高测试接缝是 operator command 的外部黑盒行为，沿用 bootstrap 的 shell fake Gitea/transport，并真正模拟缺 read:user 时 `/user` 的 403。独立 helper 用 upstream model 驱动临时数据库测试，避免 mock 再次批准错误接口。真实旧 token 归属、撤销与缓存行为须在独立授权的现场补证，不由隔离 DB PASS 推断。

## 非目标与回滚

不改变账号、密码、协作者、分支保护、routine opt-in、生产部署或其它 Issue。不修其它历史 rollback，不把新路径偷偷替换到现有 pilot 回滚中。不升级 Gitea server。源码可 revert，但 live PAT 撤销不可逆；回滚 helper/source 不能恢复已撤销 PAT，凭据事故按上述 journal/candidate 恢复并单独授权。

## 未决问题

方案 A 已获用户批准，凭据消费位置冲突已解除。T03 runtime 与 T04 局部验证已实施；本轮 T04A 仅应用下方精确补充治理合同并停止，下一 fresh run 才进入 T04B。live 对象是否已手工轮换与 live operator grant 由现场授权阶段真实读回，当前不能推断；这些是未来现场闸门，不阻塞已批准源码实施。没有新产品依赖。

## T04A/T04B installed-drift 精确补充合同（2026-10-03，已批准）

用户在本票聊天以“确认继续”批准 [补充提案](evidence/t04-installed-drift-extension-proposal.md)，绑定 Issue #316、branch `change/316-service-pat-rotation` 和 proposal 所记录的新增安装面。此确认授权 source 合同补充及后续范围内实现/测试；PR 提交、merge、安装、operator grant provision 与 live Secret 操作保持原独立边界。

T04A 是独立、只修改治理合同的受控步骤：仅更新本票四份 mapped Markdown、该提案批准记录及本票脱敏证据，文档检查、本地原子 commit 后停止本 turn。当前运行不修改 mapper、fixture、runtime、shell、CI、AGENTS 或 CLAUDE。T04B 必须在下一 fresh run 重新读取本合同后执行，沿用本次批准，不重复启动确认。

T04B 明确授权以下两个 exact 源码文件的变更、对应验证与回滚：

- `codex/tools/check-installed-drift.py`：只维护 #316 broker 新安装目标的映射、generated metadata verifier、独立公开制品证据比较及可选 CLI 参数。
- `codex/tests/fixtures/installed-drift/test-installed-drift.py`：仅对应同一 fixture_source 的 installer acceptance fixtures、负向恢复及零写入/零越界读取验证。

本票 mapped documents/evidence 可同步记录真实结果。既有 smoke 已接入该 suite；不修改 installer、CI workflow、manifest、skills、Controller、其它 Issue 文档、sudoers 或真实安装面，不增加 skip/弱化硬门。回滚通过后续受控 PR revert 上述两个源码文件及对应本票文档；checker 零写入，不需要安装回滚。治理合同补充不取消此前组合 smoke FAIL，源码修复与重跑完成前不能写成 PASS。

### 安装面与比较政策

| 安装面 | 规则 |
|---|---|
| `/usr/local/libexec/aisoft/rotate-gitea-service-account` | 按对应 `.sh` 源码字节核对；缺失、旧字节、链接或异常类型报 GAP |
| `/usr/local/share/aisoft/credential-rotation-source.json` | 独立标准库 verifier；严格 schema/重复键拒绝；固定四个 files 键从源码映射推导，不跟随 JSON 提供的路径；依据 checker 的本地源码及缓存 origin/main 核对声明源码 SHA、merged-main 状态、源码与安装文件摘要；缓存 ancestry 不证明远端 freshness；不执行 installer，不 import 轮换 runtime |
| metadata 的 `helper: null` | 普通 broker 可以通过，明确 `LOCAL_HELPER_NOT_DECLARED`、`rotation=NOT_ASSESSED`；installer 未选择 helper 时可以保留旧 binary，该文件不得被报告为已验证 helper，checker 不读取其内容。Mac 本机可无 Linux helper 而使用 VM helper，不能据此判断整个轮换不可用 |
| metadata 的非 null helper | 必须有独立非 Secret build provenance，严格绑定固定 Gitea 1.26.4/Go1.26.3、Linux 架构、clean source commit、Go 源码/go.mod/go.sum/build-lock 输入及 binary 摘要；只比较固定 libexec binary，不执行 `--version`；证据缺失或不等报 GAP，不能信 installed receipt 自报 hash 就报告制品有效 |

授权新增可选 CLI 参数 `--pat-helper-provenance ABSOLUTE_PUBLIC_PROVENANCE`，仅接受明确指定的公开构建证据文件 `gitea-pat-helper.provenance.json`。不从 installed JSON/env 派生证据路径；参数的词法绝对路径在回执标明；source-only 不 stat、不 resolve 或解引用外部证据路径。这是 checker CLI/验收合同的新增，只用于只读比较，不授予安装或运行 helper。缺参数而已选择 helper 时返回 GAP；显式提供 helper 证据但安装 metadata 尚未选择 helper 也返回 GAP。仅输出校验结果与摘要，不输出 build_info/未知值，不跟随 provenance 的 Dir/路径。此比较仅证明与指定外部 build receipt 一致，不能证明签名可信 release；制品证据本身的签发/审批不由 drift checker证明。

保留恰好八个 installer、退出码 0/1/2、source/installed 分层与原有 source identity 硬门。`--source-only` 只检查映射定义与仓库 SOURCE 输入，即使给出新参数也不 stat/read/resolve 外部制品证据，绝不 stat/read target metadata 或 helper；不能输出 installed/helper PASS。source identity 必须纳入新增生成/制品验证输入，避免遗漏 helper Go/mod/sum/lock/build 定义。

### 验证与停止边界

- 真实 installer 在同一独立 fixture_source baseline 安装，避免 generated source SHA 来自另一个 HEAD。
- rotate 缺失/同长度旧字节；metadata 缺失/坏 JSON/重复键/额外字段/错 SHA/错固定键和摘要；helper 缺失/错摘要/错 provenance、model/toolchain/platform/dirty source；各项恢复后回到预期结果；provenance 路径本身及父目录的 symlink/FIFO/异常类型不得读取。
- `helper:null` 加遗留 binary 必须真实反映未选择政策；metadata 自选 path/Secret 字段拒绝，输出无 synthetic canary。
- metadata/helper symlink、FIFO、parent 替换均不读取 Secret。source-only 使用 read/stat spy 证明零 target 访问；installed 模式禁止 installer/helper/sudo/network/修复调用，文件树前后相等且无 temp/cache/pyc。
- 映射和 acceptance fixtures 同步通过后才更新 installer 指纹；重跑 source-only、drift fixture、默认 locale fresh-main 组合完整 smoke 及双轴复审。
- 不 rebase/merge/change branch。Controller 的 fresh-main 基线整合仍须走它的受控流程；本合同不授权绕过 `BASE_BRANCH_STALE`。required CI 在获得唯一 manual PR 提交确认后真实运行。
- helper 安装、operator grant provision、PAT 轮换、消费端副本清理和 live AC-2 仍为 NOT RUN，不继承 #313/#308 的安装批准。
