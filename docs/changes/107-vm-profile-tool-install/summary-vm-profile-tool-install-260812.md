---
issue: 107
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/107
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 manifest 已声明但从未可用的四个 vm.profile typed 操作；change_type=platform 强制 complex
risk_flags:
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-vm-profile-tool-install-260812.md
  spec: spec-vm-profile-tool-install-260812.md
  plan: plan-vm-profile-tool-install-260812.md
  verification: verification-vm-profile-tool-install-260812.md
confidence: high
override_reason: ''
depends_on: []
status: analyzed
branch: change/107-vm-profile-tool-install
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/109
created: 2026-08-12
updated: 2026-08-12
---

## 问题/需求总结

`vm.profile.read-back` 与 `vm.profile.plan` 对 `--project newemaint` 均返回
`HOST_COMMAND_FAILED / BLOCKED_EXTERNAL`。根因是 VM `gitea-ci` 内**从未安装**
`install-host-access-broker.sh` 的产物，而 `broker._vm_profile()` 恰恰要在 VM 内执行
其中的 `project-profile-migration`。

发现来源：NewEMaint #65 平台合同基线回补盘点的范围外观察。

## 影响范围

- `codex/runtime/aisoft_host_access/broker.py`：`_vm_profile` 增加确定性 preflight 与
  可区分的 typed 错误。
- `codex/runtime/tests/test_host_access.py`：覆盖新错误分支与正常分支。
- `06-运维手册与踩坑集.md`：记录安装面归属（哪台机器执行哪个安装器）与本次踩坑。
- 运维执行面：在 VM 内运行既有幂等安装器并执行 profile 迁移（已获用户授权）。
- 不改动：平台 `AGENTS.md`（本次运行正遵循它）、labels/governance manifest、CI 定义、
  任何业务仓库、`change/106-*` 与 `change/101-*` 等他会话在途分支。

## 根因

`broker._vm_profile()`（`broker.py:1023-1043`）执行：

```
orb -m gitea-ci -u benque /usr/bin/sudo -n <mac_host.vm_profile_tool> --project <id> --action <action>
```

手工复现该 exact 命令得到 `sudo: '/usr/local/libexec/aisoft/project-profile-migration':
command not found`。`sudo -n true` 在 VM 内对 `benque` 返回 OK，故唯一阻塞是文件缺失。

`project-profile-migration.sh` 在非源码树场景依赖三个安装路径，VM 内**全部缺失或为空**：

| 依赖 | 期望 | VM `gitea-ci` 实际 |
|---|---|---|
| `RUNTIME_ROOT` | `/usr/local/lib/aisoft-host-access` | 目录存在但**为空** |
| `ACCESS_MANIFEST` | `/usr/local/share/aisoft/host-access-broker.json` | **缺失**（该目录仅有 host-role 两个文件） |
| `GOVERNANCE_MANIFEST` | `/usr/local/share/aisoft/gitea-governance.json` | **缺失** |
| 工具本体 | `/usr/local/libexec/aisoft/project-profile-migration` | **缺失**（该目录仅有 `verify-host-role`） |

这三处正是 `codex/install-host-access-broker.sh` 的 `LIB_ROOT` / `SHARE_ROOT` /
`LIBEXEC_ROOT`。该脚本只在 Mac 上执行过（Mac 侧三个文件齐备，Aug 9）。

安装面归属此前无任何文档约束：

- `install-vm.sh` 是 **user-scoped**（装进 `$TARGET_HOME`，不需 root），不覆盖 `/usr/local/**`。
- `install-host-role.sh` 是 root-scoped，但只装 `verify-host-role`（VM 内现有的那一个，Aug 3）。
- `install-host-access-broker.sh` 是唯一提供 `project-profile-migration` 的安装器，
  却只在平台 `AGENTS.md` 目录节被列举，未说明须在哪台机器执行。

## 连带症状（同一根因，非独立缺陷）

因迁移从未执行，VM 仍停在 pre-#61 布局，与 `vm_profile_policy` 声明三处不符
（`token_root`、`backup_root` 均不存在；profile 仍内联 `GITEA_TOKEN=`）。由此：

1. 陈旧内联令牌不能认证——该 profile 经 `gitea-readonly.sh` 请求 `repo`、`issues/65`、
   `labels` 全部 404，而同 VM 内 `/api/v1/version` 对 `gitea-ci.orb.local:3000` 与
   `127.0.0.1:3000` 均 HTTP 200（网络正常，故判为鉴权失败）。
2. `ANALYSIS_PROVIDER=codex` 与 manifest 声明的 `analysis_provider: claude` 漂移。

## 次生缺陷：错误不可诊断

`broker._run()`（`broker.py:1045-1059`）把所有非零 returncode 与非 `TypeError` 异常一律
塌缩为 `HOST_COMMAND_FAILED / "structured host operation failed"`。定位根因必须绕过 broker
手工复现 `orb ... sudo -n ...`。`_default_runner` 其实已捕获 stderr（`broker.py:133`），
但该信息在失败路径上被完全丢弃。

## 初步方案与建议

1. `_vm_profile` 增加确定性 preflight（在 VM 内 `test -x` 探测工具），缺失时抛出可区分的
   typed 错误码，指向应执行的安装器名。**不解析 stderr 文本**——避免依赖 sudo 的本地化
   消息，也避免把 stderr 内容漏进错误响应。
2. 在 `06-运维手册与踩坑集.md` 固化安装面归属表与本次踩坑，使「哪个安装器在哪台机器执行」
   成为可查事实。
3. 在 VM 内执行既有幂等安装器与 profile 迁移，按合同做两次幂等 + 一次故意失败回滚验证。

不改平台 `AGENTS.md`：平台合同规定普通 implementation run 不得修改本次运行正在遵循的
`AGENTS.md`。安装面事实写入 06，`AGENTS.md` 目录节的补充留给独立的治理合同变更。

## 风险

- broker 是治理写路径核心，改动影响所有 typed 操作。缓解：只在 `vm.profile.*` 分支增加
  preflight，不触碰 `_run` 通用语义与其它操作路径；新增分支有测试覆盖。
- VM 内安装与迁移是运维变更。缓解：安装器自身幂等且 credential-free（其 banner 明示不绑定
  凭据/profile/service/timer）；迁移按合同做两次幂等 + 一次故意失败回滚，证据记入 verification。
- **令牌重新签发不在本次范围**：属 Secret 操作，由人执行。本次不读取、不打印、不生成、
  不搬运任何 token 值；AC 中涉及令牌的验证只观察 HTTP 状态码。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
reason: 恢复 manifest 已声明但从未可用的四个 vm.profile typed 操作；change_type=platform 强制 complex
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

- `aisoft_loop/classification.py` 的 `Route`：`change_type in {"feature","platform"}`
  无条件进入 `forced_reasons`；`platform-governance` 亦属 `FORCED_COMPLEX_RISKS`。
- `contract_effect: restore`——manifest 早已声明 `vm_profile_tool` 且四个 `vm.profile.*`
  操作已在 allowlist 中，本次是让既有声明真正可用，不新增外部合同。
- `required_docs` 追加 `verification`：本次涉及在 VM 内执行 profile 迁移，按模板规则
  「部署或迁移再追加 verification」，并须记录两次幂等与一次故意失败回滚。

### 缺失的 acceptance criteria 或决策

- 无。令牌重签与 #106 的 label 检查能力均已明确划为范围外。
