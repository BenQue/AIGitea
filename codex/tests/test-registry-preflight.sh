#!/usr/bin/env bash
# templates/project/ci/registry-preflight.sh 的路径覆盖与负向验证（Issue #201）。
#
# 负向验证靠起停一个替身 registry 完成，不靠清空 npm 缓存：后者验的是另一件事
# （缓存有没有命中），而本断言要证明的是「registry 到底还在不在供包」。
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT/templates/project/ci/registry-preflight.sh"
FAKE="$ROOT/codex/tests/fake-npm-registry.py"
TMP="$(mktemp -d)"
SERVER_PID=''

cleanup() {
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
  rm -rf "$TMP"
}
trap cleanup EXIT

fail() {
  echo "registry-preflight test: $1" >&2
  exit 1
}

# 先占一次 0 号端口拿一个空闲端口再放掉。整个测试固定用这一个端口，
# 「停掉再起回来」才落在同一个地址上，与生产故障的形状一致。
PORT="$(python3 -c 'import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()')"
REGISTRY="http://127.0.0.1:$PORT"

start_registry() {
  python3 "$FAKE" "$1" "$PORT" &
  SERVER_PID=$!
  for _ in $(seq 1 50); do
    if curl -sS -o /dev/null --max-time 2 "$REGISTRY/fflate" 2>/dev/null; then
      return 0
    fi
    sleep 0.1
  done
  fail "替身 registry（mode=$1）没有在超时内起来"
}

stop_registry() {
  [ -n "$SERVER_PID" ] || return 0
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  SERVER_PID=''
  for _ in $(seq 1 50); do
    if ! curl -sS -o /dev/null --max-time 2 "$REGISTRY/fflate" 2>/dev/null; then
      return 0
    fi
    sleep 0.1
  done
  fail '替身 registry 没有在超时内停掉'
}

run_probe() {
  # 回显合并后的输出，退出码写进 PROBE_STATUS。
  set +e
  PROBE_OUTPUT="$(NPM_CONFIG_REGISTRY="$REGISTRY" REGISTRY_PREFLIGHT_TIMEOUT=5 \
    bash "$SCRIPT" 2>&1)"
  PROBE_STATUS=$?
  set -e
  printf '%s' "$PROBE_OUTPUT"
}

expect_pass() {
  run_probe >"$TMP/out"
  [ "$PROBE_STATUS" -eq 0 ] || fail "$1：期望退出 0，实际 $PROBE_STATUS"
  grep -Fq 'AISOFT_REGISTRY_PREFLIGHT_OK' "$TMP/out" \
    || fail "$1：缺少成功标记"
  grep -Fq 'AISOFT_REGISTRY_PREFLIGHT_FAIL' "$TMP/out" \
    && fail "$1：成功路径不应打印失败标记"
  return 0
}

expect_fail_stage() {
  run_probe >"$TMP/out"
  [ "$PROBE_STATUS" -eq 1 ] || fail "$2：期望退出 1，实际 $PROBE_STATUS"
  grep -Fq "AISOFT_REGISTRY_PREFLIGHT_FAIL stage=$1" "$TMP/out" \
    || fail "$2：期望 stage=$1，实际输出为 $(head -1 "$TMP/out")"
  grep -Fq 'AISOFT_REGISTRY_PREFLIGHT_OK' "$TMP/out" \
    && fail "$2：失败路径不应打印成功标记"
  return 0
}

# 1. 健康路径。
start_registry healthy
expect_pass '健康 registry'

# 2. 负向验证：停掉服务，同一条命令必须变红，且落在 connect 这一 stage 上。
#    这就是 2026-08 那次故障在断言层面的形状。
stop_registry
expect_fail_stage connect '停掉 registry 之后'
grep -Fq '不要往 uplink 配置' "$TMP/out" \
  || fail '连接被拒的结论必须显式排除 uplink 方向'
grep -Fq 'pm2' "$TMP/out" \
  || fail '连接被拒的结论必须给出不依赖 pm2 online 的判活方法'

# 3. 恢复后复绿。绿-红-绿三段齐了，才算证明这条断言真的在读服务状态。
start_registry healthy
expect_pass '恢复 registry 之后'
stop_registry

# 4. registry 在监听但 packument 返回 5xx。
start_registry http500
expect_fail_stage http 'packument 返回 500'
stop_registry

# 5. HTTP 200 但响应体不是 packument。
start_registry notpackument
expect_fail_stage packument '响应体不是 packument'
stop_registry

# 6. packument 正常但 tarball 取不到。npm ci 真正要的是包体。
start_registry tarball404
expect_fail_stage tarball 'tarball 返回 404'
stop_registry

# 7. 没有 registry 配置时不猜、不回退到 npmjs。
set +e
unset_output="$(env -u NPM_CONFIG_REGISTRY -u REGISTRY_PREFLIGHT_REGISTRY \
  bash "$SCRIPT" 2>&1)"
unset_status=$?
set -e
[ "$unset_status" -eq 1 ] || fail "未设置 registry：期望退出 1，实际 $unset_status"
grep -Fq 'AISOFT_REGISTRY_PREFLIGHT_FAIL stage=config' <<<"$unset_output" \
  || fail '未设置 registry 时应落在 config stage'

# 8. 断言本身不得依赖 npm、npm 缓存或进程管理器——那正是被它穿透的两层假绿。
# 只拦「作为命令调用」：在失败提示里提到 npm ci 或 pm2 是本断言的价值所在，
# 拦掉它反而会逼着把结论写模糊。
if rg -n '^[[:space:]]*(npm|pm2|systemctl|service|node|jq)\b' "$SCRIPT"; then
  fail '断言正文不得调用 npm、进程管理器或额外运行时'
fi
if rg -ni '_cacache|npm[- ]cache' "$SCRIPT" | rg -v ':[[:space:]]*#'; then
  fail '断言不得读取 npm 缓存'
fi
if rg -n 'registry\.npmjs\.org' "$SCRIPT"; then
  fail '断言不得回退到直连 npmjs'
fi

echo 'registry preflight tests passed'
