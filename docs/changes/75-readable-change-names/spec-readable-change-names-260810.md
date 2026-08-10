---
issue: 75
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/75
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authorization
  - external-contract
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/75-readable-change-names
pr_url:
created: 2026-08-10
updated: 2026-08-10
---

# Readable issue-scoped Change naming spec

## 目标与原因

保留 Issue number 作为唯一审计主键，同时让所有新 Change 的 branch、semantic docs directory 和 worktree
在列表中直接表达主题。平台必须把名称解析、格式化、匹配、legacy compatibility、duplicate detection 和
PR binding 收敛为同一 fail-closed 合同，不能由各脚本维护相似但不同的正则。

## 规范命名合同

新 Change 的 canonical tuple 为 `(issue_number, slug)`：

- `issue_number`：正整数，十进制、无前导零。
- `slug`：2–4 个 segment，以单个 `-` 连接；只允许 ASCII lowercase `a-z` 与 digit `0-9`；总长
  `2..32`，至少包含一个字母。禁止 uppercase、Unicode、whitespace、`.`、`_`、`/`、连续/首尾 `-`。
- exact reserved slug：`main`、`master`、`head`、`merge`、`pull`、`pr`、`refs`、`change`、`changes`、
  `docs`、`worktree`、`tmp`、`temp`、`legacy`；同时禁止以 `tmp-`、`temp-` 或 `legacy-` 开头。
- branch：`change/<N>-<slug>`。
- semantic docs directory：`docs/changes/<N>-<slug>/`。
- worktree label/path basename：`issue-<N>-<slug>`；父目录仍由 project profile 固定。
- semantic document basename 继续为 `<role>-<slug>-<YYMMDD>.md`，其 slug 必须与 Change slug 完全一致。
- 所有 front matter `issue` 与 `branch` 必须分别 full-match `<N>` 和 canonical branch；不能只比较 prefix。

slug 可在不同 Issue 之间重复，因为唯一键是 `(issue_number, slug)`。同一 Issue 在 local/remote branches、
docs directories 与 open PR 中最多存在一个 active slug。

## Slug 生成与重命名策略

- analyzer 继续输出并验证 `document_slug`；wrapper 在任何 branch/docs/worktree mutation 前把它解析为
  `ChangeName`，随后只从该对象生成所有路径和 ref。
- 若 exact remote legacy `change/N` 已存在，wrapper 进入 evidence-derived legacy maintenance；否则它先发现
  0 或 1 个 remote readable branch。0 个时使用 analyzer slug 创建新 Change，1 个时必须复用其 exact slug，
  多个时 fail closed。
- canonical branch 或 summary 首次创建后 slug 即不可变。任何 typo 或主题变化都不得原地 rename、复制目录或
  新建第二个 branch/PR；关闭/保留当前 Issue 审计链，并由人创建新的 Issue。
- caller 不能提供 `--slug`、`--legacy`、raw directory、worktree path、remote、URL 或 refspec 绕过 analyzer/
  manifest。交互式人工创建也必须把所选 slug作为 exact typed ChangeName 输入并接受同一 validation。

## Legacy 兼容合同

- legacy branch 只指 operation 开始前已经存在于 manifest-fixed remote 的 exact `refs/heads/change/N`。
  legacy docs 只指已在 Git history 中 tracked 的 `docs/changes/N/`。本地新建同名对象不构成 legacy evidence。
- resolver/loader、controller maintenance、PR/status readback 和 cleanup/deployment history parser 可以读取或
  维护 evidence-derived legacy Change；new analyzer/writer、first push 与 first PR 默认拒绝纯 `change/N` 和
  新建 `docs/changes/N/`。
- legacy branch 不强制迁移到 readable 名称；不得批量 rename/delete branch、worktree、directory、PR 或 commit。
- legacy 与 readable 对象对同一 Issue 并存、多个 readable slug、或多个 matching open PR 均为
  `CHANGE_NAME_CONFLICT`，不能自动选择“较新”对象。
- compatibility evidence 由 Git remote/history/runtime 产生，不新增 caller-controlled boolean，也不以 Issue
  number cutoff、当前日期或本地未跟踪文件猜测。

## Controller、文档与 PR 合同

- 在 `aisoft_loop` 内提供共享 parser/formatter；analysis、contract、documents、controller、Gitea adapter、
  state/worktree 和 agent shell wrappers 全部使用它。
- new document resolver 只接受 exact `docs/changes/N-slug/`，要求 directory slug、summary `documents` mapping、
  每份 semantic basename、每份 front matter branch 完全一致；legacy resolver 只在 evidence-derived mode 读取
  `docs/changes/N/` 与既有 legacy/semantic basenames。
- worktree discovery/creation basename 固定为 `issue-N-slug`。已有错误 label/path 不自动 move；冲突直接停止。
- 新 PR 的 head 必须 exact `change/N-slug`，body 必须恰有一行 `Closes #N`，且 summary link 必须 exact 指向
  `docs/changes/N-slug/<mapped-summary>`。`Closes #N` 不能通过 substring 命中 `#N0`，新 PR 不允许附加其它
  `Closes #M`。历史 batch-close PR 仍可被只读/deployment history parser 解析。
- controller push/create PR 前必须读取 remote branches 与 open PR，证明同一 Issue 不存在其它 active slug/legacy
  ref；结果为空或 exact self 才能继续。

## Host-access broker 与 bootstrap

- `host-access-broker/v1` 的 `git.fetch.change` 与 `git.push.change` 接受 exact
  `change/N-slug`，使用共享等价 grammar full-match；调用方仍只提供 typed `branch`，项目、remote、owner、repo、
  URL 与 refspec 均来自 manifest/runtime。
- push 保留 current worktree/common-dir、exact branch/HEAD、clean、fresh main ancestry、no merge commit、non-force、
  non-delete、same-name refspec 和 protected-main gates；另在 credential/network write 前拒绝 same-Issue duplicate
  remote branch/open PR。
- legacy `change/N` 只允许 fetch/read 与对已存在 exact remote ref 的 fast-forward maintenance push；不能用 broker
  first-push 创建新的纯编号 branch。
- Issue #75 的 installed broker 不理解新格式。完成 candidate tests 后，唯一允许的 bootstrap 是从本 exact
  worktree 运行 repository source broker，指定 manifest project `aisoft-platform`、operation
  `git.push.change`、branch `change/75-readable-change-names`。source broker 仍读取 protected project credential，
  固定 manifest remote/refspec，并接受相同 host approval；禁止 generic `git push`、curl、`ci-bot`、force/delete。
- source candidate 只能推本 Issue branch并创建/更新唯一 `Closes #75` PR；merge 始终由 `admin` 人工执行。人工
  合并后才能从 exact protected-main bytes 安装 broker/controller/skills；installer 保留 `.previous`，second run
  必须 no-op，readback 必须 byte-equal main。下游项目迁移需独立 Issue。

## 治理文件授权与运行隔离

root `AGENTS.md` 与 `codex/global-AGENTS.md` 的规则变更已由独立 governance-only step 提交；后续 runtime
implementation run 以重新读取后的 ruleset 作为 immutable input。本 spec 继续授权在 Issue #75
范围内修改 Agent/Controller/broker、skills、templates、tests 和相关平台文档；若还需改变 governing rules，必须
停止并建立新的独立治理合同。

## Acceptance criteria

- [ ] **AC-1 Shared parser**：一个 deterministic ChangeName parser/formatter 覆盖上述 issue/slug/保留字规则；
  branch、directory、worktree、document 与 front matter full-match，任一编号/slug 不一致均 fail closed。
- [ ] **AC-2 New default and legacy compatibility**：new analyzer/writer/first push/first PR 拒绝纯 `change/N` 与新建
  `docs/changes/N/`；已有 remote/history evidence 的 legacy Change 可读、可做 non-force maintenance，不要求
  rename/delete，且不存在 caller `legacy` bypass。
- [ ] **AC-3 Single active name**：同一 Issue 的 legacy/readable 并存、多个 readable slug、多个 directory 或多个
  open PR 均返回 `CHANGE_NAME_CONFLICT`；不同 Issue 可复用同一 slug。
- [ ] **AC-4 Controller and worktree**：analyzer 在 mutation 前锁定 slug；controller/state/worktree 使用
  `issue-N-slug` 并复用 exact branch，slug 创建后不可 rename；provider commit/ancestry/clean gates 保持。
- [ ] **AC-5 Broker Git boundary**：`git.fetch.change`/`git.push.change` 支持 exact readable branch，拒绝 main、
  wrong number/slug、force/delete、arbitrary refspec、cross-project/URL/remote、dirty/detached/merge/non-FF；legacy
  first push 被拒绝，existing legacy maintenance 有 deterministic evidence。
- [ ] **AC-6 PR binding**：新 PR head、exact single `Closes #N` 与 mapped summary link 三者的 N/slug 完全一致；
  `#N0` substring、wrong/duplicate slug、第二个 `Closes`、多个 matching open PR 全拒绝；history parser 保留旧 PR。
- [ ] **AC-7 Documentation and scaffolding**：fresh implementation run 更新 root/global AGENTS、README、03/04/06/08、
  skills、agent templates、change templates 与 onboarding examples；所有新示例使用 readable branch/docs/worktree，
  legacy 仅标记兼容，不把历史批量重写。
- [ ] **AC-8 Verification matrix**：unit/public CLI/real temp Git/shell/smoke 覆盖合法、编号/slug mismatch、保留字、
  duplicate、legacy read/maintenance、first-push denial、PR exact closure、bootstrap push fail-closed；修改 shell 后
  `bash -n`/ShellCheck（若可用）、JSON/Secret/diff gates 全部通过。
- [ ] **AC-9 Governed delivery and install**：唯一 `change/75-readable-change-names`、唯一 semantic directory、唯一
  `Closes #75` PR；candidate source broker only 完成 typed bootstrap，停止在人工 merge；exact-main install、second
  no-op/readback 在合并后执行，下游迁移、部署、Secret/权限/VM/数据库操作均保持独立授权或 `NOT RUN`。

## 接口、数据与兼容性影响

这是 Git/文档/controller/PR 外部合同变更，不修改业务 API 或数据库。新格式只影响新 Change 的创建默认值；
历史 branch、docs、PR 和 commits 保持可恢复、可审计。下游在安装 exact merged platform bytes 前继续使用旧合同，
安装后新 Change 必须 readable，existing legacy 只进入 evidence-derived compatibility path。

## 风险与回滚约束

候选代码回滚使用 normal PR revert。post-merge installer 必须保留 `.previous` 并支持 exact rollback/readback；
若新 runtime 误拒绝 legacy maintenance，停止新 Change 创建并回滚 installed bytes，不 rename/delete history。
任何 duplicate/conflict 都升级给人，不自动清理。

## 非目标

- 自动 merge、删除/批量重命名历史 branch/worktree/docs、force-push 或 rewrite history。
- 修改 project Secret、credential、PAT、ACL、permission、protection、required CI、VM/service、Docker、数据库、部署或生产。
- 普通 Git/curl 绕过 broker、访问 `ci-bot`、caller-controlled URL/remote/refspec/path/legacy mode。
- 在本 analysis/spec run 修改它正在遵循的 root `AGENTS.md`。

## 未决问题

无。实现方向、compatibility evidence、immutability、bootstrap 与 governance fresh-run boundary 均已明确。
