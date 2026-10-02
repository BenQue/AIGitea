#!/usr/bin/env python3
"""Fixed helper build; never installs a binary or accesses Gitea configuration."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


def run(go, args, env):
    return subprocess.check_output([str(go), *args], cwd=ROOT, env=env)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--go', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    lock = json.loads((ROOT / 'build-lock.json').read_text())
    env = {**os.environ, 'GOTOOLCHAIN': 'local', 'GOENV': 'off', 'GOWORK': 'off',
           'GOFLAGS': '', 'CGO_ENABLED': '1'}
    version = run(args.go, ['version'], env).decode().split()
    if len(version) != 4 or version[2] != lock['version']:
        raise SystemExit('TOOLCHAIN_PIN_MISMATCH')
    module = json.loads(run(args.go, ['list', '-mod=readonly', '-m', '-json',
                                    lock['gitea']['module']], env))
    pin = lock['gitea']
    if module.get('Version') != pin['version'] or module.get('Sum') != pin['module_sum'] or 'Replace' in module:
        raise SystemExit('MODEL_PIN_MISMATCH')
    model = Path(module['Dir']) / pin['model_path']
    if hashlib.sha256(model.read_bytes()).hexdigest() != pin['model_sha256']:
        raise SystemExit('MODEL_BYTES_MISMATCH')
    run(args.go, ['mod', 'verify'], env)
    run(args.go, ['test', '-mod=readonly', '-tags', 'sqlite,sqlite_unlock_notify', './...'], env)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    run(args.go, ['build', '-mod=readonly', '-trimpath', '-tags', 'sqlite,sqlite_unlock_notify',
                  '-ldflags=-buildid=', '-o', str(output), '.'], env)
    evidence = {'schema': 'aisoft-gitea-pat-helper-build/v1',
                'toolchain': version[2], 'platform': version[3], 'gitea': pin,
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
