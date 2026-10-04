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
updated: 2026-10-03
status: approved
---

# #327 最小治理与发布合同

## 目标与原因

保持 original remote tip 为每次新 head 祖先，允许严格来源限定的 fresh manifest main 整合，并经 ordinary FF push 发布；禁止 force、lease-force、任意 merge 与更宽身份 fallback。原合同和独立 T01/T04 已确认、应用并 STOP；fresh T02 已有未提交 source WIP。此前“按建议执行”仅授权A草案；本聊天现直接“批准”审阅卡绑定的具体资源/工具链合同。本轮T05仅原14治理+四角色/验证/localcommit/STOP，不修改runtime或执行镜像/安装/服务动作。

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

## 原可信证据合同（T04 已确认并应用；历史基线）

负责人先“按建议继续”准备 A 路线，在草案 ac172e515a47357d24ff268473af6bbee5c13fe1 和具体审阅卡形成后，本聊天直接“确认”。批准绑定 #327 / `change/327-broker-ff-integration` / manual / 该 draft commit 与原 spec+plan SHA256（外部 `t04-application-approval.json`）；当时仅独立 T04 治理应用并 STOP，后续 fresh T02 已产生 WIP。原 T01 commit `061b0f3ec59869fe379d70b7d2f0455df4b8708a` 与原 FF/竞态/人工自举方向保持；当时新 runtime 尚未实现；当前部分 source WIP 见 verification。原具体 source 合同批准不表示 installed 权限/注册/启动已批准或执行。

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

原 T04 source policy 为 `change-verification/v1`；grant/record 原为 `change-grant/v1` / `change-record/v1`。新T05已确认v2私有绑定，见下文；旧批准不自动授权 v2。默认形状如下，仅是获确认的 source 形状（待 T02 实现），**没有写入 installed config**：

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

I01为两机独立exact版本文件安装/字节/mode/owner、installer重复no-op与一次受控文件安装失败rollback；不要求未注册authority先做真实FF。AC-7的realFF/publish no-op/reject/运行权限与authority资源rollback在I01文件读回完成后的I02执行，完整验收要求不减。I02 新增“verification authority 注册/启动/受控验收”卡。I02 只有在源码人工合并、I01 完整读回且本份新权限合同获确认后，分别获得 **每台机器 exact** UID/GID、program/hash、state/context/socket/service 路径、grant digest、启动/关闭、真实正反向测试与恢复清单批准，才可由指定 operator 执行。不继承 #316、T01、路线 A 选择或一般 installer 许可；不启用任一 provider/profile/timer，不创建或复制 auth/PAT/账户。若将来需要新增账号/Secret或配置其他项目，那是新范围，不从本草案推导许可。

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

T01 只在独立受控治理应用步骤，按已确认本 spec 精确修改以下文本，不混入 Python/runtime/install/CI 实现；commit 后立即停止。原合同准备阶段没有修改 AGENTS.md；T01 后经直接确认独立应用并已 STOP。原可信根合同确认后的 T04 也只使用下表14项和四角色、应用后 STOP；原草案准备没有应用该表；当时确认后的 T04 仅应用该表及四角色，不混入 runtime。后续 fresh run 必须重新读取本 worktree 的治理、Issue、有效评论、spec/plan 和 installed 能力，不继承旧上下文替代读取。

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

原已批准范围不改 operation/参数。T04 已确认的可信证据补充仅增加 begin/verify 及下表 exact source 文件；这些已有范围的实施历史见 verification。新安全合同另列exact增补范围，T05独立STOP及后续fresh run前不能实施它。`git.push.change(branch)` 与 Gitea governance 身份/权限/main/context/routine 值仍不变；无 public merge/approve operation。

## 可信证据 source 精确扩展（已确认，fresh T02 才实施）

此表是原 runtime 映射的最小新增集合，不是目录级授权；这些文件本轮均不创建或修改；既有 WIP 保留。原表 installer 职责在本合同中增补为安装 authority/helper/default-disabled 配置与 inert service 描述的受管映射，仍不执行真实安装、provision 或 enable；不得改变八个 source provenance guard。

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

历史T04独立治理应用仍仅原 14 个治理 exact 文件和四角色文档：在各自 #327 活段落同步 authority 的可信记录/独立重算、两项接口与仅 source 扩展、root critical 与非 root provider、default-disabled、I02 独立批准及不把 installed 缺口报 PASS；不改历史 docs 或上游 vendor，不写任何上表 runtime/config/service 文件。T04 应用验证+本地原子 commit 后停止，不能同 run 借新治理许可实施 T02。

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

## 资源与工具链安全补充合同（已直接批准；T05独立治理应用）

本节补齐 T02 实际发现的 `TOOLCHAIN_CLOSURE_GAP` 与 `SCRATCH_QUOTA_GAP`。负责人选择A最初只授权方案；具体草案和审阅卡完成后，本聊天直接“批准”。本节数值/路径/schema/source扩展现为已批准source合同；原spec/plan SHA256保存在外部t05-application-approval.json，不是已安装能力或主机执行许可。当前无条件 GAP 拒绝保持；不能为绿色测试删除它。本节已具体确认，以此节覆盖旧 v1/宽泛 pin/资源说明的对应项，其他 FF、R0、manual、唯一 PR、credential/main/CI/provider 边界不变。

### 固定资源上限与隔离

| 资源 | 已确认固定上限 | 失败行为 |
|---|---|---|
| Mac verifier scratch | 一个64 MiB逻辑磁盘；UDIF/UDRW，HFSX、无分区表；镜像实际大小≤72 MiB且冻结 exact st_size | 不支持此格式/容量/flags/owner 或 ENOSPC → GAP/执行失败；无扩容/宿主 tmp fallback |
| Mac root Git 对象暂存 | 256 MiB逻辑磁盘，同一受管后端；镜像实际大小≤264 MiB；最多两个挂载对象卷（当前写入和前一只读） | fetch/对象处理需更多空间则在 remote mutation 前拒绝；不只在 fetch 后做 du |
| 挂载并发/只读输入 | 全 authority 最多一个 scratch，最多两个对象卷；镜像 backing 总量≤600 MiB；全局同时最多一个完整只读展开副本≤256 MiB；≤4096文件/目录entries、depth≤16、单segment≤255bytes | 串行新 scratch；重复 blob 每个路径都计费；禁止跨 verifier/generation 复用 |
| 保留 state | 所有 owned 镜像、sealed Git 对象、CONTEXT输入/平台临时文件、lease/record/metadata 合计预留≤8 GiB；平台state/context元数据总预算≤64 MiB | 创建前保护锁内预留最大 backing/输入/记录预算；余额不足停止；不自动删除历史或重置 R0 |

这里的数字是产品支持上限，不证明64 MiB HFSX在任何 Mac版本都可成功创建。文件系统元数据同样占有限磁盘；不声称存在独立可配置 inode quota。大量 tiny file 测试必须实际触发有限元数据/ENOSPC；RLIMIT_FSIZE 或事后监控不能替代磁盘总量边界。kernel/global缓存不纳入该磁盘额度承诺；process/输出/时间上限与真实 descendant 终止仍独立验收。Linux 保持受限 tmpfs/namespace：scratch64 MiB、nr_inodes=4096、相同并发/展开/保留上限；root Git使用受限256 MiB tmpfs（nr_inodes=16384）并将sealed快照有界复制到protected state。Linux真实root mount/namespace/drop仍 I02 NOT RUN，不能由 Mac 模板测试推导。

所有CONTEXT/readonly input和平台temporary也必须登记于同一protected预算，不能仅统计STATE。创建前按exact完整tree、逐路径regular bytes和已接受OSallocation/目录metadata上界预留（未知上界即GAP），copy期间每步受界；原子化完成前不可暴露。全局最多一个输入副本，无遗留副本时才创建下一份；generation/verifier结束且owned进程/lease均已安全终止后，依平台生成并保护的exact文件/目录清单与dirFD/no-follow逐项删除root-owned readonly input并fsync/release。不得以递归遍历user scratch替代清单。失败保留预算/清单、quarantine，不继续累积context；空generation目录、临时平台元数据也计入64 MiB上限。任何保留与暂存重叠都计费，包括Linux tmpfs中对象向sealed state复制的双份窗口。

不新建或迁移整块 STATE 文件系统。STATE 保持原固定0700目录；project/verifier 不可写该目录或 backing file。所有不可信 Git 数据处理的输出、临时目录与 pack 写入必须限定于 bounded root Git 卷；Git 配置、hook、credential helper 仅来自核验的平台固定代码。protected 元数据写入有字节/条目上限和预留预算，host 本身空间不足仍必须失败、保全已知状态并如实报告可能落地 H，不能伪称零写。

### Mac 模板、设备与生命周期

1. **模板只由未来 I02 指定 operator 创建并登记**：`STATE/seed/blank-64m.dmg` 和 `STATE/seed/blank-256m.dmg`，root0400、regular/nlink1、父0700，冻结模板 SHA256、st_size、逻辑 sectors、文件系统/volume UUID和创建工具链。I01只安装惰性代码/空登记，不创建模板。operator 卡示例为 `/usr/bin/hdiutil create -size 64m -type UDIF -fs HFSX -layout NONE -volname AISOFTScratch -uid 0 -gid 0 -mode 0755 -noautostretch <fixed-template-path>`；对象模板只以同一固定模板将 size改256m/volname改AISOFTObjects。这是文本蓝图，本轮未执行。`-type UDIF`产生UDRW；禁止误用 `-type UDRW`。无 `-ov`、`-attach`、resize、sparse、shadow、压缩、加密或自由imagekey/plugin；模板不含项目/凭据内容。
2. protected durable lease/nonce/容量预留先持久化，再在 `STATE/<generation>/scratch/<lease>.dmg` 以root0600建立完整预分配byte copy。禁止hardlink/symlink/reflink/sparse拷贝；核验模板与clone内容后才暴露卷。objects lease同样固定在 `STATE/<generation>/objects/`，不接受caller路径。镜像名、generation/lease由服务生成，目录FD/no-follow校验。
3. 仅固定 `/usr/bin/hdiutil attach -nomount -plist -owners on -nobrowse -noautoopen <owned-image>`，然后 `/sbin/mount_hfs -o nodev,nosuid,noexec,nobrowse <observed-device> <fixed-mountpoint>`。不传caller设备；不 mount `/Volumes`、任意设备或更换文件系统。`hdiutil info -plist`只在内部将本服务镜像canonical路径与设备绑定，不输出其他镜像inventory。attach必须恰好一个owned设备；exit0或名字匹配不算证明。
4. scratch mountpoint固定 `CONTEXT/<generation>/scratch`，底层root0700；挂载后卷根root:registered_gid0750，仅其 `work/` 子目录registered UID/GID0700可写。`TMPDIR/TEMP/HOME`与cache仅指向work；只读输入另置root所有的固定context，不落回宿主 `/tmp`/HOME。对象卷固定 `STATE/<generation>/objects/mount` root0700；provider/verifier不可读写。kernel statfs/getfsstat实读filesystem、FSID、容量、nodev/nosuid/noexec/nobrowse、无 MNT_IGNORE_OWNERS及actualmount/device映射；device/path/FD dev+inode+ctime/nonce均保留。任何ownership失效均拒绝。禁止root递归遍历不可信scratch以清理；mount之后的权限设置只作用已核验卷根/固定空work child。
5. 所有 hdiutil/mount_hfs 程序、原生依赖及其系统delegate属于下节 closure/OS TCB。runtime没有格式化入口、不接受script/helper/设备参数，也无 diskutil/resize/create/recover force operation。I02模板命令需要单独exact卡批准，不由T02执行。
6. 每 required verifier使用新lease与新空模板。先验证本服务真实进程树全部退出，再recheck镜像→设备→mount映射，然后只普通 `hdiutil detach <owned-device>`；readback确认自己卷已卸载、设备不再指向该镜像后才dirFD删除exact backing并fsync/release。busy/descendant未知/设备号复用/映射失配/权限漂移/崩溃/断电→blocked quarantine，保留lease/backing/proof、禁止下一generation或自动force/retry；不删除已挂载镜像、不动未知设备。
7. 重启扫描仅核对protected lease及本服务设备事实；未完成generation记interrupted，不接收caller PASS，不把重启/消失的mount当作可重pin R0。恢复/人工detach/模板替换仅在每主机exact operator卡中，保留旧record/object镜像和可能已发表H。sealed对象镜像冻结为只读且保留hash以供独立重算；总保留预算耗尽不自动evict。rollback先stop/preserve再按exact own lease对象解除，不恢复旧leased publish。

`noexec`意味着此首版 Mac scratch 不支持执行其中新编译的native binary；所需native test应记录能力GAP，不能放宽flag、把build产物移到宿主可执行目录或伪称一般SDK/build支持。provider自己的必要onboarding资源仍只能来自原合同已独立接受且隔离的绑定；不因scratch放宽credential/helper/其他项目/control socket边界。

### Python 加载前的 bootstrap 与完整闭包

- 新的固定native bootstrap源只做平台预检/角色调度，必须在任何Python平台模块导入前运行。非root deterministic build，artifact绑定source SHA、编译器/SDK/链接清单和binary hash；未来I01安装 `/usr/local/libexec/aisoft/verification-bootstrap` root0755，无setuid。bootstrap自身的native loader/OS初始化属于已冻结root/OS TCB；不虚构“main之前无任何库执行”。不在root下编译项目、下载工具或安装全局Python/Git/SDK。
- 仅固定 daemon/operator/worker 三种角色及既有严格命令，不给caller arbitrary exec/path/argv/root/descriptor参数。特权角色实际UID0；worker实际已登记非root身份并依原OS隔离。服务描述/critical wrapper只调用installed bootstrap，没有source/PATH/未知shim fallback。env/FD清理先于Python；Python使用canonical regular final interpreter `-I -S -B`，固定root cwd，禁用户site/.pth/sitecustomize/PYTHONPATH/PYTHONHOME、DYLD/LD/Git覆盖和继承敏感FD。`-B`不保证不会读取已有pyc；所有可加载py/pyc/extension必须pin，或明确拒绝pyc加载。
- closure来自冻结的build dependency manifest、全部相关trusted目录inventory及native静态/显式dynamic dependency解析，运行trace只是交叉核对。必须列出平台所有模块（含late import）、interpreter/全stdlib/extension/loader、Git本体/remote-https/transport/helper/固定hook与解释器、OS隔离/资源工具、非秘密trust资源和所需系统delegate。每个qualified import到exact路径/内容hash/mode/owner的binding受加载前校验；未知root import/dlopen/plugin/service delegate直接GAP，不把“当前loaded”集当完整闭包。
- Linux递归解析ELF interpreter/needed libs及登记动态加载项；Mac递归解析Mach-O linked dylib和显式dlopen。`@rpath/@loader_path/@executable_path/$ORIGIN`只解析已冻结root-custodied目录；环境搜索/用户可写路径/未知动态目标拒绝。Mac cache-only库记录logical install name/imageUUID/cacheUUID/OSbuild/arch，并hash所有实际cache/subcache backing files；不存在独立 `.dylib` 文件不能作为漏pin理由。`/usr/bin/dyld_info -linked_dylibs/-dlopens/-uuid`可辅助但不是完整性证明，tool自身也须pin。cache或权限不可完整枚举时GAP，不hash逻辑名假装字节验证。
- alias只允许operator登记时有限解析已验证root所有、不可写parent下的OS symlink链；每个link文本/owner和最终目标都冻结。runtime执行canonical regular target，逐次拒绝link漂移；未知shim/redirect、user Homebrew、不能解析的二次interpreter/helper拒绝，不顺着普通PATH找替代。既有合格OS工具存在与否留待I02；缺失就GAP，不借此授权安装新工具链。
- descriptor strict：≤8 MiB、≤16384 entries、pin普通文件streaming hash总输入≤64 GiB；字节/条目/路径深度/解析时间均有上限。role表无泛命令，禁止group/other writable、可变user library、秘密内容。首次注册与每个critical prepare/apply/approve/approve-pr/restore/generation/verify/publish/worker前校验全闭包与exact role/resource digest；不能只cachemtime。只能复用独立证明仍immutable的snapshot，其他情况重hash到boundeddeadline失败即GAP；实际时延/TOCTOU/可用性纳入I02。root/OS管理员改写不在非root攻击承诺内，但漂移后新活动必须拒绝。
- 登记只通过原private root operator `prepare --apply` + strict v2 exact卡，descriptor只从 `/usr/local/share/aisoft/verification-incoming/toolchain.json`、`/usr/local/share/aisoft/verification-incoming/resources.json` 读入；v2卡固定 `/usr/local/share/aisoft/verification-incoming/operator-card.json`。incoming父root0700、文件root0600/regular/nlink1/no-follow/实际FD与hash/≤8MiB（operator卡≤1MiB）均核验，拒绝同名替换或caller path；read-only prepare/check不建立该目录、不改文件。首次I02仅指定operator按批准card建立incoming，native bootstrap先以冻结build/I01artifact与exact staged descriptor完成全闭包校验、持有固定FD证明，再允许Python执行原prepare --apply将同一digest原子登记；不以未注册为由跑未核验Python或自动信任incoming内容。卡与descriptor缺/漂移则GAP，不新增publicapprove/路径/命令。compiled bootstrap的安装hash由独立operator与I01receipt绑定；descriptor绑定artifact hash，grant绑定descriptor hash，避免二进制自含自身hash的循环信任。无新签名密钥/PAT/Secret。

### 默认登记、schema 与 publish 的持续状态

新source配置仅为以下惰性形状，installed位置固定 `/usr/local/share/aisoft/verification-toolchain.json` 与 `/usr/local/share/aisoft/verification-resources.json`，root0644：

```json
{"version":"verification-toolchain/v1","enabled":false,"hosts":{"mac":null,"gitea-ci":null}}
{"version":"verification-resources/v1","enabled":false,"hosts":{"mac":null,"gitea-ci":null}}
```

I01安装空绑定且不enable；I02分别登记具体program/closure/resource/template/OSbuild descriptor和exact hashes。public `change-verification/v1` 四key默认policy不扩字段；private grant/record/operator变为 `change-grant/v2` / `change-record/v2` / `change-operator/v2`，authority_pin必须增加toolchain/resource descriptor digest；sealed record必须绑定exact closure/execution profile/lease digest。v1历史只读保留，不能用于新授权/执行；无自动迁移、清空或revision/R0重pin，旧source fixture不能充root grant。`change-ledger/v1` envelope可保留，payload明确v2且resource lifecycle事件strict prefix/序号持久化。

closure全量预检可能超出client等待窗口。既有 `git.push.change(branch)` 不增operation/参数；服务将publish作为一个持久attempt，preflight/密封检查与pending记录完成后才进入transport。断线/timeout/重启之后保持实际H、possible_write和phase；同branch重入只poll既有pending，不再次推送。未知remote必须只读取证/adoption决策，不能超时后自动retry或报告零写。publish前closure漂移则零mutation拒绝；transport已开始后发现漂移只报告真实可能落地状态并停止后续活动。begin/verify依原pending语义接线，不通过放宽RPC时限伪造成功。

### T05 治理、exact source 增补与 I02 卡

具体合同确认后，T05只在**原14治理表**各文件#327活段落同步bootstrap/完整closure、boundedscratch与ownlease、default-none/source-installed、schema和I02/STOP边界，不增加治理文件，不改变main/CI/routine/credentials。四角色同步批准状态/批准receipt和graph。独立治理commit后STOP；既有T02 WIP不混入commit、也不丢弃。后续fresh run重读新governing+具体批准、Issue/comments/installed才能继续T02。

| exact新增source文件（均后续fresh T02；本轮不创建） | 限定职责 |
|---|---|
| `codex/config/verification-toolchain.json` | 上述default-disabled空host closure登记 |
| `codex/config/verification-resources.json` | 上述default-disabled空host resource登记 |
| `codex/runtime/aisoft_host_access/toolchain.py` | strict闭包/alias/cache/role descriptor、pin重验、pre-import binding；无发现后自动批准 |
| `codex/runtime/aisoft_host_access/scratch.py` | 固定resource bounds/模板lease/owneddevice/mountreadback/只读objects/隔离保全；无arbitrary设备/format/create public入口 |
| `codex/tools/verification-bootstrap.c` | 固定native pre-Python核验/清env/角色调度；无setuid/callerexec |
| `codex/tools/build-verification-bootstrap.sh` | 仅非root确定性source build与非秘密build receipt；不安装/下载/启动 |
| `codex/runtime/tests/test_toolchain.py` | 完整inventory/late-import/alias/缓存/v2/schema/未知依赖/漂移 source fixture |
| `codex/runtime/tests/test_scratch.py` | 额度预留/lease/own-device/崩溃恢复/strictargv fixture；模拟不报realmount PASS |
| `codex/tests/test-verification-bootstrap.sh` | 非rootbuild/descriptornegative/installed映射fixture；不创建实际root卷/service |

原已确认 installer/drift/smoke/authority/launchers/units/contract/evidence/client/Loop测试职责仅增补本节映射、v2和pending接线。新source统一100644；native安装0755、配置0644仅是未来I01受管mode。全部八个provenance guard保持，不以新build绕staleness。新registry不是另一份Gitea manifest；不改 `gitea-governance.json` 或其他身份/权限。

I02每主机exact卡必须包括：source/build artifact/OSbuild/arch/closure完整hashinventory/descriptor digest与入口role；existing UID/GID；模板logicalsectors/st_size/hash/空白proof；实际device/mountpoint/FSID/容量/flags/owner读回；retained/input/concurrency限额；start/stop、ENOSPC/tinyfiles/timeout/descendant/busy/reuseddevice/reboot/断电恢复和closure漂移/late-import/cache/aliasenv负向；credential/helper/其他项目/socket不可达；实际FF/no-op/strictR/race正反向；前态缺失项、完整保全/隔离/rollbackreadback。不记录secret。无真实可用目标就GAP，不由AI创建canary身份/Issue/PR。没有这些实际证据，AC-9/10/11和原AC-7不能闭合。

技术来源：Context7检索 Apple hdiutil 未返回适配的一手库，未把无关结果作依据。已只读本机Apple随附 `hdiutil(1)`、`mount(8)`、`mount_hfs(8)`、`dyld_info(1)`、`dyld(1)` 手册；本机观察27.0.1/build26A434不作为已接受hostmatrix。另参考 [Apple磁盘镜像指南](https://support.apple.com/en-gb/guide/disk-utility/dskutl11888/mac)、[Apple dyld cache layout](https://github.com/apple-oss-distributions/dyld/blob/main/doc/CacheLayout.md) 与 [Apple动态库加载说明](https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/DynamicLibraries/100-Articles/DynamicLibraryUsageGuidelines.html)。这些仅支持格式/工具和依赖模型，不能证明本设计已实现或安全；limits/lease/bootstrap为本Issue已确认source设计。所有模板/挂载/nativebootstrap/root/I02实测 NOT RUN。

## Acceptance criteria

- [ ] AC-1：四角色 exact 映射、platform/complex/manual、来源/授权、单 writer与triage/分类读回可复核；准备期零 live mutation。T01/T04/T05治理只改映射合同并分别停止；fresh run记录重读后才能runtime；A路线选择不当作具体新增合同批准。
- [ ] AC-2：R0/R/H、M、commit/tree/scope 全门有效；首次创建、普通FF、无冲突限定整合、重复整合、summary backfill/CI repair及no-op可完成；每次 old tip 为 new tip祖先。
- [ ] AC-3：真实 bare remote的非FF、首创抢占、R1处于R→H之间、公告后竞态、异常删除/重建与本地HEAD移动均被拒绝或如实报告落地不明；失败不能覆盖他人历史，无force/fallback。
- [ ] AC-4：foreign/other-Issue/反序/octopus/stale-main/tampered-tree/范围越界/driver/缺对象/不支持历史、错误project/owner/branch/dirty树均在 mutation前拒绝；原单writer与provider merge deny不弱化；历史 #298 AC-5/6覆盖有测试。
- [ ] AC-5：逐push H/R和actual remote readback一致；不明网络失败、mark写入失败、main推进分别记录真实状态，不把已经写入写成零写；全部broker/Controller组合、完整smoke、语法/ShellCheck与文档门真实执行。
- [ ] AC-6：本Issue人工UI首PR唯一且exact branch，local L与human H分层、tree/blob/mode等价、fresh main与CI实证；无未合并安装或directGit绕行，最终manual merge证据明确。
- [ ] AC-7：源码merge后，Mac及gitea-ci各获exact版本安装批准，I01读回完整受管组件前后SHA256/mode/owner、installer重复no-op及受控文件失败rollback；I02注册后读回真实FF正反向/竞态、publish no-op与authority/resource操作rollback；旧字节仅rollback停写，不再被用于leased publish。source/local/CI不能代替installed/live。
- [ ] AC-8：main保护/context/身份/单writer/唯一manualPR保持；不改业务项目、不代写#289/#319或重复建PR。安装AC完成及原owner真实采用前，不声称已解锁其Agent发表；人工更新不要求等待#327。

- [ ] AC-9：可信 authority 的 default-disabled、strict grant/record、固定 begin/verify、独立完整内容验证、真实 OS peer/privilege separation、防篡改/replay/未知提交/adoption/restart 与 broker 拒绝无记录均有 source/local 实证；I02 两机 exact 授权后 root custody/真实执行/启动关闭/FF与rollback均读回；未执行层保持 GAP/NOT RUN。

- [ ] AC-10：完整trusted module/interpreter/native loader/library/Git/helper/OSdelegate/alias/shared-cache闭包在Python平台导入前有固定bootstrap gate；unknown/late-import/env/alias/cache/descriptor/role漂移和v1滥用全部mutation前拒绝，source fixture及每主机I02真实证据分层；未注册/default-disabled不得执行。
- [ ] AC-11：scratch/rootGit/输入/并发/保留上限有创建前预留和真实有限filesystem证明；大量tinyfile/ENOSPC/busy/child/reuseddevice/断电重启/cleanup/rollback均保持own-lease证据，不force/resize/hosttmp/删除历史；Mac noexec能力范围如实GAP，I02未运行不报PASS。

## 风险、回滚与完成边界

整合来源假冒、tree污染、hook/config注入、竞态、freshness窗口和installed差异是核心风险；对应AC-2～5/7均要求负向真实验证。source失败通过追加修复或独立revert PR，不force改历史。

两机安装以合并且稳定pin的source为唯一输入；安装card明确所有变化文件及缺失前态（含新增helper）、精确owner/mode、保存的旧文件集合与hash。不能仅恢复broker.py或信任`.previous`自动完整。rollback恢复完整前态，删除仅本版本新引入的受管文件并核验列表，保留证据；回滚后禁用本新发布路径，旧lease路径不重新获得合规许可。不得为验收创建新身份/PAT、扩大保护、任意服务/timer或部署；本合同authority服务仅未来exact I02明确批准的start/stop/rollback范围。

安装与 authority AC 只能在源码merge后闭合，故`Closes #327`的Gitea自动closed不等于本Issue真实完成。若源码合并自动关闭而 AC-7/AC-9/AC-10/AC-11 尚缺，owner据已确认合同通过现有typed `gitea.issue.state.set`保持/恢复open并记录“source merged / installed acceptance pending”；不写completed、不触发runtime、不清理/归档。已有终态工具的自动source-only计划不能覆盖本合同AC。本项是该Issue的确定性验收保留，不新增通用终态机制。

AC实证全部满足后才terminal reconcile、文档check、精确cleanup/归档。本地L若不是merge祖先先保留可恢复bundle并验证human H等价，不能冒称已合并本地对象并强删；清理仍要对exact目标保全读回。

## 非目标

合同准备不修改治理；独立 T01/T04/T05 只按映射治理表应用并分别停止；不恢复#319 remote、不更新#289 PR、不修其业务/UTF-8范围、不操作他人worktree。不开放任意 merge、冲突解决、force 或身份/PAT/保护/context/routine 变更、应用部署或 provider 启用。新 typed source 范围仅为已确认的两项；原T04只应用映射governing文本；本轮仅批准的T05 governing文本与四角色，不改operation/config/service/runtime。不批量重命名/删除历史Change或上游skills。

## 未决问题

本聊天直接“批准”审阅卡绑定的T05具体补充合同（#327/exactbranch/manual/spec+planhash），本轮仅独立T05治理应用/验证/localcommit后STOP。原批准字节与批准登记保存在外部，当前状态/证据回填不扩技术合同。无需重复确认同一source范围；后续fresh重读才能继续保全T02 WIP。I01/I02每主机仍各需exact operator卡，实际工具chain/UID/模板/OSmatrix未注册不虚构hash。新source/真实closure/quota/主机/FF/安装验收均未运行，旧FAIL和GAP真实保留；source approved不作live标签或protected grant。


## T06：canonical-main 治理基线同步补充合同

本补充须由负责人确认 exact 审阅卡后生效；summary 原 approved 与恢复卡 A 不能代替本补充确认。
T01/T04/T05 历史、原 AC 与 source/installed 分层保留。此次仅消除主线基线落后，不扩大现场授权。

- exact Issue #327、branch `change/327-broker-ff-integration`、owner `01a0fcec-eb78-7790-a36a-daea917f43d2`、
  worktree `/private/tmp/issue-327-broker-ff-integration`；原 HEAD `bba5ea1790d4f8508746acb9a59ec99d39fbd4ab`；
  canonical main `dc9aa468580f92a73dfa054c6f04ef5113f56694`。main 或 source/owner 漂移停下重新核对，不自动换 pin。
- T06/G01 仅同步原14治理集合中的7路径：`03-Issue-Spec-Plan与单闸门开发流程.md`、
  `04-Agent编排与定时任务.md`、`06-运维手册与踩坑集.md`、`README.md`、
  `codex/skills/issue-session-flow/SKILL.md`、`skill-for-claude/issue-session-flow/SKILL.md`、
  `skill-for-codex/references/private-gitea-access.md`。只应用 external receipt 固定 patch 中
  main 已有 #286/#289/#316 段落，保持本分支 #327 T05 段落；明确将该基线同步纳入本 complex spec。
  不改 `AGENTS.md` 或其余7原治理文件，不改 required CI、权限、Secret、provider 或部署合同。
- 映射 summary/spec/plan 仅追加此授权与 frontier；原角色/front matter 路径、业务目标、AC-1～11与
  已批准 source touch points 保留。external 卡、receipt 与 proposals 保留 exact bytes/hash，无自引用 commit SHA。
- T06 独立治理-only 本地原子 commit（仅上述7文件与mapped summary/spec/plan），原32WIP先保全，
  source字节/index不混入该commit；验证后立即 STOP。不得在该运行继续 runtime。
- 后续 fresh run 重读 governing、该具体批准、mapped docs、Issue/comments/source/installed 能力后，
  T02/R01 才能先作 pinned main 的无冲突纯基线 integration checkpoint；第一 parent 为本Issue旧tip，
  第二 parent 为 exact main，tree 必须等于限定干净 merge；保留已发表/本地历史，不 rebase/force。
  若纯基线整合出现冲突、tree不符或scope漂移则停止，不手工改进 integration commit。
- 基线整合后按三方 preview 恢复未提交32WIP；唯一已知 `broker.py` 冲突保留 #327 authority dispatch
  与 upstream #286 dependency / #316 operator-only credential dispatch，随后作独立source验证/原子commit。
  此手工修复绝不混进纯 integration checkpoint；新增冲突/权限或合同决策必须升级。
- source既有closure/dispatch/resources/Loop与旧13methods/16cases回归继续按T02完成；旧失败如实保留，
  不改成统一CUSTODY_GAP、skip或移除guard。完整runtime与默认locale smoke在实质修复后重跑。
- 本地checkpoint不是发表或启用许可；I01/I02/root/安装/Secret/socket/service/image/mount、remote mutation、
  PR/merge/deploy 均无本补充授权。main保护、唯一manualPR、默认disabled与B01/I01/I02独立闸门保持。
- 回退先停source活动，使用保全的 source-wip.tar、tracked-wip.patch 与完整HEAD bundle核对恢复；
  保留已产生的本地checkpoint和回执，不删共享refs、不重写历史或丢WIP。无远端变动可回退。


## T07：canonical main 固定 Python 3.9 兼容范围补充

本补充须负责人批准 external exact 卡后生效；旧 approved、T06/R01 与恢复卡 A 不授权此新增两个文件。
Issue、exact branch、manual policy、owner、原 AC 与所有治理/安全/安装边界保持。

R01 已整合 main `dc9aa468580f92a73dfa054c6f04ef5113f56694`。其中 #286 的
`codex/runtime/aisoft_host_access/dependencies.py` 在模块加载时执行 `Dependency = int | str`，
固定 `/usr/bin/python3` 3.9.6 实际导入失败，使 source broker 拒绝 fixture 和 native fixture FAIL。
完整 source broker 导入链还触发既有 `profiles.py` 的模块级 Callable/PathLike union 别名同类失败。
该别名来自原既有 profile runtime，并非 #286 新增；#327 固定解释器入口需要两处均兼容。
不更换固定解释器、隔离参数、PATH，不移除测试硬门；最小恢复使用 `typing.Union` 保持这两处类型别名。

| exact 新增 runtime 文件 | 唯一允许职责 |
|---|---|
| `codex/runtime/aisoft_host_access/dependencies.py` | 仅新增 `typing.Union` import，并把模块级 `Dependency = int | str` 改成 `Dependency = Union[int, str]`；不改解析、target、permission、credential、remote 或其它运行逻辑 |
| `codex/runtime/aisoft_host_access/profiles.py` | 仅新增 `typing.Union` import，并把模块级 `Replace` 的两个 `str | os.PathLike[str]` 改为 `Union[str, os.PathLike[str]]`；不改 profile/identity/token/path 迁移、权限或其它运行逻辑 |

批准绑定 source/candidate 文件与补丁 SHA256。类型别名之外的代码或主线任一文件发生漂移即停止核对，
不借此扩展为 #286 其它修复。此两个文件的四行精确新增归原 T02，唯一最终 PR 仍绑定 #327。

T07 仅独立应用本目录 mapped summary/spec/plan 三份治理合同及其中两项确定性完成投影，
不改原14治理文件、verification 或任何 runtime WIP；文档校验、独立本地原子 commit 后立即 STOP。
完成投影仅 plan graph 的 T07 row（pending→completed）和 summary 的 T07 frontier line；
外部 receipt 记录批准/实际 commit，避免提交内自引用。后续 fresh run 重读合同、批准、Issue/comments、
main/source/owner/installed，才允许 T02 应用该四行 source 修复并继续原已批准实现。

实际 checkout 应用后分别重跑固定 Python3.9 导入与 deny fixture、native source fixture、
相关 dependency/toolchain/host-access 回归和完整默认 smoke；完整 runtime 在原可信链和回归迁移完成后重跑。
隔离副本的 47 项 unit 与 nonroot native 仅为候选证据，不能替代 actual checkout、root、installed 或 live。
不新增 direct Git/API、force、身份、Secret、账户、安装、service、grant、image/mount、PR、merge 或部署权限。

应用前保全原33 WIP 与 HEAD/index/owner。失败只撤回本次 exact doc/source bytes，保留已经完成的
T06/R01 main checkpoint 与原 WIP，不 reset/rebase 历史、不改其它 Issue 文件；不自动回退或重建远端 ref。

## T08 候选：Mac 完整后代 observer 的安全与签名边界

本节是待具体确认的新增安全合同，旧 T07 确认不覆盖这项选择。本节确认前不实现新后端，
不改实际17治理合同，不调用 ES client 或改变 host 状态。当前 source loader 增量不是 observer 能力。
现有 SDK 与 Apple XNU 都注明 kqueue NOTE_TRACK/NOTE_TRACKERR/NOTE_CHILD 自10.5起不受支持；
PID轮询、进程组/leader退出、事后killpg或可伪造 callback 不能代替原AC-11的完整实际后代证明。

### 唯一 Mac 后端选择与权限限制

仅采用 macOS27+ 的 `es_new_descendants_client`，观察固定native supervisor自身与其完整后代。
不使用可观察全host的 `es_new_client`、auditpipe、DTrace，不能通过TCC/Full Disk Access、
系统审计策略、SIP调整或其他全局权限作为fallback。API、accepted OS/build/arch、entitlement、
冻结签名artifact或事件完整性任何一项不具备，保持EXECUTION_TRACKING_GAP且无资源创建/执行。
本机27.0.1与SDK声明仅为read-only事实，不证明kernel client创建、签名授权或该OS能力已接受。

native bootstrap的特权daemon/operator角色在完整闭包预检后建立本角色的native supervisor；
supervisor先获得真实kernel descendants client，再启动固定canonical Python子进程，并持有client
直到本次活动及全部实际后代结束。worker仍是原固定已登记非root角色，不扩public角色/命令/argv，
不把caller UID、文件、env/FD、descriptor Boolean或local receipt当成kernel observer证明。
observer只订阅本scope必要的fork/exec/exit notify事件，使用kernel audit token的PID+pidversion与
generation/lease nonce关联；不记录argv、env、文件内容、凭据、其他进程/项目数据或AUTH决策。
未知默认muting、subscription不足、seq/drop/queue overflow、未知事件/身份、client中断、
启动失败或重启一律quarantine并保留预算/objects/proof；不能以空队列或leader退出宣称全部后代结束。
真实事件顺序、loss证明、doublefork/setsid/reparent/短命后代/exec/PID复用与上限须I02实证，
source模型及mock只能验证解析/拒绝，不报告kernel/root PASS。

### private profile、签名和闭包绑定

Mac private resource profile新增 `verification-resource-profile/v2`，在原exact限额/模板字段上
仅加exact `observer`：`backend=endpoint-security-descendants/v1`、`minimum_macos_major=27`、
`bootstrap_sha256`、`required_entitlement=com.apple.developer.endpoint-security.client`。
它必须绑定相同closure的bootstrap实际hash、OS matrix和resource digest；字段或类型未知则拒绝。
public四keypolicy与registry `verification-resources/v1` 默认disabled/hosts=null保持，Linux原合同保持。
Mac v1 profile只供历史读取与纯数据兼容，不作为新的运行/注册能力；禁止自动迁移、清空或重pin R0。
grant/record仍使用现有v2的resource/toolchain/execution/lease digest绑定，不新增public批准接口。

实际observer能力只能来自kernel成功创建及冻结签名artifact，不能用entitlement plist存在、
证书字符串、codesign exit0、capability Boolean或未经accepted OS matrix的SDK常量替代。
EndpointSecurity/framework/loader/Blocks runtime、SDK和签名后artifact均进入原完整build/closure清单，
每critical仍需全闭包与同FD证明。source build可无署名、非root、重复构建并如实SOURCE_ONLY；
这类artifact不具备I01/I02 enable资格。源阶段不签名、不获取Apple资格、不读/创建签名私钥或账户。
未来I01需要独立exact卡接受外部operator提供的冻结签名artifact、source/compiler/SDK/link/unsigned到
signed hash对应、公开签名身份与required entitlement，不能在root下编译或自动签名。
未来I02需要独立exact卡接受该主机的真实client/事件完整性/隔离/资源及rollback；
无可接受签名来源则真实GAP，不新增Secret/账号，不改TCC/SIP或部署来绕过。

### exact source 与受控治理步骤

后续fresh T02只在原T05已映射的这些现有文件内实现该选择：
`codex/tools/verification-bootstrap.c`、`codex/tools/build-verification-bootstrap.sh`、
`codex/runtime/aisoft_host_access/toolchain.py`、`codex/runtime/aisoft_host_access/scratch.py`、
`codex/runtime/aisoft_host_access/verification_authority.py`、
`codex/runtime/tests/test_toolchain.py`、`codex/runtime/tests/test_scratch.py`、
`codex/runtime/tests/test_verification_authority.py`、
`codex/tests/test-verification-bootstrap.sh`；原installer/drift映射仅接受固定签名artifact的pin/惰性安装，
不得借此执行签名、申请entitlement、创建root registry/service/grant或更换SDK/解释器。
原33 source WIP与新loader/verification增量须按卡逐文件hash/mode保全，不混入治理commit。

T08独立步骤只修改本目录mapped summary/spec/plan三文件，检查语义映射、graph、exact diff，
仅在实际成功时投影T08 graph row与summary frontier为治理完成，独立本地原子commit后立即STOP。
不改AGENTS或其余14治理合同、verification、runtime/config/units；失败撤回exact三文档增量并保存证据。
后续fresh run重读批准/合同/owner/main/source/live Issue/installed后才进入上述T02 source。
未确认本卡前停于该新增安全边界；已完成T07/四行source提交不重问，原其它source合同保留。
所有完整闭包、source全回归、旧13方法16cases合法迁移、B01唯一manual PR和未来I01/I02门不放宽。


## T09 候选：Mac interpreter 的执行对象与 held FD 绑定

本节待负责人具体裁决，T08批准不覆盖本项。当前完整闭包/同FD调度门仍关闭；
下述路径执行方案只形成待审合同，不是已经安全、已实现或已验收的能力。
本机SDK未提供fexecve/execveat入口，普通用户的/dev/fd执行探针返回EACCES；
这些仅证明已检查入口/已测试路径，不能推断所有Mac同FD技术均不可能。
现有合同同时写canonical regular target与同FD证明，未明确解释器exec原语，
不可将路径稳定性检查自行当成同FD执行。本节只具体化这一个新增安全选择。

### 可选择的执行证明与剩余风险

负责人可保持原严格门并保留Mac TOOLCHAIN_CLOSURE_GAP；这不需重复批准T08，
也不等于T02完成。另一选择是明确接受本节的Mac限定方案：解释器通过固定canonical
regular路径exec，同一native supervisor保留原验收FD，并将kernel NOTIFY_EXEC目标
与held FD绑定；平台Python源码仍必须从同一已验收FD的bytes加载，不能重新从路径/pyc读取。
Linux原FD执行要求不变。该方案不是fexecve，不能声称内核从held executable FD取像。

路径exec可能先执行interpreter/loader初始化，NOTIFY_EXEC核对及seed阻塞不能追溯阻止
这段执行；ES的stat/signing字段也不证明所有代码页已验证。原root/OS管理员主动改写
不在非root攻击承诺内，但OS更新/管理员造成的真实漂移仍须拒绝后续活动，并报告可能
已启动解释器/loader，不能报告零执行。若负责人不接受此窗口，或完整冻结TCB、
immutable root目录/文件及其动态闭包无法独立成立，本方案不得实施或打开执行门。
本节不放宽root custody、全量hash/inventory、签名来源、accepted OS matrix或资源门。

### 放行前必须同时成立的条件

1. native预检完成原全闭包/冻结build与dependency/OS matrix语义，持有实际FD；
   interpreter为固定canonical regular文件，root所有、父链不可被非root改写，
   nlink/mode/size/hash及dev/inode/mtime/ctime在launch前全部复核。未知动态加载、
   alias/cache、snapshot immutability或文件替换均GAP，无PATH/未知shim/exec路径fallback。
2. 只使用T08已限定的真实es_new_descendants_client、签名artifact和fork/exec/exit通知。
   在子进程创建前建立client和完整subscription/无未知muting证明；将本次子进程实际
   audit PID+pidversion、native生成的generation/lease nonce与FD验收状态绑定。
   只取必要exec目标file stat与身份，不读/记录argv、env、文件内容、其它进程或AUTH数据。
3. 固定-ISB interpreter的compiled seed在任何平台模块导入前阻塞；native只通过自己
   创建的固定私有channel传递批准的FD表与bytes。channel不是public参数或caller FD，
   不接受caller PID/退出码/PASS/capability Boolean；关闭其它敏感继承FD，角色和注册UID不变。
   interpreter初始runtime/stdlib及loader仍属于先验冻结TCB，不能把seed当作main前全拦截。
4. native核对kernel EXEC target的实际对象身份、可用stat字段及前后held FD稳定性，
   对同一FD重hash；要求已知fork→exec身份转换、nonce与活动匹配。路径、身份、
   截断、字段/版本未知、重复exec、订阅/sequence gap、client中断或deadline耗尽均
   quarantine，不向seed发放行。只有这组证据与原grant/resource门全部有效才允许平台导入。
5. 放行后每critical活动仍重验全闭包、真实observer及对象绑定；发生loss/漂移即停止
   新活动并保留lease/budget/objects/proof，报告真实phase/possible_write。未知后代
   不以leader退出/empty queue/killpg认定完成，不自动detach/删除/重pin R0或再次publish。

上述条件的任一实现或真实能力缺口保持GAP；不能仅凭contract/model PASS放开当前无条件门。
I02必须在原每主机exact卡下实证canonical替换/修改、exec身份与PID复用、短命/reexec、
初始化窗口、seed前拒绝、late-import同FD bytes、loss/timeout/quarantine及资源保全。
源码阶段只做模型、unsigned/nonroot构建与拒绝测试，不调用实际ES或改变系统权限。

### exact源范围和治理STOP

本补充不增加source文件，仍仅使用T08表的9个现有文件；不新增public role/argv/API/schema字段，
private profile v2、public/registry默认关闭、Linux和既有B01/I01/I02卡边界保持。
确认若采用本方案，T09先独立只应用mapped summary/spec/plan三合同；校验/本地原子commit后STOP，
仅在实际成功时投影T09 row与summary frontier各一行。失败保存证据并只撤回本次三文档/index。
随后fresh T02重新读具体批准/合同/owner/main/source/live Issue/installed，先完整闭包与本节
对象绑定，再observer/resources/authority/FF、原installer-drift与旧回归。旧T01–T08历史不改。
这次确认不授权ES实际调用、签名/资格/Secret、安装/注册/服务/挂载、远端push/PR/merge或部署。


## T10 待裁决：新 main 文档基线与 R02 边界

本节仅为 private exact 卡的待审提案，T06/T08/T09 与旧 PASS 不授权新的 main 或整合。
本卡准备本身不修改本 worktree 合同、source、index、branch 或批准 pin，不执行 runtime。
保持 #327 / change/327-broker-ff-integration / manual / 原 owner session 与 worktree。
当前 H=2271843dba6e958953db3a2c30f53a3e9faa74a0；原获准 main 为
dc9aa468580f92a73dfa054c6f04ef5113f56694；broker 只读 fresh fetch 观察到
M=e2edb3e08194624a6647212571c6cc866298575b，common base 仍为原 main。
负责人若具体选择 B，只把这个 exact M 选为后续 source 基线目标并批准以下治理步骤；
不从 observation、live label、local approved 或历史 R01 receipt 推导 runtime/grant 授权。

### 独立治理的 exact 七文件

先同步四条原治理路径中的 main 文档更新：03-Issue-Spec-Plan与单闸门开发流程.md、
04-Agent编排与定时任务.md、08-双工具共存与实施.md、README.md；具体 before/candidate
bytes、patch、hash/mode 绑定 external 卡。前三文件只替换 main 已更新且唯一匹配的
非 #327 段落；README 保留 main 全部新内容并保留原 #327 一行治理摘要。
主线 #289 已实现/#334 更新、提交确认顺序、source/installed 分层和导航不得退回旧措辞。
其余 main 19路径在未来纯基线整合中继承，本步骤不修改 #334 文件或给其它 Issue 增硬依赖。
另只追加 mapped summary/spec/plan 的本段合同和 T10 frontier；verification 属33 WIP，不混提交。
AGENTS.md 与其余原治理路径、33 WIP、scope/AC-1～11、required CI、provider none/disabled/null、
public/private schema 与 T09 初始化窗口选择保持，不扩 runtime/source 文件清单。

应用前再核 actual H/M/branch/owner/index 与卡 SHA；任何漂移重新审阅，不自动采用更晚 main。
治理应用限 external exact7 proposal；resolver、semantic、graph、exact diff 与全保全实际通过后，
仅把 T10 row 与 summary T10 frontier 各一行投影完成，独立本地原子 commit G 后立即 STOP。
proposal/projected 两状态及全部14候选/patch SHA在卡固定；未发生的 G/hash/tree 保持 null。
失败保留 evidence，仅撤回本次七文档增量/七 index 项，不能覆写未知 bytes 或 reset 已提交历史。

### R02 的拟议形状与当前能力 GAP

T10完成也不自动执行 R02 或 fresh T02。本卡不授权实际 merge、merge-tree/commit-tree、
ref/index 更新、WIP parking/恢复或新 runtime。本节只给下一受控卡的约束，不新增执行入口。
如以后另有 exact 执行裁决，纯基线整合第一 parent 须为 actual G（或经另外明确核验的
本 Issue 线性末端 C），第二 parent 仅 exact M；tree 必须等于受控无冲突 merge 的独立重算。
无 actual G、preview/actual tree、qualified 固定执行程序/角色/hash，就保持 null/GAP。
只有既定外层 Controller maintenance 可构造该对象；Agent/provider 仍只作线性 commit，
不得改名冒充 Controller 或临时拼装 merge helper。已保留 R01 4cb627d9525611bff34387830978ba5c5785863e
仅是旧 pin 的 source-only 历史事实，不是新授权、protected checkpoint 或安装能力。
现有 installed broker 未提供 begin/verify，managed bootstrap 不存在，closure/observer/资源仍 GAP；
原 R01 脚本不是已登记 authority 程序，本卡不重跑或改写它。能力不足立即停，不先装 unmerged
代码、不启用服务/创建 grant、不新增 typed operation 或换身份绕行；不把 I01/I02 或 #333
人工操作造成本票准备 source PR 的 product hard dependency。

以后 R02 开始前必须另有 actual G 与全历史/WIP恢复包、登记且合格的固定角色程序证据和 exact卡。
完整已批准第一父链与 R01、T07四行修复、T08/T09 commit 必须保留为祖先；R0 不被重pin。
fresh R/ref 当前独立观察缺口，不推断 missing ref 或把 owner last_push=null 当 R0=null；
未来发表前仍须 canonical exact-ref 查重/真实 R0/R/adoption 与 broker 独立全 DAG/tree/delta 验收。
有冲突、多 base、对象缺失、driver/replace/graft/shallow 或 scope/来源漂移一律 STOP；
不往 integration tree 混入手工解决或33 WIP，不 endpoint 复制旧 owner 文档覆盖 main。
main 文档新23路径完整继承并按 blob/mode/hash 读回；本 Issue delta 与 WIP内容分别核验。

未来符合精确执行卡的 R02 后，source guard 仍原样保留，先实际核新 H 的 M 祖先与新字节/mode，
才 fresh T02 重读合同/Issue/installed 并继续原范围。实际 source 修复后重跑全 runtime discover、
默认 host locale smoke 与适用静态门，旧失败日志完整保留；定向80 PASS不替代完整回归。
完整closure、真实kernel/签名/installed仍 GAP；本卡无 ES/signing/资格/Secret/TCC/SIP/root、
registry/state/socket/grant/资源/安装/service/PAT/remote push/PR/merge/label/deploy 权限。
