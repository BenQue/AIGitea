# 服务账号 PAT 轮换：源码执行卡（#316）

本卡说明 T03 源码的受控入口，不是现场已执行回执。helper 安装、grant provision、真实轮换和 audit/no-op 仍为 NOT RUN；各项须有独立 exact 授权，不能由方案 A 或源码批准推断。

## 固定入口与身份

公开 typed operation 为 `gitea.credential.rotate(issue, sha, token_kind)`，另带 broker 的 manifest project。独立 `CredentialRotationRunner` 不连接 provider/project/普通 Git runner。Mac 必须由独立提升的 root operator 调用，普通用户直接拒绝；不修改 sudoers、不新增 provider 权限。operator 工具仅接受 `--project`、`--issue`、`--sha`、`--token-kind` 四个唯一字段，不接受 token、URL、路径、SQL、shell 或 force。

Mac store 固定为 `/Users/benque/Library/Application Support/AISoftPlatform/credentials`，owner 为 benque。目录 0700、文件 0600，legacy 只读文件可读 0400；交易在同一 store/文件系统，逐级 descriptor-relative no-follow，拒绝 symlink、hardlink、错误 owner/mode。旧/候选 PAT 只在保护区与内部管道，不进入公开回执/argv/日志。既有 VM 副本不更新、不清理；撤旧后不能继续消费旧副本。

固定 VM 是 gitea-ci；CLI/helper 以现有 git service user 运行。Mac root 经已有 benque OrbStack 会话发送有界 stdin JSON。VM 在任何 Gitea/helper 命令前验证独立 operator capability；公开 tuple、VM grant 的摘要或相同 git UID 不能代替授权。两端私有入口仅接受匿名 OS pipe：Linux 核对 FIFO 与 `/proc/self/fd` 的 exact pipe inode；Darwin 核对 FIFO、device/link count 为零；TTY、普通文件、具名 FIFO（含 unlink 后）拒绝，输出 Secret 前复核。Gitea 固定为 1.26.4、Go helper 固定为 go1.26.3 的对应 Linux 制品。缺安装来源或 grant 时零签发/撤销，不使用其它身份 fallback。

## 独立现场授权前须形成的具体卡片

记录 Issue/source SHA、项目、token kind、canonical store、VM exact helper、制品摘要、操作窗口、原 creation Issue 及 ownership evidence 是否齐全。原 marker 内容不改、不补建；缺失拒绝。负责人若已手工轮换首个对象 `newemaint-routine-merger`，先明确专用对象，不能自动创建账号。

Mac 与 VM 都须有 root-owned `credential-rotation-source.json`，安装器记录 exact source SHA、merged-main 证据、关键安装字节摘要与 helper 制品 pin。只有 clean source HEAD 已在 origin/main 的 ancestry 中，且当前安装字节一致，才接受该来源。VM installer 的独立 helper 安装参数是 `--pat-helper-artifact <Linux binary>`，旁边必须有固定 build.py 生成的 `.provenance.json`；校验失败在任何安装写入前拒绝。未提供制品时保持普通 broker 安装能力，轮换 fail closed。该参数不是本卡的安装授权。

grant 固定于 `/usr/local/etc/aisoft/credential-rotation-grants/<project>-<token-kind>.json`，不从环境或参数选取。Mac 目录 root/0700、文件 root/0600；VM 目录 root:git/0750、文件 root:git/0640，仅现有 service user 可读。两份都必须由独立 operator provision；安装器不创建 grant。JSON schema 精确包含：

```text
version=1, operator_uid=0, issue, source_sha, project_id, token_kind,
credential_root, helper_path, not_before, expires_at, creation_issue,
Mac only: operator_capability
VM only: operator_capability_sha256
```

时间是 UTC epoch 整数，窗口必须当前有效；`creation_issue` 绑定既有 account/token/password-policy marker，而不是新 rotation Issue。授权不包含 PAT。每个 exact 授权另用 CSPRNG 生成 256-bit capability，编码为 64 位 lowercase hex，原文仅存于 Mac root grant。VM 只存该 ASCII 字符串的 SHA-256 lowercase hex，不存原文；两端 strict schema 不允许互换字段。安装器不生成或 provision capability/grant。本卡不提供真实生成命令或授权。

capability 是窗口内 bearer 授权，不是单次调用能力；它仅在 root 与批准的固定 transport/service process 内存及私有管道中传递，不进入 argv/env、公开 stdout/stderr、journal、provenance、审计或回执。VM 用固定长度 constant-time 摘要比较；普通 benque/Agent 直接复用 `orb -u git` 入口而无 capability 时零命令/零 Secret 返回。它不提供针对已控制 VM root/Gitea service process 的 OS 隔离。授权替换时使用新的独立 capability，旧值不再匹配。一个 exact Issue/source/project/kind 请求完成后重试为 no-op；新轮换必须另有不同的已授权请求，保留上次完成 provenance，不能 force。

## 恢复与验收

先验证授权、版本、owned markers 与旧 exact token，再隔离旧 canonical，保存候选并验证 identity/scopes，撤旧并保存确认，最后原子发布。撤旧前 scope 验证失败时精确补偿候选；仅旧 PAT 仍有效且符合当前 scope policy 才恢复旧 canonical。撤旧后写入失败使用已保存候选继续，不再签发。

若 CLI 可能已签发但 raw 候选丢失，或 DB 撤销已经发生但 durable journal 未确认，保留 journal/隔离并报失败，不盲目重签、不凭 token-unknown 推断 exact ID 已消失；由负责人单独决定修复。source revert/previous 安装文件不能恢复已撤销 PAT。

现场必须保存脱敏回执：旧 PAT 新请求 401、新 identity 为 exact non-admin、scope 集合精确相等、Mac typed audit 非 BLOCKED、第二次同请求 no-op。Mac PASS 不代表既有 VM profile/所有消费端通过。任何未执行项仍写 NOT RUN。

隔离源码验证入口：`bash codex/tests/test-rotate-gitea-service-account.sh` 和 Python `test_credential_rotation.py`；shell fixture 仅替代隔离安装 runtime/外部 Gitea，使用真实临时文件系统与 synthetic PAT，不替代真实 helper 或 installed/live 验收。
