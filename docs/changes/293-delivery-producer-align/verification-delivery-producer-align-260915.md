---
issue: 293
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/293
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - external-contract
depends_on: []
status: verified
branch: change/293-delivery-producer-align
created: 2026-09-15
updated: 2026-09-15
---

# Verification · 对齐本机构建-离线交付合同

## 基线与范围

- Commit SHA: 首次 PR head `4dacf21`（基于 a2f8854）；rebase 到 `f0e3296` 后由后续 commit 形成最终 head，以 PR #294 页面为准
- 基线：`origin/main` = `a2f8854`（PR #291 merge）
- 环境: Mac 本机 change worktree `/private/tmp/issue-293-delivery-producer-align`，真实 `/opt/homebrew/bin/rg`
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-5；AC-6 由人合并 manual PR 时完成，不部署

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `rg -n '公司 Windows x64 Runner 构建\|唯一正式权威源\|与公司 Gitea 无关系' 12-Windows平台自动部署方案.md` | PASS | 0 命中，exit 1；改前 L25/L26/L27 各 1 命中。§2 末新增带日期历史注记不复述原句 |
| `rg -n 'versioned release bundle\|GitHub Release\|GitHub 不进入公司信任链' 07-内网与生产平移路线.md` | PASS | 命中 §1 L13、L18、L35 与 §2 图 L57；「GitHub 不进入公司信任链」保留 |
| `rg -n 'WR\b\|Windows x64 Runner' 07-内网与生产平移路线.md` | PASS | 0 命中；§2 图公司侧 `WR` 构建节点已改为 `CV` 核验节点（确认点 1 认可） |
| `rg -n 'locked-mode\|buildx\|emulated\|release_producer\|transport' skill-for-codex/references/onboarding-runbook.md` | PASS | 命中 §4.2 L194/L196、§4.4 L215/L216、§4.5 L234/L235 |
| `rg -n 'release_producer\|transport' templates/project/AGENTS.md` | PASS | 命中「项目事实」L53、L55 两个独立 bullet |
| `bash codex/tests/smoke.sh` | PASS | exit 0，2 分 41 秒；末行 `Codex platform static smoke checks passed.`；内含 890 项 Python 测试 OK |
| `PYTHONPATH=codex/runtime python3 -B -m unittest discover -s codex/runtime/tests` | PASS | `Ran 890 tests in 65.130s` / `OK`，含钉住 07 短语的 `test_company_delivery.py` 与 `test_architecture_governance.py` |
| `bash codex/tests/test-project-check.sh` | PASS | `project check tests passed (58 cases)`；模板新增两行未触发 delivery-profile 占位符判定 |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` | PASS | `PASS: change-documents`、`PASS: change-pr-url`、`result: changes=133 pass=2 gap=0` |
| `git diff --check origin/main` | PASS | 无输出 |
| `bash skill-for-claude/check-drift.sh`（改后、重装前） | 观测 | `DRIFT: aisoft-platform/references/onboarding-runbook.md` |
| `bash skill-for-claude/install.sh` | PASS | 从本 worktree 安装 aisoft-platform 与 issue-session-flow，Pruned 0，无凭据 |
| `bash skill-for-claude/check-drift.sh`（重装后） | PASS | `CLEAN`；`diff -q` 源 runbook 与已安装副本一致 |
| PR #294 首次 head `4dacf21` 的 `CI / verify (pull_request)` | PASS | success，1m27s；随后 `origin/main` 被 #295（#292）推进到 `f0e3296`，分支保护要求 head 基于最新 main |
| `git rebase origin/main`（f0e3296，#292 只新增自身 change 文档，零重叠） | PASS | 8 个 commit 干净重放，`0 8`（不落后，领先 8） |
| rebase 后 `bash codex/tests/smoke.sh` 与 `check-change-documents` | PASS | smoke exit 0，`Codex platform static smoke checks passed.`；`result: changes=134 pass=2 gap=0` |
| `codex/tools/apply-classification-labels.sh 293` → `--apply` → `--verify 293` | PASS | plan `applied:false`；apply `result:updated`；verify `result:projected`，`change_type:platform`、`complexity:complex` |

命令与输出照实抄。改动前观测：AC-1 三句在 `origin/main` 的 12-Windows §2 表 L25–L27 各命中一次；
check-drift 改后先 DRIFT 再 CLEAN 的前后对比只在本记录留下。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 三句 0 命中；12-Windows §2/§3、07 §1/§2 图、runbook §4.4/§4.5 统一为「本机 Gitea 唯一源码源、构建在开发侧、GitHub 私有仓 Push Mirror 加 Release 资产中转、公司 Gitea 只核验与独立授权部署、GitHub 不进入公司信任链」；diff review 见 commits 5e60bf8、c6dc532、d9c2ae1 |
| AC-2 | PASS | 07 §1「结果」段含已测试 versioned release bundle（完整 merge SHA + SHA256SUMS + release.json/manifest）、handoff 证据带出校验和与 release SHA、公司侧对照、GitHub Release 资产为允许介质、「GitHub 不进入公司信任链」保留 |
| AC-3 | PASS | runbook §4.4 新增 producer 钉版本不变量（SDK 容器 digest + lock 文件 + locked-mode）；§4.2 新增 buildx/Rosetta 交叉构建与 `emulated` 标注；§4.5 新增 `release_producer`（local 或 github，一个项目一种）与 `transport` 声明及 GitHub Actions 候选三条适用条件 |
| AC-4 | PASS | `templates/project/AGENTS.md`「项目事实」新增 `release_producer` 与 `transport` 两个占位 bullet |
| AC-5 | PASS | 890 项单测 OK、smoke 绿、check-change-documents PASS、project-check 58 例通过 |
| AC-6 | NOT RUN | 唯一 manual PR 由人合并；不部署 |

## 遗留风险与未完成项

- Codex 侧 `~/.agents/skills` 未重装，由人在 Codex 会话用 `codex/install-skills.sh` 另行自查。
- 已对齐项目（LocalWMS、NewEMaint）的 `AGENTS.md` 尚未填 `release_producer` 与 `transport`，按 runbook
  §4.5 在各自项目仓独立 Issue 补填，本 PR 不改项目仓。
- `13-项目结果迁移与内网切换实施手册.md` §2「迁移/不迁移」边界与 07 §1 新「结果」定义的措辞未逐句对齐
  （Issue 范围外），如需对齐另开 Issue。
- 未执行：真实 GitHub Release 上传、公司侧下载核验、任何部署；本 Issue 只改合同文字。
