---
issue: 271
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/271
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - security
  - schema
depends_on:
  - 268
status: approved
branch: change/271-company-platform-baseline
created: 2026-09-06
updated: 2026-09-06
---

# 只读接管基线验证与最终 PR 候选

## 基线与范围

- exact worktree：`/private/tmp/issue-271-company-platform-baseline`；branch：`change/271-company-platform-baseline`。
- source 基线：`2a012bd832926b210581e84fbfd74b180490ca15`（#268 / PR #269 已合并）；#268 live=closed+completed 已读回。
- 本 Issue：#271 正文完整读回，comments=0；用户委托已批准只读合同/启动，未授权现场 mutation、push 或提交 PR。
- 实现：`41d3f8e3fe5f6c0744c0b06217c08957ad8c6df6`；审查修复：`89185edd0c80b72c3c729501c7c2a6f1f2070bf5`、`38052962da76ded5d02152c6c3f8566d1ce822c8`。最终 head 由交接卡读取，避免在提交内部自引用。
- 证据环境：本地 macOS Python/unittest、注入的 Linux fixed-host seam；不是公司 installed/live 证据。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker gitea.issue.read #271 | PASS | 正文与 exact repo=admin/aisoft-platform 一致；sandbox TRANSPORT_ERROR 后受控 host 路径读回，无公司连接 |
| broker gitea.protection.read | PASS（开发侧） | main direct/force push=false，manual admin merge，required `CI / verify (pull_request)`；不代表公司配置 |
| broker gitea.pulls.read --state open | PASS（开发侧） | `[]`，未创建 PR |
| analyzer AnalysisResult/from_yaml/route | PASS | platform / complex / contract_effect=add；required summary/spec/plan/verification |
| resolve-documents 271 --repo . | PASS | 四角色 exact slug/basename 映射；最初行内 YAML 数组错误已改为逐行列表 |
| apply-classification-labels.sh 271 dry-run/apply/verify | PASS | dry-run=set-classification；apply=updated；verify=projected，type/platform+complexity/complex |
| broker lifecycle approved / labels.read | PASS | live=approved+type/platform+complexity/complex；启动授权已复核 |
| Matt triage 标签投影 | GAP | 本地 brief=enhancement/ready-for-agent；broker 无该维度 typed writer，live 保留 triage/needs-triage；未扩大 broker 或 direct API 权限 |
| targeted unittest test_company_baseline.py | PASS | 最终 35 tests，0.444s，OK；无现场连接 |
| complete runtime unittest discover | PASS | 最终 `Ran 734 tests in 44.982s`，`OK`；35 项为本 Issue 新增测试；此前发现修复后重新执行 |
| check-change-documents --repo . | PASS | `changes=124 pass=2 gap=0`；最终提交前已再读回 |
| fixed command/HTTP/stat projection | PASS（local mock） | argv 白名单、两次相同状态结果一致、仅 8888/55432、两个 GET、两个 stat 目录；拒绝错误 host/digest 在探针前发生 |
| published schema vs CLI stdout | PASS | 测试按 bytes 比较；JSON 类型/未知字段/重复键、checksum/receipt/绑定/过期校验通过 |
| command block length | PASS | 3 段分别 1/7/7 行，均 <=50；现场 `python3 -I -S -B` |
| stdout broken pipe / injected PYTHONPATH | PASS（local subprocess） | exit20/stderr空；隔离模式忽略 sitecustomize 和 PYTHON* 注入；unsafe interpreter 先拒绝 |
| git diff --check | PASS | 每次本地提交前执行，最终检查 clean |
| shell bash -n / ShellCheck / bash codex/tests/smoke.sh | NOT RUN | 未修改或新增 shell、CI、installer、skills；运行完整 Python runtime suite 覆盖新增模块 |
| 远端 PR CI | NOT RUN | 尚未 push/建 PR，不用本地 tests 代替 CI |
| 公司盘点、重复现场运行、备份/恢复操作 | NOT RUN | 无批准 host pin/current 回流/可访问现场，按授权替代路径交付用户采集包 |

## 双轴 code-review

- Standards：首轮 1 个 P2：stdout 提前关闭时解释器 flush traceback。已用集中 emit、显式 flush、固定 exit20 修复；审查者实测 stderr 空，复核 PASS。
- Spec：首轮 1 个 P1 + 3 个 P2：health 任意 checks 可假 PASS、缺失 repo/sync 被迫填 SHA、Python 启动环境未隔离、schema 仅对象相等而非 bytes 相等。均已修复并补回归，复核 PASS。
- 最后一处 README health 判定说明已同步 exact database:ping/cache:ping。空仓、缺备份/恢复集可用 null 诚实表示；关键恢复 GAP 仍 BLOCKED，null-null 不产生 adopt，复核 PASS。
- 最终自检：Runner unknown 不能作为已知 GAP 进入整改候选；删除该枚举，未知必须保留 NOT RUN；负向回归 PASS。
- 审查未访问现场、未改动其他任务文件。输出结果为代码/规范审查结论，不是 installed/live 验收。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS（source/local） | 校验 host/role/environment/source/digest/UUID；错 pin 无探针；隔离启动；stdout-only 无配置文件 mutation |
| AC-2 | PASS（source/local）；现场 NOT RUN | 固定探针和人工记录覆盖 25 项，认证/ACL/object/network 独立；server/binary 分开；现场不伪造结果 |
| AC-3 | PASS（source/local） | 严格 schema、语义校验与全部负向用例；历史 PASS 无法填充 current |
| AC-4 | PASS（source/local） | adopt/remediation/BLOCKED 分支与 critical GAP、备份集一致性、缺失证据单测；mutation_authorized 恒 false |
| AC-5 | PASS（source/local） | checksum、独立 verify 与 supplement；schema bytes 一致；用户检查块和 B2/B3 卡位于 baseline/README |
| AC-6 | PASS（授权的替代交付） | 无公司访问时提供版本化 stdout collector、全部 NOT RUN 示例与 BLOCKED_EXTERNAL；无扩权或临时生产命令 |

## 当前公司基线与 B2/B3

公司 current：25/25 NOT RUN；接管结论 BLOCKED；没有任何现场 PASS。
历史版本/路径来自既有固定 target 合同与历史线索，只作为采集目标，不导入当前事实。
`blocked-envelope.example.json` 使用零 pins 和固定日期，只演示结构，不能当作本轮采集结果。

B2/B3 需要真实 current envelope、操作员审核事实及其 digest、批准主机与实例/仓库身份、备份和隔离恢复证据、差异清单；
后续 mutation 还依赖 #270 已合并 exact platform pin 与新的环境/版本/脚本/范围授权。
source merge 不代表公司安装或接管完成。

## 持久化交接状态

- 交互式本地候选：`AWAITING_PR_CONFIRMATION`；policy=`manual`；本 Issue 一个最终 PR。
- 本地提交之后等待用户按 exact #271/branch/manual 确认提交。确认后才可受控 push/建 PR，并继续当前合同内 CI 修复；required CI 通过停在 `READY_FOR_REVIEW`，由人审核合并。
- 本会话没有启动自动 Controller/provider；此处是交互式候选的持久化记录，不冒充 VM Loop 运行回执。
- 未执行：push、PR 创建、merge、deploy、安装、credential 读取/复制、主机写入、权限/UFW/数据库/服务/仓库/Runner/timer 变更和清理。
- 已知 GAP：triage live projector 缺口；公司 current 与 host pin 未取得。二者均明确保留，不通过另一身份绕过。

## 回滚

本地代码和文档可普通 revert。公司现场未执行 mutation，无本工具引入的状态需要回滚；无 backup/restore 实操授权。

## 最终源码字节

- `codex/runtime/aisoft_company_baseline.py` SHA-256：`3561d2f1fc607cdee1ba4688489645db1b2142cf57cc4d99433c35b1f33a7a88`。
- `company-delivery/baseline/inventory-v1.schema.json` SHA-256：`98663edac823c465600a8d0b01ab71778144a7372e146728a5702310ec39b8c6`。
