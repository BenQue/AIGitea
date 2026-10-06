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

# #336 完整读取实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 正式接收与既有四角色合同治理固定；完成真实分类/批准投影、语义映射与冻结范围验证，本地 commit 后 STOP | - | completed |
| T02 | fresh run 完成三路径完整 PR 读取与 #333 namespace 证明垂直切片，新正例/失败夹具及受影响回归通过 | T01 | completed |
| T03 | 本地完整 smoke/恢复/结果投影已推进；唯一 manual PR 卡及 exact-head required CI 待独立发布门 | T02 | in-progress |

2026-10-05 本人已通过总调度的直接决定及本会话派发批准既有三路径合同启动与后续本地 Development Loop。原 owner 实际交回后，本接收 session `01a10c82-7f6b-7093-80d5-d389a18198c0` 已使用现有 takeover 接管；T01 已完成治理 commit 并独立结束运行；2026-10-06 本轮是重读该合同的 fresh T02/T03 本地执行，不重复启动确认。`IMPLEMENT_PROVIDER=none`，不启动未验收 provider。

## Expected touch points

| Ticket | 允许的文件与职责 |
|---|---|
| T01 | 本目录 summary/spec/plan/verification；现有 claim-worktree takeover 及必要所有权证据；通过现有 typed projector 只投影本票 type/security、complexity/complex、approved 并真实读回。不修改 `AGENTS.md`、runtime 或安装端，不改其他 Issue 标签 |
| T02 | `codex/runtime/aisoft_host_access/broker.py`、`codex/runtime/aisoft_host_access/cli.py`、新增 `codex/runtime/tests/test_host_access_complete_reads.py`；同一 owner 顺序实现 |
| T03 | 运行验证、保留 private evidence、按真实结果更新本目录四角色投影；范围内失败修复限 T02 三路径，不改其他 Issues 的测试 |

T02 启动先 fresh 读 main、required CI/保护与 #327 已正式交付的能力，核 branch/owner/base 和原审阅 patch hash。原基线为 `e2edb3e08194624a6647212571c6cc866298575b`；T01 时只读缓存 main/origin/main 为 `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`。T02 使用 installed canonical `git.fetch.main` fresh 读回同一 main；未 rebase/merge 或移动 change HEAD。main 或等价 namespace 能力变化时重新固定 actual diff，不直接套用旧 prototype。本地三路径垂直切片不因 #327 未发布而空等，FF/发布/安装门仍独立，不新增跨票产品依赖。

T02 已在核验后采用原三路径补丁为参考起点并继续硬化；runtime commit=`4cf6af48463238a7f019f94da56a9e5b663aa666`，最终 patch/hash 与三路径 bytes/mode 已固定并恢复验证。`reader-capability-source.patch` SHA256=`11ab13f03770725e74d75fafc2de4572b484ef3480e7f6b8bae57f441f5cd2a2`；原审阅包 `/private/tmp/issue-333-pat-rotation-acceptance/T14-readiness-proposal-261004/` 固定历史 bytes 和失败日志。#333 五路径 `source-consumer-prototype.patch` 不得混入 #336。

## 数据库迁移

无。

## 测试与验收映射

以下为固定验收要求；实际结果见 verification。T02 新源专项/受影响回归 237 项及全量 runtime 1156 项 PASS，固定 runtime HEAD 的完整默认 smoke 与 exact delta forward/reverse/forward PASS。原型 217/330 tests 仍只作历史记录；最终 PR CI、merged pin 与 installed/live 保留 NOT RUN。

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1～4 | 在 `codex/runtime` 执行 `python3 -m unittest -v tests.test_host_access_complete_reads tests.test_host_access`，使用公开契约夹具；实际新 typed 全历史/namespace readback 须在 merged 后独立批准安装，再记录 installed 层脱敏输出/hash/退出码 |
| AC-2 | 新夹具覆盖空集合、50/51条、短页后还有数据、正确末页、缺/错误 totals、重复/非法 IDs、foreign repo、JSON duplicate key/NaN、漂移、page/byte/output/time/ref 上限、redirect、transport 与 namespace 正/负例 |
| AC-3～5 | strict stdout/stderr/error receipt schema、精确 bytes hash与既有 consumer 兼容性审阅；冻结的 push/identity/target 方法 AST 比较及 operation/参数目录比较 |
| AC-5～6 | 新夹具、既有受影响 broker suites；repo root `bash codex/tests/smoke.sh`（默认完整执行，不用跳过模式）；语义文档检查与 `git diff --check` |
| AC-6 | Controller 获唯一最终 PR 确认后读回 exact head/base 下的 `CI / verify (pull_request)`；头或 base 变化重读，不以本地测试替代 PR CI |
| AC-7 | 在 disposable worktree 对最终 patch 做 forward/reverse/forward，比较每个路径 baseline/candidate bytes、Git mode 和新文件不存在/存在；保存命令与各步骤 exit code |
| AC-8 | 独立 source 范围、#327 实际可用发布能力、manual/routine-disabled、merged pin和安装缺口审阅；无 installer/credential/其他 Issue diff |

只在出现新改动、失败或尚未解决的风险时扩展/重复回归；不为了获得 PASS 弱化夹具、把 transport failure 当 absence 或改别人的 tests。shell 文件冻结；如确需扩大 shell/治理范围，先交 exact diff 升级合同，后续适用 `bash -n`/ShellCheck 与 smoke 要求。

## 部署与回滚

本源变更无部署/安装操作。`verification` 用于源行为、缺口与恢复证据，不包含部署验收章节；源结果、CI、installed 与 field 分别记录。

T03 在实际合规 FF/自举通道可用后准备 exact #336/branch/manual 最终 PR 卡。#327 负责该通道，禁止借用未合并实现、force/lease-force 或混装 broker 自举。最终 PR 由本人确认后交 Controller 创建唯一一个；manual merge 由人执行，PR merge 不传递安装或部署授权。

源回滚先在 disposable worktree 完成 exact 三路径恢复证明；合并后用独立 revert/manual PR。未来 installed 操作必须另备 merged stable pin、全变更字节/provenance/compatibility、上一版本回退与 readback 卡，独立确认后再执行。本次不生成可执行安装卡，不启用额外 operation。

## 停止条件与归属

- 当前合同/启动已批准；T01 已固定治理后独立 STOP，本轮 fresh T02 已完成三路径本地实现与提交。
- T03 本地验证/文档投影按同一 writer 顺序执行；最终发布/PR/CI 门仍独立，没有并行 runtime 实施。
- 发现合同冲突、三个代码路径范围扩大、发布/安装能力缺失或重复失败，保存 exact evidence 并交本人处理； unaffected 本地准备可继续。
- #333 保持既有 owner、T13与现场验收职责；#327 保持既有 owner及发布职责。本票不写它们的 live label、owner 或工作区。

## Mac 前置完成后的受控范围投影（2026-10-06）

#327 / PR #346 的固定 merge `1a86a0037ee76f462eac52dc7dc08d3d3fbd2ed4` 已在当前 Mac 完整安装、真实恢复、再安装和幂等复验，安装回执为 PASS。它解除本机旧 installed FF qualification 缺口，不表示 #336 新读取协议已安装或发布。

本轮发现 approved spec 缺少当前 Controller 必需的 `git_scope`，先独立投影原三代码路径与四映射文档，作本地文档 commit 后 STOP。后续 fresh run 才继续 T03：重读 owner/合同/当前 main、在三路径内修复兼容性，先证明合规无冲突 main 整合，再固定实际候选执行适当回归/默认完整 smoke/真实恢复/唯一性与发布硬门。不得把私人候选套入实际 worktree 后手工解决 merge 冲突绕过 Controller。

隔离预演的范围/history 前置门 PASS，但旧源与 v2 兼容候选对固定 main 均返回 `MERGE_CONFLICT`；预演未修改实际 runtime。既有私人 v2 345/1226 项结果不算最终 integrated 候选 PASS。本轮没有真实整合、push、PR 或 #336 安装。
