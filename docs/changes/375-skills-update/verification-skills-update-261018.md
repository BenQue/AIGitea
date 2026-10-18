---
issue: 375
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/375
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: verified
branch: change/375-skills-update
created: 2026-10-18
updated: 2026-10-18
---

# #375 验证记录

## 基线与范围

- Commit SHA: 代码与测试的验证对象 `e0ea16ea8bffa1455b07efd51c483e35c83c16c2`；本记录随后的 commit 只改本目录文档，最终 head 另跑 `check-change-documents` 与泄漏检查
- 基线：`origin/main` = `c3d49edcda9383ee0a57c01a51d91cfab976437d`
- 环境: macOS 本机（Darwin 27.0.0，Python 3.14.4，`/opt/homebrew/bin/rg`）
- 本记录负责证明的 acceptance criteria: AC2、AC3 本机实跑、AC4、AC5、AC7

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/smoke.sh`（worktree，HEAD `e0ea16e`，前后 `git status` 干净） | PASS | 退出 0，末行 `Codex platform static smoke checks passed.`；主 runtime 套件 `Ran 1238 tests`，全部 unittest 合计 1502 个；含 `RECORD_OK superpowers adapted=7.0.0` 与 `external skill versions tests passed` |
| `bash codex/tests/test-external-skill-versions.sh` 反向证明 | PASS | 临时把版本比较改成恒返回 `BEHIND`，测试退出 1：`FAIL: claude-newer: exit 0, expected 1`；还原后通过 |
| smoke 新锚点反向证明 | PASS | 两侧技能副本删去成对短语后，对应 `grep -Fq` 退出 1 |
| `python3 -B codex/tests/check-project-leak.py` | PASS | `15 baseline files, 93 hits`，与基线相同，未新增命中 |
| `check-change-documents --repo .` | PASS | `gap=0` |
| `bash codex/tools/check-external-skill-versions.sh`（本机真实 home） | PASS | 见下方原文 |
| Codex 独立审查 | FAIL → 已修复 | 首轮指出 4 处读取漏判（Codex 配置标量或字符串 `enabled`、marketplace 标量、Claude 插件键缺 marketplace、CLI 版本不认识未计入失败、缓存目录不可列出时崩溃）与 SC2016；`e0ea16e` 全部改为 `UNKNOWN` 退出 1 并补回归用例，smoke 加注释 |
| 负责人重装两侧平台技能后读回（AC4） | NOT RUN | 合并后由负责人执行，结果补记到本节 |

本机实跑输出（`e0ea16e`）：

```text
CLI claude 2.1.228
CLI codex 0.161.0
SUPERPOWERS claude ADAPTED installed=7.0.0 adapted=7.0.0
SUPERPOWERS codex NOT_LOADED enabled=superpowers@openai-curated marketplace=unregistered cached=5.1.3 adapted=7.0.0
MATT claude PIN_CLEAN
RESULT PASS
```

## AC2：Codex 侧 superpowers 实际生效版本

- `~/.codex/config.toml` 有 `[plugins."superpowers@openai-curated"] enabled = true`，`[marketplaces.*]` 只注册了 `openai-bundled`、`claude-code-warp`、`claude-plugins-official`、`openai-codex`、`openai-primary-runtime`，没有 `openai-curated`。
- 缓存：`~/.codex/plugins/cache/openai-curated/superpowers/bd2122cb/.codex-plugin/plugin.json` 版本 5.1.3；`openai-curated-remote/superpowers/6.4.2` 存在但未启用。
- `codex debug prompt-input "hi"`（codex-cli 0.161.0）：模型可见技能共 253 个，技能根目录 `r0`–`r8` 不含上述两个 marketplace，列表中没有任何 superpowers 技能。
- 结论：Codex 侧 superpowers 当前未生效。若负责人想让两侧一致，可选做法是在 Codex 里注册提供 superpowers 的 marketplace 并启用对应插件；Codex 侧 marketplace 目前最高可见 6.4.2，启用后脚本会报 `BEHIND`。本票不改本机插件配置。

## AC5：provider 验收矩阵（`08` §7）

| 层 | 结果 | 依据 |
|---|---|---|
| 1 技能静态验证 | PASS | 全量 smoke 的技能 front matter、触发描述、成对规则与危险参数检查 |
| 2 合成 Issue | PASS | 全量 smoke 内 `codex/runtime/tests`（含 `test_classification.py` 五类 classifier case 与四种终态） |
| 3 真实集成 pilot | NOT RUN | 需要 VM 上启用 provider 跑真实 Issue；`IMPLEMENT_PROVIDER` 仍为 `none` |
| 4 项目 profile 验收 | NOT RUN | 同上，按项目各自执行 |
| 5–7 自修复、升级、CI feedback | NOT RUN | 依赖第 3 层的真实运行 |
| 8 非生产首次部署 | not applicable | 平台仓无应用部署目标 |
| 9 生产负向边界 | NOT RUN | 依赖真实 provider 运行 |

CLI 版本：Mac 上 Claude Code 2.1.228、codex-cli 0.161.0。VM 服务层 CLI 版本未读取（NOT RUN）。
