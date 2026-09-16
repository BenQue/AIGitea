#!/usr/bin/env bash
set -euo pipefail
side="${1:?producer or consumer required}"
registry="${2:?exact Registry address required}"
[[ "$registry" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:5296$ ]] || exit 2
case "$side" in
  producer) engine=29.7.1; compose=5.1.4; snapshotter=true ;;
  consumer) engine=28.1.1; compose=2.35.1; snapshotter=false ;;
  *) exit 2 ;;
esac
[[ "$(cat /etc/aisoft-296-owner)" =~ ^issue296:[a-f0-9]{32}:$side$ ]] || exit 3
[[ ! -e /usr/local/bin/dockerd && ! -e /etc/docker/daemon.json ]] || exit 4
python3 -B - "$side" <<'PY'
import hashlib,json,pathlib,sys,tarfile
side=sys.argv[1]
root=pathlib.Path('/mnt/aisoft296')
for item in json.loads((root/'software-lock.json').read_text())['artifacts']:
    if item['id'].endswith('-'+side):
        path=root/item['filename']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        if item['id'].startswith('engine-'):
            with tarfile.open(path) as archive:
                for member in archive.getmembers():
                    assert member.name.startswith('docker/') and '..' not in pathlib.PurePosixPath(member.name).parts
                    assert member.isfile() or member.isdir()
PY
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq iptables curl ca-certificates
install -d -m 0755 /usr/local/lib/docker/cli-plugins /etc/docker /opt/aisoft-296
# Static Docker distribution includes its matching containerd/runc binaries.
tar -xzf "/mnt/aisoft296/docker-$engine.tgz" -C /opt/aisoft-296
install -m 0755 /opt/aisoft-296/docker/* /usr/local/bin/
install -m 0755 "/mnt/aisoft296/docker-compose-$compose" /usr/local/lib/docker/cli-plugins/docker-compose
cat > /etc/docker/daemon.json <<EOF
{"data-root":"/var/lib/aisoft-296-$side","exec-root":"/run/aisoft-296-$side","hosts":["unix:///run/aisoft-296.sock"],"features":{"containerd-snapshotter":$snapshotter},"insecure-registries":["$registry"],"userland-proxy":false}
EOF
# Plain HTTP is allowed only for this exact task-owned Registry endpoint.
cat > /etc/systemd/system/aisoft-296-docker.service <<'EOF'
[Unit]
Description=Issue 296 disposable Docker daemon
After=network-online.target
[Service]
ExecStart=/usr/local/bin/dockerd --config-file=/etc/docker/daemon.json
Restart=no
Delegate=yes
KillMode=process
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl start aisoft-296-docker.service
for _ in $(seq 1 30); do
  if /usr/local/bin/docker --host unix:///run/aisoft-296.sock info >/dev/null 2>&1; then exit 0; fi
  sleep 1
done
exit 5
