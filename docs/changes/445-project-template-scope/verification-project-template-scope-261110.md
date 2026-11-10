---
issue: 445
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/445
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
depends_on: []
branch: change/445-project-template-scope
created: 2026-11-10
updated: 2026-11-10
---
# 验证：项目来源规范模板 scope

BASE `30c8994e74767fbe660c22bfd739d7d51a9bd6b1`（2026-11-10 `git ls-remote origin refs/heads/main` 读回未移动）。负责人已选择仅更新 fresh main 已存在的规范模板，首次新增仍拒绝。

## 接手（2026-11-10）

- Codex 停止写入后，Claude 在 fresh run 中读回 Issue 合同、治理提交 `c15e63d64f24455cbba5dce01efaf964ff1d5456`、ADR 补充、工作区、branch 与 HEAD（=`c15e63d`，tracked 干净）。
- `AISOFT_SESSION_ID=b1ecf3c7-9797-423f-ae98-d2732138cd6d aisoft claim-worktree --branch change/445-project-template-scope --worktree /private/tmp/issue-445-project-template-scope --takeover` → `taken-over`；原 owner `01a1c32a-009d-7663-af62-d65a27032a16`，`last_push_head` 保持 `null`，未重置推送记录。
- 未触碰 #444 与 CarbonEngine #98 的工作区。

## 实现

- `5e457c6f`：`aisoft_main_integration.py` 新增 `ExistingMainTemplateContext`；`GitRepository.scope()` 对它逐路径要求 `ancestor(main, head)` 与 `_template_tree(main, path, required=True)`（父目录 `040000 tree`、文件 `100644 blob`），每次 `verify()` 重新 ls-remote 读 main，不等即 `BASE_BRANCH_STALE`，读不到也按 `BASE_BRANCH_STALE` 拒绝；站点 `TemplateScopeContext` 分支不变。`project_source.py` 的 `_template_context` 改为用本次已核验凭据的 Git 环境读 fresh main 构造上下文，凭据清理时一并清空。`broker.py` 推送流程未改。
- `8afcdaed`：E2E 用例、fixture 与使用包 1.23.2。
- `c0b15f7b`（审查 R1 修复）：项目来源下 `git_history_paths` 中的规范模板必须同时属于当前 `git_scope`；新增 HEAD 修成 100644 而 main 为 100755/符号链接的用例；使用包 1.23.2 按新字节重发（尚未进入 main）。

## 测试（全部本机实际运行）

| 层 | 命令 | 结果 |
|---|---|---|
| 源码 · 单元 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_project_declared_source tests.test_main_integration` | 76 tests OK |
| 源码 · 新增 | `ProjectTemplateScopeTest` 13 个用例 | OK：全部更新/部分更新与第二次推送 PUBLISHED；不读站点 manifest；main 缺任一目标（`()`、`spec`、`summary,plan`）、100755、符号链接、父目录为链接或文件、未声明路径、四种错误仓库/owner/Issue/host 绑定、提交中途删除/改 100755/改符号链接再恢复全部拒绝且远端无分支；第 1–3 次 main 读取后移动 main 均在传输前拒绝且没有 `git push`；传输后两个时点移动 main 分别报 `BASE_ADVANCED_AFTER_PUSH` 与 `BASE_BRANCH_STALE`，回执带 `possible_write: true`、`write_status: PUBLISHED`；main 不可读拒绝；main 为 100755/符号链接而 HEAD 已修成 100644 时报 fresh-main 专属拒绝且无 `git push`；模板只留在 `git_history_paths` 而移出当前 `git_scope` 时拒绝 |
| 反向证明 | 删掉 `_template_tree(context.main, …)`；令 `verify()` 恒等；删掉历史模板集合 require | 第一项 first-time-add 3 个子用例与 main 类型专属用例 2 个子用例转红；第二项传输后漂移用例转红；第三项历史用例转红；均已恢复 |
| Fixture · E2E | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_project_source_e2e`（loopback 假 Gitea + http-backend，隔离临时仓库） | 6 tests OK；新增 open-pr 首推、summary 回填为 `pr-open`、PR 查重返回同一编号、第二次 typed push PUBLISHED；首次新增 `plan.md` 经 `aisoft-access` 被 `SCOPE_DENIED` 拒绝 |
| 站点回归 | `python3 -m unittest discover -s tests -t .`（codex/runtime 全量，含 `test_host_access` 与 `test_main_integration` 的 canonical 模板用例） | `8afcdae` 829 tests OK；`c0b15f7` 831 tests OK |
| smoke | `bash codex/tests/smoke.sh` | `8afcdae` 与 `c0b15f7` 均通过（rc=0） |
| 发布包 | `bash codex/tools/usage-bundle.sh --release 1.23.2 … --compatibility patch` 后 `--verify` | 重发后 `VERIFIED 1.23.2 sha256:908047ad679fe8e24faa43879498776efe72ed97795688fa99ccc7693f7c8987` |
| 判级 | `aisoft classify --verify 445` | `projected`（security / complex） |

## 证据分层

- 源码：上表单元、反向证明与全量 runtime。
- Fixture：E2E 在隔离仓库与假服务上跑，不创建真实项目 PR。
- 发布包：1.23.2 已发布并 verify；并行 #444 计划 1.24.0，后合并者重读 main 的 `usage/bundle.json` 顺延版本号。1.23.1 不会自动获得修复。
- 安装：NOT RUN（本票不重装；项目来源随使用包下发，不经 /usr/local installer）。
- 真实项目采用：NOT RUN。CarbonEngine #98 需另行升级到含本修复的版本并经负责人授权后再推送。
- 部署、merge：不在本票授权内。

## 交叉审查

- 实现前设计预审：Herdr Claude `t24`（Opus 5.5 / high）认为选定设计可行，这不是最终候选审核。
- 最终候选审核：实现方 Claude（Opus 5.5），审查方独立 Codex 会话 `gpt-6-astra` / `model_reasoning_effort="high"`，`-s read-only -a never`，hc 终端 `t27`（名 `review-445`，挂在 Herdr 标签页 `review-445`）；hooks 信任提示由负责人处理。BASE `30c8994e74767fbe660c22bfd739d7d51a9bd6b1`。
  - R1 审 `8afcdaeda21381508bc56d06adfac3b6e2c5abb9`：FAIL。P1：`git_history_paths` 可携带当前 `git_scope` 外的模板绕过（审查方内存复现 ACCEPTED）；P2：main 非法类型用例未与 HEAD 隔离，可能假绿。其余（首次新增、别名、其他 Issue、删除后恢复、merge 夹带、推送后 BrokerError 保留 `possible_write`、站点 AST 不变、1.23.2 校验）未见问题。
  - R2 审 `c0b15f7b0044e4af9a2948fcee67530a537297fe`：PASS，P0/P1/P2/nit 无；R1 两条关闭，站点来源不变，重发的 1.23.2 校验通过，改动均在 spec `git_scope` 内。审查方未重跑全量 runtime/E2E/smoke，动态验证为其内存探针。
  - 之后仅提交本 verification、spec `git_scope` 增列 `docs/governance/review-evidence-index.md` 与证据索引行。

## 历史记录（Codex 起草阶段）

- 基线 `test_template_owning_changes_need_the_site_source` 1/1 通过（旧版拒绝行为）；该用例已改为 `test_template_context_needs_a_verified_git_operation`。
- `aisoft prepare-ticket 445 T01 --provider codex` 返回 `prepared`；`aisoft check-change-documents` 为 `changes=205 pass=2 gap=0`。
- 项目侧只读核对：CarbonEngine Gitea main `b97c61d49acd63e3b4a4d56dbdaaed227ed6c25d` 的四份规范模板均为 `100644` blob；#98 本地 HEAD `43a81e47a59ecf09262ad1a73fe75dc2cc98090a`。这不是新版本项目采用或真实推送证据。
