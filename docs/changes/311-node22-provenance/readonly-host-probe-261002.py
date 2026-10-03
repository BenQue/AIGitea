"""#311 待授权的固定主机只读探针；禁止独立直接运行，见相邻 readonly-request。

不调用 shell、不 source profile、不打开 .env/auth/credential、registration 或日志；
只返回 marker allowlist、工具链元数据和 node22 引用位置/布尔值。
权限失败与动态 PATH 写成 gap，不能解释成无消费方。未新增 broker 能力。
"""
import datetime
import hashlib
import json
import os
import pathlib
import pwd
import re
import stat
import subprocess

ROOT = pathlib.Path('/opt/node22')
NEEDLE = re.compile(r'/opt/node22(?:/|\b)|\bnode22\b')
SECRET = re.compile(r'secret|token|password|credential|auth|private.?key', re.I)
gaps = []


def emit(kind, **fields):
    print(json.dumps(dict(kind=kind, **fields), ensure_ascii=False, sort_keys=True))


def scan(path, category):
    """逐行只投影引用与行号；匹配 Secret 字段时不检查/输出值。"""
    try:
        if path.is_symlink():
            gaps.append(dict(path=str(path), reason='symlink-content-not-read'))
            return
        refs = []
        paths = []
        with path.open(encoding='utf-8') as stream:
            for number, line in enumerate(stream, 1):
                if SECRET.search(line.split('=', 1)[0].split(':', 1)[0]):
                    continue
                stripped = line.strip()
                if NEEDLE.search(line):
                    refs.append(dict(line=number, comment=stripped.startswith('#')))
                # 不输出完整 PATH/env 行；只确认是否能静态解析和 node22 布尔值。
                if re.search(r'(?:^|[\s"\'])PATH=', line):
                    match = re.search(r'PATH=([\w/.:${}+-]+)', line)
                    value = match.group(1) if match else ''
                    paths.append(dict(line=number, has_node22=bool(NEEDLE.search(value)),
                                      dynamic=not value or '$' in value))
        emit('config-scan', path=str(path), category=category, node22_references=refs,
             path_assignments=paths)
    except (OSError, UnicodeError) as error:
        gaps.append(dict(path=str(path), reason=type(error).__name__))


emit('scope', issue=311, observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
     hostname=os.uname().nodename, uid=os.getuid(),
     secret_files='not-read', runtime_mutation='none',
     process_environment='not-read', coverage='fixed scopes; no proof of global non-use')
if os.uname().nodename != 'gitea-ci':
    raise SystemExit('target mismatch: gitea-ci required')
try:
    info = ROOT.lstat()
    emit('runtime-directory', path=str(ROOT), exists=True, symlink=stat.S_ISLNK(info.st_mode),
         uid=info.st_uid, gid=info.st_gid, mode=oct(stat.S_IMODE(info.st_mode)),
         mtime_is_install_date=False, mtime=info.st_mtime,
         marker_exists=(ROOT / '.aisoft-runtime-source').exists())
    if not stat.S_ISDIR(info.st_mode):
        raise SystemExit('runtime target is not a real directory')
    node = ROOT / 'bin/node'
    if not node.resolve().is_relative_to(ROOT):
        raise SystemExit('node executable escapes runtime directory')
    digest = hashlib.file_digest(node.open('rb'), 'sha256').hexdigest()
    output = subprocess.run([str(node), '--version'], capture_output=True, text=True,
                            timeout=10, check=True).stdout.strip()
    emit('node', path=str(node), sha256_observed_binary=digest,
         version=output if re.fullmatch(r'v\d+\.\d+\.\d+', output) else 'invalid-version')
    # 不执行 npm/pnpm/corepack：版本命令也可能触发 cache/bootstrap 写入。
    for tool in ('npm', 'pnpm', 'corepack'):
        package = ROOT / 'lib/node_modules' / tool / 'package.json'
        if package.is_file() and package.resolve().is_relative_to(ROOT):
            data = json.loads(package.read_text())
            version = data.get('version', '')
            emit('package-version', path=str(package), package=tool,
                 version=version if re.fullmatch(r'[\w.+-]{1,64}', version) else 'unknown')
        else:
            emit('package-version', package=tool, version='not-at-fixed-package-path')
except FileNotFoundError:
    gaps.append(dict(path=str(ROOT), reason='missing-path'))

marker_keys = {'contract', 'installed_at', 'installed_by', 'node_version', 'node_source',
               'node_sha256', 'npm_version', 'npm_source', 'npm_sha1', 'npm_integrity',
               'pnpm_version', 'pnpm_source', 'rollback', 'inventory_at', 'recorded_at',
               'consumers'}
for directory in (ROOT, pathlib.Path('/opt/node24.18.0')):
    marker = directory / '.aisoft-runtime-source'
    if not marker.exists():
        emit('marker', path=str(marker), exists=False)
        continue
    if marker.is_symlink():
        gaps.append(dict(path=str(marker), reason='marker-symlink-not-read'))
        continue
    values = {}
    for line in marker.read_text().splitlines():
        key, sep, value = line.partition('=')
        if sep and key in marker_keys:
            # 已知 provenance 文本也先排除 credential-bearing URL/value。
            if SECRET.search(value) or re.search(r'https?://[^/]*@', value):
                gaps.append(dict(path=str(marker), reason='sensitive-marker-value-suppressed'))
                continue
            values[key] = value
    emit('marker', path=str(marker), exists=True, allowed_fields=values)

# systemctl 仅公开 unit 的身份、路径和 PID 元数据，不请求 Environment/ExecStart/log。
result = subprocess.run(['/usr/bin/systemctl', 'show', 'act_runner.service',
                         '-p', 'User', '-p', 'Group', '-p', 'FragmentPath',
                         '-p', 'DropInPaths', '-p', 'ExecMainPID'], capture_output=True,
                        text=True, timeout=15)
service = {}
if result.returncode == 0:
    service = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    emit('service-metadata', **service)
else:
    gaps.append(dict(path='act_runner.service', reason='systemctl-failed'))

files = set()
for base in ('/etc/systemd/system', '/usr/lib/systemd/system', '/lib/systemd/system'):
    directory = pathlib.Path(base)
    if directory.exists():
        for pattern in ('*.service', '*.socket', '*.timer', '*.path', '*.target', '*.conf'):
            files.update(directory.rglob(pattern))
for path in sorted(files):
    if not SECRET.search(path.name):
        scan(path, 'systemd')

profiles = [pathlib.Path('/etc/profile'), pathlib.Path('/etc/bash.bashrc')]
profile_dir = pathlib.Path('/etc/profile.d')
if profile_dir.exists():
    profiles.extend(sorted(profile_dir.glob('*.sh')))
try:
    home = pathlib.Path(pwd.getpwnam('gitea-runner').pw_dir)
    profiles.extend(home / basename for basename in ('.profile', '.bash_profile', '.bashrc'))
except KeyError:
    gaps.append(dict(path='gitea-runner', reason='user-not-found'))
for path in profiles:
    if path.exists() and not SECRET.search(path.name):
        scan(path, 'profile-static-only-not-sourced')
scan(pathlib.Path('/opt/act-runner/config.yaml'), 'runner-config')

# 枚举可读 process executable symlink，绝不读取 cmdline/environ。
count = 0
for process in pathlib.Path('/proc').iterdir():
    if process.name.isdigit():
        try:
            target = os.readlink(process / 'exe')
            if target.startswith('/opt/node22/'):
                emit('process-executable', pid=int(process.name), path=target)
                count += 1
        except (PermissionError, FileNotFoundError):
            continue
emit('process-summary', node22_executable_count=count,
     scope='readable exe symlinks only; process environments and argv excluded')
for base in ('/usr/bin', '/usr/local/bin', '/opt/act-runner'):
    directory = pathlib.Path(base)
    if directory.exists():
        try:
            entries = list(directory.iterdir())
        except OSError as error:
            gaps.append(dict(path=str(directory), reason=type(error).__name__))
            continue
        for path in entries:
            if path.is_symlink():
                target = str(path.resolve(strict=False))
                if target.startswith('/opt/node22/'):
                    emit('symlink-reference', path=str(path), target=target)
emit('coverage-gap', reason='effective process PATH and dynamic profile evaluation excluded to avoid Secret access')
emit('gaps', gaps=gaps)
