---
issue: 395
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/395
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
depends_on:
  - 389
  - 391
  - 392
status: pending
branch: change/395-route-card
created: 2026-10-20
updated: 2026-10-21
---

# R10b 路由卡验证记录

## 基线与范围

- Commit SHA: 见「执行结果」各 ticket 行
- 基线：`origin/main` = `08be6f4`（broker `git.fetch.main` 2026-10-21 PASS 后读回）
- 环境: macOS 本机（bash 3.2，Python 3）
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-9

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| T02 先看着测试红：`python3 -m unittest tests.test_contract`（新增 3 个路由测试、未改 `contract.py`） | FAILED (failures=11, errors=1)，全部是 `unsupported front matter syntax at line 16` | 红的原因正是解析器不认 `route:` 缩进键 |
| T02 实现后同一命令 | Ran 30 tests, OK | |
| T02 全量 runtime：`python3 -m unittest discover -s tests -t .` | Ran 713 tests, OK | |
| `bash codex/tools/change-template-sync.sh --refresh-digest` 后 `--verify-digest` | digest pinned `sha256:ac1cef01…` | 下游 stale=4 是预期：模板前进，发布包 pin 的项目不受影响 |

命令与输出照实抄。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待填写 | |
| AC-2 | 待填写 | |
| AC-3 | 待填写 | |
| AC-4 | 待填写 | |
| AC-5 | 待填写 | |
| AC-6 | 待填写 | |
| AC-7 | 待填写 | |
| AC-8 | 待填写 | |
| AC-9 | 待填写 | |

## 遗留风险与未完成项

待填写。
