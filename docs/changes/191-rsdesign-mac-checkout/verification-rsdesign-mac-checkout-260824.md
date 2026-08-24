---
issue: 191
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/191
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: verified
branch: change/191-rsdesign-mac-checkout
created: 2026-08-24
updated: 2026-08-24
---

# Verification：rsdesign-new manifest checkout 对齐

## 基线与范围

- Commit SHA：`change/191-rsdesign-mac-checkout`
- 基线：分支最初建自 `origin/main` = `d73fee4`（#188 合并后）；实施期间 `origin/main`
  前进到 `eda2aeb`（#193 合并后），分支已 rebase 到 `eda2aeb` 并在该基线上复跑 smoke 全绿。
  下表全部证据取自 `d73fee4` 基线；rebase 引入的是他人变更，未触及本 diff 的文件。
- 环境：Mac（darwin 25.5.0），Gitea `gitea-ci.orb.local:3000`，2026-08-24
- 本记录负责证明的 acceptance criteria：AC-1 ~ AC-6（全部）
- **manifest 来源标注**：`host-access-broker.json` 是安装期固定文件。改动前一轮用**已安装**的
  `/usr/local/share/aisoft/host-access-broker.json`（经 `/usr/local/libexec/aisoft/host-access-broker`）；
  改动后一轮用**候选** manifest 直接调用同一 runtime 的 CLI：
  ```
  PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli \
    --access-manifest codex/config/host-access-broker.json \
    --governance-manifest codex/config/gitea-governance.json \
    --label-manifest codex/config/gitea-labels.json broker --project <id> --operation <op>
  ```
  这正是 wrapper 自身选择 manifest 的两条分支，runtime 与凭据解析完全相同。合并后仍需人工
  重装两端才让候选值成为已安装值。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前 10 项目 `host.onboarding.check`（已安装 manifest） | 6 BLOCKED / 4 PASS+ | 下方「AC-3 横向核对」左列 |
| `git -C /Users/benque/Projects/RSDesignTool/rsdesign-new rev-parse --show-toplevel` | PASS（命令成功，值不符） | `/Users/benque/Projects/RSDesignTool` ≠ manifest 的 `mac_checkout` |
| `git -C /Users/benque/Projects/RSDesignTool remote -v` | PASS | 只有 `origin https://github.com/BenQue/RSDesignTool.git`，无名为 `gitea` 的 remote |
| `git -C /Users/benque/Projects/rsdesign-new rev-parse --show-toplevel` | PASS | `/Users/benque/Projects/rsdesign-new`（等于自身，是独立 checkout） |
| `git -C /Users/benque/Projects/rsdesign-new remote -v` | PASS | `origin` → `http://gitea-ci.orb.local:3000/admin/rsdesign-new.git`（fetch+push）；`github` → `https://github.com/BenQue/NewRSDesign.git` |
| `broker --project rsdesign-new --operation gitea.repo.read` | PASS | `admin/rsdesign-new`，`empty: false`，`default_branch: main`，`private: true` |
| 候选 manifest `host.onboarding.check`（bind 前） | BLOCKED_EXTERNAL | `{"code": "ONBOARDING_MISMATCH", "message": "repo-local credential binding does not match"}`——路径与 remote 两处断言已过，只剩凭据绑定 |
| 候选 manifest `mac.git.bind`（第 1 次） | PASS | `{"identity": "rsdesign-agent", "operation": "mac.git.bind", "project": "rsdesign-new", "result": "updated", "status": "PASS"}` |
| 候选 manifest `mac.git.bind`（第 2 次，幂等） | PASS | `{"..., "result": "no-op", "status": "PASS"}` |
| 候选 manifest `host.onboarding.check`（bind 后） | PASS | `{"status": "PASS", "checkout": {"binding": "PASS", "remote_name": "origin", "remote_url": "http://gitea-ci.orb.local:3000/admin/rsdesign-new.git"}}` |
| 候选 manifest `git.fetch.main`（cwd=`/Users/benque/Projects/rsdesign-new`） | PASS | `{"checkout": "/Users/benque/Projects/rsdesign-new", "identity": "rsdesign-agent", "operation": "git.fetch.main", "project": "rsdesign-new", "remote_name": "origin", "status": "PASS"}` |
| 改动后 10 项目 `host.onboarding.check`（候选 manifest） | 6 PASS / 4 BLOCKED | 下方「AC-3 横向核对」右列 |
| `git diff origin/main -- codex/runtime/aisoft_host_access/broker.py` | PASS（零 diff） | 无输出 |
| `bash codex/tests/test-host-access-broker.sh` | PASS | `host access broker shell and installer tests passed` |
| `python3 -m unittest codex.runtime.tests.test_host_access` | PASS | `Ran 105 tests in 5.370s` / `OK` |
| `bash codex/tests/smoke.sh` | PASS | `Ran 523 tests in 28.432s` / `OK` / `Codex platform static smoke checks passed.` |
| `bash -n codex/tests/test-host-access-broker.sh` | PASS | 无输出 |
| 变更前后两个 checkout 的 `remote -v` 对比 | PASS（无变化） | 见 AC-6 |
| `aisoft_resolve_project_target`（#184 下游症状复验） | PASS | `/Users/benque/Projects/rsdesign-new` → `rsdesign-new / rsdesign-new (checkout)`；`/Users/benque/Projects/RSDesignTool` 仍 fail-closed 报「none of its Git remotes matches a project」——它本就不是平台项目 |

## AC-3 横向核对：全部 10 个项目

| project | `mac_checkout` | 改动前（已安装 manifest） | 改动后（候选 manifest） | 预期形态 | 结论 |
|---|---|---|---|---|---|
| aisoft-platform | `/Users/benque/MyDocs/AISoftPlatform` | `PASS`（remote `origin`） | `PASS`（remote `origin`） | PASS | 符合 |
| hsdb | `/Users/benque/Projects/HSDB` | `PASS`（remote `origin`） | `PASS`（remote `origin`） | PASS | 符合 |
| localwms | `/Users/benque/Projects/LocalWMS` | `PASS`（remote `origin`） | `PASS`（remote `origin`） | PASS | 符合 |
| myapp | `null` | `CREDENTIAL_UNAVAILABLE` | `CREDENTIAL_UNAVAILABLE` | 见下「四个 null-checkout 项目」 | 不变，已记录 |
| newemaint | `/Users/benque/Projects/NewEmaint` | `PASS`（remote `gitea`） | `PASS`（remote `gitea`） | PASS | 符合 |
| **rsdesign-new** | `/Users/benque/Projects/rsdesign-new` | **`ONBOARDING_MISMATCH`**（canonical checkout does not match the manifest） | **`PASS`**（remote `origin`） | PASS | **本次修复** |
| sap-table-migrate | `null` | `CREDENTIAL_UNAVAILABLE` | `CREDENTIAL_UNAVAILABLE` | 见下 | 不变，已记录 |
| sfm-digital-board | `/Users/benque/Projects/SFMDigitalBoard` | `PASS`（remote `gitea`） | `PASS`（remote `gitea`） | PASS | 符合 |
| smoke-test | `null` | `CREDENTIAL_UNAVAILABLE` | `CREDENTIAL_UNAVAILABLE` | 见下 | 不变，已记录 |
| wmpda | `null` | `CREDENTIAL_UNAVAILABLE` | `CREDENTIAL_UNAVAILABLE` | 见下 | 不变，已记录 |

改动前 6 个非 PASS = 1 个 `ONBOARDING_MISMATCH` + 4 个 `CREDENTIAL_UNAVAILABLE`；
改动后 6 个 `PASS` + 4 个 `CREDENTIAL_UNAVAILABLE`。除 `rsdesign-new` 外无一项目的结果改变。

### 四个 null-checkout 项目：为什么是 `CREDENTIAL_UNAVAILABLE`

`myapp`、`sap-table-migrate`、`smoke-test`、`wmpda` 的 `mac_checkout` 都是 `null`，
Mac 上也没有各自的凭据目录（`~/Library/Application Support/AISoftPlatform/credentials/projects/`
下只有 `aisoft-platform`、`hsdb`、`localwms`、`newemaint`、`rsdesign-new`、`sfm-digital-board` 六个）。
`_onboarding_check` 第一步就是 `_access_audit`，凭据缺失即在此 fail-closed，根本走不到
`mac_checkout is None` 的判定。对这四个项目而言，「Mac 上完全不存在」是诚实结论。

Issue #191 正文假设选 C 时会得到 `TARGET_UNAVAILABLE: project has no approved Mac checkout`。
实测该错误码只在 `_git` 路径抛出（broker.py:1311）；`_onboarding_check` 在
`mac_checkout is None` 时抛的是 `ONBOARDING_MISMATCH: canonical checkout is not configured`
（broker.py:1569）。人在 2026-08-24 决定：本次只记录该错误码语义差异，另开 Issue 处理，
不在本 change 内改动 broker runtime（也因此不违反 AC-4）。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 候选 manifest 下 `host.onboarding.check` 返回 `status: PASS`；改动前为 `ONBOARDING_MISMATCH` |
| AC-2 | PASS | `git.fetch.main` `status: PASS`；`mac.git.bind` 第 1 次 `updated`、第 2 次 `no-op`；bind 后 `checkout.binding: PASS` |
| AC-3 | PASS | 上表 10/10 项目改动前后两轮实测，非 PASS 项目已写明原因与预期形态 |
| AC-4 | PASS | `git diff origin/main -- codex/runtime/aisoft_host_access/broker.py` 零 diff；`_onboarding_check`/`_validated_remote` 未被触碰 |
| AC-5 | PASS | 三个套件全绿：broker shell/installer 测试、105 个 host-access 单测、smoke 523 个 |
| AC-6 | PASS | 两个 checkout 的 `remote -v` 与变更前逐字一致（下方） |

### AC-6 remote 快照（变更后，与变更前一致）

```
/Users/benque/Projects/rsdesign-new
  github  https://github.com/BenQue/NewRSDesign.git (fetch/push)
  origin  http://gitea-ci.orb.local:3000/admin/rsdesign-new.git (fetch/push)

/Users/benque/Projects/RSDesignTool
  origin  https://github.com/BenQue/RSDesignTool.git (fetch/push)
```

`mac.git.bind` 只写 repo-local credential 配置，不碰 remote：

```
credential.usehttppath true
credential.http://gitea-ci.orb.local:3000/admin/rsdesign-new.git.username rsdesign-agent
credential.http://gitea-ci.orb.local:3000/admin/rsdesign-new.git.helper
credential.http://gitea-ci.orb.local:3000/admin/rsdesign-new.git.helper /usr/local/libexec/aisoft/git-credential-aisoft-host
```

## 遗留风险与未完成项

- **合并后需人工重装两端**（Mac `sudo bash codex/install-host-access-broker.sh`，VM 同）
  才让 `/usr/local/share/aisoft/host-access-broker.json` 生效。重装前经 wrapper 调用的
  `rsdesign-new` 仍会返回 `ONBOARDING_MISMATCH`——那是旧的已安装 manifest，不是本 diff。
  重装后应复跑本记录的 AC-1/AC-2 两条命令确认。此项 `NOT RUN`（需要 sudo，属人的动作）。
- **VM 侧未验证**：本记录只覆盖 Mac。VM 上 `mac_checkout` 不参与判定（VM 走 `vm_profile`，
  本次未改），但重装后建议顺带跑一次 VM 侧自检。此项 `NOT RUN`。
- **null-checkout 错误码语义**：四个项目在 `_onboarding_check` 中先卡在 credential audit，
  `mac_checkout is None` 抛的又是 `ONBOARDING_MISMATCH` 而非 `TARGET_UNAVAILABLE`。
  已按人的决定另开 Issue，不在本 change 范围内。
- **#116 的历史文档未改写**：其「rsdesign-new Mac checkout 已本地补加 `gitea` remote」的记述
  与今日实况不符（`RSDesignTool` 现无 `gitea` remote），但历史记录按合同只读不改写。
