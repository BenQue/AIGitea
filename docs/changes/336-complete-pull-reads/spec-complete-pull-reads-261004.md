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
status: contract-drafting
branch: change/336-complete-pull-reads
created: 2026-10-04
updated: 2026-10-04
---

# #336 完整读取协议与边界草案

## 目标与原因

为固定 manifest 授权的 repository/identity 提供完整 PR 集合及 #333 精确 namespace 公开证明，使调用方能区分真实 absence、其他 slug 与读取失败。证据必须来自实际成功读取；调用方不得借 stdout 的一页数据或 transport error 推断完整集合。

本 spec 当前只供审阅，未激活 runtime 权限。后续合同/启动确认必须绑定 #336 与 `change/336-complete-pull-reads`；先由只修改四角色合同的独立步骤固定治理内容并 STOP，fresh run 重新读取后才允许实施本节约定的三个代码路径。不得修改当前运行所遵循的 `AGENTS.md`。

## Acceptance criteria

- [ ] **AC-1**：`gitea.pulls.read` 对 `open`、`closed`、`all` 正确读取到空终页；`all` 包含 open、closed、merged 历史，50 条以上及非终短页均不丢数据；每页 totals、唯一正整数 number、state 和 canonical base repository 合法。
- [ ] **AC-2**：两次完整扫描与服务器 total 相等；重复 ID、漂移、缺失/非法 total、错误 repository/state、非标准 JSON、超限、timeout、redirect 与 transport failure 均拒绝，没有部分成功结果。
- [ ] **AC-3**：成功 stdout 保留 JSON array；stderr receipt 严格符合本 spec，`stdout_sha256` 绑定实际输出 bytes，scope、count、空终页、时间与两次扫描证明均可被消费方核验。
- [ ] **AC-4**：`git.fetch.change` 在 `aisoft-platform` / Issue #333 的正例、精确 branch 缺失、同编号其他 slug、namespace 漂移及 transport failure 有不同且正确的结果；absence 只来自两次相同成功读取，保留 exit20，并携带完整公开 receipt。
- [ ] **AC-5**：operation catalog、typed caller 参数、canonical manifests、identity/custody、普通 Issue create/update、push/merge、保护及 required CI 不变；其他 project/Issue 的 fetch 行为不变，既有受影响回归通过，公开输出不含 Secret。
- [ ] **AC-6**：fresh 最终源候选的新夹具、受影响 broker suites、完整默认 `bash codex/tests/smoke.sh`、语义文档/静态门及最终 exact-head required PR CI 真实通过。历史 prototype 结果和未执行检查不计作本 AC 的 PASS。
- [ ] **AC-7**：固定最终三路径 delta 后真实执行 forward/reverse/forward；每轮核对 tracked 文件 bytes/mode 与新增测试文件的存在/撤回，恢复到 exact 源基线。已提交源变更的回退走独立 revert 分支及 manual PR。
- [ ] **AC-8**：最终范围仍可独立于未合并 #333 runtime；无 #327/#333 工作区改写、force 发布、未合并代码自举或 installed 混装。源交付完成后提供真实 merged pin 和安装缺口说明；安装授权及验收单独处理，不作为源 PR 自动闭环条件。

AC-1～5 的源验收使用公开接口契约夹具、新源码与受影响回归，不借用未合并 runtime 操作 installed custody。合并且获得独立安装批准后，才能对实际安装的新 typed operation 做全历史/namespace live readback；该层保持独立状态，不把源 PASS 提升为 installed 支持。

## 接口、数据与兼容性影响

### 1. PR 集合读取

保留 operation `gitea.pulls.read` 和唯一 caller 参数 `state={open,closed,all}`。只使用 canonical manifest 的 URL/repository/identity；内部固定请求 `pulls?state=<state>&sort=oldest&limit=50&page=N`，从 page=1 顺序读取。

每页验证实际 `X-Total-Count` 为合法非负整数并在两次扫描期间不变。只有明确空页才是终页，短页继续读取。最终 collected count 必须等于 server total；number 为正整数且不接受 bool，全集 number 唯一；state 与请求一致，base repository 与 manifest 绑定。`all` 允许 open/closed，merged PR 按服务器 closed 语义保留。

完成两次独立完整扫描，返回列表必须完全相等，包括顺序、字段与 total。它是两次观测一致性的证明；不宣称服务器提供原子 snapshot。

| 边界 | 固定上限 |
|---|---|
| limit | 50 |
| pages per scan | 100，包含空终页 |
| collected PR count | 4950 |
| 两次扫描收到的 page body bytes 总和 | 4 MiB |
| 最终 stdout bytes | 2 MiB |
| 整个 PR 操作期限 | 55 秒 |
| HTTP redirect | 禁止 |

duplicate JSON key、NaN/Infinity、非法顶层/字段/类型、count 与 total 不符、未到空页、超限与任何读取失败均 fail closed。日志只保留脱敏错误类型和公开字段；不返回部分数组，也不降级单页、UI、直接 API 或更宽身份。

### 2. PR 成功公开 receipt

stdout 保留既有 JSON array，序列化固定 `ensure_ascii=False`、`sort_keys=True`，结尾一个 newline。stderr 输出单个 JSON receipt；以下是唯一字段集合，额外字段和重复 key 均拒绝。

| 字段 | 约束 |
|---|---|
| `schema` | `aisoft.broker.pull-collection/v1` |
| `status` | `PASS` |
| `project`, `repository`, `operation`, `identity` | canonical manifest 的真实 scope；operation=`gitea.pulls.read` |
| `state` | 实际请求的 `open`、`closed` 或 `all` |
| `count`, `server_total` | 相同合法非负整数，匹配 stdout array 长度 |
| `scan_count` | 2 |
| `terminal_empty_pages` | 两次扫描实际空终页编号；长度2，每项1–100 |
| `limit`, `max_pages_per_scan` | 50、100 |
| `observed_at` | 最后成功观测的整数 Unix UTC timestamp |
| `stdout_sha256` | 精确 stdout bytes（含 newline）的 SHA256，小写64位 hex |

失败保持现有 typed error 规则，不输出成功 receipt。receipt 不携带凭据、请求 header 或私密配置。成功 stderr 从空变为 receipt 是明确共享 CLI 协议变化；消费方适配必须独立确认，本票不改 #333 Controller。

### 3. #333 change namespace 读取证明

保留 `git.fetch.change` 的 operation 与原 typed 参数。仅 project=`aisoft-platform` 且 issue=333 时使用两个固定 namespace 观测；其他目标沿用既有行为。内部请求限定为 manifest remote 的 `git ls-remote --heads` 与 `refs/heads/change/333`、`refs/heads/change/333-*`；不得暴露 caller URL、refspec、shell、page、path、credential 或 identity override。

解析合法 `ChangeName`、issue=333、40位 hex commit SHA；拒绝重复 branch、外来编号、未知 ref、控制字符和不合法输出。每次最多100 refs、65536 stdout bytes。两次观测必须完全相等；使用 broker 原有期限和错误处理，不设无限等待。

若 requested branch 存在，实际 fetch 后的 tracking head 必须等于第一次 namespace 对应 SHA，第二次 namespace 不得漂移。正常成功 stdout 携带 `namespace` receipt。

若 requested branch 缺失，stdout 为空，exit20；stderr error 的 `status=BLOCKED_EXTERNAL`、`code=REMOTE_CHANGE_ABSENT`，只在两次成功观测相等后包含 `public_receipt`。精确 branch absent 不等于整个 namespace 为空；同编号其他 slug 如实列入 `refs`。transport failure/timeout/非法输出仍是错误，不能转成 absence。

两种结果使用相同 receipt 字段集合：

| 字段 | 约束 |
|---|---|
| `schema`, `status` | `aisoft.broker.change-namespace/v1`、`PASS`（表示读取证明有效） |
| `project`, `repository`, `operation`, `identity` | canonical scope；operation=`git.fetch.change` |
| `issue`, `branch` | 333、实际 requested exact branch |
| `checkout`, `remote_name` | canonical checkout、manifest remote name |
| `scan_count`, `complete` | 2、true |
| `refs` | 完整确定顺序的 `{branch,sha}` 数组；最多100项 |
| `requested_head` | 对应 SHA，或证明 absent 时 null |
| `observed_at` | 最后成功观测的整数 Unix UTC timestamp |

此公开证明不增加 push/merge 权限。若 #327 已正式交付等价能力，先 fresh 核验 merged/installed 证据再复用，并删除重复增量、重新固定最终 diff 与回归；未合并代码不构成能力已可用的证明。

### 4. 明确冻结的权限与源范围

实现只允许 `broker.py`、`cli.py` 和新增 `test_host_access_complete_reads.py`。普通 Git push 分支、`_push_leased`、`_remote_change_heads`、`_validated_remote`、`_validated_project_worktree`、`_verify_identity` 的 AST 不得变化；operation 目录、manifest/credential policy、installer、Controller、CI workflow、Agent 与当前 `AGENTS.md` 均冻结。

四角色文档只允许当前合同固定及后续与真实结果一致的投影；不得通过结果投影扩大代码或权限范围。历史三路径审阅补丁 SHA256=`11ab13f03770725e74d75fafc2de4572b484ef3480e7f6b8bae57f441f5cd2a2`；应用前须复核 base、bytes、mode、范围及上述冻结检查。

## 风险与回滚约束

分页排序与 `X-Total-Count` 在原审阅包中已按 Gitea 1.26.4 官方实现核对；实际本站新协议读取仍为 NOT RUN。实现前必须核实际版本及接口行为，不把夹具替代 live 验收；必要时在既定安全合同内修正夹具，协议变化交合同审阅。

源回退使用最终 exact 三路径 patch，在 disposable worktree 真实校验 apply/reverse/reapply 及 bytes/mode；不得 reset/改写共享 main 或其他 owner。合并后回退使用独立 revert/manual PR，不 force history。

既有 installed public parser compatibility GAP 为 `missing=['credential_rotation_policy'] extra=[]`，且旧公开 operation catalog 为 source38/installed36。安装前重新核验 merged stable pin、完整变更路径、provenance、manifest/parser compatibility、上一可恢复版本及 readback，获得独立批准后执行版本化安装流程。不得只复制 broker/CLI；本票不授权 rotation/dependency operation、PAT、服务或 VM 改动。

## 非目标

保留历史的 main 整合与 FF 发布属于 #327；#333 的五路径 SourceFirst adapter、G4 治理和现场六项验收属于 #333。本票不关闭或重启既有 T13，不修改它们的 owner、branch、dependency 或 live label。

本票没有数据库迁移、安装、部署、服务启停、Secret/PAT 操作或生产执行；不创建额外 PR 或 chat。

## 未决问题

合同设计已具体化；当前待本人合同/启动确认，不是已获批准的 runtime 合同。正式发布路径与 installed compatibility 是后续待核验 gate。若 fresh #327 能力使实现方向或三个路径范围改变，应提交 exact diff 重审，不能自行绕过发布/安装闸门。
