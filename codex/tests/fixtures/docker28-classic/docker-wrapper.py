#!/usr/bin/python3 -B
"""Exact task daemon adapter plus logged read-only capability fault injection."""
import json
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
args = sys.argv[1:]
with (root / 'docker-calls.jsonl').open('a') as stream:
    stream.write(json.dumps(args) + '\n')
mode = (root / 'docker-mode').read_text().strip()
if mode not in ('normal', 'wrong-engine', 'wrong-compose', 'wrong-store'):
    raise SystemExit(96)
if mode == 'wrong-engine' and args[:2] == ['version', '--format']:
    print(json.dumps({'Version': '28.1.2', 'Os': 'linux', 'Arch': 'amd64'}))
elif mode == 'wrong-compose' and args[:3] == ['compose', 'version', '--short']:
    print('2.35.2')
elif mode == 'wrong-store' and args == ['info', '--format', '{{.Driver}}']:
    print('overlayfs')
elif mode == 'wrong-store' and args == ['info', '--format', '{{json .DriverStatus}}']:
    print(json.dumps([['driver-type', 'io.containerd.snapshotter.v1']]))
else:
    os.execv('/usr/local/bin/docker', ['docker', '--host', 'unix:///run/aisoft-296.sock', *args])
