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

# Spec

## 目标与原因

为 manifest 声明的 VM project profile 增加**可选工具链 PATH 声明位**，使需要非默认
工具链的项目（当前是 sfm 的 Node 22）在 `vm.profile.apply` 迁移后即获得正确 PATH，
不再依赖 VM 上未版本化的 systemd drop-in；未声明项目的 profile 生成保持逐字节不变。

## 合同定义

### 1. Manifest schema（`codex/config/host-access-broker.json` → `contract.py`）

`projects[].vm_profile` 在既有 5 键（`name`、`repo_dir`、`analysis_provider`、
`implement_provider`、`timer_unit`）之外，允许**可选**第 6 键 `path_prepend`：

- 类型：JSON 字符串数组；**省略 = 不声明**。声明空数组视为非法（declare-or-omit，
  fail closed，不留歧义形态）。
- 每个元素 fail-closed 校验，全部满足才接受，否则整个 manifest 拒载
  （`AccessContractError`）：
  - 匹配 `^/[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$`：绝对路径；受限字符集
    `[A-Za-z0-9._/-]`；天然排除空串、相对路径、`:`、空白、引号、`$`、反斜杠等
    一切 shell 元字符；排除空段、尾随 `/` 与裸 `/`。
  - 规范化：无 `.`/`..` 段（`PurePosixPath` parts 检查，与既有 `_absolute_path`
    同强度）。
  - 列表内无重复元素。
- 解析结果进入 `VMProfileContract.path_prepend: tuple[str, ...]`（未声明 = 空元组）。

### 2. Profile 生成（`profiles.py::_profile_bytes`）

- `path_prepend` 非空时，在既有 9 行之后追加**恰好一行**：
  `PATH=<e1>:<e2>:...:<eN>:$PATH`
- 未声明时生成逐字节等于现状的 9 行（AC-4 硬约束）。

**形态理由（单行 `PATH=<entries>:$PATH`，而非独立键）**：profile 的唯一消费方式是
bash `set -a; source`（`codex/agent/common.sh::load_agent_env`、
`codex/agent/project-poll.sh`），`$PATH` 在 source 时展开，天然获得 prepend 语义、
零消费者改动——消费者脚本适配是并行 #111 的地盘，独立键（如 `AISOFT_PATH_PREPEND`）
必须改消费者才生效，造成跨 Issue 耦合与「键存在但无效」的中间态。
`aisoft-agent@.service` 不用 `EnvironmentFile=`（无字面 `$PATH` 不展开的风险），
pre-#61 的 `sfm.env` 也正是 PATH 行形态。受限字符集保证该行不加引号即 shell 安全。

### 3. Read-back 校验（`profiles.py::_read_back`，被 `read_back`/`apply`/
`consume_check` 共用）

- 声明项目：expected 精确映射增加 `"PATH": "<e1>:...:<eN>:$PATH"`；缺行、值漂移、
  重复键一律 `READ_BACK_MISMATCH`（broker 侧即 GAP 证据，AC-2）。
- 未声明项目：expected 不变；目标 profile 出现多余 PATH 行同样
  `READ_BACK_MISMATCH`（fail closed）。

### 4. 投影（`cli.py profile-spec`）

输出对象固定携带 `"path_prepend"` 键（列表；未声明为 `[]`），供 VM 侧诊断与
provisioning 核对，不新增其它键。

### 5. Manifest 数据（sfm 声明）

`sfm-digital-board` 的 `vm_profile` 声明：

```json
"path_prepend": ["/opt/node22/bin", "/home/coder/.local/bin"]
```

忠实还原 pre-#61 `sfm.env` PATH 头部：`/opt/node22/bin` 提供 Node v22.22.0（AC-3），
`/home/coder/.local/bin` 保留 pre-#61 profile 一直保证的用户级 CLI 目录。其余系统
目录由 prepend 语义自动继承，不再抄写。其它三个 profile 项目不声明。

### 6. 模板注释（`templates/agent/project.env.example`）

追加注释块说明可选 PATH prepend 行形态与约束，供手工 provisioning 的项目对齐；
不改变模板既有键。

## Acceptance criteria

- [ ] AC-1 manifest 可为项目声明 `path_prepend`；`load_access_contract` 解析 sfm 得
      `("/opt/node22/bin", "/home/coder/.local/bin")`；`_profile_bytes(sfm)` 输出含
      `PATH=/opt/node22/bin:/home/coder/.local/bin:$PATH` 行（单元测试断言）。
- [ ] AC-2 `read-back` 精确校验该行：声明项目 PATH 行被篡改/删除报
      `READ_BACK_MISMATCH`；未声明项目被注入 PATH 行同样报 `READ_BACK_MISMATCH`
      （单元测试断言）。
- [ ] AC-3（仓内可交付部分）sfm 声明进 manifest 且生成 profile 携带 Node 22 路径；
      实际 VM 重迁移与 drop-in 移除列为合并后跟进项（plan §部署与回滚）。
- [ ] AC-4 未声明项目 `_profile_bytes` 输出与变更前字面量逐字节相等（测试以硬编码
      期望字节断言，不复用实现函数）。
- [ ] AC-5 测试覆盖声明/未声明/非法值三态（非法值含：空列表、非列表、空串、相对
      路径、`..` 段、含 `:`、含空白、尾随 `/`、重复项）；
      `bash codex/tests/smoke.sh` 全绿（unittest discover 自动纳入新测试，
      `aisoft_host_access.cli validate` 对真实 manifest 通过）。

## 接口、数据与兼容性影响

- manifest schema 向后兼容：`path_prepend` 可选，现有 manifest 不改即有效；
  未声明项目 profile 逐字节不变，`read-back`/`consume-check`/备份/回滚合同不变。
- 消费者（`load_agent_env` 等）无需改动即受益：source 后 PATH 生效；不认识该行的
  逐键消费者不受影响（profile 仍是 `KEY=VALUE` 行集合）。
- `profile-spec` 输出新增一个键，为纯增量投影；仓内无其它 profile-spec 消费者。
- `codex/tools/project-profile-migration.sh` 是无 schema 知识的薄封装，不改。

## 治理授权（精确文件清单）

本 spec 授权且仅授权以下文件操作：

- 修改 `codex/runtime/aisoft_host_access/contract.py`（vm_profile 可选
  `path_prepend` 解析与 fail-closed 校验、`VMProfileContract` 字段）
- 修改 `codex/runtime/aisoft_host_access/profiles.py`（`_profile_bytes` 生成、
  `_read_back` expected 映射）
- 修改 `codex/runtime/aisoft_host_access/cli.py`（仅 `profile-spec` 输出增加
  `path_prepend` 键）
- 修改 `codex/runtime/tests/test_host_access.py`（新增三态测试与 byte-identity 测试）
- 修改 `codex/config/host-access-broker.json`（仅 `sfm-digital-board` 的
  `vm_profile` 段新增 `path_prepend` 声明）
- 修改 `templates/agent/project.env.example`（仅追加注释说明）
- 新增 `docs/changes/112-profile-path-prepend/`（本变更语义文档）

清单之外的治理文件不在授权范围，实施 run 不得触碰——特别是平台 `AGENTS.md`、
CI workflow、`codex/agent/*` 与 `codex/tools/*` 的 5 个 token 消费者工具
（并行 #111 地盘）、`codex/tools/project-profile-migration.sh`、
`codex/systemd/*`、`codex/tests/smoke.sh`。

## 风险与回滚约束

- PATH 是执行边界：注入面被受限字符集 + 绝对路径 + 规范化 + declare-or-omit 完全
  收窄；任何非法声明拒载整个 manifest（fail closed），不产生部分生效。
- 未声明项目扰动：AC-4 以硬编码期望字节锁死；read-back 对多余 PATH 行 fail closed。
- 代码回滚：单 PR revert 完整回滚。VM 侧 profile 回滚：既有 `vm.profile.rollback`
  （latest/previous 备份）不受影响；sfm 重迁移前 drop-in 不动，重迁移验证通过后
  才移除 drop-in（顺序写入 plan），任一步失败可回退到当前临时覆盖状态。

## 非目标

- 不执行 sfm 的实际 VM 重迁移、不触碰 VM 上的 systemd drop-in（合并后 VM 侧跟进）。
- 不改消费者脚本（`codex/agent/*`、token 消费者工具）——#111 地盘。
- 不为 PATH 之外的环境变量（如 `NODE_OPTIONS`、私有 registry）提供声明位。
- 不改变 provider gate、备份/回滚机制、token 处理与文件模式合同。
- 不安装/更新任何 live skill、不部署、不改 live 标签。

## 未决问题

无。PATH 形态（单行 `PATH=<entries>:$PATH`）已在 §2 给出选型理由并收敛。
