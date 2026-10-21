---
issue: 408
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/408
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - artifact
depends_on:
  - 392
  - 402
status: recorded
branch: change/408-peer-review-evidence
created: 2026-10-21
updated: 2026-10-21
---

# R15 验证记录

## 基线与范围

- 基线：`origin/main` = `cee4294979f027a132de4b3abc82108cde4d9d88`（#406 合并）；分支先 rebase 到它；Codex 第 4 轮 PASS 后以无冲突 merge commit 集成 `f169b126`（#409 R12），再发 1.10.0
- 环境：macOS 本机（bash 3.2、`/opt/homebrew/bin/rg`），codex-cli 0.161.0，Claude Code 2.1.228，cursor-agent 2026.10.19（已登录）
- 本记录负责证明的 acceptance criteria：AC-1–AC-7
- 实现方 Claude（本线程），审查方 Codex（`codex exec -s read-only`）

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh`（集成 main 后的 tree `d65bea8cd1e3309bba84e3eb027b52b0b2d287fb`） | PASS | 在 `a427c05b` 上 exit 0，runtime `Ran 700 tests … OK`，`PASS: project-leak (10 baseline files, 41 hits; site 10 files, 37 hits)`，末行 `Codex platform static smoke checks passed.`。broker 推送拒绝了那次带冲突解决的 merge（`MERGE_CONFLICT`），按 #402 的做法先把 `usage/bundle.json` 退回合并基、无冲突 merge、再发 1.10.0，重做后的 `91f9d5a8` 与 `a427c05b` tree 相同；之后只追加本行 |
| `bash codex/tests/smoke.sh`（`675aae2b`） | PASS | exit 0，runtime `Ran 681 tests … OK`，`PASS: project-leak (9 baseline files, 38 hits; site 10 files, 37 hits)`，末行 `Codex platform static smoke checks passed.` |
| `bash codex/tests/test-external-skill-versions.sh` | PASS | `external skill versions tests passed`；新增 caps-pass、caps-known、caps-gap、caps-matt-content、caps-no-cursor 与 usage 用例 |
| 反向证明：拷贝树里清空 `KNOWN_EXTERNAL` | PASS | 测试内同一 Codex 状态变成 `CAPABILITY codex GAP`、exit 1 |
| `bash codex/tests/test-aisoft-entry.sh` | PASS | sandbox-exec 拒读平台检出；open-pr 的不合格正文（缺 Closes、CRLF、路径粘连、两条 summary 链接）零 broker 请求，建 PR 失败不留 commit，提交被 hook 拒绝后重跑完成，broker 顺序 `git.push.change gitea.pull.create git.push.change` 且在 checkout 内运行，重跑不再提交 |
| 反向证明：关掉 open-pr 的 Closes 检查 | PASS | `FAIL: expected status 2, got 0 … bad-body.md`；还原后 PASS |
| 反向证明：open-pr 不核对归属（Codex 第 3 轮发现 1） | PASS | 把 `authorize_push` 换成只读 marker，别的 session 续跑 `expected status 2, got 0`；还原后 PASS |
| 反向证明：open-pr 续跑仍先推送（Codex 第 2 轮发现 1） | PASS | 把续跑分支改成 `if false`，假 broker 拒推脏工作树，续跑 `expected status 0, got 1`；还原后 PASS |
| `python3 -m unittest tests.test_main_integration`（`codex/runtime`） | PASS | 34 tests OK，含 `test_spec_without_lifecycle_status_is_scoped_by_the_summary` |
| 反向证明：恢复旧 `scope()` | PASS | 上述用例 `FAILED (errors=2)`；还原后 OK |
| `python3 -m unittest tests.test_session_contract` | PASS | 12 tests OK，open-pr 三条钉子与一条突变 |
| `bash codex/tools/change-template-sync.sh --refresh-digest` | PASS | `sha256:ac1cef01… -> sha256:f59cc189…`；下游清单 holders 6，本机 HSDB、LocalWMS、NewEMaint、SFMDigitalBoard 为 stale（本机 checkout 状态），myapp、smoke-test unverified |
| `bash codex/tools/usage-bundle.sh --verify --baseline-ref origin/main` | PASS | 分支内曾发 1.9.0（未上 main，审查修复后按规则清空重发同号）；R12（#409）先合并占用 1.9.0，集成 main `f169b126` 后改发 `VERIFIED 1.10.0 sha256:5cccc9ff…` |
| `aisoft classify --apply 408` 与 `--verify 408` | PASS | `"result":"projected","change_type":"platform","complexity":"complex"` |

## 能力集读回（AC-1）

分支上的脚本拿本分支的 `skills/` 当源，而本分支改了两个平台技能，所以已安装的 Claude、Codex 落点读成 `PIN_DRIFT`，这是预期的。
为读到与已安装字节对应的状态，把本分支的 `check-external-skill-versions.py` 放进 `origin/main` 的临时 worktree 运行，
`--repo` 指向 SFM #186 的 worktree（Cursor 落点已采用）：

```text
CAPABILITY claude PASS platform-skills=PIN_CLEAN matt=PIN_CLEAN superpowers=PIN_CLEAN review=OK smoke=OK
CAPABILITY codex KNOWN_EXTERNAL platform-skills=PIN_CLEAN matt=PIN_CLEAN superpowers=[PIN_NOT_INSTALLED enabled=superpowers@openai-curated marketplace=unregistered cached=5.1.3 pinned=7.0.0] review=OK smoke=OK (#392 Codex official marketplace does not offer the pinned version; the platform does not install it)
CAPABILITY cursor PASS platform-skills=PIN_CLEAN matt=PIN_CLEAN superpowers=PIN_CLEAN review=OK
RESULT KNOWN_EXTERNAL
```

exit 0。合并并两台重装技能后，在主 checkout 上直接运行应得到同样三行。

## Cursor 使用层首次验收（AC-6）

- SFMDigitalBoard #186（small，maintenance）：Claude 建 Issue 与 worktree，`cursor-agent -p --force` 在 worktree 里完成 adopt、三份文档、两条核对与 commit `430d336`；
  两次 fresh `cursor-agent -p --mode ask` 会话：问 Issue 流程时读取 `.cursor/skills/issue-session-flow/SKILL.md`；问 small/complex 判级与路由卡时读取
  `.cursor/skills/aisoft-platform/SKILL.md` 与同目录 `references/route-policy.md`，并答出 `contract_effect` 先行、强制 complex 清单与本仓
  `change_control=development` 下命中 R2/R5。
- 判级投影 `projected`；PR：SFMDigitalBoard PR 187（负责人回「确认开」后由 Claude 推送并建，summary 已回填）。
- 项目侧 verification：SFM 仓 `docs/changes/186-cursor-landing/verification-cursor-landing-261021.md`；E2E 表「采用记录」最后一行。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 上节三行 `CAPABILITY`：Claude PASS、Codex KNOWN_EXTERNAL（登记项）、Cursor PASS；测试覆盖三种结论与反向证明 |
| AC-2 | PASS | `docs/governance/review-evidence-index.md` 13 行，覆盖 R0–R8（含 R6b）、#370、#385、#387；审查 head 与合并 SHA 为 40 位且 `git cat-file -e` 存在（Codex 第 1 轮核对），缺的写「未记录」或「未做交叉审查」 |
| AC-3 | PASS | 模板固定「交叉审查」表；`03` §7 写明实现方 ≠ 审查方与记录位置；本记录下一节用新表；反向批次按负责人决定取消（spec「已决问题」1） |
| AC-4 | PASS | broker 闸门用例与反向证明（见上表） |
| AC-5 | PASS | `test-aisoft-entry.sh` open-pr 用例；本批 PR 用 `aisoft open-pr` 开（结果见确认点 2 之后的 summary 回填提交） |
| AC-6 | PASS | 上节；SFM PR 187 |
| AC-7 | 见下 | 发布 1.10.0、`--verify` 与 digest PASS；最终 head 的全量 smoke 与 Codex 审查见下节 |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex（`codex exec -s read-only`） | `2256a105552868b805260978fe46869caa34fd02` | FAIL | major：Codex Matt 只核 manifest → 改为核对快照里每个技能的内容哈希与 `.agents/skills` 加载链接，补用例（`e3e72ef2`）；major：open-pr 本地校验与 broker 不一致（CRLF、路径边界、多条 summary、64 KiB）→ 同一字符串按 broker 规则校验后发送，补三种零请求用例；major：提交失败后无法重跑 → 只剩本 summary 的 `pr_url`/`status` 改动时允许续跑，补 hook 失败用例（`4ef731c7`）；major：AC-6 未交付 → SFM #186 与 E2E 表「工具」列；minor：本记录未填 → 本次填写；minor：`git_scope` 多一项 → E2E 表已改，复核相等；minor：索引缺合并 SHA → 补列 |
| 2 | Claude | Codex（`codex exec -s read-only`） | `26212a0ab7f6b1a921a1b4183655ff2a58b58632` | FAIL | 第 1 轮 1、2、5、6、7 确认已修；major：续跑仍先推送，真实 broker 拒推脏工作树 → 续跑先核对 summary 已回填本仓 PR 再提交、只推一次，假 broker 也拒推脏工作树，补反向证明；major：lock 为符号链接时退回最新版本，可把 GAP 读成 PASS → 只有 lock 不存在才退回，链接/目录报 `UNKNOWN`，补用例；minor：fresh 会话未证明 `aisoft-platform` 触发 → 补第二次 fresh 会话 |
| 3 | Claude | Codex（`codex exec -s read-only`） | `bc7e5d0ad487bfcb2245d118d5fb0fd3924ad20b` | FAIL | 第 2 轮三条确认已修；major：续跑在核对 worktree 归属前提交，别的会话能改动他人 HEAD → open-pr 第一步用 `authorize_push` 与 `caller_session` 核对归属并比对 marker 的 worktree 路径，任何写入与 broker 调用都在它之后，补「错误 session / 缺 session 续跑时 HEAD、index、summary 不变」用例与反向证明；minor：表格被空行截断 → 去掉空行 |
| 4 | Claude | Codex（`codex exec -s read-only`） | `8bb412c8ae1dfbdf483e7e6da33c2e3336944a82` | PASS | 第 3 轮两条确认已修；无 blocker/major/minor。沙箱内不能建临时目录的两个 shell 测试与 `test_main_integration` 由 Codex 记 NOT RUN，实现方在集成 main 后的 head 上跑全量 smoke（见执行结果） |

任务书与各轮原文在项目库 `codex-review-408.md`。

## 遗留风险与未完成项

- installed 层：合并后负责人两台重装 broker（`aisoft_main_integration.py` 变了）与技能，再读回 `check-installed-drift` 与 `--capabilities`。PR 内 NOT RUN。
- 未重装前，已安装的旧 broker 仍要求 spec `status: approved`；本批自己的 spec 保留该字段，新文档在重装前按旧规则写。
- 下游 holder 的 change 模板同步按 digest 清单各自开 Issue；pin 了发布包的项目不受影响。
- SFM PR 187 由负责人合并；合并后在 SFM `main` 上读回 `bundle status`。
