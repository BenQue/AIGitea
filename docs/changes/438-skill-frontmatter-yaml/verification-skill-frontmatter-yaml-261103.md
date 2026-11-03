---
issue: 438
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/438
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - agent-governance
  - ci-change
depends_on: []
status: passed
branch: change/438-skill-frontmatter-yaml
created: 2026-11-03
updated: 2026-11-03
---

# 验证记录：技能 frontmatter 严格 YAML

## 基线与范围

- Commit SHA: 实现候选 `95d22b71aa45ed9e78ef608602e689a44e5b9132`（之后只有本证据提交）
- 基线：`origin/main` = `7bd38270026583523878fc7ec9f6f5c811f15708`
- 环境: Mac（Ruby Psych 后端，系统 ruby；无 PyYAML）；OrbStack VM `gitea-ci`（CI 所在主机，PyYAML 6.0.3，系统包 `python3-yaml`，无 ruby），经 `/mnt/mac` 读同一 worktree
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-6

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前用 Ruby Psych 解析 8 个技能 frontmatter | 1 FAIL / 7 OK | `skills/aisoft-platform/SKILL.md: mapping values are not allowed in this context at line 3 column 262`；其余 7 个 OK |
| 先写测试：`bash codex/tests/test-skill-frontmatter.sh`（检查器尚不存在） | FAIL（预期） | `FAIL: missing backend python exits 127, want 2` |
| 检查器写好、`SKILL.md` 未改：`bash codex/tools/check-skill-frontmatter.sh`（Mac） | rc=1 | `FAIL: skills/aisoft-platform/SKILL.md: frontmatter 不是合法 YAML：(<unknown>): mapping values are not allowed in this context at line 2 column 262`；`RESULT GAP (backend: ruby)` |
| 同上（VM） | rc=1 | `mapping values are not allowed here … line 2, column 262: … delivery platform: Issue analysis …`；`RESULT GAP (backend: python)` |
| 修 `SKILL.md` 后检查器（Mac / VM） | PASS / PASS | `RESULT PASS (backend: ruby)`；`RESULT PASS (backend: python)` |
| `bash codex/tests/test-skill-frontmatter.sh`（Mac / VM，HEAD `95d22b71`） | PASS / PASS | `PASS (backends: ruby)`；`PASS (backends: python)`；各自另验证缺失的那个后端被强制时退出 2 |
| R1 P2 回归：把检查器退回 `671d0b2e` 版本跑新测试（Mac） | FAIL（预期） | `FAIL: ruby docend-ruby: exit 0, want 1` |
| `bash codex/tools/usage-bundle.sh --release 1.22.1 --today 2026-11-03 --compatibility patch --notes …` 后 `--verify --baseline-ref origin/main` | PASS | `VERIFIED 1.22.1 sha256:be99381bc8233b0a9b3500187753ffca3ae01c0f4890f4022c20a94d2db7ab3c` |
| `bash codex/tests/smoke.sh`（HEAD `671d0b2e`） | rc=0 | `Ran 808 tests … OK`；`Codex platform static smoke checks passed.` |
| `bash codex/tests/smoke.sh`（HEAD `95d22b71`） | rc=0 | `Ran 808 tests … OK`；`test-skill-frontmatter: PASS (backends: ruby)`；`Codex platform static smoke checks passed.` |
| 反向证明 1：`SKILL.md` 与 `usage/bundle.json` 退回 `origin/main`（使发布包闸门本身一致），守卫保留，跑 smoke | rc=1 | 停在守卫行：`FAIL: skills/aisoft-platform/SKILL.md: frontmatter 不是合法 YAML …`；`RESULT GAP (backend: ruby)` |
| 反向证明 2：同上，再删掉 smoke 中执行检查器的那一行 | rc=0 | 全量通过，日志里 0 处 `frontmatter 不是合法`：除本守卫外没有别的闸门拦得住旧字节；两次实验后已 `git checkout HEAD --` 还原 |
| `shellcheck` 与 `bash -n`（新脚本） | PASS | 无输出 |
| `grep -n 'skill-frontmatter' codex/tests/smoke.sh` | 6 行 | 检查器与测试各在 `bash -n` 清单、ShellCheck 清单与执行区出现一次 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 两个后端对 8 个技能 PASS；`git diff origin/main -- skills/aisoft-platform/SKILL.md` 只有 description 一行，`platform: Issue analysis` → `platform, including Issue analysis` |
| AC-2 | PASS | 本仓 PASS；`origin/main` 旧字节在两个后端都被点名拒绝（上表） |
| AC-3 | PASS | 测试覆盖 spec 所列反例，另加 R1 后的三个多文档反例；Mac 跑 ruby、VM 跑 python，各自验证缺失后端退出 2 |
| AC-4 | PASS | smoke rc=0；登记 6 行；反向证明 1/2 |
| AC-5 | PASS | `VERIFIED 1.22.1` |
| AC-6 | PASS | 见下节，R2 PASS |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex gpt-6-astra / high（Herdr「AISoftPlatform / #438 交叉审查」窗格 t18，`--sandbox read-only`） | `671d0b2e5e6fc111511075398b3e807fcc4976f3` | FAIL | 1 P2：Ruby `YAML.safe_load` 只读第一份文档，`...` 之后的非法内容与 agents 多文档漏过。已修：先 `YAML.parse_stream` 数文档，>1 拒绝；补 3 个反例 |
| 2 | Claude | 同上，同一窗格 | `95d22b71aa45ed9e78ef608602e689a44e5b9132` | PASS | P2 fixed，新发现无；审查方在只读沙箱内无法 mktemp，完整测试脚本由实现方在 Mac 与 VM 实跑 |

## 遗留风险与未完成项

- CI 主机若移除 `python3-yaml`，守卫以 2 失败、smoke 变红；这是有意的 fail closed。
- 两个后端不在同一主机上并跑：Mac 只证 Ruby，VM 只证 PyYAML；required CI 再证一次 PyYAML。
- Ruby 的 `safe_load` 拒绝日期等非基本类型，PyYAML 接受；当前 8 个技能都不含此类值，差异只会让 Mac 更严。
- 本机与项目技能未重装；合并后由人重装（`NOT RUN`）。Issue 附带的同名技能双装问题不在本批。
