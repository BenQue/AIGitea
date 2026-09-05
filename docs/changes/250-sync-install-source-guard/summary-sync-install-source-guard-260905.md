---
issue: 250
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/250
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 给 sync installer 接入 fail-closed staleness 闸门，改变安装期外部行为，且 installer 属部署链路
risk_flags:
  - deployment
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-sync-install-source-guard-260905.md
  spec: spec-sync-install-source-guard-260905.md
  plan: plan-sync-install-source-guard-260905.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/250-sync-install-source-guard
pr_url:
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

`#162` 在 broker installer 上单独修好 source provenance 与 staleness 判断，`#171`
把它抽成共用库 `codex/lib/install-source-guard.sh` 并接到五个 installer，`#182`
补上第六个 `docker-release/install`。`sync/install.sh` 是仓库里最后一个未接入的
installer：`#182` 的正文把它列为非目标并写明「若确认同因再另开」，收尾时确认同因。

同因的三条证据在 `sync/install.sh` 上逐条成立：

- 它用 `SOURCE` 取自身所在目录作为安装源，checkout 落后 remote 时忠实地装旧内容。
- `grep -c 'rev-list --count|install-source-guard' sync/install.sh` 为 0，没有任何
  staleness 判断。
- 末尾无条件打印 `installed inbound sync runtime; timer remains disabled and
  inactive`，与 `06` 踩坑 20 描述的幂等输出假阳性同形：它证明 installed == checkout，
  不证明 installed == 已合并的合同。

它比其余六个多一层后果：装的是 systemd unit 与凭据 helper，源陈旧的后果落在 VM 侧
按 timer 触发的定时同步上，而不是落在一次交互式命令的输出里。

## 影响范围

- `sync/install.sh`：在第一次文件系统写入之前 source 共用库并调用一次
  `aisoft_install_source_guard`。
- `codex/tests/test-installer-source-guard.sh`：`INSTALLERS` 数组加入
  `sync/install`，由既有的三态循环自动覆盖。
- `06-运维手册与踩坑集.md` 踩坑 20：逐 installer 可读量清单加上 `sync/install`。

不改 sync 的同步语义、systemd unit 内容、凭据 helper 与 timer 启停行为。

## 初步方案与建议

照 `#182` 对 `docker-release/install.sh` 的形态接入：先算出 `repo_root`，
`source` 共用库，在 `install -d` 之前调用一次 guard。可读量取两个文件计数，
`units` 与 `runtime scripts`，用库里已有的 `aisoft_install_source_file_count`。

`sync/` 目录里没有携带版本号的 JSON，所以不能像 `architecture` 的 catalog revision
或 `docker-release` 的 matrix revision 那样取一个会随合同变化的标量。文件计数的价值
不在于数字会变，而在于给操作者一个可以直接在目标机上比对的对象：`units` 对
`/etc/systemd/system/aisoft-inbound-sync@` 两个 unit，`runtime scripts` 对
`/opt/aisoft-sync/` 下两个脚本。版本证据由 guard 固定打印的 `source commit` 一行承担。

## 风险

- guard 会给 `sync/install.sh` 增加一条拒绝路径。源 checkout 落后 upstream 时它不再
  安装。这正是本 Issue 要的行为，但它改变了安装期的外部行为，因此 `contract_effect`
  记为 `change`。
- `sync/tests/test-install.sh` 直接在真实 checkout 上跑 `sync/install.sh`。checkout
  落后 origin/main 时该测试会随 guard 一起 fail-closed。这与其余六个 installer 的测试
  行为一致，是平台已接受的形态，不是本次变更引入的缺陷。
- 无迁移、无部署动作、不触碰凭据。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 给 sync installer 接入 fail-closed staleness 闸门，改变安装期外部行为，且 installer 属部署链路
risk_flags:
  - deployment
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `change_type: platform` 属 `FORCED_COMPLEX_TYPES`，`risk_flags` 的 `deployment`
  属 `FORCED_COMPLEX_RISKS`，两条都强制 complex，与 Issue 正文的判级提示一致。
- installer 写 `/opt`、`/etc/systemd/system` 与 `/var/lib`，属部署链路而非局部重构。
- 新增拒绝路径改变外部行为，`contract_effect` 只能是 `change`，不满足 small 候选的
  `restore|unchanged`。
- 不追加 `verification`：三条路径的验收证据全部由 `test-installer-source-guard.sh`
  在 diff review 与 required CI 上重放，本次不执行任何部署动作。

### 缺失的 acceptance criteria 或决策

- Issue 正文 AC-4 写「输出从 7 installers 变 8 installers」。origin/main 上
  `INSTALLERS` 数组实际有 6 项（broker、host-role、vm、skills、architecture/install、
  docker-release/install），因此真实数字是 6 变 7。AC 的实质是「计数行随本次接入加一」，
  按 6 变 7 实现。
- 其余无。
