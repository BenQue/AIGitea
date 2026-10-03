# #311 初始受控只读访问请求（已获批并执行）

用户在本聊天回复“确认”后执行；仅限本文件两项访问。主机写/删除及 root 补读仍须后续 exact 提案批准。原探针末尾 PermissionError 的异常捕获已修正（不扩读范围），重试成功；修正版 SHA-256 为 0b213ddd68460a9db583e4b6eace83dd776e5d4aa601a09d43a949b33d5dc5fc。首个不完整回执和重试回执均保留。

现有 source/installed broker 的 host-operator surface 只有 vm.status、runner.status 与 vm.profile 的受控操作。runner.status 不提供工具链 marker、runner PATH 或 unit/config 引用盘点；vm.profile 会触及 protected Secret profile，不能拿来代替这次盘点。

缺口不得靠临时拼任意 shell 或默认 admin 解决。当前停在可审阅命令提案；不新增 broker 功能、不调用 emergency diagnostics、不部署。

## 请求 1：其它三仓的 existing typed broker fresh read

调度把 remote 读取限定为 project=aisoft-platform，而 strict manifest 每个 project 只能读本仓；平台 project 没有 cross-repository content 操作。
为证明消费方当前 main，申请仅以下三条已有 typed 操作，每个 checkout 由对应 manifest 解析：

```bash
/usr/local/libexec/aisoft/host-access-broker --project localwms --operation git.fetch.main
/usr/local/libexec/aisoft/host-access-broker --project newemaint --operation git.fetch.main
/usr/local/libexec/aisoft/host-access-broker --project sfm-digital-board --operation git.fetch.main
```

只更新 remote tracking refs，不 checkout/rebase/commit/push，不动 dirty SFMDigitalBoard。
批准后只读固定 fresh main Git 对象，列所有 workflow、相关间接脚本和 active node22 引用，不访问 .env、auth 或 credentials。
这是 #311 消费方核对，不授权实施其它 Issue。

## 请求 2：typed surface 缺失时的 exact host 只读例外，或由负责人执行

待审探针：[readonly-host-probe-261002.py](readonly-host-probe-261002.py)。它固定目标 gitea-ci，枚举 marker 元数据和 allowlist 字段、node --version 与当前 binary hash、包版本元数据、systemd 配置引用位置、runner 静态 PATH/profile 和 config 引用、可读 process exe 与固定 bin symlink。

探针输出只有位置/布尔值和所需非 Secret marker 字段。不 source profile、不读 .env/auth/registration、任何凭据、日志、process environ 或 argv；npm/pnpm/corepack 不执行，避免 bootstrap/cache 写入。无法读取或动态 PATH 显式 GAP，探针本身不能证明全主机无消费方，不能单独据它删除目录。

探针 SHA-256：`6a1fff13a408af5619b1f4002157cc40bcdb550f2d321f64dd8a83d746951436`。AST 语法检查 PASS，主机执行 NOT RUN。正式执行前校验探针 sha256，命令通过 stdin 传送只读 Python，不把文件写入 VM；stdout 只写本 Issue 的本地证据附件。installed manifest 已核对：binary=/usr/local/bin/orb，machine=gitea-ci，user=benque。执行身份使用既有 host operator benque；如文件权限不足，仅报 GAP，不自动 sudo。

```bash
/usr/local/bin/orb -m gitea-ci -u benque /usr/bin/python3 -B - \
  < /private/tmp/issue-311-node22-provenance/docs/changes/311-node22-provenance/readonly-host-probe-261002.py \
  > /private/tmp/issue-311-node22-provenance/docs/changes/311-node22-provenance/host-inventory-261002.jsonl
```

**此命令不属于现有 broker typed operation**。只有明确批准这个受控只读例外才能由本聊天运行；否则负责人自行运行并提供脱敏结果，或由独立治理 Issue 新增能力后再回到 #311。不能把普通 host/sandbox execution permission 当作该治理例外批准。

## 授权不包含

写 marker、删除/改名 node22、改 PATH/profile、改/restart act_runner、读取 Secret、跨仓修改、installer/全局技能安装、push/PR/merge/deploy。主机 mutation 仍 NOT RUN。拿到证据后再准备具体 A 方案合同与 exact 写/回滚命令供一次启动确认。
