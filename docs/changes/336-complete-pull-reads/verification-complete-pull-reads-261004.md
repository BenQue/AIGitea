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
updated: 2026-10-06
---

# #336 合同、源实现与本地验证记录

## 基线与范围

- 初始历史 HEAD / `main` / `origin/main`：`e2edb3e08194624a6647212571c6cc866298575b`；接收草案 HEAD：`992a47b324227b8af754aaa1a05346948f6d5722`；T01 governance HEAD=`3b44155ed58e43514020eccaa01f240f4c2c6db2`；T02 runtime Commit SHA=`4cf6af48463238a7f019f94da56a9e5b663aa666`，tree=`79971240660013fd91351b280b0d25b538510bb4`。
- Branch：`change/336-complete-pull-reads`；worktree：`/private/tmp/issue-336-complete-pull-reads`。
- 当前 owner session：`01a10c82-7f6b-7093-80d5-d389a18198c0`；原准备 owner `01a100d7-2f34-7932-923d-781f3f255e09` 已实际交回，takeover 前后保全，last push 仍为 null。
- 当前实际范围：T01 四角色治理固定与 #336 分类/approved 投影；T02 exact 三路径源实现；T03 本地验证和同目录结果投影。
- 环境：本机 source worktree；网络读取与投影使用既有 project-scoped typed broker。Issue/protection/lifecycle 使用 installed canonical 入口；分类工具使用已合并原基线的既有 broker（broker/CLI/parser bytes 与 installed 相同），未使用候选 runtime 自举。
- 本轮证明：fresh T02 源行为/失败拒绝、本地回归、冻结范围与 exact delta 恢复；T01/原型记录保留为历史。PR CI、merge、installed 与新协议 live readback 分别记录，未运行不作 PASS。

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

## T02/T03 fresh 源执行与本地验证（2026-10-06）

本轮在既有启动批准内执行，单写者、branch 与 worktree 均未改变。证据目录为 `/Users/benque/.codex/visualizations/2026/10/05/01a10c82-7f6b-7093-80d5-d389a18198c0/issue-336-t02-261006/`；最终文档提交后的 exact HEAD/tree、clean、scope、源 bytes 等价及所有日志 hash 记录在 `t02-t03-local-receipt.json`，避免文档自引用提交 SHA。

| Command / check | Result | Evidence |
|---|---|---|
| independent T01 predecessor / fresh owner+HEAD | PASS | 总调度独立 T01 readback SHA256=`4b5c701c4ee99cde2a6474d115d79aa32cba36c91d7d137c2d32562173dec7a4`；原 T01 HEAD/tree/four-doc/AC/protocol/STOP 检查均真，当前 claim push ledger 保持 null；`independent-t01-predecessor.json`、`fresh-start.json`、`claim-start.json` |
| installed canonical typed `git.fetch.main`、#336/#327 Issue read、protection read | PASS，四项 exit0 | fresh main=`c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`；#336 OPEN/approved/security/complex，#327 OPEN；required=`CI / verify (pull_request)`、main push/force=false、manual/admin；`fresh-host-read-results.json` 与原始 stdout/stderr |
| canonical Gitea pin/官方接口核验 | source PASS；本站版本及新协议 live NOT RUN | manifest/parser pin=`1.26.4`；Context7 后核 [官方 v1.26.4 pull.go](https://github.com/go-gitea/gitea/blob/v1.26.4/routers/api/v1/repo/pull.go) 和 [api.go](https://github.com/go-gitea/gitea/blob/v1.26.4/services/context/api.go)：state/sort/page/limit、total 与空列表行为；当前 typed catalog 没有 version read，本轮未扩展 operation、未绕 broker 验 live API |
| 原 patch/base/scope 预检及新实现 | PASS | 原补丁仅用作参考起点；`historical-patch-preflight.json`；PR 两扫描含空终页、严格 JSON/type、4 MiB 输入/2 MiB stdout、55 秒操作期限、禁止 redirect；#333 scoped namespace 有界读取、fetch head 与二次一致性；CLI 严格公开证明和实际 UTF-8 hash |
| `cd codex/runtime && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_host_access_complete_reads tests.test_host_access` | PASS，237 tests，exit0 | `affected-v4.stdout.log`、`affected-v4.stderr.log`；新夹具含 4950/100页正边界、各 state、short page、重复/raw headers、非有限 JSON/非法 UTF-8/类型、跨扫描类型变化、identity/第二扫描超时、恶意 receipt、transport framing 和真实本地子进程超限/kill |
| repo root `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -t codex/runtime -v` | PASS，1156 tests，exit0 | `runtime-root.stdout.log`、`runtime-root.stderr.log`；既有其他 Issue 测试未修改 |
| repo root 默认完整 `bash codex/tests/smoke.sh` | PASS，exit0，固定 T02 HEAD | `default-smoke-host.stdout.log`、`default-smoke-host.stderr.log`；同一默认命令经 host 解除隔离 loopback fixture 的 sandbox bind 限制，无 skip/bypass/换 pin；isolated installer fixtures/source checks 不代表安装端操作或验收 |
| frozen AST/目录/治理文件 + exact runtime scope | PASS | `_push_leased`、`_remote_change_heads`、`_validated_remote`、`_validated_project_worktree`、`_verify_identity`、普通 push blocks、原 default transport/runner 与 `_request_json` AST 相同；AGENTS、catalog/manifests/parser、Controller/CI/smoke/installer 无 diff；`runtime-static-validation.json` |
| exact 三路径 patch forward/reverse/forward | PASS，七步命令均 exit0 | `runtime-final.patch` SHA256=`d98ad88dcbebd34ceacddc6f883fa42eb934a4b238b53e17600785a27b6994c0`；`source-replay.json` 比较原基线/candidate/撤销/再次应用每一路 bytes/Git mode，新测试文件不存在→存在→不存在→存在；临时 detached 验证 worktree 最终逆向恢复 clean 并移除，没有新增 branch 或 writer |
| T02 本地原子 commit | PASS，exit0 | `runtime-commit.json`：parent=T01，head=`4cf6af48463238a7f019f94da56a9e5b663aa666`；只含三个 runtime 路径，提交后 clean；已提交 patch 与恢复验证 patch 逐字节相同 |
| current main ancestry/发布门 | GAP，exit1 | `git merge-base --is-ancestor origin/main HEAD`，main=`c9b5ef4e…` 不是 runtime HEAD 祖先；`release-ancestry-gap.json`；无 rebase/merge/force/push/PR，未借 #327 未合并实现 |
| 最终文档/分类/owner/static 核验 | exact 结果见 `final-static-validation.json` | 四角色映射、approved contract loader、frontier=T03、AC1–8/完整协议不变、exact seven-path scope、diff check、runtime bytes 与已验证 commit 相同；运行后保存真实 exit code/hash |
| 最终 PR CI / merge / installed 完整验收 / live / field | NOT RUN | 尚无最终 PR，没有 CI/merged pin；不使用候选代码操作 installed custody，无 PAT/Secret/service/VM/deploy/现场动作 |

### 调用失败与 smoke 重跑记录

- 第一次 affected 调用从错误 cwd 导入 `tests` 失败（尚未运行测试）；改为标准 runtime cwd 后原新源 217 项通过。新增测试后初次 CLI 夹具漏 `--state all`，以及注入页号超出六次实际调用，保留 `affected-v2`/`affected-v3`/`affected-final` 失败日志；改正夹具调用及注入位置并断言真实到达失败页，新回归 237 项真实通过，没有弱化拒绝规则。
- 第一次全量 runtime 从 `codex/runtime` cwd 运行，两个既有 company diagnostics 模块找不到 `codex`，1114 项/两次 import error；改用 smoke 的 repo-root 标准调用，全量 1156 项 exit0。没有修改范围外测试。
- 第一次默认 smoke 在运行过程中提交 T02，固定源身份硬门报 `source identity drifted during regression`（exit1）；原输出保留在 `default-smoke.*.log`。固定 runtime HEAD、工作区 clean 且不再改动后的 sandbox 完整重跑通过该源身份门，但随后本地 loopback fixture bind 被拒绝（PermissionError/exit1），日志保存在 `default-smoke-fixed-head.*.log`。同一已授权默认 smoke 经 host 重新完整运行，exit0，日志为 `default-smoke-host.*.log`。失败过程不被后续 PASS 删除或提升为安装证据。
- installer fixtures 对当前无 upstream branch 给出 `staleness unchecked` warning；这是测试/source provenance 的有限观察，不能证明完整安装或发布就绪，不借此改变 source pin、跳过门或调用未合并 installer。

## Acceptance criteria 结果

| AC | 结论 | 证据/未完成项 |
|---|---|---|
| AC-1～4 | source/local PASS；installed/live NOT RUN | 新源接口夹具、CLI bytes/receipt、完整扫描和 namespace 正/负例；真实安装的新协议读取仍须 merged pin 与独立安装批准 |
| AC-5 | source/local PASS | 冻结 AST/文件范围、237 项受影响回归、1156 项全量 runtime；无权限/catalog/其他 Issue 写入范围增量 |
| AC-6 | GAP | 新夹具/affected/full runtime/固定 runtime HEAD 默认完整 smoke PASS；映射/静态门真实结果见 final receipt；exact-head required PR CI 尚无 PR，NOT RUN |
| AC-7 | source/local PASS | 最终已提交三路径 patch 真实恢复，bytes/mode/new-file 状态全匹配；回退已合并变更仍须独立 revert/manual PR |
| AC-8 | source 独立范围 PASS；publication GAP | 不包含 #333 五路径或 #327 未合并代码；未改其它 owner/工作区/live labels；fresh main ancestry GAP、完整 remote uniqueness 未证明、merged pin/安装缺口卡未执行 |

## 遗留风险与未完成项

T02 实现与本地 commit 已完成。T03 本地 smoke、恢复与结果投影已推进；manual PR 审阅准备保留 GAP，不声明 `READY_FOR_REVIEW`。#327 合规整合/FF 能力、fresh 远端完整唯一性、最终 exact Issue/branch/manual/head/body 的确认和 required CI 是后续独立 gate；本轮没有发布尝试，不混装或借用未合并 broker 自举。

公开 review 草案及最终状态见同证据目录的 `manual-pr-review-card.md`，它不是发布授权。观察的 main、T02 runtime HEAD、最终文档 HEAD、patch/log hashes 各自固定；文档投影之后仅作静态核验与源 bytes 等价校验，不将旧 prototype、安装 fixture 或本地 PASS 提升为 CI/installed/live。尚无真实 merged pin，未来 installed 操作仍须另备全变更字节/provenance/compatibility/权限与上一版本回退卡，并获得独立批准。

## Mac FF 完成后的 fresh 核对与独立范围投影（2026-10-06）

证据目录：`/Users/benque/.codex/visualizations/2026/10/05/01a10c82-7f6b-7093-80d5-d389a18198c0/issue-336-post-install-261006/`。实际提交后的 HEAD/tree/scope/owner/runtime 等价与 STOP 结果保留在 `scope-projection-receipt.json`，不在本文形成自引用提交 SHA。

| 检查 | 结果与边界 |
|---|---|
| Mac #327 / PR #346 完整安装/恢复/再安装/幂等 | PASS；固定 merge `1a86a0037ee76f462eac52dc7dc08d3d3fbd2ed4`；原回执 `execution-acceptance-receipt.json` SHA256=`d563a7c858c04d9742dbd807483db885fe9a566031c822f008f8f32f5f0916ae`，不重跑或改写原回执 |
| fresh owner/branch/HEAD 与 installed qualification | PASS；原 HEAD=`2eb10ea18f0b6548bc60f44af1f8a1be88d0966f`、单写者精确匹配；稳定 M runtime 与实际 installed 核心 qualification 一致，`fresh-start.json` |
| canonical `git.fetch.main` / #336 Issue read | PASS；fresh main=M，Issue OPEN/approved/security/complex；没有 remote write |
| canonical `git.fetch.change` #336 | PASS，exit0；`remote_known=true`、`remote_head=null`，原 stdout/stderr 保留；只证明此次 typed namespace 观测，不代替完整 PR 集合唯一性 |
| 投影前 committed scope | GAP：`SCOPE_UNKNOWN`，spec 缺 `git_scope`；本轮只投影已批准七路径，不扩大范围或放宽历史门 |
| 隔离投影后的 scope/history 门 | PASS，预演私有 clone；`scope-and-compatibility-preview.json`，不代表实际 owner commit 或 main 整合 |
| 隔离旧源 / v2 兼容源 merge-tree | 两者均 `MERGE_CONFLICT`；原始失败保留；actual runtime 未改，真实整合 NOT RUN |
| 本轮文档门 / 精确本地文档提交 / STOP | 结果见 `scope-projection-receipt.json`；仅四映射文档，无 runtime/AGENTS/Controller/installer 修改；提交后独立 STOP |
| #336 最终候选回归/smoke/恢复/PR CI/installed 新协议 | NOT RUN；旧源及私人 v2 回归结果不能提升为最终 integrated 候选证据 |

Mac 安装已完成，旧“未合并 #327 / 本机安装缺口”的门只作历史记录；现有未完成项是 #336 三路径兼容与合规 main 整合、最终候选验证、完整远端唯一性、唯一 manual PR 确认及 CI。AC 和分类不变；不改其他 Issue 的 worktree、owner、live 标签、安装或凭据。

## 2026-10-06 fresh T03 真实修复、整合与最终本地验证

本节为当前候选结果，更新此前 STOP/merge conflict 与本机安装缺口的历史状态；既有合同及其 AC 不变。证据目录：`/Users/benque/.codex/visualizations/2026/10/05/01a10c82-7f6b-7093-80d5-d389a18198c0/issue-336-t03-fresh-runtime-261006/`。

| Command / gate | 真实结果 | 证据与边界 |
|---|---|---|
| fresh owner/contract/scope/qualification + canonical main/Issue/protection/namespace | PASS | 独立 predecessor HEAD=`7f9108dc3fc1c70d863830ee632c3ba8b2b3e45d`；固定 M 的实际 installed qualification；`fresh-start.json`、四项 `*-host` 原始输出 |
| 隔离新兼容候选 + scope/history/merge-tree | PASS_NO_CONFLICT | `clean-integration-preview.json`；旧两项冲突日志仍保留，未用手工 conflict resolution 绕门 |
| 两路径线性兼容修复 local commit | PASS | `fb47f37b20d578ba4c88036b9d6810f3bbd66fcc`；原测试路径当时字节不变；`actual-repair-commit.json` |
| qualified fixed M `LocalGit.integrate_main()` | PASS | 实际 commit=`44c4651e3bb44d69a09a160b4ade94fa4aac25cf`，parents=[repair tip,M]、tree=`44ecc514176a3fb59b9c08d9af146cb616d61e06` 与独立 merge-tree 相同，history gate PASS；`actual-main-integration.json` |
| 原第三路径新增拒绝门/Git 环境回归并本地提交 | PASS | runtime HEAD=`db40d4e3ee14313dd45e25201a1ffdf1ff9e8a21`；`gate-test-commit.json`，原源码/安全合同未扩大 |
| 最终 runtime HEAD 的新夹具与受影响五 suites | PASS，347 tests，exit0 | repo-root `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=codex/runtime python3 -m unittest -v codex.runtime.tests.test_host_access_complete_reads codex.runtime.tests.test_host_access codex.runtime.tests.test_main_integration codex.runtime.tests.test_controller codex.runtime.tests.test_worktree_owner`，实际 Python3.14，`affected-final.*.log` |
| 最终固定 clean runtime HEAD 默认完整 `bash codex/tests/smoke.sh` | PASS，exit0；全量 runtime 1228 tests | `default-smoke.*.log` 与 `final-runtime-validation.json`；无 skip/bypass/运行中 commit，isolated installer/release fixtures 不代表实际安装/公司执行 |
| final exact 三路径 patch 真实 forward/reverse/forward | PASS，七步 exit0 | `runtime-final.patch` SHA256=`ed1a5ea97363ed22862333e16ad0344d9c2155b1faafe0c7b08ae09eebdfb6b0`；`source-replay.json`，bytes/mode/new-file 状态每轮匹配，末次 reverse 恢复 M clean baseline |
| 冻结 AST、scope、classification | PASS | `runtime-static-validation.json`；M 的完整 `_git`、`_remote_change_heads`、`_validated_remote`、`_validated_project_worktree`、`_verify_identity`、`_change_tip`、`_read_main_head`、`_request_json`、`_run` AST 相同，全部既有顶层 broker functions 不变；分类 exact --verify 为 projected/security/complex |
| 两次 canonical installed M open PR/namespace 唯一性 | PASS | 均显式空 page1、server open_pr_counter=0、#336 remote_known=true/remote_head=null；`final-namespace-open-pr-uniqueness.json`；仅此观测窗口，不冒充新 v1 receipt 能力 |
| 既有 Mac M 安装保全 | PASS | 28目标 bytes/mode/root:wheel 与 fixed M 安装回执一致，生成的 source receipt JSON 也完全一致；`installed-M-preservation.json`；#336 仍未安装 |
| 结果文档投影后的 final HEAD / source 等价 / clean / owner / scope | 真实结果见 final-candidate-receipt.json | 仅 summary/plan/verification 更新；spec/AC/protocol/git_scope 不变，static 门与完整最终历史门重跑 |
| push / 最终 PR / required PR CI / #336 installed/live / Secret / 服务 / VM / 部署 | NOT RUN | 最终 PR 必须取得绑定 exact #336/branch/manual 的确认；merge 仍由人完成，安装/部署独立授权 |

### 本轮失败及修正记录

首次 canonical main sandbox 读取 exit20/TRANSPORT_ERROR，不代表 main/namespace absence；原 `main.stdout.json`、`main.stderr.json` 保留，同一 typed read 经 host exit0。本轮代码应用后断言误期待三文件均 dirty，实际测试文件与既有 bytes 相同，两个源文件 dirty；保留实际状态并由 Controller 只提交精确两路径，不额外改测试制造差异。

新增环境夹具首次 1 PASS/1 FAIL，原假设只有3个 credential config；fixed M 实际先加入9个 Git 安全配置，共12项。夹具改为断言安全配置、固定 helper 顺序和 caller override 被删除，生产安全配置未减弱；最终新增2项及完整347项均 PASS。Mac 保全检查首次对 generated target 查静态 sha256 导致 KeyError，改用原固定回执 digest 与 expected JSON 验证，全28项 PASS，未写 installed 文件。原失败输出及状态说明均保留，不写成首次通过。

### 当前 AC 与交付状态

AC-1～5、AC-7 为最终 source/local PASS；AC-6 的全部本地门 PASS，最终 exact-head required PR CI 仍 NOT RUN；AC-8 的范围、已合并/已安装 bootstrap 能力、合法整合和当前唯一性准备 PASS，源 merged pin 及新协议 installed/live 在后续层记录。本轮已具备唯一最终 manual PR 的本地审阅候选，待提交确认；不声明 READY_FOR_REVIEW、CI/merge 或 #336 installed PASS。
