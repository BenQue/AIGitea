---
issue: 232
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/232
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on:
  - 231
status: approved
branch: change/232-deploy-env-guidance
created: 2026-09-02
updated: 2026-09-02
---

# Spec · 部署文档收缩为环境级指导：Linux/Windows/Docker 原则在平台，步骤与细节在项目

## 目标与原因

把平台仓里的部署内容收缩为**环境级指导性意见**：对 Linux 原生、Linux 容器化（Docker）、Windows
三类环境各给出原则与验收不变量，不再给出真正的部署步骤与全部细节。具体部署方案、脚本、参数与
差异一律在各项目仓实现——即使环境相同，不同项目也会有细微差异。

2026-09-02 定案：平台着重流程管控，项目相关内容由项目自身决定，平台更加通用化。本 spec 把
Issue #232 正文的 6 条验收标准与 4 条范围逐条落成可观察结果；Issue 正文是合同源，本文不扩张。
#231 已合并，其 `smoke.sh` 三条守卫（治理文件禁项目名、禁交付形态实现名；活文档禁分主辅措辞）
在本变更中保持成立。

## 术语

- **runbook**：`skill-for-codex/references/onboarding-runbook.md`，由 `skill-for-claude/install.sh` 与
  `codex/install-skills.sh` 同源安装到两侧技能的 `references/`。
- **§4 范围**：runbook 从 `## 4. CI 与部署` 标题行起、到 `## 5. Gitea 治理` 标题行前一行止。
- **三类环境**：Linux 原生（宿主直接承载运行时，例如 systemd 直管）、Linux 容器化（OCI 镜像 +
  容器编排）、Windows（Windows Server 承载的 Web/服务运行时）。
- **流程不变量**：对所有环境一致、由平台流程管控的验收要求，见 AC-1 清单。
- **交付形态参考**：12/13/14/15 分册、`docker-release/`、`architecture/`——项目可按自身环境选用的
  参考实现与合同，不是部署步骤的事实源。

## Acceptance criteria

- [ ] **AC-1 runbook §4 重写**：§4 范围内包含且仅包含三部分：(a) 三类环境各一段指导性原则
  （Linux 原生 / Linux 容器化 / Windows，各以 `### 4.x` 小节承载，§4.1「systemd 原生交付」小节不再
  单独存在，其不变量并入 Linux 原生一段）；(b) 对所有环境一致的流程不变量清单——不可变制品、
  测试与生产同字节晋级、部署前备份、健康检查含精确 release SHA、可回滚、生产 script-only、AI 只
  参与非生产首次部署并固化为脚本（两次幂等 + 一次故意失败回滚）、`scm-ci` 只构建/测试/发布而
  mutation 只在 AppServer role；(c)「项目仓必须自行声明与实现交付方案」的明确要求（声明位置：
  项目 `AGENTS.md`「项目事实」与 `.aisoft/architecture.json` 的 `delivery_contract`；实现位置：项目
  仓自己的 `docs/` 或脚本目录）。§4 范围内不再包含具体命令、Compose/Registry/offline bundle/
  PM2 delete+start 等实现步骤；`sed -n '<§4起>,<§4止>p' onboarding-runbook.md | grep -n -iE
  'NewEmaint|rsdesign|PM2 delete|--pull never|target-profile.example'` 为空，且
  `grep -c -E '^\s*[0-9]+\. |^\s*- ' ` 统计的列表项不含任何 CLI 子命令名（`verify-artifact`、`stage`、
  `migrate`、`activate`、`rollback`、`systemctl`）。
- [ ] **AC-2 runbook 全文去项目名**：`grep -c -iE 'NewEMaint|rsdesign' onboarding-runbook.md` 从
  `main` 的 6 降到 1，仅剩第 3 行「rsdesign-new 只是历史试点证据」说明；§1.1 两处 NewEmaint 措辞改为
  项目中立表述（strict `git_remote_name` 示例不点名项目；adoption 顺序写「项目 adoption Issue」），
  合同语义不变。项目名不再作为默认值、目录、端口或部署合同出现。§1.1 两处不在「范围」点名章节内
  但落在本条全文标准内，「只改措辞、不改合同语义」的解读已于 2026-09-02 确认点 1 由人认可。
- [ ] **AC-3 导航归类**：根 `AGENTS.md` 目录段与 README §5 各有一个独立的「交付形态参考（按项目
  选用，非部署步骤事实源）」小节，收纳 `12-Linux…`、`12-Windows…`、`13`、`14`、`15`、`docker-release/`、
  `architecture/` 七项；每行注明适用环境（Linux 容器化 / Linux 原生 / Windows / 全环境）与「参考、非
  部署步骤事实源」字样；这七项不再出现在主线列表/主表中。README §5 主表其余行（含
  `company-delivery/runbook.md` 一行）保持原位。
- [ ] **AC-4 检查器与测试不变**：`codex/tools/aisoft-project-check.sh`、`codex/tests/*.sh`、
  `codex/runtime/` 的 diff 为空；`bash codex/tests/smoke.sh` 全绿；
  `bash codex/tests/test-project-check.sh` 与 `bash codex/tests/test-install-claude-skills.sh` 全绿；
  平台仓 `aisoft-project-check.sh --repo <worktree> --kind docs` 结果与基线逐行一致
  （`pass=2 gap=2 skip=4`）。
- [ ] **AC-5 两侧技能安装内容随之变化**：`bash skill-for-claude/check-drift.sh` 与
  `bash codex/check-drift.sh` 在本机报 DRIFT（退出 1）并列出 `references/onboarding-runbook.md` /
  `references/project-align.md`；重装后 CLEAN 在 verification 中如实记为 NOT RUN（非目标：本 Issue
  不安装或更新全局 skills）。
- [ ] **AC-6 `docker-release/` 不动**：`git diff --stat origin/main...HEAD -- docker-release/` 为空。
- [ ] **AC-7 分册定位说明与模板指针**（对应「范围」第 3、4 条）：`02`、`12-Linux…`、`12-Windows…`、
  `13`、`14`、`15` 各在一级标题之后新增一段以「> 定位（#232）」开头的 blockquote，说明「参考性质、
  步骤与细节由项目仓自行实现、正文去留由后续过时文档清理 Issue 处置」，正文其余行 diff 为空
  （`git diff origin/main...HEAD -- <分册>` 只含新增行）；`templates/project/AGENTS.md`「项目事实」节
  在「交付形态」bullet 之后新增「部署方案位置」指针一行（占位符指向项目自己的 `docs/` 或脚本目录），
  常驻指针前两节与「工具分工」段 diff 为空。`skill-for-codex/references/project-align.md` checklist
  第 6/7 行事实源改为「runbook §9（architecture 声明）」与「runbook §4（环境级原则）；交付方案由
  目标仓 AGENTS.md 项目事实与项目自己的部署文档声明」。

## 接口、数据与兼容性影响

- **两侧技能 references**：`onboarding-runbook.md`、`project-align.md` 是 `skills.manifest` 声明为
  `shared` 的安装内容；安装副本在重装前保持旧文；重装是合并后的独立动作。
- **`aisoft-project-check.sh`**：`delivery-profile` 只读取项目 `AGENTS.md` 中「交付形态」bullet 起、
  下一 bullet 止的块；新增的「部署方案位置」bullet 位于该块之后，不影响判定；`pointer-sections` 只比
  对常驻指针前两节与 `CLAUDE.md`，「项目事实」节变化不改变下游结果。`architecture-lock` 不读文档。
- **`smoke.sh` 既有断言**保持成立：runbook 仍含 `ensure-gitea-collaborator.sh`、`gitea-governance.json`、
  `gitea.labels.provision`；`02` 仍含 `首次部署`；根 `AGENTS.md` 仍含 `功能性更改`；#231 三条守卫
  对本变更的活文档改动仍为空命中（新增文字不使用「维护与部署 / 开发与设计 / 默认主处理者 /
  Codex 为主 / 对等补位 / primary handler」）。
- **根 `AGENTS.md`**：只改目录段（`## 目录` 至 `## Git` 之间），工作原则、初始化与开发编排、Git 三段
  一字不动；按根 `AGENTS.md` 治理文件规则，该修改单独成一次只含 `AGENTS.md` 的原子 commit（plan
  T03），本变更没有依赖该目录段的 runtime 实施。
- **architecture catalog 事实**：§9 仍如实列出四个 profile 与五个 `delivery_contract` 取值
  （`architecture/profiles/*.json` 的 `delivery_contracts`），只去掉「见 §4.1」这类指向部署步骤的引用。
- 不改 `docker-release/`、`architecture/`、`codex/runtime/`、broker 操作表、标签 manifest、任何检查器；
  不改 `templates/docs/changes/_template/`，因此无需 `change-template-sync.sh --refresh-digest`。

## 风险与回滚约束

- 回滚 = revert 本 Issue 的唯一 PR；本机已安装的 references 用上一版源重跑
  `skill-for-claude/install.sh` / `codex/install-skills.sh` 即恢复（本 Issue 内不执行安装）。
- 本 spec 即修改治理文件（共享 references、根 `AGENTS.md` 目录段、下游模板「项目事实」节）的
  授权，范围以「术语」与 AC-1～AC-7 为限。

## 非目标

- 不删除或归档任何分册正文（12/13/14/15 与 02 的正文原样保留，只加顶部定位说明）。
- 不改 runtime、broker、标签 manifest、检查器逻辑，不新增 `smoke.sh` 守卫。
- 不改下游项目仓；不安装或更新任何全局 skills。
- 不动 `docker-release/`（#65 证据闸门冻结，扩 allowlist 属另行授权）与 `architecture/`。
- 不改 README §5 主表中 `company-delivery/runbook.md` 一行（Issue 未点名）。

## 未决问题

无。AC-2 触及 §1.1 两处项目名措辞的解读，以及根 `AGENTS.md` 目录段作为独立原子 commit（T03）
的处置，已于 2026-09-02 确认点 1 由人认可，并分别写入 AC-2 正文与「接口、数据与兼容性影响」。
