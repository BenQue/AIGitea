---
issue: 288
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/288
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - platform-governance
depends_on: []
status: pending
branch: change/288-dockerfile-digest
created: 2026-10-02
updated: 2026-10-02
---

# #288 验证记录

## 基线与范围

- Baseline `origin/main` / worktree HEAD：`5c2cd726c9aeaee9d17541d8feb049e33881bbac`。
- 日期：2026-10-02（Asia/Shanghai）；校验探针使用 `--today 2026-10-02`。
- Worktree：`/private/tmp/issue-288-dockerfile-digest`。
- Owner session：`01a0fc7b-f327-7a93-a48c-a254937cb08d`，claim 返回 `created`。
- 基线与治理步骤为历史 receipt；当前 T02 已实现，T03 尚未完成。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker `gitea.issue.read` / `gitea.issue.comments.read` #288 | PASS | open，needs-analysis，1 条旧调度评论；无 approved 合同 |
| broker `gitea.pulls.read --state open` | PASS | 空列表，无重复 PR |
| broker `git.fetch.main` | PASS | project aisoft-platform、origin、上述 exact baseline |
| broker `host.onboarding.check` | PASS | binding/permission/protection/credential metadata；required `CI / verify (pull_request)`；routine disabled |
| worktree add + claim | PASS | exact tuple / session；共享 main 未 checkout/rebase/写文件 |
| architecture unittest baseline | PASS | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py'`，57 tests，0.959s |
| 缺陷复现四场景 | CONFIRMED | 以下同一声明与四次结果 |
| analyzer JSON / resolver / document checker | PASS | 四角色映射；changes=145 pass=2 gap=0；准备脚本补齐 PYTHONPATH 后成功 |
| 初始 live platform classification / lifecycle | PASS | 合同准备阶段 typed classify/set 后独立 labels.read：type/bugfix、complexity/complex、spec-drafting；当时未 approved |
| Matt triage 双维度投影 | GAP | operation table 无对应 typed operation；仅 brief 推荐，未直接 API 绕行 |
| Issue durable brief | PASS | comment 11978；合同草案尚未 push，未发布虚假远端文档链接 |
| 修复后 CLI / build_lock / checker tests | NOT RUN | runtime 尚未修改 |
| 完整 runtime tests / smoke | NOT RUN | 待 T02/T03 |
| 修复 PR CI / installed / live / 现场验收 | NOT RUN | 尚无 PR；安装部署不在本合同 |

初始 sandbox Issue read 返回 TRANSPORT_ERROR；同一 typed 请求经受控 host 路径成功。
不把 sandbox 传输失败当成缺 Issue/权限故障。未读取/输出 token、env 或原始凭据。

## 基线缺陷探针

临时目录复制 `architecture/fixtures/valid/node-sqlite-container-project.json` 到
`.aisoft/architecture.json`；创建 `docs/deploy/Dockerfile`，对以下四场景依次运行同一命令：

```text
architecture/bin/aisoft-architecture validate
  --catalog architecture/catalog.json
  --profiles-dir architecture/profiles
  --schema-dir architecture/schemas
  --project <temporary-root>/.aisoft/architecture.json
  --today 2026-10-02
```

实际 subprocess 使用平台文件的绝对路径；测试不访问真实应用工作树、不联网、不运行 Docker。

| Dockerfile 情况 | 当前 exit / valid | lock_sha256 |
|---|---|---|
| `FROM node:22.22.3-bookworm-slim@sha256:16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644` | 0 / true | `a42e1ff7d5bd2c3d1bab1c2f3b5904d1da2669abc1962d83a0d11f9df2f172c4` |
| digest 改为 64 个 `a` | 0 / true | 同上 |
| `FROM node:22.22.3-bookworm-slim` | 0 / true | 同上 |
| Dockerfile 被删除 | 0 / true | 同上 |

结论：现有输入甚至没有 Dockerfile 路径，因此文件变化不进入 validator，也不进入 checksum。
Node 22 digest 来自现有 catalog / SFM #145 Issue 报告，未在本次重新 pull 或 Registry inspect。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1—AC-8 | NOT RUN | 仅确认 baseline bug；待已批准合同实施后填真实 receipt |

## 工作流与未完成项

分类：complex/manual；type/bugfix 与 complexity/complex 已 typed projection/read-back。
Matt triage 推荐 `triage/bug` + `triage/ready-for-agent`；现有 broker operation table 不包含
triage 双维度 projector，直接 Gitea API 不允许，本次不扩 broker 范围，标签投影记录 GAP。
用户已于 2026-10-02 确认合同/启动；T01 独立治理应用完成后停止，T02/T03、最终 PR 提交与人工合并尚未完成；不得关闭/归档。
不把静态源码检查解释为已构建镜像 provenance 或现场部署证据。

## 启动确认与 T01 受控治理步骤

- 用户原文：“确认”；绑定 #288 与 `change/288-dockerfile-digest`、manual。
- 批准时 spec/plan 的 SHA256 已冻结于 `evidence/contract-start-authorization.json`。
- broker 将 lifecycle 从 spec-drafting 投影为 approved；独立 read 后真实 `load_contract`
  返回 PASS、complex、8 条 acceptance criteria，未用 synthetic Issue 替代 live 启动读回。
- T01 仅应用 `architecture/schemas/project-architecture-v1.schema.json` 与
  `architecture/README.md`；本 Issue 文档记录授权/进度。无 runtime/Agent/CI/部署脚本修改。
- schema 增加可选 `dockerfiles` 语法：非空唯一字符串数组，拒绝空项、绝对路径、
  `.`/`..` segment、空路径 segment、反斜线、控制字符。delivery-specific 强制存在/禁止、
  文件读取和 FROM digest 执行仍由后续 T02 实现，未宣称 T01 已阻止基线假绿。
- README 写明完整已批准规则，并显式标注 T01 未实现 runtime/new CLI flag 的阶段边界。

| T01 check | Result | Receipt |
|---|---|---|
| schema 临时声明探针 | PASS | 2 valid / 15 invalid，使用真实 `validate_schema` |
| architecture suite | PASS | 57 tests / 0.949s |
| release architecture integration | PASS | `test_release_architecture_integration.py`，4 tests / 0.035s |
| `git diff --check` 与文件范围检查 | PASS | tracked diff 仅 schema/README；semantic docs 属当前 #288 |
| T02 runtime AC-1—AC-8 | NOT RUN | 治理步骤后必须停止并 fresh run |
| PR/CI/安装/部署 | NOT RUN | 用户此次仅批准合同启动 |

schema 探针有效集为单 `Dockerfile` 与多路径数组；无效集为：空数组、空字符串、absolute、
前置/中间 `..`、前置/中间 `.`、重复 slash、trailing slash、backslash、newline、NUL、
重复路径、非字符串项、非数组。探针使用现有合法 project fixture，只替换 `dockerfiles` 输入。


## T04 已批准补充的独立治理应用

用户于 2026-10-02 对完整最小补充方案明确回复“确认”。批准 patch 与 SHA256 记录于
`evidence/root-migration-proposal.json`（JSON 编码保留原 patch 字节）、`evidence/scope-amendment-authorization.json`。
只应用两个现有 shell 测试 validate 命令各一行 root 参数，以及安装用示例 declaration 的
路径与 synthetic Node 24 Dockerfile；没有修改 installer、CI context、test selection 或 runtime。

| Check | Result | Evidence |
|---|---|---|
| `git apply --reverse --check` approved patch | PASS | 四路径与批准 patch 一致，没有移除既有 flag/assertion |
| `bash -n codex/tests/smoke.sh codex/tests/test-architecture-install.sh` | PASS | exit 0 |
| `shellcheck codex/tests/smoke.sh codex/tests/test-architecture-install.sh` | PASS | 已安装，exit 0 |
| template schema / Dockerfile / declaration / catalog digest | PASS | Node 24 digest 精确一致；synthetic 注释存在 |
| semantic document checker | PASS | changes=145 pass=2 gap=0 |
| `bash codex/tests/smoke.sh` | FAIL | exit 2；安装测试 CLI 拒绝尚未实现的 `--repo-root` |
| T02/T03 runtime、最终 smoke | NOT RUN | 本步独立 commit 后停止，后续 fresh turn 实施 |
| PR required CI / installed live / deploy | NOT RUN | 不在此步骤执行 |

真实 smoke 错误：`aisoft-architecture: error: unrecognized arguments: --repo-root`。
临时安装 prefix 路径仅为 scratch 测试环境；不构成系统 installed/live 验收。
完整本地日志位于 `/private/tmp/issue-288-contract-data/t04-smoke.log`，未把阶段性失败改成 PASS，
未通过条件跳过、回退旧参数、修改 reader/root 合同或削弱测试修复。
下一步 fresh turn 重读已更新合同，实施 T02/T03 后重新跑全部必要验证；既有合同启动授权持续有效。

## T02 文件核验与 T03 初轮回归

在 `02cecb762f13cedfcef6db50af4744534ee3f8bd` fresh turn 实施 runtime。
新增回归先在旧 runtime 运行，四种原始假绿均实际 exit 0（测试预期 exit 2，因此 4 failures）。
随后在共用 build_lock 接入文件核验，全部 catalog/profile/project 原有语义检查通过后才读文件。
通过逐级 dir_fd + O_NOFOLLOW 检查实际文件；普通文件、UTF-8、1 MiB 上限、FIFO 非阻塞拒绝，
并保留原始异常/文件内容脱敏。解析多阶段、内部 stage、scratch、续行、CRLF 与 escape header；
不展开镜像变量，不加载 frontend、不联网、不执行 Dockerfile。

| Check | Result | Receipt |
|---|---|---|
| 新回归 red（旧 runtime） | CONFIRMED | 四种假绿，1 test / 4 failures |
| architecture suite（含实际 CLI/checker） | PASS | 最终本地日志 t02-architecture.log；详细数量见后续 receipt |
| release architecture integration | PASS | 4 tests / 0.037s；reader/schema 未改 |
| 完整 runtime 初轮 | PASS | 989 tests / 88.934s；后续 parser 边界补充需重跑 |
| 四个非容器 lock bytes 对比 | PASS | evidence/noncontainer-byte-comparison.json；baseline 5c2cd726，SHA256 全部相同 |
| 连续两次 lock、失败不 create/overwrite、旧正确 lock 无法掩盖源码漂移 | PASS | 新 CLI 子进程 tests；三入口检查同一 real temp repo |
| 现有项目 checker source drift | PASS | 正确源码 PASS: architecture-lock；只修改 FROM 后 GAP；checker 未改且输入 bytes 不变 |
| 平台 smoke | FAIL | t03-smoke.log；固定 evidence gate 报 unapproved source bytes: architecture/reference/newemaint/target-candidate/architecture.lock.json |
| #287/main 组合验证 | NOT RUN | #287 仍 open；本次 fresh fetch origin/main 为原 baseline |
| PR CI / installed / company live / deployment | NOT RUN | 无 PR、未安装部署 |

smoke 已越过 T04 的 --repo-root 阶段失败；本次失败发生在
`codex/tests/check-release-evidence-boundary.py`：该 checker 冻结旧 source bytes，
CURRENT_SOURCE_PINS 仅准许 runner/transport/matrix；并同时核验 disk 与 index。
不能恢复旧 declaration hash、把 lock 加 CONTENT_EXEMPT、跳过 checker 或替换历史 evidence。
已批准 spec 排除额外 CI/治理脚本改动，故该具体补充仍须独立合同批准/治理步骤。
T02 local source check 不构成真实构建、制品 provenance、安装或现场证明。

## T02 双轴审查与常规修复

初次本地提交 e799acf30af99c1256e8c44b972071be3d2834da：Standards PASS / 0；
Spec FAIL / P1 1：双尾 escape 会错误吞掉下一条真实 FROM。已核对官方 BuildKit
parser setEscapeToken（149–159）与 trimContinuationCharacter（499–504），不扩张合同。
修复为尾 escape 前一字符不是同 escape 才续行，并保留续行上的分隔空白。
新增两种 escape、2/3/4 尾字符、空白与单独未完成续行回归；先 red 2 tests / 7 failures，
修复后 architecture 71 tests PASS。来源：
https://github.com/moby/buildkit/blob/master/frontend/dockerfile/parser/parser.go

完整 runtime 第二轮（修复前 e799acf）990 tests / 86.754s PASS；
上述常规修复后将再次执行完整 runtime，旧 PASS 不外推至新 head。

## T03 最新本地验收与范围阻塞

验证 runtime head：2a5ccf9f208dd01dc8d96d8c0a06d1f8e0af3ed0。

| Check | Result | Receipt |
|---|---|---|
| architecture suite | PASS | 71 tests / 7.630s，t02-architecture-final.log |
| 完整 runtime suite（最终修复后） | PASS | 992 tests / 95.057s，t03-runtime-reviewed.log |
| Standards / Spec 独立复审 | PASS / PASS | 0 / 0；原 Spec P1 核销，Standards 无 hard violation / smells |
| release architecture integration | PASS | 4 tests / 0.036s；reader/schema 未变 |
| schema/lock/release 原外部字段与非容器 bytes | PASS | 已迁移容器 declaration checksum，其它 lock 字段不变；四非容器 receipt 相同 |
| 平台 smoke | FAIL | 仍为 exact reference lock 固定 source pin 阻塞，未重跑同根因失败 |
| #287 fresh-main 组合 | NOT RUN | 最新 broker Issue read 仍 open，最终候选前必须自行整合真实合并后的 main |
| 治理补充临时 proposal 单测 | PASS | 20 tests / 9.371s；仅临时副本，不等于已批准或已应用 |
| PR/required CI/安装/现场/部署 | NOT RUN | 无 push/PR，未安装部署 |

最小治理补充草案：evidence/boundary-amendment-proposal.json，PROPOSED_NOT_APPLIED。
只触及 codex/tests/check-release-evidence-boundary.py 的 exact architecture lock pin 与
codex/runtime/tests/test_release_evidence_boundary.py 的 disk/index 单字节篡改回归。
提案补充 CURRENT_SOURCE_PINS 可接受的唯一 fixture path，仍做 disk 与 index SHA256 双核验，
不加入 CONTENT_EXEMPT、不改变 historical baseline/evidence/runner 或 runtime/real-E2E pin。
完整 diff 已保存可审阅文件，patch SHA256：
a2538e14a46d6568470271edb86d0ffac0c241ff221d133efdb01815ba86aa55。
新增 pin 为当前 synthetic lock 文件 SHA256：
b6d39e9126b61c804b8cb188a11a3b4e1bc375236a3ffadf93909f3d49e70076。
当前 source guard 和原测试文件均未修改。批准后须独立治理应用并停止，fresh turn 才重跑 runtime。

## T05 已确认的独立治理应用

用户原文“确认”，仅绑定先前展示的完整两文件补充。授权见
`evidence/boundary-amendment-authorization.json`，实际应用与验证见
`evidence/boundary-amendment-application.json`；原 proposal 保留 PROPOSED_NOT_APPLIED
作为批准前历史快照，不静默改写提案字节。原样 `git apply` 后源码 SHA256 与 proposal
proposed hash 精确一致，`git apply --reverse --check` PASS。

| T05 check | Result | Evidence |
|---|---|---|
| exact owner / branch / pre-apply clean tree | PASS | session 01a0fc7b-f327-7a93-a48c-a254937cb08d；change/288-dockerfile-digest |
| approved patch/hash/两路径边界 | PASS | a2538e14a46d6568470271edb86d0ffac0c241ff221d133efdb01815ba86aa55 |
| Python compile / reverse patch | PASS | 两源码 compile；反向检查无偏离 |
| boundary unit suite（实际工作树） | PASS | 20 tests / 10.435s |
| 真实 fixed source identity | PASS | 仅执行 validate(root)，disk/index/hash/file set/mode/historical identity 全部通过 |
| 文档 resolver/checker、diff --check | PASS | 映射完整，change-documents / change-pr-url PASS |
| 完整 boundary check()/release regression/smoke/runtime | NOT RUN | 遵循独立治理步骤停止，fresh run 才完整验收 |
| #287 main 组合 / PR CI / installed / company-live / deploy | NOT RUN | 不从静态 source identity 推导这些证明 |

本次没有修改 shell；原 T04 shell 静态检查和真实 smoke 记录保留。之前 smoke FAIL
仍是历史真实结果，当前只证明已迁移 lock 可通过新 exact pin 的 source identity 检查，
不能把完整 smoke 改成 PASS。新增 architecture pin 不接受路径豁免；历史 evidence、
BASELINE、RUNNER_BEFORE/AFTER、runtime/real-E2E pins 与 CONTENT_EXEMPT 未改。
按已批准治理顺序，本步独立 commit 后停止，下一轮重读更新合同恢复 T03。

## T03 第一轮 fresh-main 本地验收（main 14bfe6 的历史结果）

实际已合并 PR #324 / #287，main `14bfe6edea6a78e994daac88b3615c009ae37fea`。
本 owner 在自己的 worktree 整合 main，组合 runtime head
`aa585dd5b5b7a27e8ed6cdbebb9f8746a7a27128`。保留所有已批准治理步骤与历史失败记录；
下面结果覆盖该组合源码，后续只修改状态文档/receipt，不把旧阶段 PASS 外推为 PR CI 或部署。

| Check | Result | Evidence |
|---|---|---|
| 完整 runtime | PASS | 1008 tests / 100.273s，exit 0 |
| 完整平台 smoke（受控 host） | PASS | `LC_ALL=C bash codex/tests/smoke.sh`，exit 0；含 runtime 1008 tests / 100.928s |
| 同命令 sandbox smoke | BLOCKED | 临时 localhost socket bind PermissionError；执行路径限制，未跳过测试，host 原命令完整通过 |
| Dockerfile 两版组合 suite | PASS | 16 tests / 7.443s；默认 V2/V1 文件硬门、旧 lock 和写入边界 |
| release architecture integration | PASS | 5 tests / 0.044s；V1 reader 保持，V2 fail closed |
| 四非容器合同 × V1/V2 bytes | PASS | `evidence/t03-fresh-main-noncontainer-bytes.json`，八组 SHA256 与 fresh main 相同 |
| T04 shell bash -n / ShellCheck | PASS / PASS | 只检查已批准两测试入口；无 CI context 改动 |
| 真实 approved 合同 | PASS | `evidence/t03-approved-contract-validation.json`，8 AC / exact branch / complex |
| exact #288 判级投影读回 | PASS | `evidence/t03-classification-readback.json`，bugfix / complex / projected |
| PR CI / global installed / builder provenance / company live / deploy | NOT RUN | 尚无 PR，无安装部署；scratch installer 测试不等于真实安装验收 |

完整日志的文件路径、SHA256 和命令冻结于 `evidence/t03-local-validation.json`。
main 组合 receipt 是 merge 前的历史快照，里面的 full NOT_RUN 保持原样；以上是后续真实结果。

| AC | Result | 本地证据与边界 |
|---|---|---|
| AC-1 | PASS | Node 22 实际 catalog child digest fixture；真实三 CLI 子进程修改 digest/tag 后 exit 2 |
| AC-2 | PASS | 多文件、多外部 stage、内部 stage 与 scratch tests；逐个文件/stage 与反向未使用声明检查 |
| AC-3 | PASS | ARG 默认值也拒绝 image 变量；平台变量、畸形 FROM、heredoc、无 FROM、重复/前向 stage；escape 回归 |
| AC-4 | PASS | root/cwd、路径、symlink、UTF-8/size/FIFO、缺文件与输出脱敏；缺 root 库调用 fail closed |
| AC-5 | PASS | 非容器拒绝 dockerfiles、不读取文件；四合同 × 两版本 bytes 与 fresh main 一致 |
| AC-6 | PASS | 两次输出相同、失败不创建/覆盖；旧正确 lock 不掩盖最新源漂移；默认 V2 / 显式 V1 / release V1-only 组合 |
| AC-7 | PASS | README root/语法/迁移/证明边界；完整 runtime 与 smoke；T05 exact lock pin/static evidence gate 未削弱 |
| AC-8 | PASS | 现有只读 `.aisoft` checker 在真实临时 checkout 捕获源码漂移；checker/required CI workflow/context 无变更 |

已批准 spec 的 AC 文本保持原样；这里记录执行结果。最终候选仍需单独 PR 提交确认，
人工合并与部署未授权。回滚方式为人工 revert 唯一最终 PR 后运行相同回归；旧源码盲点会恢复。

## T03 main 65268ee 初轮组合（T06 批准前的真实失败）

最终 main refresh 发现 #308 / PR #326 已合并。只由本 owner 整合自己的 worktree，
新 head `aaa9e8dc2b6875c4658f7a9c8f59f7c91907a983`，main
`65268ee5f1e622c486fd9e354dd35e20a2900f91`。无冲突；#308 的 44 个文件字节保持，
共享 smoke 只多本 Issue 已批准的 repo-root 参数。两轴 scope 审查 PASS / 0。

| 当前 check | Result | Evidence |
|---|---|---|
| 最新组合完整 smoke | FAIL | `LC_ALL=C bash codex/tests/smoke.sh`，host exit 1；23 installed-drift tests / 36.963s / 16 failures |
| 新 source-only gate | PASS | 原 gate 如实报告 cached-main source GAP，定义完整性 PASS |
| 八临时安装面 | PASS | installer expected bytes/links 全部 PASS；不足以抵消真实 source GAP |
| #288 architecture/runtime bytes | UNCHANGED | 与 aa585dd 完全相同；14bfe6→65268ee 的 architecture/runtime 同样未改 |
| 新组合完整 runtime | NOT RUN | smoke 在前置 fixture 失败后停止，不能沿用旧 head 的完整结果 |
| 未批准单文件提案测试 | PASS | 临时副本原 23 tests / 44.930s；含显式 source-drift 仍 GAP 的反向检查 |
| T06 提案双轴审查 | PASS / PASS | Spec findings 0；Standards hard 0 / possible duplicated-code smell 1（非阻塞） |
| T06 实际应用 / 最终 PR / required CI / installed-live / deploy | NOT RUN | 尚未取得范围补充授权，不绕开硬门 |

真实失败来自默认 fixture 直接使用 change checkout，而 installed 模式有意同时要求
源码与 cached origin/main 一致；正常 PR 的源码变更令全局 result GAP，即使八个安装面都 PASS。
不能改变真实 checker 的身份门、将其改成 source-only、修改真实 origin/main ref 或删测试。

最小未批准 patch 只修改 `codex/tests/fixtures/installed-drift/test-installed-drift.py`：
默认 fixture 检查临时复制当前源码建立的本地 Git baseline；显式 source-drift tests 不改变。
它不把临时 baseline 伪装成实际 main/installed 证据。原源码文件仍保持 main bytes。
patch、source before/proposed hash、两日志 SHA256 与未执行边界均在
`evidence/installed-fixture-amendment-proposal.json`。proposal 为 PROPOSED_NOT_APPLIED，
测试只针对临时副本；原 spec 尚未增加该文件权限。T03 pending / NEEDS_HUMAN_DECISION。

## T06 已确认的独立测试治理应用（独立步骤完成时的历史状态）

用户本轮明确回复“确认”；授权见 `evidence/installed-fixture-amendment-authorization.json`，
冻结批准 patch、proposal、应用前 spec/plan 与 source SHA256。映射 spec 已明确增加
单个 fixture 的权限，按同一 patch 原样应用，未改写提案的批准前 PROPOSED_NOT_APPLIED 状态。
应用与日志 hash 见 `evidence/installed-fixture-amendment-application.json`。

| T06 check | Result | Evidence |
|---|---|---|
| exact owner / branch / pre-apply clean tree | PASS | #288，session 01a0fc7b-f327-7a93-a48c-a254937cb08d，pre-head 263c851abe529d7289da82292e45f52eeac6a7d9 |
| approved patch SHA256 / before-after source / reverse check | PASS | af73fbd48c2459b0792cc88493e08af9d7c89ae74a17026b5845271fcadecf22；after 与 proposal 精确一致 |
| Python compile | PASS | 实际 fixture bytes compile，无运行时改动 |
| 实际工作树官方 fixture wrapper | PASS | `LC_ALL=C bash codex/tests/test-installed-drift.sh`，23 tests / 44.895s，exit 0 |
| approved 合同 live readback | PASS | `evidence/t06-approved-contract-readback.json`，complex / exact branch / 原 8 AC 保留 |
| semantic docs / diff --check / scope | PASS | 映射完整；只有单个 fixture 技术改动和状态文档/receipt |
| 应用双轴审查 | PASS / PASS | Spec 0；Standards hard 0 / possible duplicated-code smell 1（非阻塞，保持批准 patch） |
| 本轮完整 smoke/runtime / required CI / installed-live / deploy | NOT RUN | 独立治理步骤提交后停止，fresh run 才跑完整 gate |

真实工作树专项 tests 保留 source-only 允许合法 PR 差异但报告 main GAP、installed mode
拒绝 source 漂移、未跟踪新模块、Git 环境/clean filter 与零写入审计的反向检查。
临时 baseline 只用于 installer fixtures，不是 actual main、全局 installed 或现场证据。
真实 checker、installer、smoke/context、architecture runtime 与 actual origin/main 保持原 bytes。
本步未改 shell，不额外套用 shell 改动后的 smoke 要求；两处 T04 shell 的历史检查保持原样。
T06 done，T03 pending；独立 commit 后按已批准治理顺序停止，后续 fresh run 继续。
回滚为人工 revert 此治理 commit 并运行同一专项测试；不放宽真实 source 身份门。

## T03 T06 后 fresh-run 完整本地验收（当前权威结果）

本 fresh run 在 T06 独立提交并停止之后重读 AGENTS/批准 spec-plan，核验 exact owner、
branch、clean tree 和批准 source hashes。broker main fetch 为
`65268ee5f1e622c486fd9e354dd35e20a2900f91`，本分支已包含，无新合并冲突。
测试 code head `1507e358319ebfc2206fe0402ce1520f3392a246`；后续只保存文档/receipt/PR 草稿，
不修改已验证的 runtime 或测试技术字节。旧 FAIL/NOT_RUN 保留各自历史范围。

| Final local check | Result | Evidence |
|---|---|---|
| 完整 runtime | PASS | 1008 tests / 101.684s，exit 0 |
| 完整 smoke | PASS | `LC_ALL=C bash codex/tests/smoke.sh`，controlled host exit 0，全部原有及 #308 硬门保留 |
| smoke 内 installed-drift fixture | PASS | 实际工作树官方 wrapper 23 tests / 44.320s，真实 checker 未改 |
| smoke 内完整 runtime | PASS | 1008 tests / 101.989s |
| 四合同 × V1/V2 非容器 bytes | PASS | `evidence/t03-after-t06-noncontainer-bytes.json`，两个独立 Python 进程实际重算 pinned main/current 八组输出 |
| T04 bash -n / ShellCheck、文档、diff --check | PASS | 当前两批准 shell 及 semantic docs |
| T05/T06 exact 批准 source hashes | PASS | 两个 boundary 源码、synthetic V1 lock pin、fixture 源码 SHA256 全部与批准 receipt 相同 |
| Standards / Spec | PASS / PASS | hard violations 0 / findings 0；Standards 1 个非阻塞复制代码建议，保留已批准 patch |
| approved / onboarding / main protection / unique PR | PASS | `evidence/t03-after-t06-live-readback.json`，8 AC，main 无 push/force 权限，required CI `CI / verify (pull_request)`，routine disabled，#288 open PR 0 |
| exact #288 分类读回 | PASS | `evidence/t03-after-t06-classification-readback.json`，bugfix / complex / projected |
| PR/required CI / global installed / builder provenance / company-live / deployment | NOT RUN | 不从本地 smoke 的 scratch installer fixtures 推导真实系统验收 |

完整命令、日志绝对路径、SHA256 和 gzip 副本见
`evidence/t03-after-t06-local-validation.json`。全部 AC-1–8 的本地行为证明沿用上述
完整 suite 内的三 CLI/路径/语法/版本/只读 checker 回归；AC-7 的最新 smoke 现已实际闭环，
不会把批准前 fixture FAIL 或旧 head 的 PASS 替代本次结果。
最终候选 Policy manual，进入 AWAITING_PR_CONFIRMATION，exact candidate SHA 在本地状态中固定。
最终 PR 草稿只有一行 Closes #288。取得提交确认后才 push/建 PR；required CI 全绿后
停在 READY_FOR_REVIEW 等人审核并合并。回滚方式保持人工 revert 唯一 PR 并运行同一回归。
