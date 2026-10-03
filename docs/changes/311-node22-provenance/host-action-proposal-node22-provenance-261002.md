# #311 已批准合同与 exact 主机动作记录

选择 A：保留 `/opt/node22`，只新增 `.aisoft-runtime-source`。选择依据是 fresh SFMDigitalBoard main
`1be980d238c37495a808170ee8ce4a5bf04fbaf3` 的 CI:31 及测试守卫:73；不进入删除方案。

## 请求的启动授权

授权本聊天按映射 spec/plan 实施 #311；允许判级投影 `type/maintenance + complexity/complex` 并读回 projected。
同时**单独、明确授权** gitea-ci 主机动作，执行身份为 root，范围限以下两项：

1. 用已审阅 Python 只读探针补齐受保护 runner config、runner 用户静态 profile、unit/drop-in 必要非 Secret 字段。绝不 source profile、不读 .env/auth/registration/凭据/日志/process environ 或 argv。只输出 path/node22 布尔值、行号、身份和来源 marker allowlist。此为既有 typed 能力缺口的 exact 例外，不新增 broker 能力。
2. 根据以下固定内容创建 marker，检查、重复执行 no-op，精确回滚再重新创建并最终读回。host mutation 的 target 唯一是 `/opt/node22/.aisoft-runtime-source`，不删除目录、不改 Node/npm/pnpm 字节、不改其它运行时或任何服务/config/profile。

源文件允许修改范围为本 Issue 证据/合同及 `01` §4.2 的最小事实修正；不改 AGENTS.md、skills、controller、broker/runtime、CI/部署脚本或其它仓。
主机行为固化在本提案内的确定性 Python 命令段；无需安装运行时或全局命令。
最终 PR 提交另行绑定 exact #311/branch/manual 确认；不授权 push/PR/merge/deploy。

root 补读文件：[readonly-root-detail-proposal-261002.py](readonly-root-detail-proposal-261002.py)，AST PASS，SHA-256 `6ccb7f2d096ac10d07f55d7ba75eb4aceeee81927a2aff4d54fa6c672cb014d9`，执行 NOT RUN。

```bash
/usr/local/bin/orb -m gitea-ci -u root /usr/bin/python3 -B - \
  < /private/tmp/issue-311-node22-provenance/docs/changes/311-node22-provenance/readonly-root-detail-proposal-261002.py \
  > /private/tmp/issue-311-node22-provenance/docs/changes/311-node22-provenance/host-root-detail-261002.jsonl
```

Marker candidate SHA-256：`bd3c6ccaf6929449631684667043dc614607170722d5fb658025b6d281d5db8c`；下列 Python 段 SHA-256：`8bf02fa774bc078ca9f8f19704f8d6e98abc71cff7d26ad332cae17c68cd10e7`（不含 Markdown fences）。内容/AST 校验 PASS，mutation NOT RUN。

## Marker 内容

精确 bytes 见 [marker-node22-provenance-261002.txt](marker-node22-provenance-261002.txt)，key=value 与真实 node24 marker 形状一致，`contract=gitea-runner-node-runtime/v1`。
来源、安装日期、安装者和上游包校验值均 unknown；本次日期独立放 recorded_at。当前 binary hash 单独标 observed，不冒充上游归档 checksum。
known_consumers 只列当前已证实消费方；不声称全主机没有未知消费者。root 补读若发现更多活动引用则先更新此列表并提供差异，原 payload 未锁定前不写 marker。

## 补读前提与覆盖

普通 benque 已扫描 584 个普通 systemd 文件，无 node22 引用；219 个 symlink 没有读目标，2 个 runner 路径 PermissionError。symlink 必须用 link/target 清单区分“目标已在本次普通文件清单中扫描”和真正未扫描，不能当成219个未知服务。
act_runner unit 有两个 effective drop-in，其中 `/run/systemd/system/service.d/zzz-lxc-service.conf` 尚未在初始目录范围；仅按 service-metadata 返回的固定真实路径补读。
profile 只做静态 PATH/node22 引用核对，动态 shell 执行及 process 环境明确排除。对静态 PATH 使用正确的 Environment=PATH 语法提取器，不能将原探针未识别 PATH 字段记为 absent。

root 读取范围的进一步扩张、发现新 Secret 需求或异常 symlink 指向非配置目录立即停止。不得读取退出治理的项目 Secret profile。

## 确定性 marker 命令（已批准并执行，回执见 verification）

以下 Python 段从 stdin 送入 gitea-ci，参数只接受 `check`、`apply`、`rollback`。环境或路径不符合 pinned 基线就拒绝；既存不同 marker 不覆盖。

```python
import hashlib
import json
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys

ROOT = Path('/opt/node22')
NAME = '.aisoft-runtime-source'
PAYLOAD = b'''contract=gitea-runner-node-runtime/v1
installed_at=unknown
installed_by=unknown
node_version=22.22.0
node_source=unknown
node_sha256=unknown
npm_version=10.9.4
npm_source=unknown
npm_sha1=unknown
npm_integrity=unknown
pnpm_version=10.28.0
pnpm_source=unknown
pnpm_integrity=unknown
recorded_at=2026-10-02
recorded_by=aisoft-platform-issue-311
known_consumers=admin/SFMDigitalBoard:.gitea/workflows/ci.yml
observed_node_binary_sha256=8eeefcacdf48f58541a651016e604055d14a992e39df98636b76495bc7244395
rollback=remove-only-issue-311-marker-if-content-sha256-matches;keep-node22-runtime-and-runner-config
'''
EXPECTED_NODE_HASH = '8eeefcacdf48f58541a651016e604055d14a992e39df98636b76495bc7244395'
action = sys.argv[1] if len(sys.argv) == 2 else ''
if action not in {'check', 'apply', 'rollback'}:
    raise SystemExit('exact action required')
if os.uname().nodename != 'gitea-ci' or os.geteuid() != 0:
    raise SystemExit('exact gitea-ci/root required')
account = pwd.getpwnam('gitea-runner')
info = ROOT.lstat()
if not stat.S_ISDIR(info.st_mode) or (info.st_uid, info.st_gid) != (account.pw_uid, account.pw_gid):
    raise SystemExit('runtime identity drift')
if stat.S_IMODE(info.st_mode) != 0o755:
    raise SystemExit('runtime permissions drift')
node = ROOT / 'bin/node'
if not node.resolve().is_relative_to(ROOT):
    raise SystemExit('node escapes fixed runtime')
with node.open('rb') as stream:
    actual_node_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
if actual_node_hash != EXPECTED_NODE_HASH:
    raise SystemExit('runtime binary drift')
version = subprocess.run([str(node), '--version'], check=True, capture_output=True,
                         text=True, timeout=10).stdout.strip()
if version != 'v22.22.0':
    raise SystemExit('node version drift')
for tool, expected in (('npm', '10.9.4'), ('pnpm', '10.28.0')):
    package = ROOT / 'lib/node_modules' / tool / 'package.json'
    if not package.resolve().is_relative_to(ROOT):
        raise SystemExit('package path escapes runtime')
    if json.loads(package.read_text()).get('version') != expected:
        raise SystemExit('package version drift')

directory = os.open(ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
try:
    def read_existing():
        try:
            fd = os.open(NAME, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        except FileNotFoundError:
            return None
        with os.fdopen(fd, 'rb') as stream:
            current = os.fstat(stream.fileno())
            if not stat.S_ISREG(current.st_mode) or current.st_nlink != 1:
                raise SystemExit('marker is not an independent regular file')
            content = stream.read(len(PAYLOAD) + 1)
        if content != PAYLOAD:
            raise SystemExit('different marker; zero overwrite/removal')
        if (current.st_uid, current.st_gid, stat.S_IMODE(current.st_mode)) != (
                account.pw_uid, account.pw_gid, 0o644):
            raise SystemExit('marker owner/mode mismatch')
        return current

    current = read_existing()
    result = ''
    if action == 'check':
        if current is None:
            raise SystemExit('marker missing')
        result = 'verified'
    elif action == 'apply':
        if current is not None:
            result = 'already-current-no-op'
        else:
            fd = os.open(NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(PAYLOAD)
                stream.flush()
                os.fchown(stream.fileno(), account.pw_uid, account.pw_gid)
                os.fchmod(stream.fileno(), 0o644)
                os.fsync(stream.fileno())
            os.fsync(directory)
            read_existing()
            result = 'created'
    else:
        if current is None:
            raise SystemExit('rollback target missing; stop')
        latest = os.stat(NAME, dir_fd=directory, follow_symlinks=False)
        if (latest.st_dev, latest.st_ino) != (current.st_dev, current.st_ino):
            raise SystemExit('marker changed before rollback')
        os.unlink(NAME, dir_fd=directory)
        os.fsync(directory)
        result = 'removed-only-matching-marker'
    print(json.dumps({'issue': 311, 'action': action, 'result': result,
                      'marker_sha256': hashlib.sha256(PAYLOAD).hexdigest(),
                      'runtime_binary_sha256': actual_node_hash,
                      'marker_path': str(ROOT / NAME)}, sort_keys=True))
finally:
    os.close(directory)
```

首次 apply 写入中途失败会保留不完整 marker 并 fail closed，不覆盖或自动删除。由人审核实际 bytes 后决定清理；不假报安装成功。

## 执行顺序与验收

1. 补读完成、known_consumers 完整列明并核对最终 payload hash；记录 marker 不存在、Node/npm/pnpm 实测、runner 状态和非 marker 文件元数据基线。
2. apply → check → apply（no-op）；比对 marker owner=runner、mode=644、内容 hash；node hash 与版本不变。
3. rollback（只移除 exact matching marker）→ test marker 不存在且 node22 目录仍存在 → apply → check；最终保留 marker。
4. 比对运行时非 marker 文件元数据、node hash、runner unit/config 的非 Secret 读回；不对系统配置/Secret 文件做全量字节导出。
5. 01 §4.2 记录来源 unknown 但在用、实测版本及消费方；check-change-documents、classification --verify。

marker mutation 与上述回滚演练均须此提案的明确主机授权。CI、新安装、服务重启、主机全量环境和其它项目改动一律不执行。source/local 检查不能替代本节 live receipts。

## 授权与执行回执

用户在本聊天对包含 root补读、marker动作和判级投影的启动请求回复“确认，继续”。未包含push/PR/merge/deploy。首轮apply/check/no-op、exact rollback、目录保留检查、reapply/finalcheck及cat字节比对全部PASS。

补读探针在同一必要字段范围内补齐了HOME前缀/目录metadata及4个系统profile alias，使用真实exact target且不执行profile。marker命令段与payload保持原批准bytes；探针实执行字节hash另见validation receipt，不把原提案hash冒充修正版hash。

实际stdin文件相对批准fenced Python段只增加末尾换行，未改变语句或payload；canonical code hash与真实stdin hash分别记录在source-validation-hashes-261002.json，不混用。
