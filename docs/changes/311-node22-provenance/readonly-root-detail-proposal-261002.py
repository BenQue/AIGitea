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

# symlink 覆盖只用 metadata 归并到已扫描的普通 systemd 文件，不读取外部目标。
allowed = [Path(p).resolve() for p in ('/etc/systemd/system', '/usr/lib/systemd/system',
                                     '/lib/systemd/system', '/run/systemd/system')]
ordinary = set()
links = set()
for base in allowed:
    if base.exists():
        for suffix in ('*.service', '*.socket', '*.timer', '*.path', '*.target', '*.conf'):
            for path in base.rglob(suffix):
                if re.search(r'secret|token|password|credential|auth', path.name, re.I):
                    continue
                if path.is_symlink():
                    links.add(path)
                elif path.is_file():
                    ordinary.add(path.resolve())
for path in sorted(links):
    target = path.resolve(strict=False)
    same_scope = any(target.is_relative_to(base) for base in allowed)
    emit('unit-link-coverage', path=str(path), target=str(target),
         aliases_scanned_ordinary_file=same_scope and target in ordinary,
         outside_unit_roots=not same_scope, target_exists=target.exists())

emit('detail-boundary', effective_process_environment='excluded', dynamic_profile_execution='excluded',
     secret_files='not-read', runtime_mutation='none')
