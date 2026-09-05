---
issue: 201
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/201
change_type: reliability
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增一条 CI 侧 registry 存活断言与一项 project-check 回读，属于 CI 基础设施与平台治理工具的能力新增，AGENTS 对 CI 变更一律强制 complex
risk_flags:
  - ci-change
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-verdaccio-liveness-probe-260905.md
  spec: spec-verdaccio-liveness-probe-260905.md
  plan: plan-verdaccio-liveness-probe-260905.md
  verification: verification-verdaccio-liveness-probe-260905.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/201-verdaccio-liveness-probe
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/257
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

gitea-ci 上的 Verdaccio 曾停止监听 `4873` 约 28 小时，期间所有需要下载缓存外新包的 CI 全部
`ECONNREFUSED`，而只用既有依赖的 CI 仍然 20 秒全绿。服务本身已于 2026-08-25 恢复，本会话
2026-09-05 复核仍然存活。Issue 剩下的价值不是再重启一次，而是补一条**不依赖缓存的存活断言**，
让同一故障下次不再静默潜伏。

这次事故里有两层互相独立的假绿，缺一层都仍会骗过下一个排查的人：

1. **暖缓存层**：`npm ci` 命中 runner 的 `_cacache` 时根本不发起网络请求，于是故障期间的 CI 照常绿。
2. **进程管理层**：`pm2 list` 把 Verdaccio 显示为 `online`，而 pid 是 `N/A`、内存 `0b`、error log 为空。

第 2 层的根因据 Issue #201 评论转述自 #84 会话：PM2 保存的 `exec cwd` 指向 2026-07-19 已迁走的
Mac 路径，VM 重启时 `pm2 resurrect` spawn 失败。这是**二手转述，本会话未取到 VM 侧一手日志**，
因此停机原因在本次交付中按未独立证实处理，取证命令列为人工交接项。

## 影响范围

- 平台侧：`templates/project/ci/`、`codex/tools/aisoft-project-check.sh` 及其测试、`codex/tests/smoke.sh`、
  平台文档 `01` §5 与 `06` 踩坑集。
- 应用侧：不在本 PR 内改任何应用仓。各应用仓采纳新 CI 步骤走各自的对齐 Issue，与 #223 的合并预览同路径。
- 不触碰 broker 操作表：理由见下方风险一节。

## 初步方案与建议

在平台提供的项目 CI 参考里增加一步 registry 前置断言，放在 `Install dependencies` 之前、同一个
job 内，`workflow 名 + job key + 事件`三者不变，因此受保护 `main` 的必需检查 context 不变。

断言做的是真实取包，不是探端口：先取一个固定小包的 packument 并校验 JSON 形状，再取该版本
tarball 的响应头。它既不读 npm 缓存也不问 pm2，因此同时穿透上面两层假绿。失败时打印固定可搜索
标记并非零退出，绝不回退到直连 npmjs。

配套加一项 `aisoft-project-check.sh` 的只读回读，让「某个项目到底采纳了没有」是可核对的事实
而不是印象。

## 风险

- **与 #228 抢同一个手工常数**：`codex/tests/test-host-access-broker.sh` 把 `operation_count == 33`
  逐字钉死两处。#228 很可能新增一个 broker 只读操作。若本 Issue 也加一个，两个 PR 会各自把 33
  改成 34、文本相同而含义不同、干净合并、主干红——正是踩坑 22 的形态。本方案因此**不新增 broker 操作**，
  把该动作留给 #228 独占。
- **检测时机**：CI 侧断言只在有 CI 运行时生效。故障发生在完全没有 CI 活动的时段时，发现时刻会推迟到
  下一次 CI。这一条作为已知取舍写进 spec 的非目标，并建议另立 Issue 评估 VM 侧周期探针。
- **负向验证的可达性**：真正停掉 VM 上的 Verdaccio 超出会话可用手段。本次以本机可控的替身 registry
  完成同一失败签名的负向验证，VM 上的一次真实停机验证列为人工交接项。

## AI 判级

```yaml
change_type: reliability
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增一条 CI 侧 registry 存活断言与一项 project-check 回读，属于 CI 基础设施与平台治理工具的能力新增，AGENTS 对 CI 变更一律强制 complex
risk_flags:
  - ci-change
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

- AGENTS.md 工作原则：`CI/制品/部署/回滚` 一律按 complex 处理。
- `codex/runtime/aisoft_loop/classification.py` 的 `FORCED_COMPLEX_RISKS` 含 `ci-change` 与
  `platform-governance`，两者本次都命中。
- `contract_effect: add`：新增的是一条此前不存在的闸门与一项此前不存在的回读检查，不是恢复既有行为。
- 声明 `verification` 的依据是证据来源：交付结论依赖真实执行的探测命令与一次负向验证，这些证据
  合并后无法重放。

### 缺失的 acceptance criteria 或决策

- 停机原因需要 VM 侧只读日志才能一手证实，命令清单见 spec 的交接项一节。
- 开机自启需要一次真实重启才能证实，同上。
