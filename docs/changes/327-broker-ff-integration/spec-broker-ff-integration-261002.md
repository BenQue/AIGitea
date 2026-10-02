---
issue: 327
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/327
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - cross-module
  - security
  - rollback
depends_on: []
branch: change/327-broker-ff-integration
created: 2026-10-02
updated: 2026-10-02
status: approved
---

# #327 最小治理与发布合同

## 目标与原因

保持 original remote tip 为每次新 head 祖先，允许严格来源限定的 fresh manifest main 整合，并经 ordinary FF push 发布；禁止 force、lease-force、任意 merge 与更宽身份 fallback。原合同和独立 T01 已由本聊天确认并提交后 STOP。补充草案 ac172e515a47357d24ff268473af6bbee5c13fe1 经本聊天直接确认；本轮只执行 T04 映射治理和四角色、验证/local commit 后 STOP，不实施 runtime、发表 PR 或安装。

## 状态、来源与信任边界

| 符号 | 来源及含义 |
|---|---|
| R0 | 第一次接管时经 canonical broker 读回的 original remote tip；无远端则 null |
| R | 本次发布前同一 exact ref 的真实 tip；每次刷新，不把 last_push_head 当远端真值 |
| M | 本次 fresh fetch 的 manifest main，40 位 lowercase SHA |
| C | owner 已核验的本 Issue 线性本地提交末端，R 必须为其祖先 |
| I | Controller 构造的 main 整合 commit，parents 精确为 [C, M] |
| H | 本次验证并锁定的最终候选；允许 I 后继续追加本 Issue 线性 commit |

提交 message、author、同名 branch 和可编辑本地 receipt 都不足以证明来源。Controller 需记录每次 owner/issue/branch/base/commit/tree/scope 的验证证据；broker 独立读取 Git DAG、main 来源、批准合同与完整 delta，不把模型自述或 receipt 的 PASS 当授权。Git 对象本身没有所属分支字段，不能从 commit subject 推断 branch provenance。

## 可信证据补充合同（已具体确认；T04 治理应用，T02 待 fresh run）

负责人先“按建议继续”准备 A 路线，在草案 ac172e515a47357d24ff268473af6bbee5c13fe1 和具体审阅卡形成后，本聊天直接“确认”。批准绑定 #327 / `change/327-broker-ff-integration` / manual / 该 draft commit 与原 spec+plan SHA256（外部 `t04-application-approval.json`）；本轮仅独立 T04 治理应用、验证/local commit 后 STOP，后续 fresh run 才 T02。原 T01 commit `061b0f3ec59869fe379d70b7d2f0455df4b8708a` 与原 FF/竞态/人工自举方向保持；新 runtime 尚未实现。具体 source 合同批准不表示 installed 权限/注册/启动已批准或执行。

### 信任角色与特权边界

- 采用**本地 privilege-separated verification authority**，通过固定 Unix-domain socket 提供受限服务。authority 进程必须实际 EUID=0、使用已审计且固定的 installed runtime；root-owned Python 文件本身不证明调用进程可信。root/OS 管理员属于可信运维边界，root 已被攻陷不在本合同可保证范围。
- provider、项目代码、项目测试、可编辑 worktree、local StateStore、owner marker、环境变量、commit author/message、模型输出和客户端 JSON 均不作可信根。provider 和任何项目 verifier 子进程均以登记的非 root UID/GID 运行；特权进程永不执行项目代码、repo hook、自由 shell 或可编辑验证配置。
- 不新增 Gitea 身份/PAT、签名密钥、Keychain 访问或更宽 credential fallback。沿用 canonical broker 的 manifest-fixed project-agent 远端身份；OS root 不切换为 Gitea admin/manager/routine 身份，远端 ACL 与 credential binding 不变；可信性来自受保护的运行/登记过程与独立重算，不来自自称 PASS 或普通 hash-chain。
- 不授权为此合同创建新的 OS 账户。各主机未来 exact 绑定现有非 root `provider_uid/provider_gid`，实际数值由独立 operator 卡读回；缺可安全绑定的身份/执行隔离条件则 capability GAP，不改为 root 跑 provider。
- peer UID/GID 从 OS 的连接凭据取得，不能由 request/ENV/session string 提供。Mac 采用 getpeereid，Linux 采用 SO_PEERCRED；客户端也须校验 server EUID=0。Unix socket 身份只证明 OS peer，不证明该 peer 是 Controller 程序或人；因此即使同 UID 的 provider 调用接口，也只能请求固定流程，不能登记批准、伪造验证结果或获得 merge 权。
- 受控 Controller 的 trusted-critical 部分（冻结上下文、启动/观察限定 provider、限定 main 整合、固定验证和记录）放入 authority 已审计代码；普通客户端只编排请求。authority 自己观察被启动进程结束、复核候选与执行 verifier；不相信客户端传入 PID、退出码或 PASS。这是原本在同 UID 下运行的 Controller 的**source 运行隔离变更**，不是已有 installed 功能。
- 固定 interpreter、Git、library、daemon/entrypoint 和批准 policy 的 owner/mode/hash 均是 capability gate；清除 PYTHONPATH/PYTHONHOME/sitecustomize、调用方 PATH、Git 环境覆盖和继承敏感 FD。缺可信工具链时 fail closed，不为满足验收自行安装或切换全局工具。

### 默认关闭与固定存储

| 层 | 合同中的固定目标（未安装） | 权限 / 行为 |
|---|---|---|
| installed policy | `/usr/local/share/aisoft/change-verification.json` | root-owned 0644，strict schema；`enabled=false`，两主机 UID/GID 绑定为空，provider 默认 none；caller 无 policy/root/socket 参数 |
| Mac protected state | `/private/var/db/aisoft-verification` | root-owned 0700；approvals、records、private object snapshot 位于其内；不经调用方路径解析 |
| Linux protected state | `/var/lib/aisoft-verification` | root-owned 0700，同一 schema/语义 |
| Mac / Linux socket | `/private/var/run/aisoft-verification.sock` / `/run/aisoft-verification.sock` | root-owned，绑定后才置 0660 与 exact 已批准的 group；peer UID 仍逐请求复核；不允许 caller 自建 socket、symlink 或环境 override |
| frozen provider context | Mac `/private/var/db/aisoft-verification-context` / Linux `/var/lib/aisoft-verification-context` | root-owned 父目录 0711；每个 generation 目录 root:登记 provider_gid 0750、文件 0640；只导出本 Issue 非秘密合同/任务上下文，不导出私有 ledger、remote credential 或其他 Issue 数据 |

受保护根及所有下级对象通过 lstat/owner/mode/类型和 open 的 no-follow/实际 FD 再验证；并发替换、symlink、group/other writable、异常属主、oversized/corrupt 数据拒绝。临时文件在同一受保护目录以 0600 建立，fsync 文件、原子 rename、fsync 目录；锁内序号与 previous record digest 校验。hash-chain 仅检出非授权损坏，**不能替代 root custody**。状态根丢失或 rollback 缺失不能自动重新 pin R0；保持 ADOPTION_REQUIRED。

installer 只安装默认关闭的代码、配置及 inert service 描述，不创建 state、绑定 UID、导入 grant、启动服务、启用 provider 或替换凭据。服务描述的具体 installed 位置是 Mac `/Library/LaunchDaemons/local.aisoft.verification-authority.plist`、Linux `/etc/systemd/system/aisoft-verification-authority.service`，安装仍需各主机 exact 批准，不等于启动批准。

同 UID 的 provider 可能拥有该 UID 的普通文件权限，**仅 setuid/drop privileges 不足以隔离同 UID 的 credential/helper/环境**。能力闸门还必须在 OS 隔离边界内拒绝 provider/verifier 读取 canonical broker credential roots、root ledger、其他项目、宿主 helper 与控制端点；只允许登记 worktree、只读任务上下文、该 provider 自己经独立 onboarding 的必要资源和明确网络用途。不复制或读取 `.env`/auth/PAT 内容来创建隔离。各平台缺这个隔离实现时 capability GAP，不能声称降低 UID 已完成隔离，也不能用环境变量开关绕过。此能力需 AC-9 的真实尝试读写/exec/socket 负向验收，root 管理员本身不在不可信 provider 边界内。

候选 source policy 的固定版本为 `change-verification/v1`；grant 为 `change-grant/v1`，record 为 `change-record/v1`。默认形状如下，仅是获确认的 source 形状（待 T02 实现），**没有写入 installed config**：

```json
{"contract_version":"change-verification/v1","enabled":false,"host_bindings":{"mac":{"provider_uid":null,"provider_gid":null},"gitea-ci":{"provider_uid":null,"provider_gid":null}},"provider":"none"}
```

state/socket/context 路径是平台代码中上述固定常量，不由这份 config 或 public request 覆盖；新配置未知/缺失字段均拒绝，只有 exact operator 卡可以把绑定/enable 变为具体值。

### 权威批准基线：非 Agent 登记

1. contract/start 的人类批准仍为业务授权；把它转换成 authority 可读取的 grant，是源码合并之后另行 exact 授权的本地主机 operator 动作。登记依据是已审阅的四角色内容、批准消息/执行卡和 immutable source pin，不能从 live `approved` 标签或本地 `status: approved` 推导 grant。
2. protected grant 的 strict 字段：`version`、`project`、`repository_id`、`issue`、`branch`、`session`、`policy`、`grant_revision`、`authority_pin`、`worktree_binding`、`source_sha`、四份 `document_sha256`、规范化 `policy_sha256`、`scope_entries`、`ticket_graph`、`verifier_entries`、`initial_base`、`R0`、`adopted_commits`、`contract_start_receipt_digest`、`pr_submission_authorization`（初始 null）、`operator_receipt_digest`。枚举、字节/条目数量、SHA、整数、exact tuple、重复 key 与未知字段严格校验；authority_pin 绑定实际已批准 installed source/runtime/program/policy hash；worktree_binding 绑定 canonical 仓库的 exact worktree/path/身份与 device/inode，不由 public cwd 参数选取。policy 为既有 manual|routine-auto 枚举；#327/aisoft-platform 强制 manual，其他项目仍严格按既有 manifest/判级/人类第二确认规则，不扩大 routine 适用范围或变更其身份/字段。
3. `scope_entries` 逐条 exact path、允许 stage、操作/mode 和内容目的，禁止目录泛配授权。内容目的必须落到批准且可执行的检查规则/Verifier，不把“文件名在列表”当目的验证。规则未支持、无法判定或冲突时 NEEDS_HUMAN_DECISION，不放宽或删除检查。
4. verifier_entries 固定可执行程序/代码 hash、argv 模板、required 属性、执行 UID/GID、超时和输出上限；模型不能改程序、参数或把 optional 换成 required 的相反值。项目测试代码只在非特权子进程执行；authority 采集真实进程状态和输出 hash，不接受 caller 返回的结果作为执行证据。
5. root operator 工具的 `approve/revoke/restore` 是固定本地管理入口，不提供 public broker approve operation；要求实际 EUID=0 和 exact operator 卡。Agent 不执行这些入口，不以 sudo、环境标记、manager 或 routine identity 代为批准。新 revision 必须另有已确认合同，旧 revision 和 R0 保留；不得由 provider 自动补齐。
6. spec/plan 和机器 policy 的批准基线冻结。计划的完成状态、summary 的唯一 PR/status 回填与 verification 证据可按冻结的受限字段规则变动，不能改 tuple、判级、graph、scope、required gates 或授权。每次变动仍整体验证；回填不自动生成新的业务批准。
7. 原 owner marker 保持兼容和扫描用途；不得把标记改成 root grant 或让 claim/takeover 重置 authority 的 R0/历史。已有发表历史、T01/T04 pre-authority 本地提交和人工 UI commit 需 operator 显式 adopted_commits + exact 事件与全对象重验；缺 adopted evidence 就 ADOPTION_REQUIRED，不依据 message、同名 branch 或一次 ls-remote 默默接受。首次 absent 须由 canonical broker 精确读回，不能用 fetch error 推断。

8. 最终 PR 的第二个人工确认独立保留。root operator 的 private `approve-pr` 只登记**已经发生的** exact Issue/branch/policy 确认（#327 固定 manual）及当时候选 hash/receipt；它不能替人作决定，public client/本地 confirm-pr JSON/标签不能填写这个 protected 字段。登记是同一确认的受控落实，不增加逐 commit 确认；字段绑定 branch/policy，范围内新 H 仍重验，合法 CI repair 不重复询问。protected 字段缺失则 broker 不发表/不建 PR。#327 first PR 仍由负责人本人 UI，届时 source 尚未安装 authority，不能为了登记而先装 unmerged 版本。

### 最小 typed 接口与不可伪造的验证过程

新增 public catalog **仅两项**，仍由 canonical broker 与 manifest-fixed project 解析；均只改变本地受保护验证状态，禁止创建/更新远端 ref 或 PR：

| operation | exact 参数 | 受控效果 |
|---|---|---|
| `git.change.begin` | `branch`, `ticket` | 校验 active grant/owner/当前 plan frontier；fresh 读取 canonical Issue/main/ref，锁定 base、R0/R/M 和 generation；按 protected 阶段以登记非特权身份启动固定非模型 maintenance/Verifier worker，或已独立验收启用的 provider adapter，并由服务观察该进程；none 不启动模型，仅一个 active generation |
| `git.change.verify` | `branch`, `ticket`, `sha` | 查本服务持有的 generation，不接受 caller generation/PID/receipt/PASS；进程未结束则返回 pending；独立验每个提交、scope/内容目的、DAG/tree 和固定 required verifier；通过才追加 sealed checkpoint |

`ticket` 仅 Txx 标识、`sha` 40 位 lowercase；不新增 caller URL/remote/repository/path/root/socket/identity/UID/command/hook/refspec/force/merge/config 参数。`git.push.change` 保持仅 `branch`，只由受控 Controller 阶段调用，核对 protected 最终 PR 提交授权、读取 latest sealed checkpoint 并**再独立重算**，然后按原 FF/strict R guard/真实 readback 合同发表。daemon 不暴露 arbitrary command、grant-write 或 merge operation。

流程与每条 sealed record：

- begin 前 base 必须等于 authority 的已核验/adopted checkpoint；远端 R 必须匹配 protected publication/adoption ledger，R0 不变。被人工更改的 ref 必须走显式 adoption，不能更新 R0 掩盖异常。generation 的 nonce/序号由服务产生并保管，不把 nonce 当 peer 身份秘密。
- 模型 provider 子进程只能追加线性 commit；固定 Controller maintenance 可以基于已 adopted C 做 main 整合/重验，不需要启用 SDK/provider。worker kind 由 protected graph/阶段确定，不能由 caller 指定 arbitrary adapter 或 acceptance 命令；root authority 收集 exact base→C 的每个 commit/parent/tree/blob/mode/delta 并执行检查。sealed record 至少含 project/Issue/branch/session/ticket/grant_revision/policy hash、generation、base/C/H、parent/tree、每文件 blob 与 SHA256/mode、完整 delta digest、固定 verifier 执行结果/程序 hash、R0/R/M、sequence/previous digest。保留对象快照以供 broker 重算，不仅保留结果字符串。
- 来源定义为“在该批准上下文下由受控执行、验证或明确 adoption 纳入的 exact Git 对象”。**不声称 Git object 能证明代码最初来自哪个物理 branch 或是谁键入了它。** 复用代码不构成可伪造的创作证书；已有/未知 commit、其他 Issue grant、跨侧链或未经 adoption 的人工对象均拒绝。不能因为 provider 用本 Issue subject 重标就成为已验证来源。
- Controller main 整合只在 C checkpoint 完成后构造 I=[C,M]；provider boundary 的 merge deny 不取消。构造使用 authority 私有、hash-verified 对象快照，不在 root 身份下执行可编辑 repo 的 Git 配置/hook/driver。I 的完整 tree 由 broker 再计算；I 后新的线性 CI repair 需要新的受控 generation/record。
- 同 UID 的 provider 可以请求固定流程，但不能直接登记记录、替换 active grant、指定任意命令或输入自己的 PASS。同 UID 下伪装 executable/path/PID 不赋予 trusted-critical 代码权限。没有服务实际观察的执行与验证，verify 必须拒绝；record 缺失/篡改/跨项目/回放/跳序/heads 移动均 mutation 前拒绝。
- 对象读取/快照是 bounded/hash-verified 的内部机制；root 不调用 caller 的 Git/lib/interpreter，不执行 candidate test/plugin 代码。所有读取都须保护避免 symlink/config 与解析资源放大；不支持状态按原合同 fail closed。
- broker 发表成功与 remote readback 后，protected publication ledger 先真实追加；普通 owner last_push marker 随后更新。journal/marker 失败都报告实际已落地 H 和失败层，不把落地改称零写。服务重启恢复记录 prefix、active generation 状态和锁；中断执行不能通过 caller 重报 PASS 变成完成。

### 运维、安装与验收闭合

I01 仍为两机独立 exact 版本文件安装/字节/mode/owner/rollback；I02 新增“verification authority 注册/启动/受控验收”卡。I02 只有在源码人工合并、I01 完整读回且本份新权限合同获确认后，分别获得 **每台机器 exact** UID/GID、program/hash、state/context/socket/service 路径、grant digest、启动/关闭、真实正反向测试与恢复清单批准，才可由指定 operator 执行。不继承 #316、T01、路线 A 选择或一般 installer 许可；不启用任一 provider/profile/timer，不创建或复制 auth/PAT/账户。若将来需要新增账号/Secret或配置其他项目，那是新范围，不从本草案推导许可。

I02 rollback：停止新 authority 写入；保全批准基线、完整 record/object snapshots 和可能已发表的 H；恢复 operator 卡列出的旧代码/配置/service/state/context/socket 前态及 mode/owner。源服务原先不存在的对象只按保存的 exact 清单移除；不删除真实 remote、不重建 original tip、不回到 leased publish。不能仅依赖 `.previous`，不通过清空 ledger 重新开始。

新增 AC-9 分 source/local 与 installed/live：协议/strict schema/default-disabled/未知 capability、真实 OS peer（同 UID caller、伪 server、伪 PID、env/module污染）、provider 不可写、未知/adopted commit、篡改/replay/restart、固定 required verifier、privilege drop、root 不执行 candidate、完整范围内容与 approved baseline 不可改变均需验证。权限无法在非特权 fixture 中真实证明时写 NOT RUN/GAP；mock UID、临时用户-owned ledger 或 bare remote 不能当 root custody/installed PASS。没有 I02 真实正向与负向读回，不把可信根缺口写成已闭合。

### 技术依据与设计验证边界

[Linux unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html) 描述 SO_PEERCRED 的内核连接凭据；[Apple getpeereid(3)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man3/getpeereid.3.html) 描述 Unix-domain peer 的有效 UID/GID。这里只据此选择 peer 身份机制；它们不证明 Controller 程序身份、grant、服务权限或本设计安全。authority/record/流程为本 Issue 原创设计，runtime/真实权限/服务/安装全部 NOT RUN。fsync/rename 策略见 [fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html) 与 [rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html)，实际崩溃/恢复语义仍须本平台试验。

R0 一经 pin 就不改写。正常演进保持 R0→R→H 的祖先链。若远端被人工修改、重写、删除或换 slug，停止；先解释、保全与重新核验，不能把异常 tip 静默采为新的 R0。已有人工 main 整合的 remote commit 只有通过同样 parent/tree/range 验证及 exact 人工事件读回后才能采用。

## 受控整合与兼容

1. owner 仅在自己的 exact worktree 追加本地原子 commit。provider 仍不得创建 merge commit、push、PR、merge main 或持有凭据。
2. 若 M 已为 C 祖先，无需整合；若 C 为 M 祖先，可在不丢弃 Issue 历史且合同 delta 仍满足时本地 FF；已被 main 完全吸收的 Issue 不通过空 PR 掩盖终态。
3. 若 C/M 分叉，只有外层 Controller 的受控本地步骤可构造 I=[C,M]。M 必须来自本次 broker fetch，C 属于已核验本 Issue 第一父链，R 为 C 祖先。只支持确定性、无冲突合并；独立重算 merge tree，并要求 I tree 完全相同。
4. 有冲突、criss-cross/多 merge base、不支持的 Git 行为、非默认 merge driver、replace/graft/shallow 或缺失对象均 fail closed。拒绝 `ours`、隐藏额外 blob、未经核验的冲突解决；若需要改变支持范围，升级合同，不静默处理。
5. 首次、重复整合与之后 CI repair 都验证完整 relevant DAG；历史合法整合第二 parent 必须仍在当前 manifest main 祖先链中，且 parent/tree/provenance 全部复核。不得“遇到一个合法 merge 就放行所有 merge”。
6. 拒绝其他 change branch 的侧向 merge、外仓来源、other-Issue 未批准 commit、parent 反序、octopus、第二 parent 仅与 main 有共同祖先但不是 main 历史、merge 中额外内容或范围越界。
7. M..H 的最终差异与整合前 Issue delta 均按批准 spec 的 exact 文件清单和内容目的校验；不能只校验文件名或 commit subject。main 自身引入的其他 Issue 变化作为基线继承，不要求改写其 message。

## Ordinary FF 发布与并发

保留 `git.push.change` 的 typed argument 精确集合 `branch`，project/repository/remote/credential 仍来自 canonical manifests，不接受调用方 URL、refspec、checkout、merge、force 或 hook 参数。无新公开 merge typed operation；本地构造与 broker 的远端独立验证分开。

- 发布前验证 clean HEAD、exact branch/ref、single-writer、40 位 SHA、权限、唯一 active branch/docs/PR、R0/R/H 来源、R→H、fresh M→H、范围及本次核验 H。拒绝时零远端写。
- 使用普通单 ref push；禁止 `--force`、`--force-with-lease`、`+refspec`、`--mirror`、`--all`、delete、main 更新、push-option/fallback；传输源绑定 exact H，避免分支在核验后移动。
- 仅“先 ls-remote 再裸 push”不足以实现 strict R pin：并发的 R1 若恰好是 H 祖先，Git 仍可能允许 FF。拟采用 broker 控制的固定 pre-push guard，读取本次传输公告的 remote object id，要求 exact R（新 ref 为全零），local object id=H、唯一 exact target；不符合即拒绝。
- guard 必须由受控 runtime 生成/执行，固定 hook path、固定程序与参数、隔离环境和权限；不得执行仓库自带或调用方注入 hook，不允许 `--no-verify`、可替换 guard、symlink 或缺失 guard。新增受管代码必须纳入 installer 和漂移核对。
- 传输公告后 ref 再变由服务端 old-id ref update 检查拒绝；需实际 bare-remote race fixture 证明。首创竞争、远端删除重建、R1 位于 R→H 之间、公告后变化均覆盖。拒绝表示本次零覆盖；外部 writer 自身产生的变化如实保留。
- no-op H=R 时不依赖 hook 被调用：重新读回 exact ref 与 main 并全门验证，返回 truthful no-op；若有漂移则拒绝。 对预检H≠R却传输报告up-to-date（并发writer已把ref推进至H），不能伪称本次发表PASS；必须标为REMOTE_BRANCH_MOVED/本次零写。检查固定guard执行回执与实际更新行，预期有更新却guard未执行或无exact ref行均fail closed。首创并发者恰好创建H也同样拒绝，不误报本次创建。
- Git 单 ref push 不能把“不更新 main 的 freshness read”和 change 更新变成双 ref 原子事务。M 绑定最后一次明确读取的快照，push 前再次检查；若发现 main 前进则停止。push 后 main 发生推进，记录已发表 H、latest main、`BASE_ADVANCED_AFTER_PUSH`，停止 PR ready/merge，不 force 退回 H；重新受控整合。不得宣称整个并发窗口 main 从未改变。
- 成功后再读真实 remote SHA，必须等于 H 才报 PASS、记录 last_push_head；`previous_head=R`、`pushed_head=H` 保留原字段，新增 M/R0/verification receipt 可以向后兼容追加。网络失败或读回不明时报告“写入可能已落地”，不盲重试、不误称零写。

参考：[Git FF 定义与普通 push](https://git-scm.com/docs/git-push)、[pre-push 的 remote object id 与非零退出拒绝](https://git-scm.com/docs/githooks#_pre_push)。上述 guard/CAS 组合为本合同设计推论，实际实现与竞态验证 NOT RUN。

## 治理映射与独立停止点

T01 只在独立受控治理应用步骤，按已确认本 spec 精确修改以下文本，不混入 Python/runtime/install/CI 实现；commit 后立即停止。原合同准备阶段没有修改 AGENTS.md；T01 后经直接确认独立应用并已 STOP。新具体合同确认后的 T04 也只使用下表14项和四角色、应用后 STOP；原草案准备没有应用该表；本次直接确认后的 T04 仅应用该表及四角色，不混入 runtime。后续 fresh run 必须重新读取本 worktree 的治理、Issue、有效评论、spec/plan 和 installed 能力，不继承旧上下文替代读取。

| exact 文件 | 允许的最小治理变动 |
|---|---|
| `AGENTS.md` | 保留 Agent 无 merge 与 Controller FF；增补只有受控 Controller 可构造 [Issue first-parent, fresh main] 确定性整合；所有已发表历史不可重写；声明 source/installed 与自举边界 |
| `03-Issue-Spec-Plan与单闸门开发流程.md` | 覆盖 rebase/重推活语句，补 provenance、FF、per-push SHA 和已发表/未发表分界 |
| `04-Agent编排与定时任务.md` | Controller 专属整合步骤，不将 main merge 当 provider commit；失配与冲突停止 |
| `06-运维手册与踩坑集.md` | 标注 #136 lease 解法为历史、被 #327 取代；旧安装只读，不执行旧 leased write；写 incident/rollback 与两机验收边界 |
| `08-双工具共存与实施.md` | 两 provider 共用整合/发表边界；不新增启用权限 |
| `codex/skills/issue-session-flow/SKILL.md` | 源技能表达已发表分支追加整合和 SHA 核对；保留单 writer、两个确认点 |
| `skill-for-claude/issue-session-flow/SKILL.md` | 同一共享合同的 Claude 对等说明 |
| `codex/skills/aisoft-matt-workflow/SKILL.md` | provider 无 merge，Controller 执行限定整合；不编辑 vendored 上游 |
| `skill-for-claude/aisoft-platform/SKILL.md` | 与Codex对应的共享发布能力与installed/live边界说明 |
| `skill-for-codex/SKILL.md` | 限定 FF 能力、人工自举、source/installed 与验收前不完成 |
| `skill-for-codex/references/private-gitea-access.md` | 保留 broker-only；区分人本人 UI 自举与 Agent 禁令 |
| `docs/agents/issue-tracker.md` | Controller 整合归属与本 Issue 人工 UI 发表卡；禁止代操作 |
| `templates/docs/agents/issue-tracker.md` | 同步平台 tracker 合同；不新增另一套模板 |
| `README.md` | 仅增加 #327 source/installed 状态及导航，不改无关内容 |

建议治理核心措辞：Agent/provider 只追加本 Issue 线性 commit；外层 Controller 仅在批准合同内以 exact remote 原历史为祖先、fresh manifest main 为第二 parent，构造可复算无冲突整合；broker 全门验证后仅普通 FF 发布。此许可不包括 arbitrary merge、历史重写、force、凭据、保护调整、UI 代提交或部署。

历史 #298 spec AC-6（rebase-重推）及 AC-5 中 A 推送 B 改写 HEAD 的“推送发生”预期，以及 #136/06 的 leased rewrite，是历史验收口径。#327 生效后已发表分支重写必须拒绝；#298 的 owner、拒绝错误与逐 push SHA 回执继续保留。通过本 spec 与当前活文档明确覆盖，不改写、删除已闭合历史文档。未发表本地 rebase仅限自身 worktree、未核验/未发表历史；不传递已发表重写权限。

## Runtime 精确映射（fresh run 后）

| exact 文件 | 允许职责 |
|---|---|
| `codex/runtime/aisoft_host_access/broker.py` | 用 FF/DAG/provenance/guard/readback 替代 blanket merge deny 与 leased push |
| `codex/runtime/aisoft_loop/controller.py` | Controller 专属本地整合与验证记录；原 provider 线性提交校验保持 |
| `codex/runtime/aisoft_loop/gitea.py` | 必要的 broker fetch/push 调用接线，禁绕行 |
| `codex/runtime/aisoft_host_access/runner.py` | 同一 typed bridge 的可读 exact branch 接线（只在整合需要时）；不得恢复纯编号新 writer |
| `codex/runtime/aisoft_main_integration.py`（可新增） | 两侧共用纯本地 DAG/tree verifier 与固定 guard 支撑；无网络、凭据或宽命令入口 |
| `codex/runtime/aisoft_worktree_owner.py` | 必要的向后兼容 R0/last_push 证据扩展，不把标记当授权凭据 |
| `codex/install-host-access-broker.sh`、`codex/install-vm.sh` | 仅新增 helper 的受管安装映射；不执行真实安装，不改 provenance guard |
| `codex/tools/check-installed-drift.py` | helper 的受管文件映射；不加入自动修复 |
| `codex/runtime/tests/test_host_access.py`、`test_controller.py`、`test_worktree_owner.py`、`test_main_integration.py`（可新增） | 参数、DAG、scope、单 writer、真实临时 bare remote 与组合回归 |
| `codex/tests/test-host-access-broker.sh`、`codex/tests/test-install-host-access-broker.sh`、`codex/tests/test-agent-runtime.sh`、`codex/tests/test-installed-drift.sh`、`codex/tests/fixtures/installed-drift/test-installed-drift.py` | 固定guard、两侧安装与漂移fixture更新 |
| `codex/tests/smoke.sh` | 只接入本 Issue 必要用例/受管 helper 检查，不删改现有硬门 |
| `docs/changes/327-broker-ff-integration/` 的四份映射文档 | 同步批准状态、真实验收和 handoff |

原已批准范围不改 operation/参数。上述可信证据补充**提议**仅增加 begin/verify 及下表 exact source 文件；在本份具体合同确认前，不授权它们，也不修改任何 manifest/runtime。`git.push.change(branch)` 与 Gitea governance 身份/权限/main/context/routine 值仍不变；无 public merge/approve operation。

## 可信证据 source 精确扩展（已确认，fresh T02 才实施）

此表是原 runtime 映射的最小新增集合，不是目录级授权；以下文件本轮均不创建或修改。原表 installer 职责在本合同中增补为安装 authority/helper/default-disabled 配置与 inert service 描述的受管映射，仍不执行真实安装、provision 或 enable；不得改变八个 source provenance guard。

| exact 文件 | 提议的限定职责 |
|---|---|
| `codex/runtime/aisoft_host_access/contract.py` | strict 两项新 operation / ticket 参数及默认关闭能力；不改 Gitea 身份/ACL/routine |
| `codex/runtime/aisoft_host_access/cli.py` | fixed typed ticket 参数及受控客户端路由；不得新增 caller path/socket/command/PASS 参数 |
| `codex/config/host-access-broker.json` | 仅 begin/verify 的 operation entries，identity_route 保持 project-agent；原 entries、identity_bindings、projects 等 byte-semantic 不变 |
| `codex/config/change-verification.json`（可新增） | strict canonical default-disabled authority policy；无 active UID/GID、grant、account 或服务授权 |
| `codex/runtime/aisoft_host_access/verification_authority.py`（可新增） | 固定 socket/server、OS peer、privilege/drop/isolation capability、protected grant/journal、固定执行与 operator 管理；无 arbitrary execution |
| `codex/runtime/aisoft_host_access/verification_client.py`（可新增） | 固定端点与 server peer 校验；不读/写 protected 文件、不提供直接或 source fallback |
| `codex/runtime/aisoft_change_evidence.py`（可新增） | strict grant/record/compiled scope、完整 diff/内容目的绑定、冻结 graph/field rules；纯机制，无 public 网络/credential |
| `codex/runtime/aisoft_loop/cli.py` | authority-backed Controller 选择与 default-none/capability gate；旧 local approved 不生成 trusted grant |
| `codex/runtime/aisoft_loop/provider.py` | trusted execution 的受限 provider adapter 接线；不复制 Claude/Codex auth，不能在 root 执行 provider |
| `codex/runtime/aisoft_loop/verifier.py` | 冻结 verifier definitions/program digest 与真实受控执行结果接线；不信任 client PASS |
| `codex/runtime/aisoft_loop/state.py` | 本地 progress 只引用 authority record ID/digest，不变成可自行批准的 ledger |
| `codex/agent/loop-controller.sh` | fixed installed authority 调度；不得继承 caller PYTHONPATH 或为缺服务 fallback |
| `codex/tools/host-access-broker.sh` | 两项新操作/受控写路径的 fixed installed 路由与环境隔离；不让 source wrapper 成 live capability bypass |
| `codex/tools/change-verification-authority.sh`（可新增） | 固定 serve/prepare/check/approve/approve-pr/revoke/restore operator 入口；prepare/check 默认只读；管理变更要求真实 EUID=0 与 exact operator 卡；不得自启动/复制凭据 |
| `codex/systemd/aisoft-verification-authority.service`（可新增） | Linux inert 服务描述，fixed trusted-critical ExecStart；候选代码不以 root 运行；无自动 enable |
| `codex/launchd/local.aisoft.verification-authority.plist`（可新增） | Mac 对等 inert 描述，fixed ProgramArguments；无自动 load/bootstrap/RunAtLoad |
| `codex/runtime/tests/test_change_evidence.py`（可新增） | scope/field/内容目的、freeze、未知/adopted object、replay与坏 record 的 source unit fixture |
| `codex/runtime/tests/test_verification_authority.py`（可新增） | 真实 socket peer negative、default-disabled、process/drop/sandbox、root-only state 与启动恢复；模拟权限层不得报 real custody PASS |
| `codex/runtime/tests/test_verifier.py` | frozen required verifier/UID/program与执行结果兼容门 |
| `codex/runtime/tests/test_state.py` | 非权威 progress 与 trusted record 引用、旧 state 不获批准 |
| `codex/runtime/tests/test_contract.py` | 草案/批准状态、exact mapping 与不可自动 approved 兼容，保留自修改治理保护 |
| `codex/tests/test-verification-authority.sh`（可新增） | 新脚本语法、inert service/default-disabled/schema与受管安装 fixture，不启动 live 服务 |

上述可新增 shell 源与现有 source 文件保持普通 100644；installer 如需安装为 0755 必须映射为受管 mode 且 UI bootstrap 验 exact mode。不是给新 live 可执行入口赋权限。本表与原 runtime 表的 installer/drift/smoke/测试映射共同校验；不修改 `gitea-governance.json`、受保护 main、CI context 或 routine opt-in，不泛用其他 manifests。

T04 独立治理应用（本次具体确认后）仍仅原 14 个治理 exact 文件和四角色文档：在各自 #327 活段落同步 authority 的可信记录/独立重算、两项接口与仅 source 扩展、root critical 与非 root provider、default-disabled、I02 独立批准及不把 installed 缺口报 PASS；不改历史 docs 或上游 vendor，不写任何上表 runtime/config/service 文件。T04 应用验证+本地原子 commit 后停止，不能同 run 借新治理许可实施 T02。

## 本 Issue first-PR 自举（负责人本人 UI）

旧 installed broker 的任意首推仍携带 lease-force。本 Issue 不调用它发表，也不先安装 unmerged runtime、不用 source wrapper/direct Git/API fallback。完全自动 Agent 自举目前不具备合规路径。

只读 Chrome 已看到 Gitea 1.26.4 的 Add File → New File/Upload File；New File 的“Commit directly to main”被保护禁用，“Create a new branch for this commit and start a pull request”可选，branch name 可填写。只证明入口，不证明写入与 tree/mode 等价。

1. T01/T04/T02/T03 全在本地 exact branch完成；保存候选 L、base M、完整 binary patch/bundle、tree id、每文件 blob/mode 与文档映射。零 remote write。
2. 最终提交确认绑定 #327 / `change/327-broker-ff-integration` / manual，并明确采用负责人本人 UI publisher，AI 不代点击。发表前 fresh 查重 remote branch与唯一 PR；若能力缺失，停止 GAP，不能推断 ref absent。
3. 负责人本人使用 New File 的 new-branch 方式创建 exact branch，并在 PR 提交页面只创建一个最终 PR。若 UI 自动创建 PR，那就是唯一 PR；不再 broker create第二个。全部候选文件只写 change branch，绝不写 main。逐文件编辑/上传追加提交，保留已有 executable mode；新文件限普通文本 100644。不能保留 mode、不可精确写树或 UI 不支持时停止，不能改用 direct Git。
4. UI 创建的是 human-authored commit H，并非本地 L。owner 只通过 typed fetch 读取对象，验证 base/parent/全部文件 blob+mode、scope 和最终 tree等价；main变化则重新计算并验证组合结果。远端 H 必须重新跑全部本地必要验证和 exact head required CI，不能引用 L 的旧绿灯。
5. mapped summary 的唯一 pr_url、status=pr-open 由 owner 准备准确文件，再由负责人同一 UI追加；不调用旧 broker 回填 push。每次新 H 都重新 scope/tree/CI。CI repair由 owner本地准备并验证文件，仍由本人UI追加到同一 branch/PR；人也可 Update branch by merge，并由 owner验 exact old tip与fresh main祖先/DAG。
6. 本地 L不应 reset/rebase为human H；保留可恢复bundle与原owner worktree，本地与远端 SHA 两层分别记录。必要测试在只读 fetch 对象导出的隔离验证目录执行，不创建第二 active writer。单 writer 约束保留。
7. fresh final H、main保护/祖先、requiredCI、唯一PR、分类全满足后 READY_FOR_REVIEW。负责人本人普通人工 merge；AI 不点击 merge/Update branch，不自动排程 merge。

本路线是本 Issue 源码发表所需的人工执行卡方案；后续真实 UI tree/mode验证仍为 AC，失败就保留阻塞。它不授予 Agent ordinary Git 或 admin credential，不把 #327 设为 #289/#319 人工更新的机械前置。

## Acceptance criteria

- [ ] AC-1：四角色 exact 映射、platform/complex/manual、来源/授权、单 writer与triage/分类读回可复核；准备期零 live mutation。T01/T04治理只改映射合同并分别停止；fresh run记录重读后才能runtime；A路线选择不当作具体新增合同批准。
- [ ] AC-2：R0/R/H、M、commit/tree/scope 全门有效；首次创建、普通FF、无冲突限定整合、重复整合、summary backfill/CI repair及no-op可完成；每次 old tip 为 new tip祖先。
- [ ] AC-3：真实 bare remote的非FF、首创抢占、R1处于R→H之间、公告后竞态、异常删除/重建与本地HEAD移动均被拒绝或如实报告落地不明；失败不能覆盖他人历史，无force/fallback。
- [ ] AC-4：foreign/other-Issue/反序/octopus/stale-main/tampered-tree/范围越界/driver/缺对象/不支持历史、错误project/owner/branch/dirty树均在 mutation前拒绝；原单writer与provider merge deny不弱化；历史 #298 AC-5/6覆盖有测试。
- [ ] AC-5：逐push H/R和actual remote readback一致；不明网络失败、mark写入失败、main推进分别记录真实状态，不把已经写入写成零写；全部broker/Controller组合、完整smoke、语法/ShellCheck与文档门真实执行。
- [ ] AC-6：本Issue人工UI首PR唯一且exact branch，local L与human H分层、tree/blob/mode等价、fresh main与CI实证；无未合并安装或directGit绕行，最终manual merge证据明确。
- [ ] AC-7：源码merge后，Mac及gitea-ci各获exact版本安装批准，读回完整受管组件前后SHA256/mode/owner、真实FF正反向/竞态路径、重复no-op和一次受控失败rollback；旧字节仅rollback停写，不再被用于leased publish。source/local/CI不能代替installed/live。
- [ ] AC-8：main保护/context/身份/单writer/唯一manualPR保持；不改业务项目、不代写#289/#319或重复建PR。安装AC完成及原owner真实采用前，不声称已解锁其Agent发表；人工更新不要求等待#327。

- [ ] AC-9：可信 authority 的 default-disabled、strict grant/record、固定 begin/verify、独立完整内容验证、真实 OS peer/privilege separation、防篡改/replay/未知提交/adoption/restart 与 broker 拒绝无记录均有 source/local 实证；I02 两机 exact 授权后 root custody/真实执行/启动关闭/FF与rollback均读回；未执行层保持 GAP/NOT RUN。

## 风险、回滚与完成边界

整合来源假冒、tree污染、hook/config注入、竞态、freshness窗口和installed差异是核心风险；对应AC-2～5/7均要求负向真实验证。source失败通过追加修复或独立revert PR，不force改历史。

两机安装以合并且稳定pin的source为唯一输入；安装card明确所有变化文件及缺失前态（含新增helper）、精确owner/mode、保存的旧文件集合与hash。不能仅恢复broker.py或信任`.previous`自动完整。rollback恢复完整前态，删除仅本版本新引入的受管文件并核验列表，保留证据；回滚后禁用本新发布路径，旧lease路径不重新获得合规许可。不得为验收创建新身份/PAT、扩大保护、服务/timer或部署。

安装与 authority AC 只能在源码merge后闭合，故`Closes #327`的Gitea自动closed不等于本Issue真实完成。若源码合并自动关闭而 AC-7/AC-9 尚缺，owner据已确认合同通过现有typed `gitea.issue.state.set`保持/恢复open并记录“source merged / installed acceptance pending”；不写completed、不触发runtime、不清理/归档。已有终态工具的自动source-only计划不能覆盖本合同AC。本项是该Issue的确定性验收保留，不新增通用终态机制。

AC实证全部满足后才terminal reconcile、文档check、精确cleanup/归档。本地L若不是merge祖先先保留可恢复bundle并验证human H等价，不能冒称已合并本地对象并强删；清理仍要对exact目标保全读回。

## 非目标

合同准备不修改治理；独立 T01/T04 只按映射治理表应用并分别停止；不恢复#319 remote、不更新#289 PR、不修其业务/UTF-8范围、不操作他人worktree。不开放任意 merge、冲突解决、force 或身份/PAT/保护/context/routine 变更、应用部署或 provider 启用。新 typed source 范围仅为已确认的两项；本轮 T04 只应用映射 governing 文本，不改 operation/config/service/runtime。不批量重命名/删除历史Change或上游skills。

## 未决问题

原 FF/人工自举方向与本份可信根 source 合同已直接确认；A 路线准备和具体确认是两次不同的授权。本次独立 T04 治理应用并停止，后续 fresh run 再 T02，不额外要求同一合同重复批准。local approved 不等于 live 投影或 protected grant；具体机器 I01/I02 权限动作仍须独立 exact 卡。实际 UID/GID/工具链/安装 pin/grant/启动与 rollback 目标留在每台 I02 exact operator 卡，不为通过文档门虚构数值或启动。真实 UI/字节 mode/guard/authority 实证仍是待执行 AC。
