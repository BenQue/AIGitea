---
issue: 308
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/308
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - cross-module
  - ci-change
depends_on: []
status: approved
branch: change/308-installed-drift-check
created: 2026-10-02
updated: 2026-10-02
---

# Spec：八个 installer 的只读 installed drift 检查

## 目标与原因

平台维护者需要在不运行 installer 时发现「当前源码已合并、安装副本落后」。输出必须区分 source/local/installed/live；文件数与版本量相等也不代表实现相等。

## 用户故事

1. 维护者能用一个命令逐项查看 8 个 installer，避免依赖安装时日志。
2. 能看到源与目标的 operations、模块数、revision 等既有可读量。
3. 能定位缺失或内容陈旧的具体目标文件，覆盖 #304 的缺模块形态。
4. 能在 Mac 与 gitea-ci 本机各跑一次，无凭据、无网络、无提权。
5. 可以指定既有安装 prefix/home，并看到实际检查路径，防止把错误路径当已安装。
6. 未安装、不可读、异常文件类型或错误链接均报 GAP，不能悄悄跳过。
7. 可在隔离模拟安装面验证 PASS→GAP→PASS，不碰真实目录。
8. 检查过程没有任何安装、修复、写文件或 service/timer 动作。

## Acceptance criteria

- [ ] AC-1：存在一条命令，恰好覆盖全部 8 个 installer，每项 PASS/GAP；输出 expected/installed 可读量及 exact 目标和差异原因；退出码 0 仅用于全部通过，1 表示至少一个 GAP，2 表示参数/源定义不合法。
- [ ] AC-2（保留 Issue 原标准）：Mac 当前 main 对应真实安装面全 PASS。2026-10-02 已观测 GAP，该项待独立安装处置；不以 fixture PASS 替代，不因本实现改为 N/A，不为满足该项改真实安装面。
- [ ] AC-3：隔离 fixture 中删除/重命名已安装模块、替换为旧字节、篡改可读量均报该 installer 的 GAP；恢复后全 PASS。fixture 包括 8 个安装面；真实安装面不用于故意造错。
- [ ] AC-4：operations/count/revision 相等时缺模块、文件名替换、同长度字节差异仍报 GAP，特别覆盖 `aisoft_worktree_owner.py` 与 `aisoft_loop/worktree.py`。
- [ ] AC-5：smoke 的静态/fixture 部分覆盖 source 映射与 checker/installer 自洽性，CI 不访问真实安装面；新增 installer 或 installer 目标变化而映射遗漏时失败。
- [ ] AC-6：命令本身零写入：不创建 temp/report/cache/pyc、不调用 installer/sudo、不读取 Secret/profile/auth、不写 installed/service/config；用受控 fixture 写入哨兵及前后文件树验证。
- [ ] AC-7：Mac 与 gitea-ci 的只读真实运行分别留证。缺失、权限或 prefix 未证实均真实报 GAP/NOT RUN，不能继承另一台的 PASS。
- [ ] AC-8：源码身份输出 checkout、HEAD、已缓存 origin/main 与受管源差异；不 fetch、不用凭据。未取得 fresh main 外部证据或受管源偏离缓存 main 时不宣称「当前 main 全同步」。原子文件比对结果只证明与输出标明的 source 相等。

## 精确授权范围（启动确认后生效）

- 新增 `codex/tools/check-installed-drift.sh`（薄入口，以 python3 -B 运行 standalone checker）。
- 新增 `codex/tools/check-installed-drift.py`（仅标准库、只读映射与输出）。
- 新增 `codex/tests/test-installed-drift.sh` / 必要的隔离 fixture 支持文件。
- `codex/tests/smoke.sh` 只加新 checker/test 的静态门与 fixture 调用，不改现有门/contexts/workflow。
- README 的安装核对段、06 的踩坑 20/30 补充命令与真实验收边界。
- 仅本 Issue 的映射 summary/spec/plan/verification 与脱敏证据。

不修改 AGENTS.md、CLAUDE.md、skills、Controller、broker、installer、release runner、现有 manifest、credential、CI workflow；治理说明和 smoke 接入分别为独立仅治理步骤，应用后停止，后续 fresh run 重读才继续 runtime/验证。

## 接口、数据与兼容性影响

拟定入口：`bash codex/tools/check-installed-drift.sh [--repo ABSOLUTE_CHECKOUT] [--target-home ABSOLUTE_HOME] [--install-root ABSOLUTE_ROOT] [--agent-dir ABSOLUTE_DIR] [--architecture-prefix ABSOLUTE_PREFIX] [--json] [--source-only]`。

默认 repo 为脚本所属 checkout，target-home 为当前用户 home，install-root 为 `/`，agent-dir 为 target-home/agent，architecture-prefix 为 install-root/usr/local；输出所有 resolved roots。目标覆盖 installer 的所有受管非秘密文件；install-vm 的嵌套 skills 由 install-skills 行验证，并在父行说明关系。

`--source-only` 只校验八 installer 映射、源可读量、manifest/目录自洽性，不探测 installed；成功仅命名为 SOURCE PASS，不能输出 INSTALLED PASS。

| installer | 可读量（沿用 06） | 主要安装面 |
|---|---|---|
| install-host-access-broker | operations | install-root/usr/local 的 lib、libexec、share/aisoft |
| install-vm | runtime modules、operations | target-home/.local/lib/aisoft-loop、.local/share/aisoft、agent-dir、禁用 systemd 模板 |
| install-host-role | capabilities | install-root/usr/local 的 guard/catalog/schema、etc/aisoft 的非秘密 example |
| install-skills | skills、matt snapshot | target-home/.agents/skills、.agents/vendor/mattpocock 的 active snapshot |
| architecture/install | catalog revision、components | architecture-prefix 的 bin/lib/share |
| docker-release/install | matrix revision、schemas | install-root/opt runtime、usr/local/bin、etc 的 example |
| sync/install | units、runtime scripts | install-root/opt/aisoft-sync、etc/systemd/system、非秘密 example |
| skill-for-claude/install | skills、references | target-home/.claude/skills 中 skills.manifest 声明树 |

比对所有 expected target 的存在/类型/字节；只有读取 installer 明确安装的文件，不扫描 Secret目录。已声明 Matt current/release/skill symlink 按 installer 的 exact 链接验证，其他受管目标 symlink 报 GAP。副本 `.previous`、`__pycache__` 与用户另装的非受管技能不能冒充当前文件；额外内容只在 installer 声明 exact tree 的边界内报告，符合两侧已有 managed tree 契约。

install-vm 的首次创建用户配置（config.toml/global AGENTS）不作为源码字节等同目标，不读取用户现值；报告 USER_OWNED 边界。不存在的 installer 目录不能计作未安装的 PASS。只对源码 JSON/受管 installed JSON 提取既有字段，错误或不可读报 GAP。

## 测试决策

同一个 CLI seam 完成 source 自洽、8 面 full fixture、负向漂移和恢复；按 issuer #304 的实际漏文件形态构造。用 fixture 权限/spy 阻止写入、禁止 subprocess install/sudo/network，文件树/字节前后相等；测试 harness 可以创建 fixture 和保存报告，checker 本身不能写。

计数、JSON revision 与文件字节都要各有负向用例，不能只测版本数字。source 映射遗漏/installer 新增由静态门拒绝；受管链接合法与漂移均测试。完整 smoke 按当前平台要求跑；已知环境或其它 Issue 失败如实 FAIL/GAP，修复范围不扩张。

## 风险与回滚约束

真实运行可能持续 GAP，这是发现缺口，不是 checker 失败；同时 AC-2 仍不通过。回滚源码只需经后续受控 PR revert 本 Issue 原子提交，未改 installed 的运行无需系统回滚；fixture 恢复只操作本测试临时目录。

## 原 AC-2 的具体处置

保留全 PASS 标准，不弱化。输出 exact target 的现有 drift 和缺失组件。平台维护者需在本只读合同之外决定哪些组件/安装前缀在 Mac 实际适用，或另行明确授权从已合并 exact main 安装对应 installer；root-owned 安装、VM 安装分别授权并验收。本会话不自行创建派生 Issue，不将调度批量授权当安装授权。

在独立处置后以相同 source SHA/roots 重跑真实检查；AC-2 未通过前不声称全部验收、completed/归档。若维护者要修订 AC-2，必须明确给出新的安装适用性合同及理由，保留原 GAP 证据；不能由实现者为了绿灯自行改标准。

## 非目标

自动修复、重装、sudo、计划任务/automation、部署/Secret/服务/权限改变、写 installed metadata、远端 fetch、业务项目变更、调用 fail-open live mutation 进行反向证明均不在范围。命令可供人主动或将来调度，但本 Issue 不创建 monitor。

## 未决问题

无会改变实现方向的未决问题。用户已明确批准本合同启动；AC-2 的真实安装缺口明确挂起，安装处置不纳入本次启动授权，也不被本次批准豁免。
