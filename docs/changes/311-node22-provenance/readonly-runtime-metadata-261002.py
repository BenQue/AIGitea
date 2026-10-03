"""#311 已批准验收范围的固定只读元数据；不读配置/凭据内容。"""
import hashlib
import json
import os
from pathlib import Path
import stat

if os.uname().nodename != 'gitea-ci' or os.geteuid() != 0:
    raise SystemExit('exact gitea-ci/root required')
root = Path('/opt/node22')
if not stat.S_ISDIR(root.lstat().st_mode):
    raise SystemExit('runtime must be real directory')
entries = []
for directory, dirs, files in os.walk(root, followlinks=False):
    for name in sorted(dirs + files):
        path = Path(directory) / name
        if path == root / '.aisoft-runtime-source':
            continue
        info = path.lstat()
        entries.append([str(path.relative_to(root)), info.st_mode, info.st_uid,
                        info.st_gid, info.st_size, info.st_mtime_ns,
                        os.readlink(path) if path.is_symlink() else None])
entries.sort()
stable = json.dumps(entries, separators=(',', ':'), ensure_ascii=True).encode()
config = []
for value in ('/etc/systemd/system/act_runner.service',
              '/etc/systemd/system/act_runner.service.d/10-config.conf',
              '/run/systemd/system/service.d/zzz-lxc-service.conf',
              '/opt/act-runner/config.yaml', '/opt/act-runner/.profile',
              '/opt/act-runner/.bashrc', '/opt/node24.18.0/.aisoft-runtime-source'):
    path = Path(value)
    info = path.lstat()
    config.append([value, info.st_mode, info.st_uid, info.st_gid, info.st_size, info.st_mtime_ns])
with (root / 'bin/node').open('rb') as stream:
    node_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
print(json.dumps({'issue': 311, 'runtime': str(root), 'marker_excluded': True,
                  'non_marker_entries': len(entries),
                  'non_marker_metadata_sha256': hashlib.sha256(stable).hexdigest(),
                  'node_binary_sha256': node_hash, 'config_metadata': config,
                  'secret_contents_read': False}, sort_keys=True))
