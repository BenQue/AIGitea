---
issue: 397
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/397
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - agent-governance
  - platform-governance
depends_on:
  - 391
status: approved
branch: change/397-ops-closure
created: 2026-10-20
updated: 2026-10-20
git_scope:
  - docs/changes/397-ops-closure/summary-ops-closure-261020.md
  - docs/changes/397-ops-closure/spec-ops-closure-261020.md
  - docs/changes/397-ops-closure/plan-ops-closure-261020.md
  - docs/changes/397-ops-closure/verification-ops-closure-261020.md
---

# #397 spec：运维闭环第二步（R16）

## 目标与原因

第二轮整改计划 R16（项目库 `platform-remediation-plan-261020-final.md` §4）：平台对自己的安装面、凭据与仓库卫生要有节奏、有闸门、有通知。R10a（#391，`08be6f4`）的交接把三件遗留交给本批：routine 的 manifest 字段与 K1 routine 凭据种类、`aisoft_main_integration.py` 的 `aisoft-loop` 死路径、漂移检查的 `applies_to`。第二轮退出条件第 3 条（Mac 与 VM 漂移在 `applies_to` 语义下 PASS）由本批交付。

## 已核对的事实（2026-10-20，`origin/main` `08be6f4`，只读）

1. **Mac 漂移** `RESULT GAP`：`install-skills`、`install-host-access-broker`（34/34）、`skill-for-claude/install` PASS；`install-host-role` 只有一条 GAP，`/etc/aisoft/host-profile.example.json` 报 `symlink-parent`，原因是 macOS 的 `/etc` 是指向 `private/etc` 的系统链接，20 个 capabilities 全部在位；`architecture/install` 与 `sync/install` 全部 missing。
2. **VM 漂移**（`orb -m gitea-ci` 以默认用户跑同一检出）`RESULT GAP`：`install-host-role`、`install-host-access-broker` PASS；`install-skills`、`skill-for-claude/install` 0 个已装（VM 自 #391 起不再跑会话，`/home/benque` 下没有技能）；`architecture/install`、`sync/install` 全部 missing。
3. 结论：architecture 校验器与 inbound sync 在 Mac、VM 两台都从未安装，它们的落点是项目主机与内网同步主机（`07`）；技能只在 Mac。检查器没有「本机不适用」的概念，所以这四个面永远红。
4. `aisoft-alert-poll.sh`（#387）只读开放 PR 的 CI 状态、VM 定时器与 broker 可读性；不看判级投影。broker 已有 `gitea.pulls.read`（Gitea 原始 PR 对象，含 `head.ref` 与 `body`）与 `gitea.issue.labels.read`，判级投影闸门**不需要新增 broker 操作**。
5. `aigitea-cleanup-merged.sh` 默认 remote 是 `gitea`，平台仓的 remote 叫 `origin`，在平台仓上直接报 `missing gitea/main`；它还会直接 `git fetch --prune`，绕过 broker。
6. 本机：8 个 prunable worktree（#308×2、#333、#342、#343、#344、#349、#358）、11 个 `claude/*` 分支（全部已并入 `origin/main`，最新 10-08）、3 个 `.claude/worktrees/*` 分离头 worktree（最新 10-08）；本地 remote-tracking 有 61 个 `origin/change/*`，其中 59 个已并入 `main`（`git.fetch.main` 只取 `main`，不 prune，所以这些引用可能已陈旧，不等于远端真实分支）。正在用的是 `issue-395-route-card`（R10b）、`issue-396-site-externalization`（R13）与 #370 CI 下载缓存的 worktree/分支，本批不碰；动手前按 worktree 对应的 Issue 号逐个核对，只删已合并 Issue 的残留。
7. PAT：`06` §4 无轮换周期；#316 的轮换在完成一次交易时写 `provenance.json` 回执；readiness 不读任何凭据元数据。
8. 部署通知：`05` §1 写明「部署失败与回滚结果自动通知仍未实施」；`mark-deployed-issues.sh` 是部署成功后的钩子（只告警、永远 exit 0），没有失败与回滚的对应物。
9. 平台仓 `.gitea/workflows/ci.yml` 只有 `pull_request` 触发；required context 是精确字符串 `CI / verify (pull_request)`。
10. routine 遗留：两份 broker manifest 的 `credential_bindings.routine_merge_agent` 与七个项目的 `routine_merge_agent: null`；governance manifest 的 `routine_automation_allowed`、`routine_merge_agent_policy` 与七个仓库的 `routine_auto_merge_enabled`/`routine_merge_agent`；读者在两个 `contract.py`、`broker.py`、`reconcile.py`、governance `cli.py`、`credential_rotation.py`、`bootstrap-gitea-service-account.sh` 及其测试。Go PAT helper 以指针读 `routine_merge_agent`，字段缺失时该种类得到 `TARGET_UNMANAGED`，helper 源码（被 build-lock 与 provenance 钉住）**不需要改**。
11. 并行批次：R13（#396）同时改 manifest 与两个 `contract.py`；R10b（#395）同时改 `skills/issue-session-flow/SKILL.md`。发布包已发布到 1.4.0。

## 决定（确认点 1 默认值，负责人可覆盖）

- **applies_to 写在检查器里，棘轮基线单独一份 JSON。** 每个安装面声明适用主机：`install-skills`、`skill-for-claude/install` → `mac`；`install-host-role`、`install-host-access-broker` → `mac`、`vm`；`architecture/install`、`sync/install` → `target`（项目主机或同步主机，Mac 与 VM 都 SKIP）。新增 `--host mac|vm|target`，Darwin 默认 `mac`，其它系统必须显式给出（不猜）。`codex/config/installed-drift-baseline.json` 按主机记录每个面的期望结果；结果比基线差报 `RATCHET GAP`，比基线好报 `NOTE` 提示收紧基线，不自动改写。本批提交的基线是两台全 PASS/SKIP。
- **macOS 的 `/etc` 系统链接按已知别名处理**：只在 `install_root` 为 `/` 且主机是 `mac` 时，把 `/etc`、`/var`、`/tmp` 三个顶层系统链接解析到 `/private/...` 再做逐级无跟随检查；其余任何链接仍是 `symlink-parent` GAP。
- **重装进收尾**：`issue-session-flow` 收尾在文档自查之后加一步「重装并读回」——本批 diff 触及 broker、runtime、技能或 installer 时，会话给出两台重装的完整命令（Mac 终端可直接执行，VM 经 `/usr/local/bin/orb -m gitea-ci`），负责人执行后会话读回两台 `check-installed-drift` 与 readiness，结果写一条 Issue 评论；没触及就写「不适用」。调度会话职责加「每周一次本机 worktree/分支清扫」。R10b 同改此文件，谁后合并谁用 merge commit 集成。
- **投影闸门进 Mac 告警**：对每个开放 PR，按 exact `change/N-…`（兼容旧 `change/N`）分支名取 Issue 号，取不到再用正文唯一一行 `Closes #N`；读该 Issue 标签，缺 `type/*` 或 `complexity/*` 任一即产生告警键 `projection:<project>:<N>`；PR 无法绑定 Issue 也报一条。沿用现有「同键只通知一次、清除后再出现才再通知」与 broker 不可读时保留旧键的语义。
- **清扫工具**：`aigitea-cleanup-merged.sh` 不再自己 fetch（调用前先跑 broker `git.fetch.main`），remote 默认从仓库的平台 remote 推断，推断不出就要求显式 `--remote`；新增 `--remote-branches` 只读清单：列出已并入 `main` 的 `change/*` remote-tracking 引用，并注明它们可能陈旧、删除远端分支由负责人在 Gitea 界面或按清单执行。本机这次清零由会话执行（`git worktree prune`、`git worktree remove` 不带 `--force`、`git branch -d`），只动事实 6 列出的对象，脏或未合并的跳过并报告。
- **PAT 周期 180 天**：写进 `06` §4；readiness 新增 `PAT_AGE`，只读 manifest 声明的 Mac canonical store 里已完成轮换的回执时间（不读 token 文件），超过 180 天或没有回执都报 `NOTE`，永不 GAP。
- **部署失败/回滚通知模板**：`templates/project/ci/deploy-notify.sh`，项目在部署 job 的失败或回滚步骤里调用；按与 `mark-deployed-issues.sh` 相同的方式解析本次部署覆盖的 Issue，各发一条只含状态、阶段、提交与运行链接的脱敏评论（Gitea 再按 `05` 的邮件规则通知参与者）；任何前置缺失只告警、exit 0。平台不替任何项目接入。
- **平台仓 push-main CI**：`ci.yml` 加 `push: branches: [main]`，job 名与 key 不变，合并预览步骤本来就只在 `pull_request` 跑；required context 不变。`block_on_outdated_branch` 本批**不改**，只在 verification 记下按踩坑 29 评估所需的数据（push-main 跑过一段时间后再决定）。
- **routine 字段删除放在最后一个 ticket，等 R13 合并后再开工**，避免两批同时重写 manifest 与 `contract.py`；Go helper 不改。若其它 ticket 都完成时 R13 仍未合并，我在线程里问你是等还是拆出去。
- **发布包**：`issue-session-flow` 与 `templates/project/ci/` 是成员，本批发布当时下一个空闲版本（现在是 1.5.0；被 R10b 或 R13 先占就顺延）。

## Acceptance criteria

- [ ] AC1 Mac 与 VM（`--host vm`）`check-installed-drift` 在 `applies_to` 语义下 `RESULT PASS`，SKIP 行写明适用主机；基线 JSON 提交；夹具测试覆盖：不适用报 SKIP、比基线差报 `RATCHET GAP`、比基线好报 `NOTE`、Linux 未给 `--host` 报错、macOS `/etc` 别名 PASS 而其它父链接仍 GAP。
- [ ] AC2 `issue-session-flow` 收尾含「重装并读回」一步与调度会话的周清扫职责；技能单源生成的落点与漂移检查同步。
- [ ] AC3 反向证明：构造缺 `complexity/*` 投影的开放 PR 夹具，`aisoft-alert-poll.sh` 通知一次、第二次不重复；补齐标签后告警清除；无法绑定 Issue 的 PR 报警；broker 读失败时保留旧键。
- [ ] AC4 `aigitea-cleanup-merged.sh` 在平台仓上 dry-run 可用、不发起网络访问；`--remote-branches` 输出清单；本机 prunable worktree、`claude/*` 分支与 `.claude/worktrees/*` 清零（会话执行并读回 `git worktree list`、`git branch`），R10b、R13 的 worktree 原样保留。
- [ ] AC5 `06` §4 写入 180 天周期；readiness 输出 `PAT_AGE` NOTE，测试覆盖有回执、超期、无回执三种情形，且不读取 token 文件。
- [ ] AC6 `deploy-notify.sh` 模板与测试（失败、回滚、前置缺失时 exit 0 只告警）；`05` 状态行与 §1 改为「平台提供模板，项目侧接入」。
- [ ] AC7 `ci.yml` 增加 push-main 触发，required context 字符串不变；合并后读回 `main` 上一次 push 运行的结论。
- [ ] AC8 routine 退出收尾：manifest 字段、policy 与 K1 routine 凭据种类在真实与夹具 manifest、合同、broker、governance、轮换与 bootstrap 工具及测试中删除；`aisoft_main_integration.py` 的 `aisoft-loop` 支删除；两个 `validate` 对真实与夹具 manifest PASS；`git grep routine` 只命中 `docs/changes/`、`archive/`、`docs/adr/`、踩坑表与 Go helper。
- [ ] AC9 治理文件（技能、`ci.yml`）单独 commit 后停下重读，再改 runtime。
- [ ] AC10 `bash codex/tests/smoke.sh` 全绿；改 shell 后 `bash -n` 与 ShellCheck 通过；`usage-bundle.sh --release <下一版本>` 后 `--verify` 通过；路线图 R16 行改状态。
- [ ] AC11 Codex `codex exec -s read-only` 对候选 head 只读审查 PASS，记录写项目库 `codex-review-397.md` 与 verification；合并前 `apply-classification-labels.sh --verify 397` 读回 `projected`。
- [ ] AC12 合并后（负责人执行重装，会话读回）：两台重装 broker、host-role 与技能；Mac 与 VM 漂移按 AC1 读回 PASS；readiness 读回；Mac 告警重装后一轮读回。

## 接口、数据与兼容性影响

- `check-installed-drift` 新增 `--host`；Linux 上不带它的调用从 GAP 变为参数错误（exit 2），VM 侧读回命令要加 `--host vm`。JSON 输出每行增加 `applies_to` 与 `scope: SKIPPED` 的可能值。
- manifest schema 收窄（删字段），旧 manifest 带 routine 字段将被 `validate` 拒绝；两台必须同时重装。broker 操作数不变（34）。
- 告警多一类键；已有 state 文件兼容。
- 发布包新增一个模板成员，版本前进一次。

## 风险与回滚约束

- 漂移检查放宽成 SKIP 可能掩盖真缺失：适用表写死在检查器里并由基线 JSON 再钉一次，任何改动都会让 smoke 里的基线测试变红。
- routine 删除与 R13 撞文件：按上面的顺序约束处理，冲突行先退回 `main` 原文再重做（踩坑表与 memory 已记录的做法）。
- 本机清理不可由 revert 恢复：只用不带 `--force` 的 `git worktree remove` 与 `git branch -d`，已合并才删。
- 代码部分均可由 revert 恢复；两台重装后再 revert 需要再重装一次。

## 非目标

- 不新增 broker 操作；不改 Go PAT helper；不做真实 PAT 轮换；不删远端分支；不替任何项目接入部署通知；不改 `block_on_outdated_branch`；不处理 R11 的 `get-issue`/`list-issues`/`apply-analysis` 去留。
