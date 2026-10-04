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
status: pending
branch: change/336-complete-pull-reads
created: 2026-10-04
updated: 2026-10-04
---

# #336 合同准备验证记录

## 基线与范围

- 初始 HEAD / `main` / `origin/main`：`e2edb3e08194624a6647212571c6cc866298575b`；runtime 候选 Commit SHA：尚无。
- Branch：`change/336-complete-pull-reads`；worktree：`/private/tmp/issue-336-complete-pull-reads`。
- Owner session：`01a100d7-2f34-7932-923d-781f3f255e09`，last push 为 null。
- 当前实际范围：本目录四角色合同草案；未应用三路径代码补丁。
- 环境：本机 docs-only worktree；网络证据仅通过 installed canonical typed broker 获取。
- 本阶段负责证明：独立立案与语义合同准备；AC-1～8 的最终源行为验收尚未开始。

## 执行结果

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

## Acceptance criteria 结果

| AC | 结论 | 证据/待执行项 |
|---|---|---|
| AC-1～4 | NOT RUN | 规格和历史 prototype 已具备；等待新合同确认与 fresh run 实现，随后执行新源夹具/回归；真实 typed 读取另记 installed 层 |
| AC-5 | NOT RUN | 冻结范围已写入 spec；最终代码/AST/operation/既有回归尚未执行 |
| AC-6 | NOT RUN | 不把草案文档检查或原型 217/330 提升为默认 smoke/PR CI |
| AC-7 | NOT RUN | 原型恢复 PASS 不能替代最终 exact delta 恢复证明 |
| AC-8 | NOT RUN | 当前仅完成合同边界声明；最终独立源交付、merged pin和安装缺口说明尚无 |

## 遗留风险与未完成项

合同待审阅，runtime 尚未启动。#327 合规发布能力与 installed compatibility 仍须在相应阶段 fresh 核验；本票不更改其他 owner 或 live 状态。安装端、现场和 Secret 动作没有授权，不通过混装/宽身份 fallback 解阻。

最终验证必须补齐每个 AC 的真实命令、exit code、exact head/tree/base与 evidence hash；未执行项保留 NOT RUN。本变更未部署，按模板删除部署验收章节。
