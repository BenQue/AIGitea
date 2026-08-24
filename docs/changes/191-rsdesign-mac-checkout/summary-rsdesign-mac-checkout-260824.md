---
issue: 191
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/191
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 治理 manifest（host-access-broker.json）声明变更，触发平台治理强制 complex；内容是把 rsdesign-new 的 mac_checkout 与 git_remote_name 改回与主机实况一致，不新增能力也不改 broker runtime
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-rsdesign-mac-checkout-260824.md
  spec: spec-rsdesign-mac-checkout-260824.md
  plan: plan-rsdesign-mac-checkout-260824.md
  verification: verification-rsdesign-mac-checkout-260824.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/191-rsdesign-mac-checkout
pr_url:
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

`codex/config/host-access-broker.json` 给 `rsdesign-new` 声明的 `mac_checkout` 是
`/Users/benque/Projects/RSDesignTool/rsdesign-new`——那是 GitHub 仓库 `RSDesignTool`
里的一个**子目录**，不是 Gitea `admin/rsdesign-new` 的工作副本。两处独立不符导致该项目
Mac 侧全部 typed git 操作与 onboarding 自检不可用：

- `broker._onboarding_check` 断言 `realpath(mac_checkout) == git rev-parse --show-toplevel`，
  子目录必然不等 → `ONBOARDING_MISMATCH`（broker.py:1582）。
- `broker._validated_remote` 取名为 `gitea` 的 remote，该 checkout 只有指向 GitHub 的
  `origin` → `TARGET_MISMATCH`，于是 `git.fetch.main`/`git.fetch.change`/`git.push.change`/
  `mac.git.bind` 全部不可用（broker.py:1493-1512）。

取证发现主机上**确实存在** Gitea `rsdesign-new` 的独立 checkout，只是在另一个路径：

```
/Users/benque/Projects/rsdesign-new          # rev-parse --show-toplevel == 自身，on main
  origin  http://gitea-ci.orb.local:3000/admin/rsdesign-new.git   (fetch+push)
  github  https://github.com/BenQue/NewRSDesign.git
```

人在 2026-08-24 确认事实为 **B1**：manifest 指错了路径，改 manifest 指向真实 checkout。

`git_remote_name: "gitea"` 对这个 checkout 同样是错的——它的 Gitea remote 名叫 `origin`
（与本平台仓同一约定；`github` 才是 GitHub 上游）。该声明由 #116 加入，当时假设 rsdesign-new
是「与 NewEMaint 同布局」的 `origin`=GitHub 形态，而 #116 的 AC-3 复验被显式推到 PR 之外，
从未执行，所以这条错误声明一直没被发现。

## 影响范围

- `codex/config/host-access-broker.json`：`rsdesign-new` 条目改 `mac_checkout`、删
  `git_remote_name`（删除后回落到 contract.py:398 的默认 `"origin"`）。
- 两处把旧声明钉死的测试断言：`codex/tests/test-host-access-broker.sh` 与
  `codex/runtime/tests/test_host_access.py` 的 `gitea` remote 项目集合由三个减为两个
  （`newemaint`、`sfm-digital-board`）。

不改 broker runtime，不动其他项目条目，不创建/改名/删除任何 Git remote
（`gitea-platform-ops` 明令禁止），不动业务仓库内容。

## 初步方案与建议

改 manifest 两行 + 同步两处测试集合；用候选 manifest 直接跑 broker CLI 完成改动前后取证，
合并后由人重装两端（Mac sudo + VM orb sudo）使 `/usr/local/share/aisoft/` 的固定 manifest 生效。

## 风险

- 极低：纯声明修正，schema strict 校验已存在，错误声明 fail-closed 而非静默放行。
- 回滚 = revert 单 PR + 重装；`mac.git.bind` 写入的 repo-local credential 配置可用
  `git config --local --unset` 撤销，不触碰仓库内容与任何 remote。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 治理 manifest（host-access-broker.json）声明变更，触发平台治理强制 complex；内容是把 rsdesign-new 的 mac_checkout 与 git_remote_name 改回与主机实况一致，不新增能力也不改 broker runtime
risk_flags:
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

- 修改 `codex/config/*` 治理 manifest → 平台治理强制 complex（`03` §2），与 #116 同类先例一致。
- `contract_effect: restore`：目标是恢复 manifest 本就声明要提供的 Mac 侧 typed git 通路，
  不新增操作、不改 broker 行为、不放宽任何断言；强制规则而非 contract_effect 决定了 complex。
- `required_docs` 含 `verification`：AC-3 的十项目横向核对与改动前基线只在本机可观测、
  required CI 不跑，落在 `03` §3 判据表第二行。

### 缺失的 acceptance criteria 或决策

- 无。A/B/C 的事实问题已由人在 2026-08-24 定为 B1，见 spec「未决问题」。
