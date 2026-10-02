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
updated: 2026-10-02
---

# #316 证据记录

## 基线与范围

- 本票固定 base：5c2cd726c9aeaee9d17541d8feb049e33881bbac；T01 仅治理文档，本地 commit SHA 由会话 handoff 与 Issue 回执记录，避免文档自引用 SHA。runtime 尚未实施。
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
| source/helper 实现、先红后绿、Go/Python/bash/smoke、PR CI | NOT RUN | 目前只是合同准备，无新实现 |
| #316 helper 安装 / operator grant / PAT 轮换 / audit / no-op 演练 | NOT RUN | 独立 live/Secret 授权尚不存在；scope 修复代码安装不证明真实 PAT 已改变 |

## T02 本地实现与隔离验证（2026-10-02 fresh turn）

已重新读取本票 AGENTS、README、03/06、批准的 spec/plan，再进入 T02。新增内容仅在 `codex/tools/gitea-pat-helper/`，没有执行安装或读取现场 config/DB/Secret。

| Check | Result | Evidence |
|---|---|---|
| Go 1.26.3 官方工具链摘要 | PASS | 本票隔离临时目录；darwin-arm64 SHA-256=875cf54a15311eee2c99b9dd67c68c4a49351d489ab622bf2cfd28c8f2078d3c；最初下载得到重定向 HTML，摘要失败后未解包，跟随官方重定向重下载才通过；未全局安装 |
| 固定 Gitea module/model | PASS | code.gitea.io/gitea v1.26.4；module sum=h1:VDA00oYg16VrQf3sES0NuS/oiDLAIVng/7jKHsBMP/w=；token model SHA-256=dcf0e3fd325fe98e91d8a2e216aedbaf08fed20625748bbbdf03f090fc1728cd；go.mod/go.sum 固定，build.py 核验无替换、model bytes 与 go mod verify |
| helper 核心 suite 先红后绿 | PASS | 待实现桩时 TestExactRevokeAndFreshReadback（当时名为 CacheReadback）、Inspect、SecretErrors 三个测试 FAIL/NOT_IMPLEMENTED；实现后固定工具链 go test -mod=readonly -tags sqlite,sqlite_unlock_notify ./... PASS；临时 SQLite、上游 auth/user/db models，无现场 Secret |
| 失败/隔离负向矩阵 | PASS | 错账号、未知 token、admin、org、inactive、版本、ID/UID/name/project/kind、歧义 salted hash 全部零删除；其它 PAT 与其它账号保留；真实 SQLite trigger 删除失败回滚、driver error 输出固定错误码，synthetic canary 不泄露 |
| 请求与 manifest/build binding | PASS | 拒绝重复/未知字段、多文档、null、超长 stdin、任意 username/SQL；canonical 两份 manifest 四种身份可解析；未知 project/kind/无 routine binding 拒绝；module replacement/toolchain mismatch 拒绝 |
| Go race suite | PASS | 固定工具链 go test -mod=readonly -race -tags sqlite,sqlite_unlock_notify ./...；无 race 报告；不代表现场并发交易已验收 |
| Mac 本地固定 build + provenance | PASS（darwin/arm64） | build.py 重跑 suite 并构建，binary SHA-256=3e72dfe4bbae9f68134062a2840cbef442ee9640bc62af368eb112a5eb4d3708；临时目录保存 source hashes、dirty 状态、Go build info；非 Linux release/installed 证据 |
| Mac binary 公开元数据与拒绝行为 | PASS | --version 返回 helper=1、model=1.26.4、toolchain=go1.26.3；普通运行先返回 HOST_UNSUPPORTED/exit 2，stderr 为空，未读取 config/DB/Secret |
| T02 双轴代码审查 | PENDING | 本地 commit 后按 implement/code-review 技能审查 Standards 与本票 T02 spec；T03/T04 尚未实施不能作为本阶段缺失实现的完成证据 |
| Linux binary/CI、typed grant/交易工具、安装/live | NOT RUN | 留在 T03/T04/T05，当前不声称整体 Issue 已完成 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 轮换工具与新测试未实施 |
| AC-2 | NOT RUN | 未授权且未执行真实 Secret 操作 |
| AC-3 | T01 文档部分完成，T04 最终复核待执行 | 03 已加入 scope 合同变化必须轮换、operator 权限和阶段边界；06 已加入轮换列、Secret/恢复合同；mapped documents/真实分类读回在 T01 复核，整体验收仍需 T04 |
| AC-4 | 本地隔离 DB suite PASS；阶段审查待完成 | fixed v1.26.4 helper 使用真实 models 覆盖精确删除/拒绝/脱敏；Linux release 与现场安装不在该 PASS 范围 |
| AC-5 | NOT RUN | transaction/failure/resume suite 尚未实施 |
| AC-6 | NOT RUN | operator-only typed 新路径尚未实施 |
| AC-7 | NOT RUN | 新 source/local/CI gates 均未执行 |

## 遗留风险与未完成项

两台 #313 installed 前置已解除，depends_on 仍保留 313，不能把批次集成排序写为产品依赖。新本地撤销 helper/operator 路线已获用户合同确认；现有 rollback 的假 self-revoke 不作真实证明。本轮 T01 只做治理合同并停止；下一 fresh turn 重读后才能 runtime。PR 提交 manual、人合并、未来安装、grant provision、live PAT 轮换均有各自明确边界。只完成 source merge 而 AC-2 未验收时不声称 #316 已真正解决，不归档本聊天。
