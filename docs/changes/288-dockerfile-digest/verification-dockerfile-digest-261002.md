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
status: pending
branch: change/288-dockerfile-digest
created: 2026-10-02
updated: 2026-10-02
---

# #288 验证记录

## 基线与范围

- Baseline `origin/main` / worktree HEAD：`5c2cd726c9aeaee9d17541d8feb049e33881bbac`。
- 日期：2026-10-02（Asia/Shanghai）；校验探针使用 `--today 2026-10-02`。
- Worktree：`/private/tmp/issue-288-dockerfile-digest`。
- Owner session：`01a0fc7b-f327-7a93-a48c-a254937cb08d`，claim 返回 `created`。
- 当前仅记录只读基线和合同准备，不宣称修复完成。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker `gitea.issue.read` / `gitea.issue.comments.read` #288 | PASS | open，needs-analysis，1 条旧调度评论；无 approved 合同 |
| broker `gitea.pulls.read --state open` | PASS | 空列表，无重复 PR |
| broker `git.fetch.main` | PASS | project aisoft-platform、origin、上述 exact baseline |
| broker `host.onboarding.check` | PASS | binding/permission/protection/credential metadata；required `CI / verify (pull_request)`；routine disabled |
| worktree add + claim | PASS | exact tuple / session；共享 main 未 checkout/rebase/写文件 |
| architecture unittest baseline | PASS | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_architecture_*.py'`，57 tests，0.959s |
| 缺陷复现四场景 | CONFIRMED | 以下同一声明与四次结果 |
| analyzer JSON / resolver / document checker | PASS | 四角色映射；changes=145 pass=2 gap=0；准备脚本补齐 PYTHONPATH 后成功 |
| 初始 live platform classification / lifecycle | PASS | 合同准备阶段 typed classify/set 后独立 labels.read：type/bugfix、complexity/complex、spec-drafting；当时未 approved |
| Matt triage 双维度投影 | GAP | operation table 无对应 typed operation；仅 brief 推荐，未直接 API 绕行 |
| Issue durable brief | PASS | comment 11978；合同草案尚未 push，未发布虚假远端文档链接 |
| 修复后 CLI / build_lock / checker tests | NOT RUN | runtime 尚未修改 |
| 完整 runtime tests / smoke | NOT RUN | 待 T02/T03 |
| 修复 PR CI / installed / live / 现场验收 | NOT RUN | 尚无 PR；安装部署不在本合同 |

初始 sandbox Issue read 返回 TRANSPORT_ERROR；同一 typed 请求经受控 host 路径成功。
不把 sandbox 传输失败当成缺 Issue/权限故障。未读取/输出 token、env 或原始凭据。

## 基线缺陷探针

临时目录复制 `architecture/fixtures/valid/node-sqlite-container-project.json` 到
`.aisoft/architecture.json`；创建 `docs/deploy/Dockerfile`，对以下四场景依次运行同一命令：

```text
architecture/bin/aisoft-architecture validate
  --catalog architecture/catalog.json
  --profiles-dir architecture/profiles
  --schema-dir architecture/schemas
  --project <temporary-root>/.aisoft/architecture.json
  --today 2026-10-02
```

实际 subprocess 使用平台文件的绝对路径；测试不访问真实应用工作树、不联网、不运行 Docker。

| Dockerfile 情况 | 当前 exit / valid | lock_sha256 |
|---|---|---|
| `FROM node:22.22.3-bookworm-slim@sha256:16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644` | 0 / true | `a42e1ff7d5bd2c3d1bab1c2f3b5904d1da2669abc1962d83a0d11f9df2f172c4` |
| digest 改为 64 个 `a` | 0 / true | 同上 |
| `FROM node:22.22.3-bookworm-slim` | 0 / true | 同上 |
| Dockerfile 被删除 | 0 / true | 同上 |

结论：现有输入甚至没有 Dockerfile 路径，因此文件变化不进入 validator，也不进入 checksum。
Node 22 digest 来自现有 catalog / SFM #145 Issue 报告，未在本次重新 pull 或 Registry inspect。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1—AC-8 | NOT RUN | 仅确认 baseline bug；待已批准合同实施后填真实 receipt |

## 工作流与未完成项

分类：complex/manual；type/bugfix 与 complexity/complex 已 typed projection/read-back。
Matt triage 推荐 `triage/bug` + `triage/ready-for-agent`；现有 broker operation table 不包含
triage 双维度 projector，直接 Gitea API 不允许，本次不扩 broker 范围，标签投影记录 GAP。
用户已于 2026-10-02 确认合同/启动；T01 独立治理应用完成后停止，T02/T03、最终 PR 提交与人工合并尚未完成；不得关闭/归档。
不把静态源码检查解释为已构建镜像 provenance 或现场部署证据。

## 启动确认与 T01 受控治理步骤

- 用户原文：“确认”；绑定 #288 与 `change/288-dockerfile-digest`、manual。
- 批准时 spec/plan 的 SHA256 已冻结于 `evidence/contract-start-authorization.json`。
- broker 将 lifecycle 从 spec-drafting 投影为 approved；独立 read 后真实 `load_contract`
  返回 PASS、complex、8 条 acceptance criteria，未用 synthetic Issue 替代 live 启动读回。
- T01 仅应用 `architecture/schemas/project-architecture-v1.schema.json` 与
  `architecture/README.md`；本 Issue 文档记录授权/进度。无 runtime/Agent/CI/部署脚本修改。
- schema 增加可选 `dockerfiles` 语法：非空唯一字符串数组，拒绝空项、绝对路径、
  `.`/`..` segment、空路径 segment、反斜线、控制字符。delivery-specific 强制存在/禁止、
  文件读取和 FROM digest 执行仍由后续 T02 实现，未宣称 T01 已阻止基线假绿。
- README 写明完整已批准规则，并显式标注 T01 未实现 runtime/new CLI flag 的阶段边界。

| T01 check | Result | Receipt |
|---|---|---|
| schema 临时声明探针 | PASS | 2 valid / 15 invalid，使用真实 `validate_schema` |
| architecture suite | PASS | 57 tests / 0.949s |
| release architecture integration | PASS | `test_release_architecture_integration.py`，4 tests / 0.035s |
| `git diff --check` 与文件范围检查 | PASS | tracked diff 仅 schema/README；semantic docs 属当前 #288 |
| T02 runtime AC-1—AC-8 | NOT RUN | 治理步骤后必须停止并 fresh run |
| PR/CI/安装/部署 | NOT RUN | 用户此次仅批准合同启动 |

schema 探针有效集为单 `Dockerfile` 与多路径数组；无效集为：空数组、空字符串、absolute、
前置/中间 `..`、前置/中间 `.`、重复 slash、trailing slash、backslash、newline、NUL、
重复路径、非字符串项、非数组。探针使用现有合法 project fixture，只替换 `dockerfiles` 输入。
