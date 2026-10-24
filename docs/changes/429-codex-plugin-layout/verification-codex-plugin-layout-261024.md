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
updated: 2026-10-24
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
| bash codex/tests/smoke.sh | PASS / exit 0；宿主授权环境原样完整重跑，含746项runtime、46项installed drift及其它脚本检查，最终Codex platform static smoke checks passed。日志 /private/tmp/issue-429-smoke-final.log。首次嵌套沙箱中止仅为执行环境失败，不记通过 |
| bash codex/tools/check-external-skill-versions.sh --home /Users/benque | PASS（符合预期的诊断结果，命令 exit 1）；日志 /private/tmp/issue-429-live-verification.json |
| 文档、判级与diff检查 | check-change-documents两项PASS；classify --verify读回bugfix/complex、applied=false；git diff --check PASS。fixed candidate与独立审查待提交后运行 |

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

fixed / residual / new：待审查后记录。


## 范围记录补齐

原六路径遗漏了03交叉审核规定的审查索引。依据用户已授权的“按平台流程”补入上述一条证据路径，仅追加本票审查记录；无新增功能、规则或安装动作。该审查台账不是正在遵守的治理规则，不触发治理规则应用后的STOP。原始开始回执不改写，显式保存旧/新范围与授权依据。

```aisoft-execution
{
  "change_base": "08aac8d5b9af4d334c53bcf34029870f09e50bf0",
  "tickets": {},
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
