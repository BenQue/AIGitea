---
issue: 288
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/288
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - platform-governance
depends_on: []
status: approved
branch: change/288-dockerfile-digest
created: 2026-10-02
updated: 2026-10-02
---

# #288 实施计划

## Ticket graph

| Ticket | Delivers | blocked_by | Status |
|---|---|---|---|
| T01 | 独立应用 Dockerfile 治理合同，提供可审阅的 schema/docs 输入面，commit 后停止 | [] | done |
| T04 | 已批准补充的两处测试 root 与 synthetic 模板，独立治理 commit 后停止 | [T01] | done |
| T02 | fresh run 后完整实现容器 FROM 文件核验，迁移 fixtures，所有 CLI 与库调用同一硬门 | [T04] | done |
| T05 | 已批准 fixed evidence exact lock pin 与防篡改单测，独立治理 commit 后停止 | [T02] | done |
| T03 | 项目 checker、lock/release 兼容与全套回归验收，完成唯一最终 PR 候选 | [T02, T05] | pending |

T01 为平台治理必须隔离的 contract-only 步骤，不伪装成 runtime 已交付。
T02 为一个完整可观察垂直切片，覆盖声明输入、文件读取、FROM 核验、CLI、fixtures 与测试。
全部 ticket 在父 Issue，不新建 child Issue，不增加 PR。

## Expected touch points

- T01：`architecture/schemas/project-architecture-v1.schema.json`、`architecture/README.md`；
  本 Issue semantic docs 同步进度。只增加已批准的声明语法与约束，停止后交 fresh run。
- T04：已批准补充的 `codex/tests/smoke.sh`、`codex/tests/test-architecture-install.sh`、
  `architecture/templates/project-architecture.example.json` 与 `architecture/templates/Dockerfile.example`；仅迁移构建输入。
- T02：`codex/runtime/aisoft_architecture/{cli,validator,lockfile}.py`，可新增局部 Dockerfile reader
  module；相关 `test_architecture_*.py`、新增 CLI/path/from 行为测试；
  `architecture/fixtures/` 与容器 reference 的 synthetic Dockerfile/对应 lock。
- T03：相关 `test_release_architecture_integration.py`、项目 checker 回归测试、verification receipt。
  现有 checker 使用 `.aisoft` 路径推导 root；不改 shell/CI/Controller/provider/AGENTS。
- 不改 catalog/profiles/checksum 规则（#287）、release schema/runtime、其它 Issue 文档。

## 测试与验收映射

| AC | Verification command or review |
|---|---|
| AC-1 | SFM digest 正确/失配/可变 tag subprocess CLI 三入口探针 |
| AC-2 | 多文件、多外部 stage、内部 stage 与 scratch 外部行为 tests |
| AC-3 | ARG 默认值/变量、平台参数、畸形语法与 heredoc 诊断 tests |
| AC-4 | root/cwd、缺路径/文件、越界、symlink、encoding/size 与输出脱敏 tests |
| AC-5 | 非容器基线 bytes 比较与不读取 Dockerfile 的反向探针 |
| AC-6 | 两次 byte-identical lock、失败不覆盖、旧 lock 失配、lossless release-reader regression |
| AC-7 | README review；`PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py'` |
| AC-6 / AC-7 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_release_architecture_integration.py'` |
| AC-7 / AC-8 | 临时应用 checkout `.aisoft` checker 集成探针；`bash codex/tests/smoke.sh` |
| 文档/分类 | `resolve-documents 288`、`check-change-documents`、真实 exact #288 classification projection/read-back |

用户于 2026-10-02 确认本计划启动；授权 receipt 保留批准前 spec/plan SHA256。
T01 已应用 schema/README，语法探针、architecture 57 tests、release integration 4 tests 与文档检查通过。
本受控步骤独立提交后停止；T02/T03 继续遵循本已批准合同。

完整 runtime unittest 与平台 smoke 在最终候选前运行；新失败按真实原因修复，不能让合同后退。
shell 仅允许 T04 明确批准的两个测试入口，各新增 root 参数；运行 bash -n、ShellCheck（可用）与真实 smoke。其它 shell/CI 改动仍属范围扩张，必须先提出合同调整。
治理 T01 检查 schema 与旧调用兼容，不以尚未实现的 AC 报 PASS。

## 依赖、整合和两个确认点

`depends_on: []`，Issue body 声明无硬依赖。#287 为文件邻近关联，不创建虚假的阻塞边。
2026-09-15 评论的延后顺序由 2026-10-02 本轮派单重新推进；若最终 owner/main 状态产生真实
冲突，交由调度协调，双方仅改自己的 worktree。
用户合同/启动确认之后可在范围内实现与修复；T01 后按治理要求停止，后续 fresh run 继续。
最终候选完成测试及分类 projected 读回后，另取 exact #288、branch、manual 的 PR 提交确认。
人工合并前停止 READY_FOR_REVIEW；任何批准均不授权 AI merge、直推 main、force 或部署。

## 数据库迁移、部署与回滚

数据库迁移：无。安装与部署：无。容器 declaration/lock 的输入升级需要同步路径与 checksum，
仅迁移本仓 fixtures/reference；真实应用在自己的 Change 内执行。
回滚：人工 revert 本唯一 PR 的 source bytes，运行相同回归；说明旧 validator 漂移盲点重现。

## 已批准补充的治理停止点

用户已确认 T04 补充 patch。T04 独立提交后停止，fresh turn 读取更新 spec/plan 后执行 T02；不再请求原合同启动确认。

## T02 runtime 进度

文件核验、三 CLI 入口、库 root 硬门、fixtures/reference lock 与 checker 探针已实现。
T03 仍 pending：smoke 的 release evidence 固定源码边界拒绝已迁移的 reference lock，
T05 已按用户确认完成该 pin 的独立治理补充，静态 source identity 与单测通过；
完整 smoke/runtime 待 fresh run。历史 evidence 未修改。#287 的最终整合状态待 fresh read，
最终候选前须由本 owner 自行整合真实合并后的 main 并复核 lock/release 组合。

## T05 已批准治理补充

用户确认 `evidence/boundary-amendment-proposal.json` 中完整两文件 patch。
T05 只应用 checker 的 exact reference lock pin 与对应 disk/index 防篡改单测，
保持原 historical evidence 与 runtime/real-E2E pins；本 Issue semantic docs 同步授权与进度。
检查批准 patch/hash、source identity 与 20 项边界单测，独立 commit 后停止；
T03 后续 fresh run 才重跑完整 smoke/runtime 与 #287 main 组合。
原合同/启动批准持续有效，不重复询问普通实现；最终唯一 PR 仍需单独提交确认。
