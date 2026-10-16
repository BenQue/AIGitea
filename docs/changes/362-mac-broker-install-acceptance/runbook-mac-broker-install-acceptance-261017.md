# #362 本人私密 Mac 终端接续 runbook（尚未执行）

本文是既有原生命令的有界操作卡，不是新installer或分发框架；唯一安装入口仍是固定pin既有installer。
2026-10-17已批准整包；本轮执行被原生 `sudo -n` exit1/password required 阻塞，系统写入窗口未开。
本文的可执行命令尚未用于root/安装/恢复；语法审查和只读helper baseline通过不等于现场验收。

## 责任与先决条件

- 唯一文档/证据owner是会话 `01a1457e-699f-7372-8b6a-7a21d613d407`，claim不交给其他会话。
- 本人 benque 若手工执行root操作，receipt明确 `operator=human:benque`；session绑定只用于本票只读qualification，不冒称Agent执行了root命令。
- 本人在同一私密Mac终端执行以下步骤，密码仅由原生sudo交互读取。不要把密码放聊天、脚本、argv或日志，不用 `sudo -S`。
- 先由本人/根调度协调共享工具写入窗口，确保其他broker/Controller调用者在P0–P6结束前不使用共享工具；不暂停业务服务。不把 `ps`/marker视为排他证明。
- 原生sudo认证与实际命令必须在同一终端及适用timestamp上下文。另一个终端 `sudo -v` 不保证 Codex `sudo -n` 生效；若本人完整执行本文，则所有root命令均留在该终端。
- 如希望Agent恢复root执行，先在Agent实际执行上下文验证，仍须满足已批准固定原生入口。本文不要求sudoers修改、NOPASSWD策略或新root通道。
- main/source或target baseline漂移、未知额外文件/链接/并发即STOP；不得换latest/reset、改installer、扩权限或手工快拷两个文件。

## 固定资源与hash

| 文件 | SHA256 |
|---|---|
| canonical source `codex/install-host-access-broker.sh` | `485ea19514c5f4b72c84d6cc9576fe0c2b65c34d084e74c8f80e2d6ad6f10897` |
| 原审阅卡 | `3c67a0c6a3d085735d4e20aead4fd951ead4eeb716ac41323719bff85d3ed8d9` |
| artifact `manual-acceptance-readonly.py` | `d1df20d4055441b9a66d179387f1f4313a862b29cfa3efe079c3840c30edb123` |
| artifact `snapshot-relative-paths.txt` | `2c4ddf9d3ab4bd5201f5aab50b0651aa5584e5f4120757f269177c57196b62de` |
| artifact `local-read-checks.py` | `e9f6a4eedba6f2b77a4e464356255f269b2147b19480e8008bb1cbc004c78f9e` |
| artifact `fresh-typed.py` | `5630a61889250728d2bf280d5502b14288730ff898150794925cac74eeb8ca5a` |

以上artifact都在 `/Users/benque/.codex/visualizations/2026/10/16/01a1457e-699f-7372-8b6a-7a21d613d407/issue-362`。
`manual-acceptance-readonly.py` 仅读取exact公开target/source、metadata及所选snapshot，输出JSON，不执行root写入、网络、Git整合或凭据读取；本轮仅 `baseline` 分支已实际执行。
其余 `installed/qualified/old-qualified/archive/root-entry` 分支尚未现场执行，不报告PASS。
Snapshot列表为43公开常规文件、无目录/Secret；13原缺失路径和10目录metadata由原卡完整manifest核对。
fixture不需要再次运行，F1/F2原实测和exact清理见 `fixtures.json`。

## P0：同一终端认证、fresh核验、协调窗口和snapshot

从本人私密终端启动独立shell，以下块在同一shell中顺序执行；不用 `set -x`。
`set -e` 只阻止继续运行，不自动恢复。任何安装开始后的失败立即执行本文“失败/完整恢复”，不要关闭窗口后留下混合工具。
认证过期可在同一终端重新 `sudo -v` 后继续当前恢复；不能取得root时保留现场并STOP，禁止换通道。

```bash
/bin/bash --noprofile --norc
set -euo pipefail
umask 077
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
export PYTHONDONTWRITEBYTECODE=1
export AISOFT_SESSION_ID=01a1457e-699f-7372-8b6a-7a21d613d407
EVID='/Users/benque/.codex/visualizations/2026/10/16/01a1457e-699f-7372-8b6a-7a21d613d407/issue-362'
SRC=/Users/benque/MyDocs/AISoftPlatform
CHECK="$EVID/manual-acceptance-readonly.py"
PY=/opt/homebrew/bin/python3
/bin/test "$(/usr/bin/id -un)" = benque
cd "$SRC"
/bin/test "$(/usr/bin/git rev-parse HEAD)" = 06afadfca2a950ad6ebee4b90a22e9d950bc72fa
/bin/test -z "$(/usr/bin/git status --porcelain)"
/usr/bin/shasum -a 256 "$SRC/codex/install-host-access-broker.sh" "$CHECK" "$EVID/snapshot-relative-paths.txt"
# 逐字比对上表hash；任何不符停止。用同一正式typed broker fresh核main/base和Issue：
"$PY" -B "$EVID/fresh-typed.py" > "$EVID/manual-fresh-typed.stdout.json"
"$PY" -B "$CHECK" baseline > "$EVID/manual-p0-baseline.json"
/usr/bin/sudo -v
/usr/bin/sudo -n /usr/bin/id -u > "$EVID/manual-root-uid.txt"
/bin/test "$(cat "$EVID/manual-root-uid.txt")" = 0
/usr/bin/sudo -n /usr/bin/env -u PYTHONPATH -u PYTHONHOME \
  PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$CHECK" root-entry > "$EVID/manual-root-entry.json"
```

root-entry必须读回uid0、Python3.14.4、实际Python路径和两个固定根import解析，和原卡一致；不同则STOP。
本卡保留Homebrew解释器由benque拥有的事实；不把本次readback宣称完整OS/解释器安全隔离证明。
现在本人协调并记录共享工具窗口开始UTC/参与者已避让；若不能确认避让，STOP，不写系统。
窗口中本session/根调度也不调用共享broker，不运行其他installer。

```bash
WINDOW_UTC="$(/bin/date -u +%Y%m%dT%H%M%SZ)"
SNAP="/usr/local/share/aisoft/backups/tools-362-$WINDOW_UTC"
/bin/test ! -e /usr/local/share/aisoft/backups
/bin/test ! -L /usr/local/share/aisoft/backups
/bin/test ! -e "$SNAP"
/bin/test ! -L "$SNAP"
printf '%s\n' "$WINDOW_UTC" > "$EVID/manual-window-start-utc.txt"
printf '%s\n' "$SNAP" > "$EVID/manual-snapshot-path.txt"
# snapshot parent当前absent；其有限目录创建和snapshot保留属于批准的snapshot闭包。
/usr/bin/sudo -n /usr/bin/install -d -o root -g wheel -m 0700 /usr/local/share/aisoft/backups "$SNAP"
# 在保护写入之前再比对exact baseline；只有此步骤后才归档。
"$PY" -B "$CHECK" baseline > "$EVID/manual-p0-immediate-baseline.json"
/usr/bin/cmp "$EVID/manual-p0-baseline.json" "$EVID/manual-p0-immediate-baseline.json"
/usr/bin/sudo -n /usr/bin/env COPYFILE_DISABLE=1 /usr/bin/tar -czpf "$SNAP/baseline.tar.gz" -C / -T "$EVID/snapshot-relative-paths.txt"
/usr/bin/sudo -n /bin/chmod 0600 "$SNAP/baseline.tar.gz"
/usr/bin/sudo -n /usr/bin/env PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$CHECK" archive "$SNAP/baseline.tar.gz" > "$EVID/manual-snapshot-verified.json"
```

archive分支逐项验证43常规member、精确路径、无绝对/..、无link、uid/gid/mode/bytes/hash；输出归档SHA256。
Snapshot必须完整可读且header/bytes全部通过后才进入安装。snapshot不删除。
Snapshot目录新建导致父目录entry/size/nlink/mtime变化是批准的snapshot保留副作用；受管目录uid/gid/mode/type必须保持，不能把目录mtime当no-op失败。

## P1/P2：首次安装、独立27文件/metadata/previous与资格

以下installer命令与原卡固定入口一致；不传额外artifact，不设置install-root。

```bash
/usr/bin/sudo -n /usr/bin/env -u AISOFT_HOST_ACCESS_INSTALL_ROOT -u PYTHONPATH -u PYTHONHOME \
  PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory \
  GIT_CONFIG_VALUE_0=/Users/benque/MyDocs/AISoftPlatform \
  /bin/bash /Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh > "$EVID/manual-p1-installer.txt" 2>&1
"$PY" -B "$CHECK" installed > "$EVID/manual-p1-installed.json"
"$PY" -B "$CHECK" qualified > "$EVID/manual-p2-qualified.json"
```

`installed` 必须核对27文件及生成metadata、完整previous/absence、owner/mode/type/link；metadata exact pin/helper=null。
`qualified` 在source pin fresh进程只调用 `template_scope_context(None,"hsdb")`，验证repository=`http://gitea-ci.orb.local:3000/admin/HSDB`、holder=false和context.verify；不构造GitRepository、不触碰HSDB#15资源。
任一步失败不要盲目再安装，转完整恢复流程。

## P3：同pin真实重复安装/no-op

```bash
/usr/bin/sudo -n /usr/bin/env -u AISOFT_HOST_ACCESS_INSTALL_ROOT -u PYTHONPATH -u PYTHONHOME \
  PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory \
  GIT_CONFIG_VALUE_0=/Users/benque/MyDocs/AISoftPlatform \
  /bin/bash /Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh > "$EVID/manual-p3-installer.txt" 2>&1
"$PY" -B "$CHECK" installed > "$EVID/manual-p3-installed.json"
/usr/bin/cmp "$EVID/manual-p1-installed.json" "$EVID/manual-p3-installed.json"
/usr/bin/grep -F 'host-access-broker/v1 candidate already current (no-op)' "$EVID/manual-p3-installer.txt"
```

只读helper输出排序稳定的全部受管target/previous/absence/owner/mode/link；cmp相等且真实installer输出no-op才通过。

## P4及任何安装后失败：完整restore到observed baseline

先重新校验exact archive/hash，必须与 `manual-snapshot-verified.json` 相等，不从metadata反推旧bundle来源。
如果安装部分失败，下面的新文件guard仍适用：仅main reader `.previous` 是本次批准闭包里预期新建；任何未知残留路径只记录，STOP，不glob删除。

恢复块是独立入口：即使安装子shell已因 `set -e` 退出，也可从**原私密终端**完整执行下块；不依赖上一shell的任何变量。计划内P4也执行同一入口。
此块重新认证的作用域仍是当前实际终端，不传递给Codex。若snapshot receipt缺失/不匹配，不能尝试恢复或猜测路径；保全现场STOP。

```bash
/bin/bash --noprofile --norc
set -euo pipefail
umask 077
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
export PYTHONDONTWRITEBYTECODE=1
export AISOFT_SESSION_ID=01a1457e-699f-7372-8b6a-7a21d613d407
EVID='/Users/benque/.codex/visualizations/2026/10/16/01a1457e-699f-7372-8b6a-7a21d613d407/issue-362'
SRC=/Users/benque/MyDocs/AISoftPlatform
PY=/opt/homebrew/bin/python3
CHECK="$EVID/manual-acceptance-readonly.py"
cd "$SRC"
SNAP="$(/bin/cat "$EVID/manual-snapshot-path.txt")"
"$PY" -B - "$SNAP" "$EVID/manual-snapshot-verified.json" <<'PYRECOVERY'
import sys,json,re
from pathlib import Path
snapshot=sys.argv[1]
assert re.fullmatch(r'/usr/local/share/aisoft/backups/tools-362-[0-9]{8}T[0-9]{6}Z',snapshot)
receipt=json.loads(Path(sys.argv[2]).read_text())
assert receipt['result']=='PASS' and receipt['members']==43
assert receipt['archive']==snapshot+'/baseline.tar.gz'
assert re.fullmatch(r'[0-9a-f]{64}',receipt['sha256'])
print(json.dumps({'recovery_snapshot':snapshot,'expected_archive_sha256':receipt['sha256']}))
PYRECOVERY
/usr/bin/sudo -v
/usr/bin/sudo -n /usr/bin/id -u
/usr/bin/sudo -n /usr/bin/env PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$CHECK" archive "$SNAP/baseline.tar.gz" > "$EVID/manual-before-restore-archive.json"
/usr/bin/cmp "$EVID/manual-snapshot-verified.json" "$EVID/manual-before-restore-archive.json"
# 删除前只读guard：必须是本次独占窗口创建，且仍等于写前main reader原字节；若原absent而当前也absent则无删除。
"$PY" -B - <<'PYGUARD'
from pathlib import Path
import hashlib,stat
p=Path('/usr/local/lib/aisoft-host-access/aisoft_main_integration.py.previous')
if p.exists() or p.is_symlink():
 s=p.lstat()
 assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_nlink==1
 assert (s.st_uid,s.st_gid,stat.S_IMODE(s.st_mode))==(0,0,0o644)
 assert hashlib.sha256(p.read_bytes()).hexdigest()=='6ce8072023ed627d5b67c3e9d7c7e819033398e2c9a906ec4187776386643a91'
print('PASS exact-new-previous guard')
PYGUARD
/usr/bin/sudo -n /usr/bin/env COPYFILE_DISABLE=1 /usr/bin/tar -xzpf "$SNAP/baseline.tar.gz" -C /
/usr/bin/sudo -n /bin/rm -f -- /usr/local/lib/aisoft-host-access/aisoft_main_integration.py.previous
"$PY" -B "$CHECK" baseline > "$EVID/manual-p4-restored.json"
/usr/bin/cmp "$EVID/manual-p0-baseline.json" "$EVID/manual-p4-restored.json"
"$PY" -B "$CHECK" old-qualified > "$EVID/manual-p4-old-qualified.json"
```

恢复43原文件及其完整previous链，清除唯一已证新建的exact previous，13absence及10目录uid/gid/mode/type逐项复核。
installer触及目录原本都是root:wheel/0755且没有其他合法模式差异，因此正常无需chmod/chown；任一实际差异即STOP，不递归修权限。
旧资格必须重现 `BROKER_SURFACE_GAP`。失败恢复分支到此STOP并汇报真实状态；只有计划内P4成功、且之前P1/P2/P3全部通过时，才进入P5。
恢复失败、sudo失效不能恢复、未知`.rotation-source.*`残留：保全exact snapshot与现场，记录exact路径/metadata/日志后STOP；不运行泛化清理。

## P5/P6：同pin再装与最终验收

```bash
/usr/bin/sudo -n /usr/bin/env -u AISOFT_HOST_ACCESS_INSTALL_ROOT -u PYTHONPATH -u PYTHONHOME \
  PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory \
  GIT_CONFIG_VALUE_0=/Users/benque/MyDocs/AISoftPlatform \
  /bin/bash /Users/benque/MyDocs/AISoftPlatform/codex/install-host-access-broker.sh > "$EVID/manual-p5-installer.txt" 2>&1
"$PY" -B "$CHECK" installed > "$EVID/manual-p5-installed.json"
/usr/bin/cmp "$EVID/manual-p1-installed.json" "$EVID/manual-p5-installed.json"
"$PY" -B "$CHECK" qualified > "$EVID/manual-p5-qualified.json"
/bin/date -u +%Y-%m-%dT%H:%M:%SZ > "$EVID/manual-window-end-utc.txt"
```

owner独立检查以上所有JSON和日志；之后结束协调窗口，恢复其他调用者使用共享工具。
本session再运行既有checker的broker-only focused方法（和本轮 `focused-drift.json` 相同函数），不把其他7面纳入安装。
如果P5失败，同窗口再次完整restore并STOP，不能报最终新版一致。

## 非敏感回执与接续

只回传下列字段/文件路径，不发密码、env/profile、credential、auth或完整process环境：

```json
{
  "issue": "admin/aisoft-platform#362",
  "operator": "human:benque",
  "source_pin": "06afadfca2a950ad6ebee4b90a22e9d950bc72fa",
  "window_start_utc": "实际值",
  "window_end_utc": "实际值或未结束",
  "shared_tool_users_coordinated": "本人实际确认的参与者与避让结果",
  "snapshot_path": "本窗口exact路径",
  "snapshot_sha256": "manual-snapshot-verified.json中的实际值",
  "p0_snapshot": "PASS/FAIL/NOT RUN",
  "p1_installed": "PASS/FAIL/NOT RUN",
  "p2_qualification": "PASS/FAIL/NOT RUN",
  "p3_noop_and_full_compare": "PASS/FAIL/NOT RUN",
  "p4_restore_full_compare_old_negative": "PASS/FAIL/NOT RUN",
  "p5_reinstall_and_qualification": "PASS/FAIL/NOT RUN",
  "current_state": "old-baseline/new-pin/mixed-unknown",
  "failed_command_and_exit": "无或exact命令阶段/exit",
  "snapshot_retained": true,
  "evidence_directory": "本卡EVID"
}
```

此格式目前未填写，不代表任何阶段通过。执行者保留全部 `manual-*.json/txt` 公开回执；本session独立读回再更新verification/localHEAD。
若本人只完成认证而未执行系统命令，清楚写 `system_write=0`，不能称snapshot/安装/restore已做。
本票不再请求整包开始批准；最终文档PR需完整结果后一次manual确认，人工merge。
