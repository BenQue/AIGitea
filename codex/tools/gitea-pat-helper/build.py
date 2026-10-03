#!/usr/bin/env python3
"""Fixed helper build; never installs a binary or accesses Gitea configuration."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent


def run(go, args, env):
    return subprocess.check_output([str(go), *args], cwd=ROOT, env=env)


def pinned_model_source(go, env, pin):
    module = json.loads(run(go, ['list', '-mod=readonly', '-m', '-json', pin['module']], env))
    expected = {'Path': pin['module'], 'Version': pin['version'], 'Sum': pin['module_sum']}
    if any(module.get(key) != value for key, value in expected.items()) or 'Replace' in module:
        raise SystemExit('MODEL_PIN_MISMATCH')
    inputs = {name: (ROOT / name).read_bytes() for name in ('go.mod', 'go.sum')}
    # go list reports the selected graph; a cold cache need not have its Dir.
    downloaded = json.loads(run(go, ['mod', 'download', '-json',
                                    pin['module'] + '@' + pin['version']], env))
    if any((ROOT / name).read_bytes() != value for name, value in inputs.items()):
        raise SystemExit('MODULE_INPUTS_CHANGED')
    if downloaded.get('Error') or any(downloaded.get(key) != value for key, value in expected.items()):
        raise SystemExit('MODEL_PIN_MISMATCH')
    directory = downloaded.get('Dir')
    if not isinstance(directory, str) or not Path(directory).is_absolute():
        raise SystemExit('MODEL_SOURCE_UNAVAILABLE')
    model = Path(directory) / pin['model_path']
    if hashlib.sha256(model.read_bytes()).hexdigest() != pin['model_sha256']:
        raise SystemExit('MODEL_BYTES_MISMATCH')
    return model



def verify_toolchain(go, archive, lock):
    """Bind the actual GOROOT bytes to an official checksum-verified archive."""
    pins = [item for item in lock['files'] if item['filename'] == archive.name]
    if len(pins) != 1 or hashlib.sha256(archive.read_bytes()).hexdigest() != pins[0]['sha256']:
        raise SystemExit('TOOLCHAIN_ARCHIVE_MISMATCH')
    go = go.resolve(strict=True)
    root = go.parent.parent
    if go != root / 'bin' / 'go':
        raise SystemExit('TOOLCHAIN_PATH_MISMATCH')
    expected = set()
    tree_hash = hashlib.sha256()
    with tarfile.open(archive) as packed:
        for member in packed:
            relative = Path(member.name)
            if not relative.parts or relative.parts[0] != 'go' or '..' in relative.parts:
                raise SystemExit('TOOLCHAIN_ARCHIVE_UNSAFE')
            if member.isdir():
                continue
            if not member.isfile():
                raise SystemExit('TOOLCHAIN_ARCHIVE_UNSAFE')
            relative = Path(*relative.parts[1:])
            target = root / relative
            if relative in expected or target.is_symlink() or not target.is_file():
                raise SystemExit('TOOLCHAIN_BYTES_MISMATCH')
            expected.add(relative)
            expected_hash = hashlib.sha256(packed.extractfile(member).read()).digest()
            if hashlib.sha256(target.read_bytes()).digest() != expected_hash:
                raise SystemExit('TOOLCHAIN_BYTES_MISMATCH')
            tree_hash.update(str(relative).encode() + b'\0' + expected_hash)
    actual = set()
    for target in root.rglob('*'):
        if target.is_symlink():
            raise SystemExit('TOOLCHAIN_BYTES_MISMATCH')
        if target.is_file():
            actual.add(target.relative_to(root))
    if actual != expected:
        raise SystemExit('TOOLCHAIN_BYTES_MISMATCH')
    return root, {'filename': pins[0]['filename'], 'sha256': pins[0]['sha256'],
                  'extracted_tree_sha256': tree_hash.hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--go', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--toolchain-archive', type=Path, required=True)
    args = parser.parse_args()
    lock = json.loads((ROOT / 'build-lock.json').read_text())
    tool_root, tool_evidence = verify_toolchain(args.go, args.toolchain_archive, lock)
    env = {**os.environ, 'GOROOT': str(tool_root), 'GOTOOLCHAIN': 'local', 'GOENV': 'off', 'GOWORK': 'off',
           'GOFLAGS': '', 'CGO_ENABLED': '1'}
    version = run(args.go, ['version'], env).decode().split()
    if len(version) != 4 or version[2] != lock['version']:
        raise SystemExit('TOOLCHAIN_PIN_MISMATCH')
    pin = lock['gitea']
    pinned_model_source(args.go, env, pin)
    run(args.go, ['mod', 'verify'], env)
    run(args.go, ['test', '-mod=readonly', '-tags', 'sqlite,sqlite_unlock_notify', './...'], env)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    run(args.go, ['build', '-mod=readonly', '-trimpath', '-tags', 'sqlite,sqlite_unlock_notify',
                  '-ldflags=-buildid=', '-o', str(output), '.'], env)
    evidence = {'schema': 'aisoft-gitea-pat-helper-build/v1',
                'toolchain': version[2], 'toolchain_input': tool_evidence, 'platform': version[3], 'gitea': pin,
                'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                'go_mod_sha256': hashlib.sha256((ROOT / 'go.mod').read_bytes()).hexdigest(),
                'go_sum_sha256': hashlib.sha256((ROOT / 'go.sum').read_bytes()).hexdigest(),
                'build_info': run(args.go, ['version', '-m', str(output)], env).decode(),
                'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                'source_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)),
                'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(ROOT.glob('*.go'))}}
    output.with_name(output.name + '.provenance.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({'result': 'PASS', 'sha256': evidence['sha256'], 'platform': version[3]}))


if __name__ == '__main__':
    main()
