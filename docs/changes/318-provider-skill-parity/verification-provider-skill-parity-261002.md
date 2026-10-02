---
issue: 318
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/318
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: local-verified
branch: change/318-provider-skill-parity
created: 2026-10-02
updated: 2026-10-02
---

# Verification：审查与本地实施证据

## 基线与范围

- `main`/只读远端 `refs/heads/main`：`480d1d262c3e915f546049ede3f34ad7d3362f50`。
- 环境：macOS 本机、Asia/Shanghai；2026-10-02。
- 本 Change：`change/318-provider-skill-parity`，`/private/tmp/issue-318-provider-skill-parity`，已 claim，session=`codex-318-provider-skill-parity-20261002`。
- 初始草案阶段只有 overlay；随后已获批准并以 T01/T02 本地提交实施，见下方执行证据。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 本地/远端 SHA | PASS | `git ls-remote origin refs/heads/main` 与 HEAD 完整 SHA 相等 |
| 安装前 Codex drift | DRIFT | issue-session-flow/SKILL.md、aisoft-platform/references/onboarding-runbook.md |
| 安装前 Claude drift | DRIFT | issue-session-flow/SKILL.md |
| 两侧临时 home 安装/check-drift | PASS | `evidence/installed-stage.json`，两端 CLEAN |
| 本机两侧稳定源安装/check-drift | PASS | 两端 CLEAN；保留受管 skill backup，不改 credentials/runtime/provider/service |
| Codex Matt v1.2.2 | PASS | 上游 commit `8b36d4fb2635b3c21998dcd8144439c9e5ba7302`，35 skills、manifest-bound symlink/hash 验证 |
| 初始 baseline targeted parity | PASS | 27 tests，4.813s；候选为下方 38 tests |
| 提案 apply-check | PASS | 仅 `git apply --check`，治理源未应用 |
| 新合同断言对 baseline | EXPECTED FAIL | 6 tests，5 failures，0 errors；先红证明已定位缺口 |
| 新合同断言对提案 overlay | PASS | 6 tests；不代表批准/源码实施/安装完成 |
| 完整 smoke（沙箱） | BLOCKED | 本机 socket bind EPERM，日志保留 |
| 完整 smoke（受控 host） | FAIL | registry-preflight 停 registry fixture 期望1实际0，已独立定位 UTF-8/Bash 3.2 变量解析与 EXIT trap 问题，已立 #319；不得写为通过 |
| 完整 smoke（LC_ALL=C，受控 host） | PASS | 967 tests + static smoke；保留默认 UTF-8 的独立 #319 FAIL，不写成默认环境通过 |
| 真实 Codex/Claude 项目 acceptance | NOT RUN | 当前 static/synthetic 不能代替 real small/complex/CI feedback 与部署矩阵 |
| source 修订 | PASS | T01 dc77c93 + T02 b780eab；已批准范围内本地原子 commits |
| PR、required CI、合并、候选全局安装、部署 | NOT RUN | 等最终 PR 提交确认，Policy manual；部署不在范围 |

## 核心审查发现（baseline 行号）

1. `codex/skills/issue-session-flow/SKILL.md:13-20,60-66` 两确认点权限歧义；`:112-114` 缺 projected/闭窗与 exact merge→pinned 的收尾步骤。对照 `skill-for-claude/issue-session-flow/SKILL.md:146-170`。
2. `skill-for-codex/SKILL.md:102-109` 只有 Controller 自动回填；Mac interactive broker PR 需显式 backfill（Claude `aisoft-platform/SKILL.md:32-40`）。
3. shared `onboarding-runbook.md:300` 错写第一点授权；`:333-338` 缺 deployment_lifecycle；`:291,329` 旧 provider 顺序。
4. `08-双工具共存与实施.md:44-45` 未同步 #298；正确规则在 03 与两侧 session flow。
5. `codex/runtime/tests/test_routine_merge.py:64-82` 原覆盖不足。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1/2/3/4 | PASS (source/local) | T01 四源修订、fresh T02、12 tests/27 mutations、独立只读复核 |
| AC-5 | PASS (C locale) | 候选 targeted 38 PASS，C locale full smoke 978 PASS；baseline 6/5 expected fail；默认 UTF-8 #319 FAIL 仍独立保留 |
| AC-6 | PARTIAL | 合同已批准，branch/claim/独立治理步骤/fresh read PASS；PR/CI/merge/候选全局 install/fresh adoption NOT RUN |

## 遗留风险与未完成项

spec/start 已确认并完成本地治理修订；等待唯一最终 PR 提交确认。后续项目通过自己的 project-align/provider matrix；#293 记录的下游 release_producer/transport GAP 是历史线索，当前未核对或修改下游。#308 自动 drift 监测、#316 PAT 轮换、#317 数据迁移回退等独立范围不代做。通用下游 checker 对中央平台本仓返回三个应用模板/architecture GAP；它不是中央文档平台验收矩阵，不据此创建虚假应用架构或改写当前 AGENTS。

## 本机 host broker 安装读回

`host.onboarding.check --project aisoft-platform`：PASS，但只证明已安装合同下的该仓接入。只读字节核对确认 #298/#312 已安装，#313 未安装：`/usr/local/share/aisoft/gitea-governance.json` 与 `/usr/local/lib/aisoft-host-access/aisoft_gitea_governance/contract.py` 精确匹配 `3ff6972` 而非 `480d1d2`；其余相关 13 个 Python 源文件及 host-access-broker/gitea-labels manifest 与 main 一致。routine scope 仍为 write:repository，缺 read:user。此运维/凭据边界不是 Codex 单侧故障，#318 不代做安装或 PAT 操作。

## 新项目采用方式

共享 AGENTS.md、Claude 指针 @AGENTS.md、docs/agents tracker 与平台模板保持一致；Codex 用本机受管技能。每个新项目先 exact project onboarding，再 project-align 盘点，遗漏通过该业务项目自己的 Issue/Change/唯一 PR 回补。各 provider 的真实 small/complex、普通修复、CI feedback、权限和部署范围独立验收，默认 IMPLEMENT_PROVIDER=none。

## 合同/启动确认

2026-10-02 用户明确回复“确认”，授权 #318 映射 spec/plan 启动。确认绑定 Issue 318 与 change/318-provider-skill-parity、manual policy。原始 spec/plan/proposal SHA256 与确认范围保存在 evidence/contract-start-authorization.json；PR 提交、merge、部署未授权。T01 为独立受控治理应用，完成后 fresh agent 重新读取本 worktree 指导执行 T02。

## T01 已执行的受控治理步骤

独立 worker fresh 读取旧合同与已批准 spec，仅应用四份技能/共享指导，原子 commit `dc77c93b3c92534b3f1e796dce896ea15fc43e56`；branch/claim、scope、正反补丁预检、diff --check 均 PASS。此步骤已停止；AGENTS.md、runtime、测试未改。下一个独立 fresh agent 重新读取新指导执行 T02。判级 projector apply/verify #318 已真实执行，verify result=projected；生命周期读回 approved + complexity/complex + type/platform。

## T02 fresh run 与候选验证

- fresh read 9 个文件，包括新治理指导，治理 commit 为 dc77c93；收据 evidence/t02-fresh-read.json。
- targeted：38 tests / 5.090s / exit 0，evidence/t02-targeted.log。
- full：LC_ALL=C bash codex/tests/smoke.sh，978 tests / 86.601s / exit 0 + static smoke PASS，evidence/t02-smoke-C.log。默认 UTF-8 #319 仍 FAIL，未借 C locale 宣称默认环境修复。
- 12 个 SessionContractTests，6 类 mutation tests / 27 个内存变异；独立 reviewer PASS。类外 AST 与 T01 完全一致；仅测试文件 +261。旧 Git blob 只在内存中测试：6 tests / 5 expected failures / 0 errors，未回滚四个治理源。
- T02 原子 commit b780eabb293fb000b36c0b7e01a74b44f3b2547d，branch/claim/scope/diff-check PASS。
- 两端仅在临时 home 安装候选，check-drift 均 CLEAN；3 份共享 references byte-identical，evidence/candidate-staged-skills.json。没有把 candidate 装到全局目录。

## 独立衍生问题

#320 记录既有“pushed_head 永远比对确认点 2 SHA”措辞在合法 summary/CI 后续 commit 上的语义歧义；当前未证明 runtime 故障。保持 #318 已批准规则与四源范围，不顺手改写新合同。

## 冻结前复核

#318 判级再次真实读回 projected，收据 evidence/classification-read-back.json。开放 PR 枚举为空。最新 broker git.fetch.main 完成，最终候选须为 origin/main 的本地快进后代，无 main behind；当前未 remote push。semantic audit 在更新后的四份文档上 PASS（changes=144、pass=2、gap=0）。

## 提案证据归档

原始 unified diff 的空白 context 标记必须含结构空格，直接作为新增文档触发 git whitespace 检查。为完整保存已批准提案，将原字节确定性 gzip 归档，解压 SHA256 为 `cc12b6937c3905b8f9f97f42f4c4d54713ed799e527a0797b7f651c51523690d`，未改任何治理补丁字节；另保留可直接阅读的原始副本。收据 evidence/proposal-archive.json。源码与语义文档仍执行正常 diff --check，不关闭 whitespace gate。
