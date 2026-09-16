#!/usr/bin/python3 -B
"""Call one public runtime operation from the exact disposable source snapshot."""
import argparse
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'runtime'))
from aisoft_release.docker import DockerAdapter
from aisoft_release.errors import ReleaseError
from aisoft_release.runner import ReleaseRuntime

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=('verify-artifact', 'verify-target', 'stage', 'migrate', 'activate', 'status', 'rollback'))
parser.add_argument('--release-id', required=True)
parser.add_argument('--profile', type=Path)
parser.add_argument('--release-root', type=Path)
args = parser.parse_args()
runtime = ReleaseRuntime(DockerAdapter(str(root / 'docker-wrapper.py'), compatibility_path=root / 'candidate-matrix.json'))
try:
    operation = getattr(runtime, args.action.replace('-', '_'))
    target = args.release_root if args.action == 'verify-artifact' else args.profile
    result = operation(target, args.release_id)
except ReleaseError as exc:
    result = {'ok': False, 'error_code': exc.code, 'message': exc.safe_message}
    if isinstance(exc.__cause__, ReleaseError):
        result['cause'] = {'error_code': exc.__cause__.code, 'message': exc.__cause__.safe_message}
print(json.dumps(result, sort_keys=True))
