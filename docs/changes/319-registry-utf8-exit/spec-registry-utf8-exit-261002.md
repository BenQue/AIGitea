---
issue: 319
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/319
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - ci-change
depends_on: []
status: approved
branch: change/319-registry-utf8-exit
created: 2026-10-02
updated: 2026-10-02
---

# #319 registry UTF-8 故障退出修复合同

## 目标与原因

临时 registry 停止时预检必须阻止 CI；修复 Bash 3.2 UTF-8 变量词法边界错误造成的退出 0，恢复既有合同。

## User stories

1. CI 使用者在 registry 健康时得到退出 0 和 OK。
2. CI 使用者在 registry 停止时得到退出 1 和 FAIL stage=connect。
3. 排障者看到正确地址、curl 退出码与中文诊断。
4. HTTP 500、非 packument、tarball 404、未配置时分别得到既有失败 stage。
5. macOS Bash 3.2 使用者在默认 UTF-8 下使用，无需更改 locale。
6. Linux Bash 使用者保留已有行为、env 配置和最小依赖。
7. 维护者只用临时 HTTP fixture 验证故障与恢复，不依赖真实 registry/credential。

## Acceptance criteria

- [ ] **AC-1** 中文标点前 `$REGISTRY`、`$HTTP_CODE` 使用明确花括号边界，同类字符串仅修本脚本当前 4 处，不做无关重构。
- [ ] **AC-2** UTF-8 临时 HTTP fixture：健康 0/OK；停止后同地址退出 1/FAIL stage=connect，含正确地址及 curl 退出码，无 unbound variable/OK；恢复后 0/OK。HTTP 500、非 packument、tarball 404、config 的既有 stage/退出 1 保留，HTTP 诊断正确。
- [ ] **AC-3** macOS /bin/bash 3.2.57 的默认 C.UTF-8、en_US.UTF-8、zh_CN.UTF-8 与可用 Linux Bash 5.3.9 C.UTF-8 改后验证；不可执行写 NOT RUN。LC_ALL=C 对照不能替代 UTF-8 通过证据。
- [ ] **AC-4** bash -n、可用 ShellCheck、对应 fixture、完整 bash codex/tests/smoke.sh 通过；PR required CI 独立读回。全部 registry 请求仅指向测试临时 127.0.0.1 HTTP server。

## Implementation decisions 与明确授权

此 complex spec 经人确认后，仅授权修改 `templates/project/ci/registry-preflight.sh` 的同类变量词法边界、`codex/tests/test-registry-preflight.sh` 的真实行为/诊断断言，以及本 Issue 映射文档/证据。保留 fail(stage)、stage/marker、env、curl 超时/重试、探测包默认值、无 npm 缓存及无 npmjs fallback 合同。

不通过 EXIT trap 改写或 LC_ALL=C 掩盖错误。Bash 3.2 基线证明 nounset trap 保存 $? 仍得到 0；本缺陷修复采用明确边界阻止错误变量名产生，使既有 fail 正常退出 1。若正常 fail 仍失败，应升级而非擅自扩大到通用 shell error handler。

独立治理合同步骤：本轮完成合同并停止；获确认后只记录批准状态并停止。下一 fresh run 重读 AGENTS.md、批准 spec/plan 和最新 Issue 评论，才实施 CI/runtime。不得修改本运行正在遵循的 AGENTS.md。

## Testing decisions

复用已有 HTTP fixture，验证退出码、stage、diagnostics 和绿—红—绿，不以静态字符串匹配替代行为。connect、HTTP 500、tarball 404 检查正确地址/状态码，失败路径拒绝 nounset/OK。各 UTF-8 命令使用该主机同一 Bash interpreter。

## 接口、数据与兼容性影响

无 schema/API/权限/credential 变更，只恢复既有失败退出与中文诊断；兼容 macOS Bash 3.2 和 Linux Bash。下游项目的已有副本由各自独立 Issue/PR 采纳，本次不复制覆盖。

## 风险与回滚约束

CI 强制 complex/manual。局部原子修复 commit 的反向变更经独立 PR 回滚；回滚会恢复已知 UTF-8 缺陷，应明确报告。不直推 main、不 force、不修改 workflow/required CI。

## 非目标

通用 EXIT trap 加固、真实 registry/PM2/VM 服务、下游同步、broker/triage API、Agent/controller/AGENTS、workflow、安装、凭据、部署、自动 merge。

## 未决问题

实现方向无未决；合同/启动已获本会话用户“确认”。live Matt triage 投影因缺少 typed operation 为 GAP，不夹带 broker 治理实现或直连 API。
