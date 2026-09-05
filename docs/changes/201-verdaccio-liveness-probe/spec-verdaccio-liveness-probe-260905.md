---
issue: 201
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/201
change_type: reliability
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - ci-change
  - platform-governance
depends_on: []
status: approved
branch: change/201-verdaccio-liveness-probe
created: 2026-09-05
updated: 2026-09-05
---

# Spec · registry 存活断言

## 目标与原因

让「Verdaccio 停止服务」这一故障在**任何一次 CI 运行**上立刻显形，而不是等到某个倒霉的 PR 恰好
引入缓存外新包才炸。

断言必须同时穿透两层假绿：不读 npm 缓存，也不问 pm2。因此它是一次真实的 HTTP 取包，而不是探端口、
不是 `pm2 list`、不是 `systemctl is-active`。

选择放在项目 CI 的前置步骤而不是 VM 侧周期探针，理由有三条：

1. **命中痛点**：故障的代价全部落在 CI 上。把断言放进 CI，故障期间的每一次运行都会红，而不是像
   run 644 与 657 那样绿着掩盖 28 小时。
2. **不引入新的安装面**：仓库现有七个 installer（#250 合并后补齐 `sync/install.sh`）全部纳入 `codex/lib/install-source-guard.sh`
   的陈旧源闸门，`codex/tests/test-installer-source-guard.sh` 逐个枚举。新增第八个 installer 会
   把 `06` 踩坑 20 里「已全部覆盖」的结论一并推翻，成本远超本 Issue 的价值。
3. **不与 #228 抢常数**：不新增 broker 操作，`operation_count` 保持 33，把该动作留给 #228 独占。

## Acceptance criteria

- [ ] AC-1 平台提供 `templates/project/ci/registry-preflight.sh`：读取 `NPM_CONFIG_REGISTRY`
      指向的 registry，取一个固定包的 packument 并校验 JSON 形状，再取该版本 tarball 的响应头；
      全程 `curl`，不经 npm 缓存，不读 pm2，不回退到直连 npmjs。
- [ ] AC-2 脚本按失败阶段给出**指名道姓**的结论，至少区分三类：连接不上（对应本次
      `ECONNREFUSED`，明确写出「不要往 uplink 方向排查」）、HTTP 状态异常、响应体不是 packument。
- [ ] AC-3 失败时在标准错误打印固定可搜索标记 `AISOFT_REGISTRY_PREFLIGHT_FAIL` 并以非零退出；
      成功打印 `AISOFT_REGISTRY_PREFLIGHT_OK`。
- [ ] AC-4 `templates/project/ci/ci.yml` 在依赖安装之前增加该步骤，且 `workflow 名`、`job key`、
      触发事件三者一字不改，必需检查 context 不变。
- [ ] AC-5 `codex/tools/aisoft-project-check.sh` 增加只读回读项 `ci-registry-preflight`，
      对目标仓 checkout 判定 PASS / SKIP / GAP，并在 `codex/tests/test-project-check.sh` 有用例。
- [ ] AC-6 新增 `codex/tests/test-registry-preflight.sh`，用本机可控的替身 registry 覆盖
      成功、连接被拒、HTTP 4xx/5xx、响应体非 packument、tarball 不可取 五种路径，并注册进
      `codex/tests/smoke.sh` 的 `bash -n`、ShellCheck 与执行三处。
- [ ] AC-7 负向验证：替身 registry 起着时脚本绿，`kill` 之后同一条命令红并打印
      `AISOFT_REGISTRY_PREFLIGHT_FAIL` 与连接不上的结论，重新起来后复绿。**不得**通过清空 npm
      缓存制造失败。
- [ ] AC-8 对**真实**的 `http://gitea-ci.orb.local:4873/` 跑一次脚本并记录真实输出。
- [ ] AC-9 `01` §5 记入：Verdaccio 是 CI 的硬依赖；应用仓**不得**改自己的 `ci.yml` 绕过
      `NPM_CONFIG_REGISTRY` 去直连 npmjs，那会同时抹掉离线安装能力和本故障的可见性。
- [ ] AC-10 `06` 踩坑集新增一条：`pm2 list` 报 `online` 而 pid 为 `N/A`、内存 `0b`、error log
      为空时进程实际已死；判活必须同时看 pid、`ss` 的 LISTEN 与一次真实取包。
- [ ] AC-11 停机原因与开机自启这两项需要 VM 侧证据，在 `verification` 中如实记为 NOT RUN，
      并给出人可直接执行的只读取证命令与预期输出。

## 接口、数据与兼容性影响

- 新增文件全部是平台侧参考实现与测试，不改变任何现有脚本的调用契约。
- `aisoft-project-check.sh` 新增一个 result 行。该工具的输出被 `test-project-check.sh` 逐字计数，
  必须同步。
- 无数据库、无 schema、无迁移。
- 无 broker 操作变更，`operation_count` 保持 33。

## 风险与回滚约束

- 回滚方式：本次全部改动是新增文件加三处文档与工具追加，`git revert` 单个 merge commit 即完全回滚，
  不留残留状态；平台仓与应用仓都没有需要反向迁移的东西。
- 采纳风险落在应用仓：某项目若把该步骤放进新 job 而不是既有 job，会改变必需检查 context 并让所有
  PR 永久 pending。参考文件与 `01` §5 都要写明这一条。
- 探测包一旦从 registry 消失，探针会红。因此包名可由 `REGISTRY_PREFLIGHT_PACKAGE` 覆盖，默认取
  `fflate`——它正是 run 652 首次暴露本故障时卡住的那个包，且 2026-09-05 实测该 registry 上有 58 个版本。

## 非目标

- 不新增 broker typed 操作。若需要让会话自己回读探针结果，由 #228 统一新增只读操作。
- 不新增第八个 installer，不新增 VM 侧常驻探针或 systemd timer。故障发生在完全无 CI 活动的时段时，
  发现时刻推迟到下一次 CI，这是本方案已知且接受的取舍；是否补 VM 侧周期探针另立 Issue 评估。
- 不改任何应用仓的文件，包括 LocalWMS PR #91 / #92。各项目采纳走各自的对齐 Issue。
- 不清空或重建 runner 的 npm 缓存。
- 不在本 Issue 内重启、重配或迁移 Verdaccio 进程本身。

## 未决问题

无。以下两项不是未决问题而是明确的人工交接项，实现方向不依赖它们的答案：

### 交接项 A · 停机原因的一手取证（VM 上以 benque 执行，全部只读）

```bash
pm2 describe verdaccio
pm2 jlist | python3 -m json.tool | head -80
ss -lntp | grep 4873
systemctl status pm2-benque.service --no-pager -l
systemctl is-enabled pm2-benque.service
pm2 logs verdaccio --lines 200 --nostream
ls -l ~/.pm2/logs/ && tail -n 200 ~/.pm2/logs/verdaccio-error.log
journalctl -u pm2-benque.service --since 2026-08-20 --no-pager | tail -200
journalctl --list-boots | head -10
uptime -p && who -b
python3 -m json.tool ~/.pm2/dump.pm2 | grep -iE 'name|cwd|script'
```

判读要点：`#84` 会话转述的根因是 `exec cwd` 指向 2026-07-19 已迁走的 Mac 路径导致
`pm2 resurrect` spawn 失败。要证实它，看 `dump.pm2` 与 `pm2 describe` 里的 `exec cwd` 是否仍是
旧路径，并把 `journalctl --list-boots` 的启动时刻与故障窗口对上。取不到就如实写「原因不明」，不猜。

### 交接项 B · 开机自启（需要一次真实重启）

```bash
# 重启前
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:4873/-/ping
sudo reboot
# 重启后
systemctl is-active pm2-benque.service
pm2 describe verdaccio | grep -iE 'status|pid|exec cwd'
ss -lntp | grep 4873
curl -fsS http://127.0.0.1:4873/fflate | head -c 200
```

预期输出：`active`；`status: online` **且 pid 是真实数字而不是 `N/A`**；`ss` 有 `LISTEN`；
最后一条返回真的 packument JSON。**只看 `pm2 describe` 的 `online` 不算通过**——那正是本次的假绿。
