---
issue: 413
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/413
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - artifact
  - platform-governance
depends_on: []
branch: change/413-dockerfile-arg-drift-host
created: 2026-10-21
updated: 2026-10-21
git_scope:
  - 06-运维手册与踩坑集.md
  - architecture/README.md
  - codex/runtime/aisoft_architecture/dockerfile.py
  - codex/runtime/tests/test_architecture_dockerfile.py
  - codex/tests/fixtures/installed-drift/test-installed-drift.py
  - codex/tools/check-installed-drift.py
  - docs/changes/413-dockerfile-arg-drift-host/plan-dockerfile-arg-drift-host-261021.md
  - docs/changes/413-dockerfile-arg-drift-host/spec-dockerfile-arg-drift-host-261021.md
  - docs/changes/413-dockerfile-arg-drift-host/summary-dockerfile-arg-drift-host-261021.md
  - docs/changes/413-dockerfile-arg-drift-host/verification-dockerfile-arg-drift-host-261021.md
  - usage/bundle.json
---

# Dockerfile ARG 默认值展开与漂移检查主机防误用

## 目标与原因

1. 让合规且被守住的 `ARG NAME=<tag@digest>` + `FROM ${NAME}` 写法通过 architecture 校验，
   而不放松「构建期覆盖不能绕过 pin」这条现行保证。
2. 让漂移检查在 macOS 上拒绝 `--host vm` 而不是对着本机根产出假 GAP。

## Acceptance criteria

- [ ] AC-1：全局 ARG（第一个 FROM 之前）带字面量默认值、FROM 镜像 token 恰好是 `${NAME}` 或 `$NAME`、
  且该 stage 内有 RUN 指令含 `test "${NAME}" = "<默认值>"` 时，按默认值核验 tag、digest 与声明集合，PASS，
  digest 计入引用集合（`DOCKERFILE_BASE_IMAGE_UNUSED` 不误报）。
- [ ] AC-2：以下仍报 `DOCKERFILE_FROM_VARIABLE_UNSUPPORTED`：变量未声明为全局 ARG、无默认值、只在 stage 内声明、
  默认值含 `$`/引号/空白、token 带修饰符（`${NAME:-x}`）或与字面量拼接（`node:${V}-alpine`）、
  stage 内缺守卫或守卫比较值与默认值不一致。
- [ ] AC-3：展开后镜像不合规照原诊断：缺 digest 报 `DOCKERFILE_DIGEST_REQUIRED`，digest 不在声明集合报
  `DOCKERFILE_DIGEST_MISMATCH`；诊断输出不回显默认值中的 digest。
- [ ] AC-4：macOS 上 installed 模式、安装根为 `/` 时 `--host vm` 退出码 2，`result` 为 `ERROR`，
  `error.reason` 为 `host-mismatch`，`error.detail` 给出 OrbStack 转发命令，不产出 installers 行、不读安装面。
- [ ] AC-5：合成安装根（`--install-root` 非 `/`）、`--source-only`、`--host mac` 与非 macOS 上的 `--host vm` 行为不变。
- [ ] AC-6：AC-1/AC-2 与 AC-4 各有反向证明：新测试在修复前的源码上红、修复后绿，记录在 verification。
- [ ] AC-7：使用发布包发 1.11.0（若 main 上已被占用则顺延），`bash codex/tests/smoke.sh` 全绿。

## 接口、数据与兼容性影响

- 诊断码集合不变，不新增字段；lock schema 与 lock 字节不变。原先 FAIL 的部分 Dockerfile 现在 PASS，
  原先 PASS 的不会变 FAIL（只放宽带守卫的变量形式）。
- `check-installed-drift.py` 新增一个 `error.reason` 取值 `host-mismatch` 与 `error.detail` 字段，只在原本会产出错误结果的组合出现。
- 已装主机需重装 architecture（target）才会生效；重装是负责人的动作。

## 风险与回滚约束

- 守卫识别是子串匹配，只证明「构建期覆盖会让该 stage 失败」，不证明构建实际使用了哪个镜像；
  builder provenance 仍是另一层证据，README 维持该声明。
- 回滚：revert 本 PR，再发下一个发布包版本；项目侧 lock 不受影响。

## 非目标

- build-arg 注入、修饰符展开、stage 内 ARG、ARG 引用 ARG。
- `--host mac` 在 Linux 上的对称防护、`--host target` 的判定。
- 修改 NewEMaint 或其它项目仓。

## 未决问题

- 无。负责人 2026-10-21 在确认点 1 选定守卫方案。
