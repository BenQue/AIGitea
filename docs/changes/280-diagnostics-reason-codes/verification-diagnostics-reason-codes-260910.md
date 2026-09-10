---
issue: 280
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/280
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - security
  - deployment
depends_on: []
status: approved
branch: change/280-diagnostics-reason-codes
created: 2026-09-10
updated: 2026-09-10
---

# 验证记录

## 基线与范围

- origin/main fresh broker fetch PASS；基点 de4581ede598150904695a1821c5489e9cd9a6ad。
- 本地 branch change/280-diagnostics-reason-codes，worktree /private/tmp/issue-280-diagnostics-reason-codes。
- 平台 phase=production（manifest 未声明 change_control）；用户后续明确“实施批准”；已通过 broker 投影 approved。
- v1 collector SHA-256 732c4a871c6ecdb77285f3fcc7d31e20b27cf353ab75b4f368ee3aeedf41a3ac。
- 现场回执仍由下游项目保管；平台只保留合成复现结论，不复制 profile、原始配置或 Secret。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker gitea.issue.list --state all | PASS | 146 Issues，无开放重复票；#278 closed |
| broker gitea.issue.create/read #280 | PASS | 立案时 open/needs-analysis，回读正文相同；实施批准后 labels 已更新并读回 approved/complexity/complex/type/platform |
| python3 -I -S -B /private/tmp/newemaint-79-diagnostics-repro.py | PASS | 前一复现阶段实际运行，12 cases/assertions PASS，host_probes=0 |
| v1 exact source SHA guard | PASS | 脚本 git show 固定 commit 后校验 collector hash |
| resolve-documents 280 | PASS | 四个角色精确解析到本目录实名文档 |
| check-change-documents --repo /private/tmp/issue-280-diagnostics-reason-codes | PASS | changes=129 pass=2 gap=0；change-documents 与 change-pr-url 均通过 |
| v2 targeted suite | PASS | 25/25；第二次在全套兼容回归中再次通过 |
| v2 + diagnostics v1 + baseline v2/v1 | PASS | 104/104，Python 3.14.4；所有服务/UFW/config 探针替换为 fixture，未连接公司 |
| v1 byte guard | PASS | v1 collector/schema/builder/guide SHA-256 固定不变 |
| builder fixture | PASS | 两个新目录内容相同；模式/内容/manifest/额外文件/symlink/source/schema/profile 漂移均拒绝 |
| installed/live | NOT RUN | 本票无现场操作 |

复现脚本 SHA-256 e7bbd2d08c21e0d8bb980687af6da81000698f45c553a52d7a9d741820e74dd5；
报告 /private/tmp/newemaint-79-diagnostics-findings.md SHA-256
aa2b93735069f2fbf448d4747b3638907a8b914948fe1d49b3a3f95aad280aec。
脚本由精确 Git object 编译模块；server file、invoke/config、host/platform 全 mock，
Popen 禁止调用。初始复现仅检查 run 源码；本轮新增 test_run_control_flow_with_mocked_io 与 timeout cleanup 测试，已实际覆盖 run 层 timeout/limit/decode/rc/startup。

基线观测：显式 http PASS；missing/commented/https 同值 GAP；有效合成 UFW PASS；inactive GAP；
nonzero/empty/unknown line/missing profiles/timeout/missing executable 全部同值 BLOCKED。
此结果证明诊断信息缺口，不证明 unknown/missing profiles 样例是合法现场 UFW 输出，也不证明
现场 PROTOCOL 缺失。新原因码测试完成后仍不能将 source/local PASS 代替 current UFW 策略证据。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS（local） | protocol presence table、固定配置投影与 unsafe/duplicate 负例 |
| AC-2 | PASS（local） | command/config reason table、run mocked IO/timeout cleanup |
| AC-3 | PASS（local） | strict UFW normalization、missing metadata/unknown line fail closed |
| AC-4 | PASS（local） | v1 bytes guard、版本拒绝、checksum/status/pin/freshness 负例及旧版回归 |
| AC-5 | PASS（local） | AST/固定 argv guard、stderr 哨兵、mock run/配置安全读取 |
| AC-6 | PASS（local） | targeted 25/25，包含新旧版回归 104/104；新 suite 已运行两次 |
| AC-7 | PASS（local） | exact Git fixture builder 两目录一致、故意 drift、profile/mode/symlink/extra-file 负例 |

## 遗留风险与未完成项

### Exact local commit 候选包

实现提交 cac60745c1060151ff4fec4854f23a36787e5ba4 已完成。以该 exact commit、测试合成 profile
（SHA-256 231c0ac11c02b46b7a481421a3a058b5008610dc91dbddf63f0537f39dda9e49）分别运行新 builder build：
/private/tmp/diagnostics-280-local-review-a 与 /private/tmp/diagnostics-280-local-review-b，均 PASS/6 files。
再对 a 运行 verify 亦 PASS；两个 manifest SHA-256 均为
a609f3b176f5179aac695281d431d5f163d6ca9b26c916ad8f777a4fa5363a86。

- collector SHA-256：a3e7487e017479d4438e720b517cf369661ae3591336fa39ff55c4d53f66714c。
- schema SHA-256：56f24777e08e6e15afd5ea2738ead4851553f44f147a5cc1c186575fb5cd7241。
- builder SHA-256：d86d18010cb9dcf18d75028f4e05a9bb29bd44c8d0eba87b967897ba65b1c807。

这是未合并 source/local candidate，不是公司 handoff；不包含公司 profile，不授权拷贝或运行。
本节为该实现提交之后的文档回填，不改变 candidate 所固定的 source SHA。

T01–T03 本地实现与测试已完成；没有 push/PR、merge、安装或现场调用。下一闸门为最终 PR 提交确认；人工 merge 和下游公司复采独立。现场 UFW 根因仍未知，不能由本地测试推断。
