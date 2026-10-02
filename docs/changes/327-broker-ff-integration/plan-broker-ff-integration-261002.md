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
| T02 | fresh run重读后完成Controller限定整合、broker ordinaryFF/guard/独立验证与真实bare-remote回归，纳入安装/漂移映射 | T01 | pending |
| T03 | 集成/全量/静态/文档验收、source与installed分层、人工firstPR/安装rollback卡，准备唯一manualPR候选 | T02 | pending |

T01不是普通provider修改自身governing文件的许可：必须独立治理应用步骤只含合同映射文本，应用后立即停止。runtime不在同一次run实施；fresh run读取新合同与批准记录，frontier才变为T02。合同准备阶段没有执行 T01 或 commit；负责人随后直接确认，本次独立治理提交完成 T01。提交 SHA、精确父提交和 STOP 记录由 Git 及外部 T01 receipt 读回，避免在本提交中自引用 SHA。后续 frontier 为 T02，但本轮不得启动。

合同已确认，但本轮只启动 T01；后续 fresh run 的 T02/T03 启动仍需重读合同、Issue/评论和 installed 能力，并先复核尚缺的 live approved/分类投影。不授权 push/PR；本地完整后进入AWAITING_PR_CONFIRMATION。人工UI发表B01与合并后安装I01是外部人工/受控验收阶段，不放进provider ticket graph假装可自动运行；这样不会等待尚未可安装的版本而无法准备源码PR。

## Expected touch points

exact清单只由spec两张映射表授权。T01仅治理表及四份本Issue语义文档；T02仅runtime表的实现/测试/受管映射；T03更新四份合同证据及脱敏执行卡。新文件新增模式限100644；固定运行hook若由runtime临时生成必须隔离保护、不得变为额外可配置入口。

所有stage保持owner `01a0fcec-eb78-7790-a36a-daea917f43d2`；branch `change/327-broker-ff-integration`；worktree `/private/tmp/issue-327-broker-ff-integration`。commit包含 #327 与Txx；不接受他人代做整合/rebase。

## 数据库迁移

无。owner/receipt字段如需追加，向后兼容原claim；缺少新的可信证据不能伪造R0/provenance，必须fail closed/adoption review。

## 测试与验收映射

| AC | Ticket / 外部阶段 | Verification command or review |
|---|---|---|
| AC-1 | T01；T03 | `resolve-documents 327`、`check-change-documents`、判级只读plan/verify；T01 exactdiff+commit清单与STOP receipt；fresh-run重读hash |
| AC-2 | T02 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p test_main_integration.py -v`；真实临时bare remote正向DAG/tree/ref证据 |
| AC-3 | T02 | 同integration fixture：预读/传输公告两窗口注入race，包括R1祖先候选、首次ref存在抢占、删重建；拒绝前后ref/argv |
| AC-4 | T02 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p test_host_access.py -v`；`test_controller.py`、`test_worktree_owner.py`定向；pre-mutation remote保持与provider gate |
| AC-5 | T02/T03 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -v`；`bash codex/tests/smoke.sh`；真实remote读回、receipt failure和freshness后漂移 |
| AC-6 | T03准备/B01执行 | bundle/patch/tree/blob/mode card；本人UI发表；broker fetch H/main/PR/status/actions；导出H在隔离目录重跑本地门；唯一humanPR/merge读回 |
| AC-7 | T03准备/I01执行 | 两机exact批准后，versioned installer、逐文件before/after owner/mode/hash、realFF/no-op/reject/rollback；全部前后ref与main保护读回 |
| AC-8 | T03/B01/I01 | `gitea.protection.read`、manifest byte diff、单writer scan、同Issue唯一PR读回；原owner采用receipt或保持NOT RUN |

每个定向unittest分别使用上行discover格式，只更换 -p 的exact文件名；新integration测试文件必须真实存在后才能执行。每次变动shell须运行对应 `bash -n`、可用ShellCheck及完整smoke。fixture只能本地临时remote；不创建live canary Issue/PR来伪装隔离测试。

完整smoke按默认host locale实际执行。若#319尚未入main而registry UTF-8 fixture FAIL，保存原失败、不修别人的6处Bash；LC_ALL=C可作诊断单独标注，不能替代默认结果PASS。future fresh main若已有修复，不继承旧FAIL或PASS，重读实跑。

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

AC-7未闭合保持本Issue真实未完成与chat可用；见spec自动closed后的typedopen保留验收规则。AC全闭合后确定性terminal/document/cleanup/archive，无新增确认点。
