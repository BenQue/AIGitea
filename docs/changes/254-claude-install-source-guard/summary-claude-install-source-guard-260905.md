---
issue: 254
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/254
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 给最后一个未接入的 installer 加 fail-closed staleness 闸门，改变安装期外部行为，且 installer 属部署链路
risk_flags:
  - deployment
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-claude-install-source-guard-260905.md
  spec: spec-claude-install-source-guard-260905.md
  plan: plan-claude-install-source-guard-260905.md
  verification: verification-claude-install-source-guard-260905.md
confidence: high
override_reason: ''
depends_on:
  - 250
status: approved
branch: change/254-claude-install-source-guard
pr_url:
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

`#162` 在 broker installer 上单独修好 source provenance 与 staleness 判断，`#171` 把它抽成
共用库 `codex/lib/install-source-guard.sh` 并接到五个 installer，`#182` 补第六个
`docker-release/install`，`#250`（PR 253）补第七个 `sync/install`。
`skill-for-claude/install.sh` 是仓库里最后一个未接入的 installer，`06` 踩坑 20 已如实
写明这一点。

同因的三条证据在它身上逐条成立：

- 安装源取自脚本所在 checkout（第 11 行的 `root`），checkout 落后 remote 时忠实地装旧内容。
- `grep -c 'rev-list --count|install-source-guard' skill-for-claude/install.sh` 为 0，
  没有任何 staleness 判断。
- 末尾无条件打印五行成功输出，其中包含 `Pruned N stale entries`，读起来与一次正确安装
  完全一致。

它比前七个多一层后果：装的是 `~/.claude/skills/` 下的 managed tree，安装前会 prune
每个声明 skill 目录里的 unmanaged entry。源陈旧时，它不只是装回旧版 SKILL.md，还会把
只有新版合同才有的文件删掉，并如实报成功；`check-drift.sh` 之后比对的是同一份陈旧
checkout，所以看不出区别。

这条缺口现在有直接后果：`#180`、`#243` 合并后要求本机重装 Claude 侧 skills，若在陈旧
checkout 上执行，重装会静默把旧版装回去。

## 影响范围

- `skill-for-claude/install.sh`：新增 guard 调用，不改 manifest 解析、managed tree 布局
  与 prune 语义。
- `codex/tests/test-installer-source-guard.sh`：`INSTALLERS` 加一项，三条 source state
  路径自动覆盖；新增两个期望量与一条 source tree 目录。
- `codex/tests/test-install-claude-skills.sh`：`undeclared_root` 只复制了
  `skill-for-claude` 与 `skill-for-codex`，接入后 installer 还需要 `codex/lib`，
  必须一并复制，否则该用例会以 source 失败而不是 `undeclared skill source` 结束。
- `06-运维手册与踩坑集.md` 踩坑 20：逐 installer 清单补该条，删除「仍未接入」说明。

## 初步方案与建议

在两条存在性检查之后、manifest 解析之前 `source codex/lib/install-source-guard.sh` 并调用
一次 `aisoft_install_source_guard skill-for-claude/install "$root"`，可读量为 `skills`
与 `references` 两个文件计数，形态对齐 `codex/install-skills.sh` 的 `skills` +
`matt snapshot` 与 `sync/install` 的两个文件计数。

`skill-for-claude/` 不携带版本号 JSON，所以没有 revision 标量可打印，版本证据由 guard
永远打印的 `source commit` 一行承担。第二个可读量取 `references` 而不是 SKILL.md 数：
installer 自身的双向校验（未声明的 SKILL.md fail closed、声明了却缺 SKILL.md 也 fail
closed）使得 SKILL.md 数与 skill 数恒等，再打印一次是零信息；`references` 是 managed
tree 的另一半，也是操作员在 `~/.claude/skills/aisoft-platform/references/` 下真正要
核对的那个数。

## 风险

- 接入后，源 checkout 落后 upstream 时 `bash skill-for-claude/install.sh` 会拒绝执行。
  这是本 Issue 要的行为，但会改变本机重装的既有手感；缓解办法与其余七个 installer 一致，
  错误信息直接给出 `merge --ff-only` 与 `rebase` 两条补救命令。
- `test-install-claude-skills.sh` 里 `undeclared_root` 的部分复制是本次唯一的连带修改；
  漏掉它会让该测试红在一个与被测语义无关的位置。
- 无 remote / detached HEAD / 非 git 目录降级为警告，CI 与 tarball 安装路径不受影响。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 给最后一个未接入的 installer 加 fail-closed staleness 闸门，改变安装期外部行为，且 installer 属部署链路
risk_flags:
  - deployment
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect: change`：installer 获得一条此前不存在的 fail-closed 拒绝路径，
  安装期外部行为改变，不是恢复既有合同。
- 强制 complex 规则命中「CI/制品/部署/回滚」：installer 属部署链路，与 `#182`、`#250`
  同形。
- `required_docs` 含 `verification`，与 `#182`、`#250` 不同，判据是证据来源而不是题材：
  本次要求在本机真实 `~/.claude/skills/` 上跑一次安装并观测 provenance 四行，再用一个
  落后 upstream 的临时 clone 观测「拒绝发生在 prune 之前、真实 managed tree 零变化」。
  required CI 装进一次性 tmp home，那里没有可被 prune 的既有 managed tree，因此这条
  观测只能在真实环境一次性取得，落在 `03` §3 判据表第二行。仓库的
  `deployment_lifecycle` 为 `none`，声明它不影响合并后当场到 `completed`。

### 缺失的 acceptance criteria 或决策

- 无。可读量取 `skills` + `references`（而不是 SKILL.md 数）与声明 `verification` 两项
  判断已在上文给出依据，均在 Issue 正文授权的范围内。
