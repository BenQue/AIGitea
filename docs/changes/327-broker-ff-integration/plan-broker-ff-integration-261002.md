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

# #327 实施计划与 fresh frontier

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 独立只修改spec映射治理合同的受控本地步骤；验证范围、原子commit后停止 | - | completed |
| T04 | 具体补充合同经直接确认；本次独立应用原14治理文本+四角色、验证/本地commit后STOP；runtime未实施 | T01 | completed |
| T02 | T04之后fresh重读，实施authority/受控执行证据、Controller限定整合、broker ordinaryFF/guard/独立验证与bare-remote回归；纳入安装/漂移 | T04 | pending |
| T03 | 集成/全量/静态/文档验收、source与installed分层、人工firstPR/安装rollback卡，准备唯一manualPR候选 | T02 | pending |

T01 原治理已于 `061b0f3ec59869fe379d70b7d2f0455df4b8708a` 独立提交并停止。fresh T02 分析发现可信根缺口；没有 runtime/新接口变更。负责人“按建议继续”仅选择 A 路线准备，四角色草案 ac172e515a47357d24ff268473af6bbee5c13fe1 不算 T04；随后本聊天直接“确认”本份具体合同，本次独立治理应用才是 T04。

新增 T04 保留原 ticket ID/历史，置于 T02 之前。本次已获审阅卡 exact draft/spec/plan SHA256 的具体确认，在独立治理 run 执行 T04，只改原14治理文件+四角色，应用/验证/local commit 后 STOP。批准与提交后 SHA 分别保存在外部 receipt，避免本提交自引用。后续 fresh run 重读，live 分类/approved 投影、installed/capability 和 grant 状态均真实核对，T02 才能实施其新 source 范围。任何 runtime/config/service 不得混入 T04。

T02/T03 本地实施许可不授权 push/PR。人工 UI 发表 B01、合并后 I01 文件安装及 I02 authority 注册/启动验收均是 graph 外的独立受控阶段，不等待未合并代码先安装才能准备源码 PR。最终 PR 确认只问一次；其 protected 登记不作新的业务决定，CI repair 每次 exact H 重验而不逐 commit 问。
## Expected touch points

exact 清单由 spec 原治理/runtime 表与新可信根扩展表逐项定义。新增 source 表已具体确认，但不能在本 T04 run 使用。T01 已完成；T04仅原14治理表+四角色；T02仅获确认的 runtime/可信根表；T03只更新四份证据和外部脱敏 B01/I01/I02 卡。新文件新增模式限100644；固定运行hook若由runtime临时生成必须隔离保护、不得变为额外可配置入口。

所有stage保持owner `01a0fcec-eb78-7790-a36a-daea917f43d2`；branch `change/327-broker-ff-integration`；worktree `/private/tmp/issue-327-broker-ff-integration`。commit包含 #327 与Txx；不接受他人代做整合/rebase。

## 数据库迁移

无数据库迁移。新 protected grant/record schema 是独立初始化的 `change-grant/v1` / `change-record/v1`；无自动旧状态升级。owner/progress 只作兼容审计/引用，不升级成批准记录；缺可信证据必须 fail closed/adoption review。状态丢失、旧 root 或异常 remote 不重置 R0。

## 测试与验收映射

| AC | Ticket / 外部阶段 | Verification command or review |
|---|---|---|
| AC-1 | T01/T04；T03 | `resolve-documents 327`、`check-change-documents`、判级只读plan/verify；T01 exactdiff+commit清单与STOP receipt；fresh-run重读hash |
| AC-2 | T02 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p test_main_integration.py -v`；真实临时bare remote正向DAG/tree/ref证据 |
| AC-3 | T02 | 同integration fixture：预读/传输公告两窗口注入race，包括R1祖先候选、首次ref存在抢占、删重建；拒绝前后ref/argv |
| AC-4 | T02 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p test_host_access.py -v`；`test_controller.py`、`test_worktree_owner.py`定向；pre-mutation remote保持与provider gate |
| AC-5 | T02/T03 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -v`；`bash codex/tests/smoke.sh`；真实remote读回、receipt failure和freshness后漂移 |
| AC-6 | T03准备/B01执行 | bundle/patch/tree/blob/mode card；本人UI发表；broker fetch H/main/PR/status/actions；导出H在隔离目录重跑本地门；唯一humanPR/merge读回 |
| AC-7 | T03准备/I01执行 | 两机exact批准后，versioned installer、逐文件before/after owner/mode/hash、realFF/no-op/reject/rollback；全部前后ref与main保护读回 |
| AC-8 | T03/B01/I01 | `gitea.protection.read`、manifest byte diff、单writer scan、同Issue唯一PR读回；原owner采用receipt或保持NOT RUN |
| AC-9 | T04；T02/T03；I02 | 对 `test_change_evidence.py` / `test_verification_authority.py` / `test_verifier.py` / `test_state.py` / `test_contract.py` 分别执行 unittest discover；新文件存在后才运行；真实 peer、privilege/FS/exec/socket negative、grant/record/adoption/replay/restart/default-disabled + 两机 I02 受控实证 |

每个定向unittest分别使用上行discover格式，只更换 -p 的exact文件名；新integration测试文件必须真实存在后才能执行。每次变动shell须运行对应 `bash -n`、可用ShellCheck及完整smoke。fixture只能本地临时remote；不创建live canary Issue/PR来伪装隔离测试。

完整smoke按默认host locale实际执行。若#319尚未入main而registry UTF-8 fixture FAIL，保存原失败、不修别人的6处Bash；LC_ALL=C可作诊断单独标注，不能替代默认结果PASS。future fresh main若已有修复，不继承旧FAIL或PASS，重读实跑。

## 可信根 source 分步验收

T02 同一 ticket 内按以下依赖推进：strict schema/冻结政策与 scope → default-disabled fixed client/server/OS peer → protected operator grant 与受控 generation/非 root sandbox execution → per-commit/完整 delta 与限定 integration checkpoint → 独立 broker重算+protected PR授权+strict R ordinary FF → installer/drift/inert unit 和全量回归。任何阶段缺可信输入均 fail closed，不能先发布“暂用本地 PASS”的版本；不改既有 required gate 或让 fixture 开关进入 public runtime。

必须区分 unit/mock、真实普通用户 Unix socket/bare remote、真实 root custody 与 installed/live。无权限环境的 root/另UID/服务测试真实 NOT RUN/GAP，不能 monkeypatch UID 后写 PASS。两机 I02 之前 source merge 不表示功能启用，不自动创建授权记录。

I02 卡须完整列出实际 root runtime/interpreter/Git hash、registered existing UID/GID、隔离能力、socket/context/state/service 前态、grant/业务批准与 protected PR确认登记、停止/恢复对象、真实 FF/negative/restart/rollback 目标。source-only smoke 不代替这些项；不自动 provision credential/账户/SDK auth/profile/provider/timer。

## 风险与失败分支

- 非FF或未知remote/provenance：fail closed，不 rebase已发表历史、不force；不删除重建branch。
- 合并冲突/范围变化/不支持Git：NEEDS_HUMAN_DECISION，保全原候选；超出最小无冲突合同须明确裁决。
- 外部UI不能保留tree/mode：B01阻塞；不先装unmerged版本，不directGit/API，重新交负责人具体路径决定。
- 相同外部根因连续三次：BLOCKED_EXTERNAL；不空提交重试CI、不移除CI/action硬门。
- postpush readback不明：可能已落地，先只读取证再决策，不force恢复。
- main在publish后推进：保留已发表H，再整合/重验；不按旧CI通知merge。

## 发布、安装与回滚

B01先取得绑定#327/branch/manual的最终PR提交确认，使用spec人工UI卡；owner不代提交。H不同于L，exact新H验收、summary唯一URL回填与requiredCI均重新取证；manual合并只由人。

I01只在源码merge且fresh stable pin后，分别取得Mac/gitea-ci exact安装批准。只改安装卡列出的受管byte/mode/owner；不继承#316授权、不启用profile/service/provider、不涉及credential或应用部署。完整旧态保全、两次执行/no-op、故意失败rollback与新行为realFF实证均必须完成。

AC-7/AC-9 未闭合保持本 Issue 实际未完成与 chat 可用；见spec自动closed后的typedopen保留验收规则。AC全闭合后确定性terminal/document/cleanup/archive，无新增确认点。
