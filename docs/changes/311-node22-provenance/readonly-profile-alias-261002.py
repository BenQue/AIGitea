"""#311 待合同启动批准的 root 补读；仅必要静态字段，无 Secret/环境/argv。"""
import json
import os
from pathlib import Path
import pwd
import re

if os.uname().nodename != 'gitea-ci' or os.geteuid() != 0:
    raise SystemExit('exact gitea-ci/root required')


def emit(kind, **fields):
    print(json.dumps(dict(kind=kind, **fields), sort_keys=True))


def fields(path, category):
    if not path.exists():
        emit('detail-file', path=str(path), category=category, exists=False)
        return
    if path.is_symlink():
        emit('detail-gap', path=str(path), reason='symlink-not-read')
        return
    refs = []
    paths = []
    env_blocks = []
    try:
        with path.open(encoding='utf-8') as stream:
            for n, line in enumerate(stream, 1):
                left = line.split('=', 1)[0].split(':', 1)[0]
                if re.search(r'secret|token|password|credential|auth|private.?key', left, re.I):
                    continue
                comment = line.lstrip().startswith('#')
                if re.search(r'/opt/node22(?:/|\b)|\bnode22\b', line):
                    refs.append({'line': n, 'comment': comment})
                if line.strip() == 'envs:':
                    env_blocks.append(n)
                # Environment=PATH= 和 Environment="PATH= 都允许；不解析其它环境变量。
                match = re.search(r'\bPATH\s*(?:=|:)\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\']+))', line)
                if match and not comment:
                    value = next((x for x in match.groups() if x is not None), '')
                    paths.append({'line': n, 'has_node22': '/opt/node22/bin' in value.split(':'),
                                  'dynamic': '$' in value or '`' in value,
                                  'known_home_prefix': value in ('$HOME/bin:$PATH', '$HOME/.local/bin:$PATH'),
                                  'static_literal_paths': [v for v in value.split(':') if re.fullmatch(r'/[A-Za-z0-9_./+-]+', v)],
                                  'inherits_path': any(v in ('$PATH', '${PATH}') for v in value.split(':')),
                                  'unknown_parts': sum(not (v in ('$PATH', '${PATH}', '$HOME/bin', '$HOME/.local/bin') or re.fullmatch(r'/[A-Za-z0-9_./+-]+', v)) for v in value.split(':')),
                                  'absolute_segments_only': bool(value) and all(x.startswith('/') for x in value.split(':'))})
        emit('detail-file', path=str(path), category=category, exists=True,
             node22_references=refs, path_assignments=paths, envs_line_numbers=env_blocks)
    except (OSError, UnicodeError) as error:
        emit('detail-gap', path=str(path), reason=type(error).__name__)


for name in ('/etc/systemd/system/act_runner.service',
             '/etc/systemd/system/act_runner.service.d/10-config.conf',
             '/run/systemd/system/service.d/zzz-lxc-service.conf',
             '/opt/act-runner/config.yaml'):
    fields(Path(name), 'effective-runner-unit-or-config')
home = Path(pwd.getpwnam('gitea-runner').pw_dir)
emit('runner-home', path=str(home))
for name in ('.profile', '.bash_profile', '.bashrc'):
    fields(home / name, 'runner-static-profile-not-sourced')
for path in (home / 'bin', home / '.local/bin'):
    emit('runner-profile-bin', path=str(path), exists=path.exists(),
         symlink=path.is_symlink(), target=str(path.resolve(strict=False)),
         target_is_node22=str(path.resolve(strict=False)).startswith('/opt/node22/'))


for value in ('/etc/profile.d/000-orbstack.sh', '/etc/profile.d/70-systemd-shell-extra.sh', '/etc/profile.d/80-systemd-osc-context.sh', '/etc/profile.d/999-orbstack.sh'):
    link=Path(value)
    target=link.resolve(strict=True)
    info=target.stat()
    if not target.is_file() or info.st_uid != 0 or not info.st_mode & 0o004 or str(target) not in ('/opt/orbstack-guest/etc/profile-early', '/opt/orbstack-guest/etc/profile-late', '/usr/lib/systemd/profile.d/70-systemd-shell-extra.sh', '/usr/lib/systemd/profile.d/80-systemd-osc-context.sh'):
        raise SystemExit('public profile alias identity mismatch')
    if not any(str(target).startswith(p) for p in ('/usr/lib/systemd/', '/opt/orbstack-guest/', '/opt/orbstack/')):
        raise SystemExit('unexpected system profile alias target; stop')
    emit('profile-link', path=value, target=str(target), root_owned_public_shell=True)
    fields(target, 'public-system-profile-alias-fields-only')
