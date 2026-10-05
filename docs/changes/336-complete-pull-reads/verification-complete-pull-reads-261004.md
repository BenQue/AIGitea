---
issue: 336
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/336
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - security
  - shared-core
  - platform-governance
depends_on: []
status: in-progress
branch: change/336-complete-pull-reads
created: 2026-10-04
updated: 2026-10-05
---

# #336 合同准备与 T01 治理固定验证记录

## 基线与范围

- 初始历史 HEAD / `main` / `origin/main`：`e2edb3e08194624a6647212571c6cc866298575b`；接收草案 HEAD：`992a47b324227b8af754aaa1a05346948f6d5722`；runtime 候选 Commit SHA：尚无。
- Branch：`change/336-complete-pull-reads`；worktree：`/private/tmp/issue-336-complete-pull-reads`。
- 当前 owner session：`01a10c82-7f6b-7093-80d5-d389a18198c0`；原准备 owner `01a100d7-2f34-7932-923d-781f3f255e09` 已实际交回，takeover 前后保全，last push 仍为 null。
- 当前实际范围：本目录四角色治理固定及本票分类/approved 投影；未应用三路径代码补丁。
- 环境：本机 docs-only worktree；网络读取与投影使用既有 project-scoped typed broker。Issue/protection/lifecycle 使用 installed canonical 入口；分类工具使用已合并原基线的既有 broker（broker/CLI/parser bytes 与 installed 相同），未使用候选 runtime 自举。
- 本阶段负责证明：独立立案的历史记录、正式接收与 T01 治理固定；AC-1～8 的最终源行为验收尚未开始。

## 历史合同准备执行结果（2026-10-04）

| Command / check | Result | Evidence |
|---|---|---|
| typed `gitea.issue.list --state open` 立案查重 | PASS，实际 host read | 创建前 #327/#333；sandbox `TRANSPORT_ERROR` 保留，不能解释成未发现 Issue |
| typed `git.fetch.main` 与 main 读回 | PASS | private intake `main-host.stdout.json`；source base=`e2edb3e08194624a6647212571c6cc866298575b` |
| typed `gitea.protection.read` | PASS | required=`CI / verify (pull_request)`、push=false、force=false、merge whitelist=`admin`、admin override block=true；原输出保留 |
| typed `gitea.issue.create`，随后 `gitea.issue.read --number 336` | PASS | 实际 #336 OPEN，title/body/request marker/URL/入口标签匹配；body SHA256=`d40875cb8666a00d2ee039033812fbe86e9789df77633856156e2b20d1b93df7` |
| `git worktree add -b change/336-complete-pull-reads … e2edb3e…` | PASS | 隔离 worktree 从 exact 基线创建；未移动 main |
| `aisoft_loop.cli claim-worktree`，exact branch/worktree/session | PASS | owner result=`created`；无 takeover，last_push_head=null |
| `aisoft_loop.cli resolve-documents 336` / `resolve-required-documents 336` | PASS，exit0 | 四角色完整映射，exact Issue/slug/日期一致；`contract-validation.json` 与两个原始输出 |
| `Classification.from_yaml`、front matter 一致性、ticket graph、owner 核验 | PASS | `complex` / `summary,spec,plan,verification`；owner SHA256=`854c749e3e2a6e137d4d442fb7809efd81dc5da8956a2e973870ceaa1d72e5ef` |
| `aisoft_loop.cli check-change-documents --repo … --porcelain` | PASS，exit0 | `change-documents` / `change-pr-url` 两项均 PASS；扫描包括新目录的全部 change 目录 |
| `git diff --check` / `git diff --cached --check` | PASS，exit0 | staged scope 恰为四份草案；全部156个 change 目录通过，原基线155个；`staged-document-validation.json` |
| 审阅补丁 hash / exact 三路径 / `git apply --check --whitespace=error-all` | PASS，exit0 | hash 与固定补丁相同；只检查，不应用；broker/CLI 仍为基线 bytes，新增测试不存在 |
| #336 runtime unit / 完整默认 smoke / 最终 PR CI | NOT RUN | 当前未启动 runtime、未创建最终 PR |
| installed / field / PAT / service / VM | NOT RUN | 超出本次立案及合同准备授权 |

立案及当前 private readback：`/private/tmp/complete-pull-reads-intake-261004/`。该目录中的公开元数据/脱敏 receipt 不含 Secret；保留 sandbox/host 两种执行路径证据及 creation 的唯一 request marker。原始输出是本机 evidence，不是跨环境验收。

文档核验首次调用漏设 `PYTHONPATH`，在导入时失败（`ModuleNotFoundError: No module named 'aisoft_loop'`），尚未运行检查。原失败记于 `contract-validation-first-attempt.txt`；改为 `PYTHONPATH=codex/runtime python3 …/validate-contract.py` 后真实检查通过。该调用环境错误不计作 runtime 或 AC 测试。

三个路径的原补丁、独立原型日志/receipt、恢复记录和旧 compatibility GAP 已另外复制至 `/private/tmp/complete-pull-reads-intake-261004/reader-review/`，以 `provenance.json` 记录逐文件 SHA256 与原路径。副本仍为历史审阅材料；原包没有改写，#333 五路径调用方补丁没有混入新副本或本分支。

### 历史原型证据

| 对象 | 历史结果 | 限制 |
|---|---|---|
| `reader-capability-source.patch` | SHA256=`11ab13f03770725e74d75fafc2de4572b484ef3480e7f6b8bae57f441f5cd2a2`；只有三个代码路径 | 未应用至 #336，未来 diff 需 fresh 固定 |
| 独立读取原型 + main M | 217 tests / exit0 PASS | `independent-reader-main-regression.json` 与 log；私人副本，非 #336 新源候选 |
| 读取 + #333 调用方组合原型 | 330 tests / exit0 PASS | `prototype-affected-regression-final.log`；含范围外五路径，不纳入本票实现 |
| 源恢复原型 | forward/reverse/forward PASS | `reader-source-replay.json`；最终 #336 delta 仍需重新验证 |
| installed public compatibility | GAP | `public-installed-contract-compatibility.json`：parser 缺 `credential_rotation_policy`；source38/installed36 来自原审阅观测，非本轮 live 刷新 |

历史包：`/private/tmp/issue-333-pat-rotation-acceptance/T14-readiness-proposal-261004/`；manifest SHA256=`24481550f17f3efaf52602c35c8f6790e8e8c4d85490212b31eab04f35b4293d`。初次失败/错误日志、当时八文件快照与回放 mode 问题记录均保留；不因最终原型 PASS 删除失败过程。`validation-final.log` 的 stale negative `cat-file` 汇总值已在原包 `validation-completion.json` 解释，实际测试 exit0 以独立 receipt/log 为准。

## T01 正式接收与治理固定（2026-10-05）

本轮批准来自总调度 `01a0fc77-cef9-7442-9bf9-7f6799268198` 的直接用户决定与本接收会话派发。它覆盖既有合同启动与后续本地 Loop；本轮独立 STOP，runtime 在后续 fresh turn 才开始。旧四文档“待确认”不代表本次批准缺失。

接收证据目录：`/Users/benque/.codex/visualizations/2026/10/05/01a10c82-7f6b-7093-80d5-d389a18198c0/issue-336-t01/`。原 handback、交接核验与 claim 前后原始 bytes 均保留；最终 commit/head/tree/scope 与 STOP 回执记录在同目录 `t01-receipt.json`，不在四文档内形成自引用 SHA。

| Command / check | Result | Evidence |
|---|---|---|
| 接收 HEAD/branch/index/工作区与 handback 对照 | PASS | HEAD=`992a47b324227b8af754aaa1a05346948f6d5722`，tree=`b8a0095ed8426db9dad1d8076de936d0035e8504`；index/工作区 clean；`intake-before-takeover.json` |
| 交接 archive SHA256、保存包逐文件 bytes 与原 claim 核验 | PASS | archive=`10f3c2acc64bad7cb745cb9441f9af46994d9e10a133455db79beb949c3bdb18`，62个文件与保存包逐字节相同；claim=`854c749e3e2a6e137d4d442fb7809efd81dc5da8956a2e973870ceaa1d72e5ef` |
| 原 owner 实际 handback 后既有 `claim-worktree --takeover` | PASS，host exit0 | result=`taken-over`；当前真实 session 与 exact tuple 匹配；原 created/push ledger 保留，`claim-before.json`、`claim-after.json` |
| installed typed #336 Issue/comments/main protection/#327 read | PASS，四项 host exit0 | #336 OPEN、评论为空；required=`CI / verify (pull_request)`、push/force=false、merge whitelist=`admin`、block_admin_merge_override=true；#327 OPEN；`host-read-results.json` |
| 当前本地 main/origin/main 观察 | 只读事实 | 均为 `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`；无 fetch/rebase/merge，不以缓存推导远端当前 head 或 #327 已发布 |
| Mac public installed/source bytes 与字段观察 | 有限字节一致 | source38/installed38、`credential_rotation_policy` 存在，access manifest/broker/CLI/contract 与当前 main source bytes 相同；原 #336 manifest bytes 不同；`public-installed-byte-observation.json` |
| 四角色映射/分类/单写者/冻结范围、静态门 | PASS，exit0 | `validate-t01.py`、两个 resolver、`check-change-documents` 与 diff/cached-diff check；真实 readback 的 approved 合同通过 `load_contract`，frontier=T02，未启动 Controller/provider；AC-1～8及完整协议段与草案相同，base/draft diff 恰为四文档，runtime/AGENTS/Controller/CI/installer 无变化；`t01-static-validation.json` |
| #336 分类/approved typed 投影及读回 | PASS，apply/readback 均 exit0 | 既有 `apply-classification-labels.sh --repo … --apply 336` 从 mapped summary 投影 type/security、complexity/complex；installed `gitea.issue.labels.set --number 336 --lifecycle approved`；独立 `--verify 336` 为 projected；Issue 读回 OPEN，labels=[approved,complexity/complex,triage/needs-triage,type/security]；`projection-readback-results.json` |
| T01 本地治理 commit / STOP | exact 状态见 `t01-receipt.json` | 仅提交本目录四文档；记录实际 HEAD/tree、clean 状态与 STOP 边界；不执行 T02，不发 push/PR |

接收初次误用 `git write-tree` 被 sandbox 拒绝 index.lock（exit128），未更改 index/HEAD，随后改为只读 `git ls-files --stage` 完成证据核验。takeover 首次 sandbox 写 marker 被拒绝（exit2），原 marker 不变；同一已授权 takeover 经 host 执行成功。#336 首次 sandbox typed read 为 `TRANSPORT_ERROR`（exit20），同一 installed typed read 经 host 成功。投影前 `--verify 336` 为 projection-missing（exit1），投影后独立读回为 projected（exit0）。首次失败输出保留，不解释为对象不存在或能力已发布。

上述公共字节观察把旧 installed36/缺字段记录标为历史；完整安装 provenance、权限、全部文件、VM 和现场验收仍为 NOT RUN，不宣称整包 installed PASS。仅有一个 exact 本地 #336 branch/worktree；远端完整 branch/PR absence 或唯一性本轮没有证明，last_push=null 也不能替代该证明。

## Acceptance criteria 结果

| AC | 结论 | 证据/待执行项 |
|---|---|---|
| AC-1～4 | NOT RUN | 合同/启动已批准；T01 后 fresh turn 实现，随后执行新源夹具/回归；真实 typed 读取另记 installed 层 |
| AC-5 | NOT RUN | 冻结范围已写入 spec；最终代码/AST/operation/既有回归尚未执行 |
| AC-6 | NOT RUN | 不把草案文档检查或原型 217/330 提升为默认 smoke/PR CI |
| AC-7 | NOT RUN | 原型恢复 PASS 不能替代最终 exact delta 恢复证明 |
| AC-8 | NOT RUN | 当前仅完成合同边界声明；最终独立源交付、merged pin和安装缺口说明尚无 |

## 遗留风险与未完成项

合同/启动已批准，runtime 尚未启动，T01 本地治理 commit 后必须 STOP。#327 合规发布能力与完整安装验收仍须在相应阶段 fresh 核验；本地三路径垂直切片准备不因此空等，不增加跨票产品依赖。本票不更改其他 owner、工作区或 live 状态。安装端、现场和 Secret 动作没有授权，不通过混装/宽身份 fallback 解阻。

最终验证必须补齐每个 AC 的真实命令、exit code、exact head/tree/base与 evidence hash；未执行项保留 NOT RUN。本变更未部署，按模板删除部署验收章节。
