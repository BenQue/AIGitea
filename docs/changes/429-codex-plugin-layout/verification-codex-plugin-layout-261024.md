---
issue: 429
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/429
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - external-contract
depends_on: []
branch: change/429-codex-plugin-layout
created: 2026-10-24
updated: 2026-10-25
---

# 验证记录

## 来源与边界

change_base：08aac8d5b9af4d334c53bcf34029870f09e50bf0；writer：01a16b94-fd7f-7842-852c-af5e58c3f9df；provider：Codex；执行入口 Matt implement v1.3.1。本机目录/配置只读，凭据不读取。

## Before

旧 main 的实际输出：SUPERPOWERS codex PIN_NOT_INSTALLED enabled=superpowers@openai-curated marketplace=unregistered cached=5.1.3 pinned=7.0.0；RESULT PASS，exit 0。
配置明确 enabled=true；当前会话可见插件的元数据为 superpowers / 7.0.1，路径位于 openai-curated-remote/superpowers/7.0.1。

## 执行与核验

T01 使用原始开始回执，ticket_base 为 3715f09b89b18291f0765f826ea88616bc2f8e0f；起始 staged/unstaged/untracked 均为空。任务语义 SHA256：50c578826c83ea824e1ac8ea28ebfdb97cbb951b1799c399477cea34fce59eb2；policy SHA256：184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40。Codex 实际模型/推理强度未由 runtime 暴露，不将路由要求 frontier/max 冒充运行观测。

| 检查 | 实际结果 |
|---|---|
| RED-1：初始新布局+旧缓存 fixture 对未修改检查器 | exit 1（测试失败）；旧检查器实际 PIN_NOT_INSTALLED cached=5.1.3、RESULT PASS / exit 0，符合缺陷复现预期 |
| RED-2：加入实机安装标记的 fixture 对初版修复 | exit 1（测试失败）；把常规安装标记误计成第二个版本，UNKNOWN，未能报告实际版本；已修复 |
| bash codex/tests/test-external-skill-versions.sh | PASS / exit 0；包含已启用/禁用/缺配置、新旧布局回退、旁车标记、单/多版本、错元数据、JSON重复key、路径链接、异常类型/FIFO、权限错误、能力汇总与零写入 |
| bash -n codex/tests/test-external-skill-versions.sh | PASS / exit 0 |
| shellcheck codex/tests/test-external-skill-versions.sh | PASS / exit 0 |
| bash codex/tests/smoke.sh（R1候选） | PASS / exit 0；宿主授权环境原样完整重跑，含746项runtime、46项installed drift及其它脚本检查，最终Codex platform static smoke checks passed。日志 /private/tmp/issue-429-smoke-final.log。首次嵌套沙箱中止仅为执行环境失败，不记通过 |
| bash codex/tools/check-external-skill-versions.sh --home /Users/benque | PASS（符合预期的诊断结果，命令 exit 1）；日志 /private/tmp/issue-429-live-verification.json |
| 文档、判级与diff检查 | check-change-documents两项PASS；classify --verify读回bugfix/complex、applied=false；git diff --check PASS。固定候选、Codex双轴与Claude独立审查均已实际通过，详见下方对应HEAD记录 |

实机 After：

```text
CLI claude 2.1.309
CLI codex 0.164.0
SUPERPOWERS claude PIN_CLEAN installed=7.0.0 commit=pinned pinned=7.0.0
SUPERPOWERS codex PIN_DRIFT enabled=superpowers@openai-curated marketplace=builtin layout=openai-curated-remote installed=7.0.1 pinned=7.0.0
MATT claude PIN_CLEAN
RESULT REVIEW_NEEDED
```

实机 Codex config、Superpowers plugin.json、安装标记与 Claude installed_plugins.json 的 SHA256 前后相等；fixture 的 HOME/链接目标也做了前后快照。只读安装版本证据不等于新的 provider session 行为验收。Cursor 在未传 --repo 时仍为 NOT_CHECKED，缓存注释保持原行为。

远端 CI、安装、插件升级、fresh-session 功能验收、PR、merge：NOT RUN。

## Findings

首轮固定候选 994c2db9f5edce400ccaa631159cb1fba27ced1d；T01 BASE 3715f09b89b18291f0765f826ea88616bc2f8e0f；整批 BASE 08aac8d5b9af4d334c53bcf34029870f09e50bf0。mechanical_checks=PASS；package_sha256=a3b36088d050aca3eeadf821cff3f7ff37078725a195b156ebf339abe9088923；候选无遗漏 staged/unstaged/untracked。

| 轮次 | 轴 | 审查方 | 结论 | 发现与处置 |
|---|---|---|---|---|
| R1 | Standards | Codex 子代理 review429_standards，继承模型配置 | FAIL（1项P2） | F1：.codex父目录为链接时，在拒绝链接前先读取了链接外config；此为新合同未兑现，不称为新引入的任意读取漏洞 |
| R1 | Spec | Codex 子代理 review429_spec，继承模型配置 | FAIL（1项P2） | 同一F1违反AC-3；两个轴独立报告、没有以一个轴覆盖另一个 |

F1 已将 .codex lstat 检查前移至任何配置读取之前。新增顶层执行路径的 Python audit hook 反例：旧候选真实尝试打开链接外配置并触发 AssertionError；修复后 UNKNOWN且无该open事件。未改真实HOME。定向回归、bash -n、ShellCheck及实机复核再次通过；该修复后的完整smoke已在宿主授权环境原样重跑PASS / exit 0（746项runtime及46项installed drift、其它脚本门均通过），日志 /private/tmp/issue-429-smoke-r2.log；尾部Codex platform static smoke checks passed。R2固定HEAD 02a4c604a89fa4695057f023c76ead799be4ce9c 的两轴复审已完成，独立探针均得到UNKNOWN且files_read=[]；Standards PASS、Spec PASS，各轴fixed=1、residual=0、new=0。R1完整审查加R2全部增量覆盖原始T01及整批BASE到该HEAD。未将R1结论直接沿用。

另修复整批 git diff --check 发现的三处EOF空白行。plan只把证据区之后的空白移到证据标记之前，清除证据区后的完整语义文本及SHA256保持不变；原回执仍有效。

R2机械候选包sha256=34d04870eb26fc3e70872196cb7edfde5776a78b33e746578d181aab0c10c42c；原回执/owner/branch、任务语义摘要均一致，工作区干净，整批diff --check通过。两轴回执保存于 /private/tmp/issue-429-local-reviews-r2.json，并在下面持久化。08ef62fcc41f6b2876d92dbe11e55a70219c9fd1 的最终三份文档增量已由原两轴复核，均PASS（fixed=1、residual=0、new=0）；代码和测试与R2相同。/private/tmp/issue-429-local-reviews-final.json 已取得并经validate_reviews绑定候选包94bba3c533db6e111ee2d661bcf39c405ff6cb1262aa27aa304b22d5fde19ad6，本节结构化证据同步持久化这份最终回执。

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 请求1 | Codex | Claude Code（未实际调用） | 994c2db9f5edce400ccaa631159cb1fba27ced1d | NOT RUN | 自动审批在进程启动前拒绝：完整diff含非公开源码，缺少向该外部模型服务发送本批材料的明确授权。未发送、未换通道重试，不当成review FAIL或PASS；需用户明确授权后继续 |
| R1 | Codex | Claude Code（claude-fable-5-1 / high，fresh，只读） | 08ef62fcc41f6b2876d92dbe11e55a70219c9fd1 | PASS | 0阻断；3条P3观察已登记边界并补证，代码无需变更；结果与session见下文 |

2026-10-25，用户明确授权：“同意，授权将 #429 的 diff 和相关规范发送给本机配置的 Claude Code 模型服务，继续只读交叉审查及必要复审。”同一服务调用重新送审后获准，未更换目的地或绕过审批。最终PR提交仍保留确认点2。

R1实际调用沿用本机模型配置fable[1m]，请求effort=high；实际返回model=claude-fable-5-1，session=dcb1a530-f92f-4f68-bd12-1984199473f6，duration_ms=223534，num_turns=20，is_error=false，permission_denials=[]。调用采用safe-mode、禁用skills/plugins/hooks、仅Read/Glob/Grep、plan权限、无会话持久化。结果原文：/private/tmp/issue-429-claude-r1.json；审查完整change BASE 08aac8d5b9af4d334c53bcf34029870f09e50bf0到上述HEAD，含所有四个提交，不限HEAD~1。

Standards PASS、Spec PASS、总PASS；0阻断，3条非阻断P3观察的处置如下：

1. 额外非标记条目（如.DS_Store）会参与候选计数并使目录UNKNOWN；“versions recorded”诊断文字可能把非版本条目也计为版本。这是当前保守识别边界，记录而不扩大过滤规则，未变更代码。
2. .codex本身为链接时，旧marketplace路径同样被拒绝为UNKNOWN。这是AC-3有意要求的读取边界收紧；配置读取前即拒绝，不穿透链接。
3. 将08ef62fc的Codex两轴回执写入本节结构化证据，补齐其只存于临时文件的记录。历史02a4c604结果仍保留在正文，避免混用不同HEAD。

2026-10-25另以08ef62fc原样运行真实HOME只读核验，Codex仍准确PIN_DRIFT 7.0.1 / pin7.0.0、Claude PIN_CLEAN7.0.0，命令exit 1为预期版本差异；四份配置/元数据hash前后相等。回执：/private/tmp/issue-429-live-verification-261025.json。该实机结果由实现方取得；Claude本轮没有执行测试、Git或真实HOME检查，不能把其代码审查称作独立重跑。

完成证据回填后，prepare-ticket --resume实际返回done-evidence-verified；原ticket_base不变，plan语义SHA256不变；文档两项门再次PASS。

本轮审查已经解除外发授权阻塞，T01全部AC完成；证据/状态/索引回填后核对最终完整HEAD，再进入AWAITING_PR_CONFIRMATION。最终仅证据HEAD的只读复核回执归本Issue，避免为回写自身SHA而不断追加提交。未推送、未建PR，CI/安装/部署/merge仍NOT RUN。


## 范围记录补齐

原六路径遗漏了03交叉审核规定的审查索引。依据用户已授权的“按平台流程”补入上述一条证据路径，仅追加本票审查记录；无新增功能、规则或安装动作。该审查台账不是正在遵守的治理规则，不触发治理规则应用后的STOP。原始开始回执不改写，显式保存旧/新范围与授权依据。

```aisoft-execution
{
  "change_base": "08aac8d5b9af4d334c53bcf34029870f09e50bf0",
  "tickets": {
    "T01": {
      "start": {
        "identity": {
          "issue": 429,
          "branch": "change/429-codex-plugin-layout",
          "owner": "01a16b94-fd7f-7842-852c-af5e58c3f9df",
          "worktree": "/private/tmp/issue-429-codex-plugin-layout",
          "provider": "codex",
          "plan_path": "docs/changes/429-codex-plugin-layout/plan-codex-plugin-layout-261024.md",
          "semantic_hash": "50c578826c83ea824e1ac8ea28ebfdb97cbb951b1799c399477cea34fce59eb2"
        },
        "ticket": "T01",
        "ticket_base": "3715f09b89b18291f0765f826ea88616bc2f8e0f",
        "raw_plan_sha256": "e705ea79059175aaaa756f2b238a06a456df19c739975d2a7b590cc31a8dc58c",
        "scope": [
          "codex/tools/check-external-skill-versions.py",
          "codex/tests/test-external-skill-versions.sh",
          "docs/changes/429-codex-plugin-layout/summary-codex-plugin-layout-261024.md",
          "docs/changes/429-codex-plugin-layout/spec-codex-plugin-layout-261024.md",
          "docs/changes/429-codex-plugin-layout/plan-codex-plugin-layout-261024.md",
          "docs/changes/429-codex-plugin-layout/verification-codex-plugin-layout-261024.md"
        ],
        "initial_state": {
          "staged": {},
          "unstaged": {},
          "untracked": {}
        },
        "derived_plan": ".superpowers/aisoft/429/issue-429-b6c741eff9899db1-50c578826c83ea82.md",
        "scratch": ".superpowers/sdd/issue-429-b6c741eff9899db1-50c578826c83ea82",
        "policy_sha256": "184608fd3d3553e7a688712adb99ba98f62e81e9e919e96233f422126486ff40",
        "route": {
          "process": "complex-production",
          "tier": "frontier",
          "effort": "max",
          "skills": "to-spec, to-tickets, implement, issue-session-flow",
          "method": "spec-plan",
          "verify": "full+reverse-proof",
          "review": "cross-provider",
          "confirm": "2"
        },
        "source_evidence": {
          "codex/vendor/mattpocock/v1.2.2/manifest.json": {
            "sha256": "a7e1ccccdc1ccc3d0c9af8ec0e7788cf3ac7bc0c308aaaa011ccc493c5d216da",
            "tag": "v1.2.2",
            "commit": "8b36d4fb2635b3c21998dcd8144439c9e5ba7302"
          },
          "codex/vendor/mattpocock/v1.3.1/manifest.json": {
            "sha256": "7cbdaa40307eed3258eddc1019db7f0927864b70d48cd382e202be1e7214e3dd",
            "tag": "v1.3.1",
            "commit": "24fe0ef7737efae15c87225755e9f6f5965e4888"
          },
          "codex/vendor/superpowers/v7.0.0/manifest.json": {
            "sha256": "ad9a021021ce607b35d6aa4e54bf3fb6ef572b148e08966bdf7200293629f692",
            "tag": "v7.0.0",
            "commit": "bb92a77741419a4ab5f06e711a283343f1ada0c3"
          }
        },
        "model_configuration": "not observed by helper; caller records actual model/effort in verification"
      },
      "base": "3715f09b89b18291f0765f826ea88616bc2f8e0f",
      "semantic_hash": "50c578826c83ea824e1ac8ea28ebfdb97cbb951b1799c399477cea34fce59eb2",
      "local_candidate_head": "08ef62fcc41f6b2876d92dbe11e55a70219c9fd1",
      "local_reviews": [
        {
          "axis": "Standards",
          "base": "3715f09b89b18291f0765f826ea88616bc2f8e0f",
          "head": "08ef62fcc41f6b2876d92dbe11e55a70219c9fd1",
          "package_sha256": "94bba3c533db6e111ee2d661bcf39c405ff6cb1262aa27aa304b22d5fde19ad6",
          "verdict": "PASS",
          "reviewer": "/root/review429_standards",
          "evidence": "R1整批+R2修复复审+最终3份文档增量；代码/测试与R2相同；fixed=1,residual=0,new=0；Claude NOT RUN，AC5仍PARTIAL。"
        },
        {
          "axis": "Spec",
          "base": "3715f09b89b18291f0765f826ea88616bc2f8e0f",
          "head": "08ef62fcc41f6b2876d92dbe11e55a70219c9fd1",
          "package_sha256": "94bba3c533db6e111ee2d661bcf39c405ff6cb1262aa27aa304b22d5fde19ad6",
          "verdict": "PASS",
          "reviewer": "/root/review429_spec",
          "evidence": "R1整批+R2修复复审+最终3份文档增量；代码/测试与R2相同；fixed=1,residual=0,new=0；Claude NOT RUN，AC5仍PARTIAL。"
        }
      ],
      "ac": {
        "AC-1": "PASS",
        "AC-2": "PASS",
        "AC-3": "PASS",
        "AC-4": "PASS",
        "AC-5": "PASS"
      },
      "head": "08ef62fcc41f6b2876d92dbe11e55a70219c9fd1",
      "validation_sha256": "403860adbc6da9acb07aa22ac4e47da452e3d7a6879d17a121cde3025a82d8e0",
      "checks": [
        {
          "command": "bash codex/tests/test-external-skill-versions.sh",
          "result": "PASS",
          "evidence": "PASS after F1 fix; RED/GREEN and zero-read audit proof recorded above"
        },
        {
          "command": "bash -n codex/tests/test-external-skill-versions.sh",
          "result": "PASS",
          "evidence": "exit 0 after final shell change"
        },
        {
          "command": "shellcheck codex/tests/test-external-skill-versions.sh",
          "result": "PASS",
          "evidence": "exit 0 after final shell change"
        },
        {
          "command": "bash codex/tests/smoke.sh",
          "result": "PASS",
          "evidence": "/private/tmp/issue-429-smoke-r2.log; exit 0; 746 runtime and 46 installed-drift tests; code/test bytes identical through reviewed HEAD"
        },
        {
          "command": "bash codex/tools/check-external-skill-versions.sh --home /Users/benque",
          "result": "PASS",
          "evidence": "/private/tmp/issue-429-live-verification-261025.json; expected exit 1 and PIN_DRIFT 7.0.1 / 7.0.0; checked files unchanged"
        },
        {
          "command": "bash codex/tools/aisoft check-change-documents --porcelain --repo /private/tmp/issue-429-codex-plugin-layout",
          "result": "PASS",
          "evidence": "both document gates PASS for reviewed candidate"
        },
        {
          "command": "bash codex/tools/aisoft review-candidate 429 T01 --head 08ef62fcc41f6b2876d92dbe11e55a70219c9fd1 --repo /private/tmp/issue-429-codex-plugin-layout",
          "result": "PASS",
          "evidence": "/private/tmp/issue-429-cross-review-candidate-r1.json; mechanical PASS; same original ticket/change BASE"
        },
        {
          "command": "claude --safe-mode --disable-slash-commands --strict-mcp-config --tools Read,Glob,Grep --allowedTools Read,Glob,Grep --permission-mode plan --permission-prompts none --no-session-persistence --output-format json --effort high -p < /private/tmp/issue-429-claude-r1.prompt > /private/tmp/issue-429-claude-r1.json",
          "result": "PASS",
          "evidence": "independent cross-provider PASS on 08ef62fcc41f6b2876d92dbe11e55a70219c9fd1; claude-fable-5-1/high; session dcb1a530-f92f-4f68-bd12-1984199473f6"
        }
      ],
      "cross_provider_review": {
        "provider": "claude",
        "head": "08ef62fcc41f6b2876d92dbe11e55a70219c9fd1",
        "model": "claude-fable-5-1",
        "effort": "high",
        "session_id": "dcb1a530-f92f-4f68-bd12-1984199473f6",
        "verdict": "PASS",
        "blocking_findings": 0,
        "nonblocking_observations": 3,
        "evidence": "verification cross-provider table and /private/tmp/issue-429-claude-r1.json"
      }
    }
  },
  "scope_amendments": [
    {
      "from_scope": [
        "codex/tools/check-external-skill-versions.py",
        "codex/tests/test-external-skill-versions.sh",
        "docs/changes/429-codex-plugin-layout/summary-codex-plugin-layout-261024.md",
        "docs/changes/429-codex-plugin-layout/spec-codex-plugin-layout-261024.md",
        "docs/changes/429-codex-plugin-layout/plan-codex-plugin-layout-261024.md",
        "docs/changes/429-codex-plugin-layout/verification-codex-plugin-layout-261024.md"
      ],
      "to_scope": [
        "docs/governance/review-evidence-index.md",
        "codex/tools/check-external-skill-versions.py",
        "codex/tests/test-external-skill-versions.sh",
        "docs/changes/429-codex-plugin-layout/summary-codex-plugin-layout-261024.md",
        "docs/changes/429-codex-plugin-layout/spec-codex-plugin-layout-261024.md",
        "docs/changes/429-codex-plugin-layout/plan-codex-plugin-layout-261024.md",
        "docs/changes/429-codex-plugin-layout/verification-codex-plugin-layout-261024.md"
      ],
      "authorization": "用户于2026-10-24明确要求按平台流程修复并核验；03交叉审核要求本批追加review-evidence-index。本次仅补齐该必要审查证据路径，不新增运行行为或修改治理规则；原T01 BASE与开始回执保持不变。"
    }
  ]
}
```
