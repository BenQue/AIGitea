---
issue: 231
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/231
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/231-governance-provider-parity
created: 2026-09-02
updated: 2026-09-02
---

# Plan · 平台治理去项目化、去部署细节，Claude/Codex 等价

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 下游模板瘦身：`templates/project/AGENTS.md` 常驻指针两节去平台内部实现、「工具分工」换等价句、「交付形态」占位符改环境类别；`test-project-check.sh` fixture 匹配新占位符并全绿 | - | pending |
| T02 | Claude 侧 `aisoft-platform` 技能：description 去项目名/去 docker-release、部署边界只留流程不变量、工具分工换等价句、会话标准动作 4–7 步各压一行指向 `06`、Common Mistakes 去项目名、新增「approved 之后默认自主推进 / 只在这些情况暂停」 | - | pending |
| T03 | Claude 侧 `issue-session-flow` 技能：新增「approved 之后默认自主推进 / 只在这些情况暂停」两段，与 Codex 侧语义一致、不逐字复制 | - | pending |
| T04 | Codex 侧四份文件：`skill-for-codex/SKILL.md` 去 rsDesign / 去 Codex-first / 主处理者换等价句；`codex/global-AGENTS.md` 去 rsDesign、provider 规则换等价句；`codex/skills/aisoft-matt-workflow`、`codex/skills/issue-session-flow` 审计（当前三条 grep 均为空，预期无改动或仅措辞对齐） | - | pending |
| T05 | 静态守卫与验证：`smoke.sh` 新增 AC-1/AC-2 范围 grep 与 AC-3 活文档 grep 三条守卫；跑 `smoke.sh`、`test-project-check.sh`、`test-install-claude-skills.sh`、两侧 `check-drift.sh`、平台仓 `aisoft-project-check.sh --kind docs`；填 verification | T01, T02, T03, T04 | pending |

Ticket ID 固定为 `Txx`；依赖只引用本表中的 ID。T01–T04 互不依赖、各自保持仓库全绿，可由
`$implement #231 Txx` 独立执行与验证；T05 是把 AC 的 grep 固化为守卫并出具证据，必须等四份文本
定稿后运行，否则守卫会对半成品报红。选 vertical slice 而非 expand→migrate→contract：
本变更是纯文本治理收敛，没有需要跨批次保持红/绿的运行时重构。

## Expected touch points

- **T01**：`templates/project/AGENTS.md`；`codex/tests/test-project-check.sh`（`make_aligned_repo` 的
  awk 占位符匹配 `/^  <docker-release\/v2/` → 新占位符首字样；其余 `sed 's|  docker-release/v2;|…|'`
  作用于 fixture 已替换后的具体值，保持不变）。`templates/project/CLAUDE.md` 不动。
- **T02**：`skill-for-claude/aisoft-platform/SKILL.md`。
- **T03**：`skill-for-claude/issue-session-flow/SKILL.md`。
- **T04**：`skill-for-codex/SKILL.md`、`codex/global-AGENTS.md`、`codex/skills/aisoft-matt-workflow/SKILL.md`、
  `codex/skills/issue-session-flow/SKILL.md`。
- **T05**：`codex/tests/smoke.sh`（三条 grep 守卫，放在既有 skill 静态检查之后）；
  `docs/changes/231-governance-provider-parity/verification-governance-provider-parity-260902.md`。

这是范围提示，不授权扩大 spec：`codex/tools/aisoft-project-check.sh`、`skill-for-codex/references/`、
编号分册、README、根 `AGENTS.md` 都不在 touch points 内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 去项目化 | `grep -rn -iE 'NewEMaint\|SFMDigitalBoard\|HSDB\|WMPDA\|SapTable\|rsdesign\|myapp\|smoke-test\|LocalWMS' <7 份范围文件>` 为空；review 两份 `aisoft-platform` description；T05 守卫固化 |
| AC-2 去部署细节 | `grep -rn -iE 'docker-release\|PM2\|Compose\|systemd-native\|IIS' <7 份范围文件>` 为空；review「部署边界」段；T05 守卫固化 |
| AC-3 provider 等价 | `grep -rn -E '默认主处理者\|primary handler\|维护与部署\|开发与设计\|Codex 为主\|对等补位' --exclude-dir=archive --exclude-dir=changes --exclude-dir=vendor --exclude-dir=.git .` 为空；`diff` 提取 Claude 技能与模板「工具分工」段逐字相同；T05 守卫固化 |
| AC-4 Claude 侧简化取向 | review 两份 Claude 技能新增段落与 Codex `issue-session-flow` 的「Default autonomy after approval」逐条对照；`grep -c` 会话标准动作 4–7 步各为一行且含 `06` 编号 |
| AC-5 项目模板瘦身 | `grep -n -iE '1\.26\|merge-only\|custody\|allowlist' templates/project/AGENTS.md` 为空；`bash codex/tests/test-project-check.sh` 全绿并含 `PASS: pointer-sections`；`bash codex/tools/aisoft-project-check.sh --repo <平台仓> --kind docs` 与基线 `pass=2 gap=2 skip=4` 一致 |
| AC-6 测试与漂移 | `bash codex/tests/smoke.sh` 退 0；`bash skill-for-claude/check-drift.sh` 与 `bash codex/check-drift.sh` 改动后输出 DRIFT 且退 1；重装后 CLEAN 记 NOT RUN |
| AC-7 下游不动 | `git diff --stat origin/main...HEAD` 只含平台仓路径；verification 记一句下游 GAP 预期 |

## 部署与回滚

无部署影响。回滚 = revert 唯一 PR；本机 skills 副本在本 Issue 内不重装，因此无需回滚安装。
映射的 `verification` 文档记录 AC-1～AC-3 的 grep 输出、`check-drift.sh` 改动前后对比与未执行项，
不含「部署验收」节。
