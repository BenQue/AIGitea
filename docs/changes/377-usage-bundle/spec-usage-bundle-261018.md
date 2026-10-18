---
issue: 377
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/377
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/377-usage-bundle
created: 2026-10-18
updated: 2026-10-18
git_scope:
  - docs/changes/377-usage-bundle/summary-usage-bundle-261018.md
  - docs/changes/377-usage-bundle/spec-usage-bundle-261018.md
  - docs/changes/377-usage-bundle/plan-usage-bundle-261018.md
  - docs/changes/377-usage-bundle/verification-usage-bundle-261018.md
  - usage/CONTRACT.md
  - usage/bundle.json
  - codex/tools/usage-bundle.sh
  - codex/tools/usage-bundle.py
  - codex/tests/test-usage-bundle.sh
  - codex/tools/aisoft-project-check.sh
  - codex/tests/test-project-check.sh
  - codex/tests/smoke.sh
  - templates/project/AGENTS.md
  - templates/docs/changes/_template/summary.md
  - codex/config/change-template-sync.json
  - codex/config/project-leak-baseline.json
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 04-Agent编排与定时任务.md
  - 08-双工具共存与实施.md
  - README.md
  - skill-for-codex/references/project-align.md
  - skill-for-codex/references/onboarding-runbook.md
  - skill-for-claude/aisoft-platform/SKILL.md
  - skill-for-codex/SKILL.md
  - docs/governance/remediation-roadmap.md
---

# #377 spec：平台使用合同、版本化发布包与验证矩阵分层（R6）

负责人于 2026-10-18 在项目线程“R6”回复“确认”，批准本合同并启动实现；R6 之后剩余的 NewEMaint 耦合按建议另开 R6b 批次。

## 目标与原因

ADR 0001 D6 要求项目使用层有一份独立于维护层 `AGENTS.md` 的“平台使用合同”，经 project-align 下发；D7 要求平台对使用层的输出是带版本号的发布包，项目 pin 某个版本，平台内部改动不直接改变正在开发中的项目。负责人的目标是项目实例与平台之间没有直接硬性依赖，部署细节留在项目，平台只保留流程与解决方案模式。

## 已核对的事实（2026-10-18，确认前取证）

- NewEMaint（`gitea/main` `dfcde808`）与 LocalWMS（`origin/main` `de829b9`）的 `AGENTS.md` 指针都写“合同源：`~/MyDocs/AISoftPlatform/`”，即本机平台仓 live main。
- project-check 的 `pointer-sections` 与 `change-templates` 拿项目文件与平台**当前**模板逐字节比较；NewEMaint 的 summary 模板已因平台模板多出的 #286 依赖边注释而不一致。
- NewEMaint 发布 workflow 按平台 commit `e1290d2` checkout 平台仓，读 `.aisoft/docker-release-contract.bytes.json` 钉住的 27 个 `docker-release/**` 与 `aisoft_release/**` 文件。本票不动这些字节（ADR D7）。
- 平台 runtime 已无 NewEMaint 字样；剩余平台侧耦合（测试读真实 manifest、pilot 回滚脚本、`architecture/reference/newemaint`、`docker-release` 示例值、`aisoft_company_*`）归 R6b 与 R8。

## Acceptance criteria

- [ ] AC1 平台使用合同 `usage/CONTRACT.md`：项目使用层唯一合同入口，内容为流程不变量（Issue 主键与可读元组、判级、两个确认点、单闸门与 routine 边界、broker 写路径、部署流程不变量）、项目必须自行声明的扩展点（交付形态、部署方案位置、发布 producer 与 transport、禁改边界、provider 选择）与版本跟进规则（项目升版本走自己的 Issue）。只含占位值，不含项目名、主机、部署步骤；维护层规则不复制进来，维护层 `AGENTS.md` 不改。
- [ ] AC2 项目指针模板：`templates/project/AGENTS.md` 常驻指针改为指向本仓 vendored 的 `.aisoft/platform-usage.md` 与 `.aisoft/platform-usage.lock.json` 的版本，不再把本机平台仓路径写成合同源（平台仓位置只作为安装与工具来源提及）。
- [ ] AC3 发布包声明 `usage/bundle.json`（`contract_version: aisoft-usage-bundle/v1`）：
  - `members` 每项 `{source, mode, target}`；`mode` 取 `exact`（项目在 `target` 持逐字节副本）、`pointer`（项目 `AGENTS.md` 的常驻指针两节，摘要按指针两节计算）、`seed`（初始化时复制，项目可改，不核对）、`skill`（安装到工具目录，无项目落点）。成员为使用合同、项目指针与 `CLAUDE.md` 模板、change 模板四件套、`docs/agents` 三件套、项目 CI 示例模板、两侧 `aisoft-platform` / `issue-session-flow` / `aisoft-matt-workflow` 技能源与共享 references。
  - `releases` 只追加，每项 `{version, released, bundle_digest, files}`，`files` 为成员 source → sha256，`bundle_digest` 为 `files` 的规范化摘要。版本为严格递增的 `MAJOR.MINOR.PATCH`。
  - 本票发布 `1.0.0`。
- [ ] AC4 工具 `codex/tools/usage-bundle.sh`（实现 `usage-bundle.py`，只用标准库，`PYTHONDONTWRITEBYTECODE`）：
  - `--verify`：声明结构合法、历史只追加且版本递增、每个版本的 `bundle_digest` 可复算、当前成员文件的摘要与最新版本完全一致；成员内容变了而没有发布新版本即失败，并提示 `--release`。平台 smoke 运行它。
  - `--release VERSION --today YYYY-MM-DD`：用当前成员内容追加一个新版本（版本必须大于最新版本）。
  - `--build DIR`：在当前内容等于最新版本时，确定性导出 `DIR/project/`（`exact`、`pointer`、`seed` 成员放到项目落点，另生成 `.aisoft/platform-usage.lock.json`）与 `DIR/skills/`（`skill` 成员按 source 路径），供 project-align 复制；DIR 必须不存在或为空。
  - `--project-status REPO`：只读，供 project-check 调用，输出 `platform-pin`、`pointer-sections`、`change-templates` 三项的 PASS/GAP 与细节。
  - 回归测试 `codex/tests/test-usage-bundle.sh` 覆盖：verify 通过；成员改动未升版本失败；历史被改写或版本不递增失败；release 追加；build 产物与摘要一致且两次 build 字节相同；project-status 在 pin 当前版本、pin 旧版本、无 lock、lock 摘要不符、版本不存在时的结论。按 smoke 五处登记。
- [ ] AC5 project-check 按 pin 核对：新增 `platform-pin` 检查（lock 存在、版本在历史中、摘要一致；落后于最新版本时 PASS 并打印 `NOTE:` 行）。`pointer-sections` 与 `change-templates` 改为对照 pin 版本的摘要；没有 lock 时对照最新版本。`test-project-check.sh` 的计数与清单同步（对齐夹具 pin 最新版本），增加缺 lock 与使用合同副本漂移的 GAP 用例；pin 旧版本仍 PASS 并打印 `NOTE:` 由 `test-usage-bundle.sh` 在伪造的平台树上覆盖（project-check 固定读真实平台仓，无法构造旧版本）。
- [ ] AC6 `08` §7 验证矩阵拆成两层：平台维护层（技能静态、合成 Issue、自修复、升级、CI feedback；两个 provider 对等，平台仓自己验收）与项目使用层（真实 pilot、项目 profile 验收、非生产首次部署、生产负向边界；每项目每个选用工具各自验收，记在项目仓）。原有九项内容不丢，只重新归层；`04` §10 的重复清单改为指向 `08` §7。
- [ ] AC7 R4 遗留：summary 模板删除写死的 #286 跨仓依赖边注释，改为中立说明“跨仓依赖只用 manifest 授权的引用”；刷新 `change-template-sync.json` digest；泄漏基线收紧。
- [ ] AC8 文档：project-align 参考改写为“按发布包版本对齐”（盘点 → 复制 `--build` 产物 → 项目 Issue/PR → 复检），两侧平台技能的 project-align 指引同步一句；`03` §3 vendored 模板一节与 `README.md` 目录说明提到发布包；onboarding-runbook 的模板复制步骤指向 `--build`。
- [ ] AC9 路线文档：R5 行改为已完成（#375，PR 376，`bcf2fd7`）；R6 行写本票状态；新增 R6b 行（测试夹具解耦与 pilot 回滚脚本通用化）。
- [ ] AC10 macOS 全量 `bash codex/tests/smoke.sh` 通过；`python3 -B codex/tests/check-project-leak.py` 不新增命中；`usage/` 无项目名。对 NewEMaint 与 LocalWMS 当前 main 只读运行 project-check 的本地段，记录采用前的结论。

## 接口、数据与兼容性影响

新增使用层合同、发布包声明与工具；project-check 输出多一条 `platform-pin`。不改 broker、runtime、manifest、installer、`docker-release/`、`aisoft_release`、`aisoft_company_*`。已接入项目在采用 1.0.0 前 `platform-pin` 与 `pointer-sections` 报 GAP，属于各项目自己的采用 Issue。`change-template-sync` 的广播与 digest 闸门本批保留不动，它与发布包的整合留给后续批次评估。

## 风险与回滚约束

之后任何改动发布包成员的平台 PR 都必须同时发布新版本，否则 smoke 红；并行 PR 可能撞版本号，按既有“并行会话撞编号”做法由后合并者 rebase 改号。回滚：revert 本 PR 后重装两侧技能；项目侧未采用前不受影响。

## 非目标

- 不改 NewEMaint、LocalWMS 仓库；它们采用发布包是各自项目的 Issue。
- 不动 ADR D7 冻结的 docker-release 合同字节与参考实现；不做 R6b（测试夹具解耦、pilot 回滚脚本）与 R8（参考实现迁出）。
- 不新增 broker 操作，不用 Gitea Release 或 tag 分发。
- 不改维护层 `AGENTS.md`。

## 未决问题

无。
