---
issue: 232
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/232
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更把安装到两侧技能的共享 references（onboarding-runbook §4/§4.1/§9、project-align）里的部署实现细节收缩为 Linux 原生 / Linux 容器化 / Windows 三类环境级原则加全平台一致的流程不变量，并把根 AGENTS.md 目录段、README §5 与 02/12–15 分册的部署文档改列为「交付形态参考（按项目选用，非部署步骤事实源）」；属平台治理文档与共享 references 的合同变更，强制 complex，change_control=production 需 spec+plan
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-deploy-env-guidance-260902.md
  spec: spec-deploy-env-guidance-260902.md
  plan: plan-deploy-env-guidance-260902.md
  verification: verification-deploy-env-guidance-260902.md
confidence: high
override_reason: ''
depends_on:
  - 231
status: approved
branch: change/232-deploy-env-guidance
pr_url:
created: 2026-09-02
updated: 2026-09-02
---

## 问题/需求总结

平台仓仍把具体部署步骤写在治理位置：`skill-for-codex/references/onboarding-runbook.md` §4「CI 与部署」
把 `docker-release/v2` 的五步接入（target profile 模板、Registry publish、offline bundle、逐 action
grant）、legacy PM2 维护清单（delete+start、online 断言）与 §4.1 systemd 单元文件细节写成了「新 Linux
仓库默认」；§9 又用「见 §4.1」把 architecture profile 选择绑到这些步骤上。根 `AGENTS.md` 目录段与
README §5 把 `12-Linux…`、`12-Windows…`、`13`、`14`、`15`、`docker-release/`、`architecture/` 列在平台主线里，
读者会把它们当作部署步骤的事实源。这些 references 随两侧技能安装到每台开发机，等于把某个项目的
交付形态复制给所有项目。

2026-09-02 定案：平台着重流程管控，项目相关内容由项目自身决定，平台更加通用化。部署方案平台只
给环境级指导性意见（Linux 原生、Linux 容器化、Windows 各一类原则），不是真正的部署步骤和全部
细节；同一环境下不同项目也有细微差异，步骤与细节在项目仓实现。

本 Issue 的合同是 Issue #232 正文的「范围」「验收标准」「非目标」，本 summary 只做判级与路由。
#231（技能与项目模板去项目化、provider 等价）已于 2026-09-02 合并（PR #234，merge commit
`aefb135`），本变更在其之上，并沿用它写进 `smoke.sh` 的三条守卫口径。

## 影响范围

只改 Issue 正文列出的文件：

- 共享 references（两侧技能安装内容）：`skill-for-codex/references/onboarding-runbook.md`（§4 重写、
  §4.1 并入 §4、§9 措辞、§1.1 两处项目名措辞以满足全文 grep 标准）、
  `skill-for-codex/references/project-align.md`（checklist 第 6/7 行事实源措辞）。
- 导航与定位：根 `AGENTS.md` 目录段、`README.md` §5 文档导航新增「交付形态参考（按项目选用，非部署
  步骤事实源）」小节。
- 分册顶部定位说明（不重写正文）：`02-CI与自动部署流水线.md`、`12-Linux-GitHub-Gitea-双服务器自动部署方案.md`、
  `12-Windows平台自动部署方案.md`、`13-项目结果迁移与内网切换实施手册.md`、`14-Windows部署与迁移验收清单.md`、
  `15-VMware-Fusion-Windows-ARM原型实施手册.md`。
- 下游项目模板：`templates/project/AGENTS.md`「项目事实」节新增「部署方案位置」指针一行（常驻指针
  前两节与「工具分工」不动，`pointer-sections` 比对结果不变）。

不改 `docker-release/`（#65 证据闸门冻结）、`architecture/`、`codex/runtime/`、broker 操作表、标签
manifest、`codex/tools/aisoft-project-check.sh` 与任何检查器逻辑；不安装或更新全局 skills；不改动任何
下游项目仓；不删除或归档任何分册正文。

## 初步方案与建议

1. runbook §4 重写为三段环境原则（Linux 原生 / Linux 容器化 / Windows）、一份对所有环境一致的流程
   不变量清单，以及「项目仓必须自行声明与实现交付方案」的要求；§4.1 的 systemd 细节不再作为平台
   步骤保留，其不变量并入 Linux 原生原则段。§9 只保留 architecture catalog 的合同事实（profile 与
   `delivery_contract` 取值互斥、如实声明），去掉指向部署步骤的「见 §4.1」。
2. 根 `AGENTS.md` 目录段与 README §5 各新增「交付形态参考」小节，把 12/13/14/15、`docker-release/`、
   `architecture/` 移入，每行标注适用环境与「参考、非部署步骤事实源」。
3. 02 与 12–15 只在标题下加一段定位说明：参考性质、步骤与细节由项目仓自行实现、正文去留由后续
   「过时文档清理」Issue 处置。
4. `templates/project/AGENTS.md`「项目事实」补一行「部署方案位置」指针，让项目把自己的部署方案
   位置写明；放在「交付形态」bullet 之后、「禁改边界」之前，不进入 `delivery-profile` 检查器读取的
   交付形态块。
5. 验收用 Issue 正文的 grep 命令自证；`smoke.sh` 既有 #231 守卫覆盖 README/AGENTS/分册的活文档
   grep，本 Issue 不新增守卫（非目标：不改测试逻辑以外的检查器；守卫是否要扩到 references 留给
   后续 Issue）。

## 风险

- 治理文件：本次运行遵循的根 `AGENTS.md` 在范围内（仅目录段）。按根 `AGENTS.md`「治理文件必须先由
  独立、只修改治理合同的受控步骤应用并停止」的要求，目录段修改作为独立 ticket（T03）单独成一次
  只改 `AGENTS.md` 的原子 commit，不与其它文件混提；本变更没有依赖该目录段的 runtime 实施，因此
  无需 fresh run 再实施。工作原则段一字不动。
- 两侧技能安装内容随 references 变化：本机 `check-drift.sh` 在基线上已因 #231 未重装而 DRIFT，
  本 Issue 内不重装（非目标），verification 如实记 DRIFT 与 NOT RUN。
- 全文 grep 标准（AC-2）触及 §1.1 的两处 NewEmaint 措辞（strict `git_remote_name` 示例、#73 adoption
  顺序），它们不在「范围」点名的章节内但落在 AC-2 的全文标准内；本 summary 采用「只改措辞、不改
  合同语义」的解读，需在确认点 1 认可。
- README §5 现有「公司交付 runbook」一行（`company-delivery/runbook.md`）不在 Issue 点名清单内，
  保持原位不动，避免范围扩张。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更把安装到两侧技能的共享 references（onboarding-runbook §4/§4.1/§9、project-align）里的部署实现细节收缩为 Linux 原生 / Linux 容器化 / Windows 三类环境级原则加全平台一致的流程不变量，并把根 AGENTS.md 目录段、README §5 与 02/12–15 分册的部署文档改列为「交付形态参考（按项目选用，非部署步骤事实源）」；属平台治理文档与共享 references 的合同变更，强制 complex，change_control=production 需 spec+plan
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- Issue 正文自述「complex（平台治理文档与共享 references，影响两侧技能安装内容；强制规则）。
  change_control=production，需要 spec + plan」。
- 根 `AGENTS.md` 工作原则：「Agent 或平台治理变更一律按 complex 处理」；被改的 references 是
  `skill-for-claude/install.sh` 与 `codex/install-skills.sh` 安装到 `~/.claude/skills/`、`~/.agents/skills/`
  的 Agent 行为源，根 `AGENTS.md` 目录段与下游模板也在范围内。
- `contract_effect: change`：runbook §4 从「默认消费 docker-release/v2」变为「平台只给环境级原则，
  交付方案由项目声明与实现」，onboarding 读者看到的合同发生改变。
- `verification` 的声明依据是 `03` §3：改动前的基线观测（runbook grep 计数、`check-drift.sh` 状态、
  平台仓 `aisoft-project-check.sh --kind docs` 结果）与改动后的 DRIFT/NOT RUN 观测属 required CI 不复现的
  一次性观测。

### 缺失的 acceptance criteria 或决策

- AC-2「全文 grep 减少到只剩历史证据说明处」需要触及 §1.1 两处 NewEmaint 措辞（不在「范围」点名
  章节内）。本 summary 采用的解读：只改措辞（改为「已接入项目按各自 manifest 声明」与「项目 adoption
  Issue」），不改合同语义；目标计数为 1（第 3 行「历史试点证据」说明）。需在确认点 1 由人认可。
