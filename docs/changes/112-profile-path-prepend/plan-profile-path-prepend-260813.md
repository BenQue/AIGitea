---
issue: 112
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/112
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - schema-change
depends_on: []
status: ready-for-review
branch: change/112-profile-path-prepend
pr_url:
created: 2026-08-13
updated: 2026-08-13
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 合同层：`contract.py` 可选 `path_prepend` 解析 + fail-closed 校验 + `VMProfileContract` 字段；manifest 为 sfm 声明；三态合同测试（声明/未声明/非法值矩阵） | - | pending |
| T02 | 生成与校验层：`_profile_bytes` PATH 行生成 + `_read_back` expected 映射；迁移器测试（sfm 端到端 apply/read-back、未声明项目 byte-identity、漂移 `READ_BACK_MISMATCH` 双向） | T01 | pending |
| T03 | 投影与模板：`cli.py profile-spec` 输出 `path_prepend` 键 + `templates/agent/project.env.example` 注释 + 配套测试 | T01 | pending |

每个 ticket 一个原子 commit，独立可验证（`PYTHONPATH=codex/runtime python3 -m
unittest tests.test_host_access` 逐票全绿）。

## Expected touch points

- T01：`codex/runtime/aisoft_host_access/contract.py`、
  `codex/config/host-access-broker.json`、`codex/runtime/tests/test_host_access.py`
- T02：`codex/runtime/aisoft_host_access/profiles.py`、
  `codex/runtime/tests/test_host_access.py`
- T03：`codex/runtime/aisoft_host_access/cli.py`、
  `templates/agent/project.env.example`、`codex/runtime/tests/test_host_access.py`

范围提示即 spec §治理授权清单，不授权扩大。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_host_access -k path_prepend`：sfm 解析为 `("/opt/node22/bin", "/home/coder/.local/bin")`；`_profile_bytes(sfm)` 含 `PATH=/opt/node22/bin:/home/coder/.local/bin:$PATH` 行；sfm 端到端 apply 后目标 profile 含该行 |
| AC-2 | 同上测试模块：声明项目 PATH 行篡改/删除 → `READ_BACK_MISMATCH`；未声明项目注入 PATH 行 → `READ_BACK_MISMATCH` |
| AC-3（仓内部分） | manifest diff 审阅（sfm `path_prepend` 声明）+ AC-1 测试；VM 落地见 §部署与回滚跟进项 |
| AC-4 | byte-identity 测试：`_profile_bytes(newemaint)` 与硬编码的变更前 9 行字面量逐字节相等 |
| AC-5 | 三态矩阵测试（声明/未声明/非法值 9 种）+ `bash codex/tests/smoke.sh` 全绿 |

## 部署与回滚

本 PR 自身无部署动作（纯仓库合同与 runtime 变更）；合并即生效于源码，安装态更新
与 sfm 落地为**合并后 VM 侧跟进项**（按序执行，属 gitea-platform-ops 职责边界，
需独立授权，非本会话执行）：

1. Mac 侧重装 broker 安装件：`codex/install-host-access-broker.sh`
   （刷新 `/usr/local/lib/aisoft-host-access` 与
   `/usr/local/share/aisoft/host-access-broker.json`）。
2. VM 侧重装：`codex/install-vm.sh`（刷新 VM 安装态 manifest 与 runtime）。
3. sfm 重迁移：broker `vm.profile.plan` → `vm.profile.apply` → `vm.profile.read-back`
   全 PASS；验证 `aisoft-agent@sfm` 运行环境 `node --version` = v22。
4. 验证通过后移除临时 drop-in
   `~/.config/systemd/user/aisoft-agent@sfm.service.d/10-path.conf` 并
   `systemctl --user daemon-reload`，复跑 read-back 与一次 agent poll 确认无回归；
   SFMDigitalBoard 侧对应 Issue 同步关闭。
5. 回滚路径：任一步失败——代码层单 PR revert；profile 层 `vm.profile.rollback`
   恢复 latest 备份；drop-in 在第 4 步前保持在位，即保留现有临时覆盖兜底。
