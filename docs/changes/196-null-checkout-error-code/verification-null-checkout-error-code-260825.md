---
issue: 196
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/196
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - external-contract
  - shared-core
depends_on: []
status: passed
branch: change/196-null-checkout-error-code
created: 2026-08-25
updated: 2026-08-25
---

# Verification：`host.onboarding.check` 的 null-checkout 分支

## 基线与范围

- Commit SHA：`change/196-null-checkout-error-code`
- 基线：分支最初建自 `origin/main` = `a43f11c`（#194 合并 PR 199 之后）；实施期间
  `origin/main` 前进到 `abcfd18`（#192 合并 PR 198 之后），分支已 rebase 到 `abcfd18`
  并在该基线上复跑全量测试与 smoke 全绿。下表证据取自 `a43f11c` 基线；rebase 引入的
  是他人变更，未触及本 diff 的文件（`git diff a43f11c abcfd18 -- codex/runtime/aisoft_host_access/` 为空）。
- 环境：Mac（darwin 25.5.0），Python 3.14.4，2026-08-25。
- 本记录负责证明的 acceptance criteria：AC-1 ~ AC-4（全部）。
- **manifest / runtime 来源标注**（沿用 #191 的两分支写法）：
  - 「已安装」= `/usr/local/libexec/aisoft/host-access-broker`，用安装期固定的
    `/usr/local/share/aisoft/host-access-broker.json` 与**安装期 runtime**。
  - 「候选」= 本 worktree 的 runtime + 仓库内 manifest：
    ```
    PYTHONPATH=codex/runtime python3 -m aisoft_host_access.cli \
      --access-manifest codex/config/host-access-broker.json \
      --governance-manifest codex/config/gitea-governance.json \
      --label-manifest codex/config/gitea-labels.json broker --project <id> --operation <op>
    ```
    wrapper 自身就是在这两条分支间选择，runtime 入口与凭据解析完全相同。
  - 本变更改的是 **runtime**（不是 manifest），所以「改动前」与「改动后」两轮都用
    候选路径跑（同一 manifest、只有 broker.py 不同），对比才是单变量。已安装一轮
    另列，用途是记录本机现状，见下方说明。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 改动前 · 已安装 broker · 10 项目 `host.onboarding.check` | 记录 | 6 PASS + `rsdesign-new` `ONBOARDING_MISMATCH` + 4 `CREDENTIAL_UNAVAILABLE`（见下「已安装一轮为何不同」） |
| 改动前 · 候选 runtime（`a43f11c`，未改 broker.py）· 10 项目 | 记录 | 6 `PASS` + 4 `CREDENTIAL_UNAVAILABLE`，见下表「改动前」列 |
| 新测试先红 | FAIL（预期） | `test_null_mac_checkout_onboarding_check_is_target_unavailable`：`AssertionError: 'TRANSPORT_ERROR' != 'TARGET_UNAVAILABLE'`；`test_null_mac_checkout_is_decided_before_credentials`：栈停在 `broker.py:1567 access = self._access_audit(...)` → `AssertionError: credential resolution must not run` |
| 改动后 · 两个新测试 | PASS | 见下 AC-2 |
| `PYTHONPATH=codex/runtime python3 -m unittest tests.test_host_access` | PASS | `Ran 107 tests ... OK` |
| `cd codex/runtime && PYTHONPATH=. python3 -m unittest discover -s tests -t tests` | PASS | `Ran 536 tests in 28.028s ... OK` |
| `bash codex/tests/smoke.sh` | PASS | `Ran 536 tests ... OK` / `Codex platform static smoke checks passed.`，exit 0 |
| 改动后 · 候选 runtime · 10 项目复跑 | 记录 | 见下表「改动后」列 |
| 单条原始输出（`wmpda`，改动后） | 记录 | `{"code": "TARGET_UNAVAILABLE", "message": "project has no approved Mac checkout", "status": "BLOCKED_EXTERNAL"}`，CLI 退出码 `20` |

### 10 个项目 `host.onboarding.check` 改动前后对照（候选 runtime，同一 manifest）

| 项目 | `mac_checkout` | 改动前 | 改动后 | 变化 |
|---|---|---|---|---|
| aisoft-platform | `/Users/benque/MyDocs/AISoftPlatform` | `PASS` | `PASS` | 无 |
| hsdb | `/Users/benque/Projects/HSDB` | `PASS` | `PASS` | 无 |
| localwms | `/Users/benque/Projects/LocalWMS` | `PASS` | `PASS` | 无 |
| **myapp** | `null` | `CREDENTIAL_UNAVAILABLE` | **`TARGET_UNAVAILABLE`** | **变** |
| newemaint | `/Users/benque/Projects/NewEmaint` | `PASS` | `PASS` | 无 |
| rsdesign-new | `/Users/benque/Projects/rsdesign-new` | `PASS` | `PASS` | 无 |
| **sap-table-migrate** | `null` | `CREDENTIAL_UNAVAILABLE` | **`TARGET_UNAVAILABLE`** | **变** |
| sfm-digital-board | `/Users/benque/Projects/SFMDigitalBoard` | `PASS` | `PASS` | 无 |
| **smoke-test** | `null` | `CREDENTIAL_UNAVAILABLE` | **`TARGET_UNAVAILABLE`** | **变** |
| **wmpda** | `null` | `CREDENTIAL_UNAVAILABLE` | **`TARGET_UNAVAILABLE`** | **变** |

改动前 6 `PASS` + 4 `CREDENTIAL_UNAVAILABLE`；改动后 6 `PASS` + 4 `TARGET_UNAVAILABLE`。
变化的 4 个恰好是 `mac_checkout: null` 的全部项目，没有第五个项目受影响。
四例的 `status` 都仍是 `BLOCKED_EXTERNAL`、退出码都仍是 `20`。

### 为什么这 4 个项目的新结果更贴近事实（AC-4 要求逐个说明）

四个项目的成因完全同构，理由因此也相同，逐个复述如下：

- **myapp**：manifest 声明 `mac_checkout: null`，即本项目没有 Mac 侧交付路径。
  改动前的 `CREDENTIAL_UNAVAILABLE`（「approved credential binding is unavailable」）
  描述的是次生事实——因为没有 Mac 交付路径，所以 `~/Library/Application Support/
  AISoftPlatform/credentials/projects/myapp` 本就不该存在；该错误码会把运维引向
  「去补一份凭据」这个错误动作。`TARGET_UNAVAILABLE: project has no approved Mac
  checkout` 描述的是首要事实，且是终态而非待修缺陷。
- **sap-table-migrate**：同上。
- **smoke-test**：同上。
- **wmpda**：同上。

共同论据还有两条：
1. 同一条件在 typed git 路径 `_git`（broker.py:1311）本来就抛 `TARGET_UNAVAILABLE`。
   改动后两条路径逐字一致，调用方不再需要按操作名记两套错误码。
2. 「凭据缺失是先命中的真实约束」这一反方理由在此不成立：凭据之所以缺失，正是因为
   `mac_checkout` 为 `null`，前者是后者的推论。把推论排在前提之前才是顺序错误。

### 已安装一轮为何与候选一轮不同（取证陷阱备注）

改动前用**已安装** broker 跑同样 10 个项目时，`rsdesign-new` 返回
`ONBOARDING_MISMATCH: canonical checkout does not match the manifest`，而候选一轮是
`PASS`。差异与本变更无关：`rsdesign-new` 的 `mac_checkout` 修正随 #191 合并进
`origin/main`，但本机 `/usr/local/share/aisoft/host-access-broker.json` 仍是安装期
旧值，需要独立授权的 `sudo bash codex/install-host-access-broker.sh` 才会更新。
上面的前后对照表因此一律取候选一轮，保证单变量只有 broker.py。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 四个 `mac_checkout: null` 项目现在返回 `TARGET_UNAVAILABLE: project has no approved Mac checkout`，与 `_git`（broker.py:1311）逐字一致；字面含义即「本项目没有获批的 Mac checkout」，与 `mac_checkout: null` 这一完整声明相符，不再宣称「配置与实况不符」 |
| AC-2 | PASS | 新增 `test_null_mac_checkout_onboarding_check_is_target_unavailable`：用真实 manifest 的 `myapp`（`mac_checkout` 为 `null`）配 `StaticCredentials()`（凭据必然解析成功）构造现网不存在的「有凭据 + null」组合，并让 transport 一旦被调用即失败；断言 `code == "TARGET_UNAVAILABLE"` 且 message 逐字相符。配套 `test_null_mac_checkout_is_decided_before_credentials` 用会抛 `AssertionError` 的 credential resolver，钉住该判定在任何凭据解析之前发生。两者先红后绿，红的输出见上表 |
| AC-3 | PASS | 未删除、未弱化、未跳过 `_onboarding_check` 的任何断言；diff 只是把已存在的 `mac_checkout is None` 判定上移并换错误码。`mac_checkout` 非 `null` 时执行路径逐行不变——对照表中 6 个非 null 项目结果全部不变即为实测佐证。既有 `test_onboarding_check_combines_access_remote_and_repo_binding`（覆盖 PASS 路径与凭据绑定漂移的 `ONBOARDING_MISMATCH`）未改动且仍绿；全量 536 测试 OK |
| AC-4 | PASS | 10 个项目改动前后各跑一轮，对照表见上；4 个变化项目逐个给出「为什么新结果更贴近事实」 |

## 遗留风险与未完成项

- 本机已安装的 `/usr/local/libexec/aisoft/host-access-broker` 仍是安装期 runtime，
  合并后需人工执行 `sudo bash codex/install-host-access-broker.sh`（两台）才会让
  新错误码生效。该重装需要独立授权，不属于本变更范围，本次也未执行。
- `docs/changes/191-rsdesign-mac-checkout/verification-rsdesign-mac-checkout-260824.md`
  记录的 `ONBOARDING_MISMATCH: canonical checkout is not configured` 是 2026-08-24
  当时的实况，作为历史记录保留不改；本文件是它的后继。
