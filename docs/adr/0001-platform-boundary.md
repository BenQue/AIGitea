# ADR 0001 · 平台边界与两层分离

- 状态：已采纳（Issue #364，负责人 2026-10-17 确认）
- 日期：2026-10-17
- 依据：2026-10-17 平台全面评审（项目库 `platform-review-261017-20261017T051455-f916.md`）与负责人 10-17 的定位答复
- 取代：无。本 ADR 不撤销 Claude 与 Codex 对等、单闸门、受保护 `main`、broker 唯一写路径等既有决定，只给它们划出边界。

## 1. 背景

平台的定位是“通用的标准流程、自定义技能和外部技能”，项目专属的构建部署细节属于项目仓。
评审发现目标在代码层漂移：`codex/runtime` 约 3 万行实现加 3 万行测试，broker 有 39 个 typed 操作，
其中一部分直接写死项目名、主机、服务和路径（#340 application target、#213 routine pilot），
项目模板携带某个项目的依赖边与 registry（#201、#286），通用流程文档夹带项目事故细节，
新技术栈需要平台登记 profile（#358）。同时 `AGENTS.md` 达 13 KB 并含 #327 单票合同，
9 月以来 54% 的提交只改证据文档。

根因不是“平台有代码”，而是**通用内核与项目需求之间没有成文边界**，项目需求可以直接变成平台代码。

## 2. 决定

### D1 平台交付什么

平台只交付四类东西：

1. **标准流程**：Issue → 判级 → spec/plan → 实现 → 唯一 PR → 人工合并 → 独立部署授权，以及它的文档合同与模板。
2. **自定义技能**：`aisoft-platform`、`issue-session-flow`、`aisoft-matt-workflow` 与兼容 adapter。
3. **外部技能的 pin 与适配约束**：Matt、superpowers 等，平台不改写原文。
4. **通用执行内核**：只限下列五类代码。

| 内核类别 | 职责 | 现有代表 |
|---|---|---|
| K1 凭据与身份隔离 | typed 操作、凭据托管、manifest 绑定 | `aisoft_host_access`、`host-access-broker.sh`、`git-credential-aisoft-host.sh` |
| K2 受保护 main 与硬门 | 分支保护、required CI、routine merger、标签治理 | `aisoft_gitea_governance`、`aisoft_main_integration.py`、label/settings 同步工具 |
| K3 通用流程 runtime | 命名、语义文档 resolver/publisher、判级投影、Controller | `aisoft_loop`、`aisoft_change_name.py`、`aisoft_worktree_owner.py` |
| K4 通用校验器 | schema 与结构校验、漂移检查、项目对齐检查 | `aisoft_architecture` 的 schema/lock 校验、`aisoft-project-check.sh`、`check-installed-drift.*` |
| K5 安装与站点引导 | installer、source guard、平台自身的引导与同步 | 8 个 installer、`install-source-guard.sh`、`platform-bootstrap/`、`sync/` |

任何新代码必须先能归入 K1–K5 之一；归不进去的，属于项目仓或“参考实现”。

### D2 什么不进平台

- 某个项目的构建、发布、部署、迁移步骤与脚本。
- 代码、模板、技能和通用流程文档里的项目名、项目主机、服务名、路径、端口和技术栈清单。
- 为某个技术栈或某个项目单独登记的 profile、target、pilot 或闸门分支。
- 单张 Issue 的合同、状态和授权细节（它们属于该 Issue 的 `docs/changes/` 目录）。

### D3 项目数据只能出现在哪里

已注册项目的名称和项目专属值，只允许出现在：

- `codex/config/` 下的 canonical manifest；
- 测试 fixture（`codex/runtime/tests/`、各 `tests/` 目录中的夹具数据）；
- `docs/changes/` 与 `archive/`；
- `06-运维手册与踩坑集.md` 的踩坑表（事故记录本身需要具体对象）；
- `docs/adr/` 与 `docs/governance/` 中叙述决策背景的段落。

平台仓自身的名称不受此限。其余位置出现项目专属值视为渗入。平台需要按项目区分行为时，做成**扩展点**：manifest 字段，
或项目仓自带的 profile 文件，平台只提供 schema 与引擎。#340 的 application target、#213 的 pilot、
#358 的 architecture profile 都按扩展点处理。

### D4 项目需求的准入规则

来自项目的需求进入平台之前，triage 必须回答一个问题：**把这个项目换成任意一个已注册项目，需求还成立吗？**

- 成立：按平台流程判级处理。
- 不成立：退回项目仓；或者先抽象成 D3 的扩展点，平台只实现扩展点本身，项目数据留在项目侧。
- 说不清：停在 `awaiting-triage` 请人裁决。

### D5 现有目录的归类

| 目录或包 | 归类 | 处置方向 |
|---|---|---|
| `01`–`08` 分册、`README.md`、`GLOSSARY.md` | 维护层文档 | 保留；去掉项目事故与已退出项目的 as-built 叙述 |
| `09-v3…规划.md` | 已完成规划 | 归档到 `archive/` |
| `12`–`15`、`company-delivery/`、`docker-release/` | 参考实现 | 保留为可选参考；不作硬门、不作新项目默认合同 |
| `architecture/` | 拆分 | schema、校验器与 lock 规则属 K4；按技术栈登记的 profile 迁为项目自带 |
| `codex/runtime/aisoft_loop`、`aisoft_change_name.py`、`aisoft_worktree_owner.py` | K3 | 保留 |
| `codex/runtime/aisoft_host_access` | K1 | 保留；application target 改为 manifest 数据 |
| `codex/runtime/aisoft_gitea_governance`、`aisoft_main_integration.py` | K2 | 保留；routine pilot 写死项改为 manifest 自洽校验 |
| `codex/runtime/aisoft_architecture` | K4 | 保留校验部分 |
| `codex/runtime/aisoft_platform_bootstrap`、`platform-bootstrap/`、`sync/` | K5 | 保留 |
| `codex/runtime/aisoft_release` | 参考实现 | 冻结；NewEMaint 正在 pin 它的合同字节，迁出前先有发布包（D7） |
| `codex/runtime/aisoft_company_delivery`、`aisoft_company_baseline*.py` | 参考实现 | 冻结；NewEMaint 公司内网路线定案后裁决迁出或归档 |
| `codex/tools/application-target-preflight.py` | K1 扩展点 | 2026-10-18 #373 裁决：无消费方，typed 操作退役，采集器归档到 `archive/` |
| `codex/tools/install-runner-flutter.sh` | 站点 runner 能力 | 保留，在 `01` 标注为按项目需求提供的 runner 能力 |
| `codex/tools/rollback-gitea-routine-pilot.sh` | pilot 遗留 | pilot 闸门退役后归档（#373 保留 pilot，写死项改为 manifest 自洽校验） |
| `skill-for-claude/`、`skill-for-codex/`、`codex/skills/` | 自定义技能 | 保留；后续合并为单一来源（D8） |
| `codex/vendor/mattpocock/` | 外部技能 pin | 保留 |
| `templates/` | 使用层发布物 | 保留；必须项目中立，例子用占位值 |
| `docs/changes/`、`archive/` | 证据与历史 | 只读保留，不改写历史 |

“参考实现”的含义：可以被项目复制或 pin，平台不为它承诺新功能，smoke 只验证它自身不坏，
不能因为它让其他平台改动变红；它的项目示例必须标明是示例。

### D6 两层分离

| 层 | 参与者 | 合同入口 | 安装面 | 验收 |
|---|---|---|---|---|
| 平台维护层 | Claude 与 Codex，对等 | 平台仓 `AGENTS.md`（只写维护层规则） | 维护者本机、broker、VM | 双提供者验收；complex 平台变更由未参与实现的一方独立审查 |
| 项目使用层 | 项目按 profile 选用 Claude、Codex 或 Cursor | 一份独立的“平台使用合同”，经 project-align 下发到项目仓指针 | 项目仓的项目级目录，带版本 pin | 每个项目、每个选用工具各自验收；默认 `IMPLEMENT_PROVIDER=none` |

- 项目使用层只消费平台发布的技能、模板和 CI 硬门，不能修改平台合同；项目对平台的需求以使用层 Issue 提出，经 D4 准入。
- 交叉审核：complex 平台变更的最终 PR，由未参与实现的另一方提供者做一次独立审查，结论写进该 Issue 的证据。它不增加人的确认点。
- 安全边界不依赖 AI 工具：受保护 `main`、required CI、manual 合并、broker 凭据隔离由 Gitea、CI 和 broker 强制；使用层接入新工具只需证明能走通流程。
- Cursor 先只进入使用层。

### D7 发布与版本

平台对使用层的输出是带版本号的发布包（技能、模板、流程文档、使用合同）。项目 pin 某个版本，
平台升级时项目按需跟进；平台内部改动不直接改变正在开发中的项目。在发布包可用之前，
NewEMaint 等项目已经 pin 的合同字节（如 docker-release 合同）保持冻结，不随清理改变。

### D8 技能单一来源

技能正文只写一份 SKILL.md，不出现某一家独有的工具名；必须依赖的能力用能力名描述并写明降级做法，
由安装器生成 Claude、Codex、Cursor 三种落点。在合并完成前，两侧现有技能继续并存，任何一侧都不得被删除或破坏。

### D9 治理成本预算

- `AGENTS.md` 不超过 5 KB，只写稳定的维护层规则和指针。
- 单张 Issue 的合同、授权和状态不得写进 `AGENTS.md`、技能或 `docs/agents/`，只写在该 Issue 的 `docs/changes/` 目录。
- verification 只记结论、命令、SHA 与证据层；大段读回输出放 CI artifact 或附件。目标是证据行数不超过变更行数。
- 测试钉结构（标题、字段、键存在），不逐字钉文档句子和项目名。新增渗入守卫（D3）由 smoke 执行。

### D10 事实来源与范围

- 本地 Gitea 与本机仓库是事实来源，GitHub 只是镜像。
- 平台服务的项目以本地 Gitea 注册和 governance manifest 为准。
- NewEMaint 是首要标杆。清理工作不得删除或改变 NewEMaint 当前依赖的平台能力；有冲突先停下说明。

## 3. 后果

- 新增平台代码多了一道归类门槛，项目专属需求会更多地留在项目仓。
- #340、#213、#358 需要返工为扩展点，相关测试要从钉项目名改为钉结构，短期内工作量增加。
- `docker-release`、`company-delivery`、`aisoft_release`、`aisoft_company_*` 在发布包和 NewEMaint 路线定案前保持冻结，冗余暂时无法全部清除。
- `AGENTS.md` 瘦身、渗入守卫和两层合同属于治理文件变更，按路线由独立的受控步骤实施；本 ADR 本身不修改任何治理文件。

## 4. 实施

整改按批次推进，见 [平台整改路线](../governance/remediation-roadmap.md)。
