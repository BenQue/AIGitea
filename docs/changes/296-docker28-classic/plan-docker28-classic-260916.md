---
issue: 296
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/296
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - deployment
status: approved
branch: change/296-docker28-classic
created: 2026-09-16
updated: 2026-09-16
---

# 执行计划草案

| Ticket | blocked_by | 交付与完成条件 |
|---|---|---|
| T01 | [] | 批准spec及本地专属VM/fixture范围；四文档独立合同提交后停止 |
| T02 | [T01] | fresh run实现新provision/preflight/real harness与静态回归，默认NOT RUN，生成精确approval-plan |
| T03 | [T02] | 创建两个专属VM，确认daemon版本/store/ID与checksum；预检PASS方可执行fixture |
| T04 | [T03] | 跨store Registry/offline完整lifecycle、重复执行/失败/回滚，保存不可变evidence，清理并回读自有资源 |
| T05 | [T04] | 仅真实PASS后追加精确矩阵行；更新当前boundary检查、反例及README |
| T06 | [T05] | focused/full smoke、语义文档/diff/secret检查，本地原子提交；唯一manual PR确认和CI读回 |

T02的fixture软件选型须查询当前官方文档并锁定正式下载来源、checksum与digest。
provision入口在未提供本Issue批准标记、名称不精确或已有资源冲突时零mutation退出。
审批marker不是授权来源，只是对本任务已有人工批准的程序校验。

T04任一必要项失败则不能进入T05；保留BLOCKED与根因，不能更新supported绕过失败。
如果classic只能通过Registry而不能通过现有offline合同，也不标完整支持，需先裁决更窄合同。

验证：新harness bash -n/ShellCheck；新fake正反例；release unittest；
现有evidence-boundary正反例；bash codex/tests/smoke.sh；
check-change-documents；git diff --check。
具体软件版本和资源分配入口在T02冻结后由T03读回，不依赖公司执行或公司网络。

## 后续项目阶段（不在本Issue实施）

1. NewEMaint冻结已合并平台runtime、应用release/digests与外部4000。
2. 准备宿主机专用部署身份、root-owned adapter、固定gate、target profile/grants、
   精确sudo allowlist与newemaint-test-deploy唯一标签的可审阅安装包。
3. 公司用户按独立授权安装/注册；verify-target后分阶段stage、独立数据库migration、activate/status。
   公司主机不能从Mac访问；所有现场操作由用户执行。


## 启动批准

2026-09-16用户明确“批准实施”。T01本轮固化合同；T02由读取已提交合同的独立实现上下文继续。

## 本轮执行结果

- T01 PASS：de26edc合同提交。
- T02 PARTIAL：cb3df34/f65a7a2/b73af5a/90b8150实现与修复最小身份门，完整public lifecycle未实施。
- T03 PASS：两台amd64专属VM精确版本/store/独立daemon ID预检通过。
- T04 BLOCKED：真实Registry pull与offline load完成，均被原_verify_content拒绝；完整lifecycle未执行。精确清理PASS。
- T05 NOT RUN：matrix原字节保持。
- T06 PARTIAL：140项release测试及16项专项PASS；完整smoke在既有registry-preflight负例FAIL；PR未提交。

2026-09-16用户“了解了，我已经批准。请继续”：T07独立固化已批准增补合同后结束合同编辑步骤，T08由fresh implementation context实现transport/runner最小身份投影及正反例，
然后恢复T02/T04/T05/T06。T04重新开始前，先将已清理实验的LAB目录按版本化入口归档，
保留原approval/evidence；禁止覆盖历史测试结果或复用未清理VM。

| 增补Ticket | blocked_by | 交付与完成条件 |
|---|---|---|
| T07 | [T03] | 已批准增补的独立合同提交，不修改runtime |
| T08 | [T07] | fresh context实现追加范围的身份兼容与正反例；完成后恢复T02/T04/T05/T06 |
