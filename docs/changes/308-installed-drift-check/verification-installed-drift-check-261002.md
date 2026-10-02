---
issue: 308
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/308
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - cross-module
  - ci-change
depends_on: []
status: pending
branch: change/308-installed-drift-check
created: 2026-10-02
updated: 2026-10-02
---

# Verification：基线与待验证范围

## 基线与范围

- 日期：2026-10-02（Asia/Shanghai）。
- 基线 HEAD/origin/main：`5c2cd726c9aeaee9d17541d8feb049e33881bbac`。
- worktree：`/private/tmp/issue-308-installed-drift-check`；session `01a0fc7b-d0b3-7802-af08-555307d048a6`，claim created。
- 下表为准备合同时一次性 Python 只读 inventory，尚非 #308 checker 的最终运行。只读源与受管 target、比较存在和 SHA-256，不运行 installed 程序；不能宣称 AC-1 已实现。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| installed broker `gitea.issue.read --number 308`（sandbox） | BLOCKED_EXTERNAL | TRANSPORT_ERROR |
| 同一 typed 请求受控 host 重试 | PASS | #308 open/needs-analysis，comments=0 |
| installed broker `gitea.issue.comments.read --number 308` | PASS | []，没有批准 |
| installed broker `git.fetch.main` | PASS | exact project aisoft-platform，remote origin |
| installed broker `gitea.pulls.read --state all`，筛 #308 head/body | PASS | []，未发现最终 PR |
| local `git worktree add` 后 `claim-worktree` | PASS | branch exact；owner 本会话；last_push_head=null |
| Mac `python3 -B` 一次性文件 inventory | GAP | 下表；没有写真实安装面 |
| gitea-ci `orb -m gitea-ci -u coder python3 -B -` 一次性模块 inventory | GAP | 下文；没有 sudo/重装/故意漂移 |
| protected main broker 只读回读 | PASS | enable_push=false；enable_force_push=false；required `CI / verify (pull_request)`；merge allowlist admin |
| #308 classification --apply / --verify | PASS | type/platform + complexity/complex，read-back projected；使用 byte-identical projector 临时副本，broker symlink exact installed 路径 |
| lifecycle `spec-drafting` | PASS | 保留 classification；未写 approved |
| triage brief 发布 | PASS | Issue comment 11977；合同草案尚未 push |
| #308 新 checker、反向 fixture | PASS（T02 local） | 22 tests；八个真实 installer 的隔离副本；不证明真实 installed |
| 完整 smoke，sandbox 默认环境 | BLOCKED_SANDBOX | loopback bind PermissionError；相同命令 host 重试 |
| 完整 smoke，host 默认环境 | FAIL | registry-preflight 停 registry fixture 期望 1、实际 0；保留原失败 |
| 完整 smoke，host `LC_ALL=C` | PASS（T03 接入前） | 978 runtime tests；全部既有 smoke 门通过 |
| 新 checker 的 smoke 集成、CI | NOT RUN | T03 独立治理接入待执行；最终 T04 fresh run；没有 PR |

## Mac 初始文件 inventory（非最终完整 checker）

| installer | 已匹配/expected | 初始结果 | 可读量 expected / installed |
|---|---|---|---|
| install-vm | 37/51 | GAP，14 个目标不符 | runtime modules 31/29；operations 36/31 |
| install-skills | 123/123 | 初始字节 PASS，active symlink 仍待完整验证 | skills 8/8；snapshot v1.2.2/releases/v1.2.2 |
| install-host-role | 4/4 | 初始字节 PASS | capabilities 20/20 |
| install-host-access-broker | 19/22 | GAP，3 个目标不符 | operations 36/36（计数等同仍漂移） |
| architecture/install | 0/25 | GAP，默认 prefix 缺失；真实另装 prefix 尚无证据 | revision 2026.09.0/missing；components 31/missing |
| docker-release/install | 0/25 | GAP，默认安装面缺失 | matrix revision 2026.09.1/missing；schemas 8/0 |
| sync/install | 0/5 | GAP，默认安装面缺失 | units 2/0；runtime scripts 2/0 |
| skill-for-claude/install | 5/5 | 初始字节 PASS，exact tree 待完整验证 | skills 2/2；references 3/3 |

Mac install-vm 缺少 `.local/lib/aisoft-loop/aisoft_loop/worktree.py`；cli.py/gitea.py/broker.py 等字节不符。broker 三处为 `/usr/local/lib/aisoft-host-access/aisoft_gitea_governance/contract.py`、`/usr/local/share/aisoft/gitea-governance.json`、`/usr/local/libexec/aisoft/bootstrap-gitea-service-account`。

这是按 installer 映射手动 inventory 的下限：尚不覆盖 install-vm 嵌套 skills、首次创建用户文件边界、全量链接/额外受管项/文件 mode；不得将初始 PASS 行升级为最终 installed 全 PASS。

## gitea-ci 初始模块 inventory（部分范围）

- `/home/coder/.local/lib/aisoft-loop/`：31 个 expected 模块，5 个 GAP：aisoft_loop/cli.py 字节差、aisoft_loop/worktree.py 缺失、aisoft_host_access/broker.py 字节差、aisoft_gitea_governance/contract.py 字节差、aisoft_worktree_owner.py 缺失。
- broker runtime：14 个 expected 模块，1 个 GAP：aisoft_gitea_governance/contract.py 字节差。
- 默认 `/usr/local/share/aisoft-architecture/catalog.json`、`/opt/aisoft-docker-release/docker-release-v1/compatibility/image-stores-v1.json`、`/opt/aisoft-sync/inbound-sync.sh` 不存在。
- 其它文件、8 个最终 installer 行及完整可读量：NOT RUN。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS（local fixture） | 八 installer 行、quantities、exact gaps、退出码；真实面结果待 T04 |
| AC-2 | GAP | Mac 当前至少 install-vm/broker 实际漂移及三组件默认缺失；保留原全 PASS 要求 |
| AC-3/4/6 | PASS（local fixture） | 22 tests：缺失/同量旧字节/恢复、写入 audit/tree 指纹、Secret/链接边界 |
| AC-5 | 部分 PASS，集成待 T03/T04 | source-only 八面通过，新增 installer/改 installer 拒绝；尚未接入 smoke |
| AC-7 | 部分基线 GAP，最终 NOT RUN | 两台初始 read-only inventory；非新工具验收 |
| AC-8 | PASS（local），fresh remote 待 T04 | checkout/HEAD/cached main；untracked、已删受管源、Git filter/环境隔离 fixture；无 fetch |

## 遗留风险与未完成项

AC-2 要求与当前实际安装面冲突，但不能删除标准或制造 PASS。详细处置留在 spec：先交付只读发现能力；安装/适用性另行明确裁决和授权，随后真实重跑。缺口存在期间不得宣称所有 AC 已完成或归档。

源、合同草案与局部 inventory 不证明 CI、安装同步、live 拒绝条件生效、现场或部署。未发生 push、PR、merge、installed 写入、sudo、凭据/权限变更、timer/服务变更。

## T01 治理步骤

- 用户“批准”收据：`evidence/contract-start-authorization.json`，包含批准前四份文档 SHA-256 与 exact Issue/branch/manual 边界。
- preflight：`evidence/contract-start-preflight.json`；approved 真实回读：`evidence/approved-contract-readback.json`。
- README/06 合同说明已补齐；T01 尚不执行新 checker、fixture 或 smoke。未改 shell，因此本步骤 bash -n/ShellCheck/full smoke 均 NOT RUN，后续 T02-T04 执行。
- 辅助校验脚本第一次误导入不存在的 aisoft_loop.matt，在 API 调用前失败；删除错误辅助 import 后 approved loader 校验 PASS。未修改仓库 runtime。
- initial frontier T01，完成后 next frontier T02；本轮到治理应用后停止，不在同轮实施 runtime。

## T02 实现与验证

新增薄 shell 入口、标准库 standalone checker、fixture harness。覆盖八个 installer 的所有受管非秘密文件，按存在/类型/字节和声明链接核对；保留 user-owned 配置边界。源定义以 installer 指纹、Matt 固定版本 manifest 及内容声明 fail closed；Git 身份仅用本地 raw tree metadata 和 Python blob 哈希，禁用可执行 clean filter 路径。

`evidence/t02-local-validation.json` 保存命令、日志指纹、源码指纹与阶段范围；`t02-targeted-tests.log` 为 22 项测试 PASS；`t02-source-only.json` 为八项 SOURCE PASS，执行时 HEAD 是初始 T02 候选、代码含后续未提交修订；source 候选的 managed bytes 与 cached main 等同，不证明 remote freshness。

两轴 code-review 初审发现 Standards 1 项 P2、Spec 3 项（最严重 P1）；修复后分别复审均无未关闭发现，详见 `evidence/t02-two-axis-review.md`。禁止以 review 静态结论替代真实验收。

完整 smoke 原环境阻断/失败与 `LC_ALL=C` 成功分别保留。此 smoke 尚不含新 checker 的 T03 hook，不能宣称集成门已验证。T02 完成后下一 frontier T03；T04 仍负责 fresh run 的全部门和两台真实只读证据。AC-2 GAP、CI/PR/安装/部署 NOT RUN。
