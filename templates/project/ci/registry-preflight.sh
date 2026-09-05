#!/usr/bin/env bash
# npm registry 存活断言（AISoft 平台 Issue #201）。
#
# 在依赖安装之前，对 NPM_CONFIG_REGISTRY 指向的 registry 做一次**真实取包**。
#
# 为什么需要它：2026-08-24 起 gitea-ci 上的 Verdaccio 停止监听 4873 约 28 小时，
# 期间任何需要下载缓存外新包的 CI 都以 ECONNREFUSED 失败，而只用既有依赖的 CI
# 仍然 20 秒全绿——npm ci 命中 runner 的 _cacache 时根本不发起网络请求。
# 故障因此静默潜伏，只在某个倒霉的 PR 恰好引入新依赖时才炸。
#
# 这一步就是把那个藏身处拆掉：它每次都真的连一次 registry，所以故障期间的
# **每一次** CI 运行都会红，而不是等某个 PR 撞上。
#
# 断言穿透两层假绿，因此这两样它一个都不用：
#   - 不读 npm 缓存：全程 curl，不经 npm、不经 _cacache。
#   - 不问进程管理器：pm2 曾把已死的 Verdaccio 显示为 online（pid N/A、内存 0b、
#     error log 为空）。只有真的取到包才算活着。
# 同理它也不是探端口——端口开着而 registry 不能供包，仍然是 CI 停摆。
#
# 失败绝不回退到直连 npmjs。那会同时抹掉离线安装能力和这条故障的可见性，
# 是本 Issue 明确不做的事。
#
# 不解析 JSON：tarball 路径由 registry/包名/版本三者拼出来，是确定的。
# 这样脚本在任何最小 CI 镜像里都能跑，不依赖 python3、jq 或 node。
set -euo pipefail

MARK_OK='AISOFT_REGISTRY_PREFLIGHT_OK'
MARK_FAIL='AISOFT_REGISTRY_PREFLIGHT_FAIL'

REGISTRY="${REGISTRY_PREFLIGHT_REGISTRY:-${NPM_CONFIG_REGISTRY:-}}"
# 默认探测包取 fflate 0.8.3：它正是 admin/LocalWMS run 652 首次暴露本故障时
# 卡住的那个 tarball，2026-09-05 实测该 registry 上有 58 个版本。
PACKAGE="${REGISTRY_PREFLIGHT_PACKAGE:-fflate}"
VERSION="${REGISTRY_PREFLIGHT_VERSION:-0.8.3}"
TIMEOUT="${REGISTRY_PREFLIGHT_TIMEOUT:-20}"

# 失败时先打标记再打原因：日志检索按标记走，人按原因走。
fail() {
  stage="$1"
  shift
  echo "$MARK_FAIL stage=$stage registry=${REGISTRY:-<unset>} package=$PACKAGE@$VERSION" >&2
  for line in "$@"; do
    echo "[registry-preflight] $line" >&2
  done
  exit 1
}

if [ -z "$REGISTRY" ]; then
  fail config \
    'NPM_CONFIG_REGISTRY 没有设置，本步骤无法判断该断言哪个 registry。' \
    '这一步不猜、也不回退到 npmjs：请在 workflow 的 env 里显式设置它。'
fi

# 去掉结尾斜杠，避免拼出 //package 这种路径。
REGISTRY="${REGISTRY%/}"

# 结果经全局 HTTP_CODE / CURL_STATUS 带出，调用方**不能**写成命令替换：
# $(...) 起子 shell，函数里的赋值出不来，而 curl 的退出码正是这里要判的东西。
http_get() {
  set +e
  HTTP_CODE="$(curl -sS --max-time "$TIMEOUT" --retry 0 -o "$2" -w '%{http_code}' "$1" 2>/dev/null)"
  CURL_STATUS=$?
  set -e
}

# curl 的连接类退出码。这一类是本 Issue 的故障签名，单独成一个 stage，
# 因为它的排查方向与「registry 活着但供不了包」完全相反。
connect_failure() {
  case "$1" in
    6 | 7 | 28 | 35 | 56) return 0 ;;
    *) return 1 ;;
  esac
}

body="$(mktemp)"
trap 'rm -f "$body"' EXIT

# 第一段：packument。证明 registry 在监听、并且能回答包元数据。
http_get "$REGISTRY/$PACKAGE" "$body"
if connect_failure "$CURL_STATUS"; then
  fail connect \
    "连不上 $REGISTRY（curl 退出码 $CURL_STATUS）。" \
    '这是「那个端口上没有任何进程在监听」，不是「拉不到上游」。' \
    '不要往 uplink 配置、npmmirror 可达性或网络策略方向排查——' \
    'Verdaccio 活着但代理不到上游会是 404 或 5xx，不是连接被拒。' \
    '判活三件套（缺一不可）：pm2 describe 的 pid 是真实数字而不是 N/A；' \
    'ss -lntp 有 4873 的 LISTEN；以及一次真实取包成功。' \
    '只看 pm2 的 online 会被假绿骗过，见平台文档 06 踩坑集。'
fi
if [ "$CURL_STATUS" -ne 0 ]; then
  fail transport "curl 以退出码 $CURL_STATUS 失败，registry=$REGISTRY。"
fi
if [ "$HTTP_CODE" != "200" ]; then
  fail http \
    "取 $REGISTRY/$PACKAGE 返回 HTTP $HTTP_CODE，期望 200。" \
    'registry 在监听但没有正常回答。这一类才该往 uplink、存储或包本身的方向查。'
fi
if ! grep -q '"dist-tags"' "$body" || ! grep -q '"versions"' "$body"; then
  fail packument \
    "取 $REGISTRY/$PACKAGE 返回了 HTTP 200，但响应体不是 packument。" \
    '缺少 dist-tags 或 versions 字段——多半是代理、登录页或错误页顶替了 registry。' \
    "响应体前 200 字节：$(head -c 200 "$body" | tr '\n' ' ')"
fi

# 第二段：tarball。packument 能取到不代表包体能下载，而 npm ci 真正要的是后者。
tarball="$REGISTRY/$PACKAGE/-/$PACKAGE-$VERSION.tgz"
http_get "$tarball" /dev/null
if connect_failure "$CURL_STATUS"; then
  fail connect \
    "packument 取到了，但取 tarball 时连不上（curl 退出码 $CURL_STATUS）。" \
    '两次请求之间 registry 掉了，或存在同端口的野生进程。'
fi
if [ "$CURL_STATUS" -ne 0 ]; then
  fail transport "取 tarball 时 curl 以退出码 $CURL_STATUS 失败：$tarball"
fi
if [ "$HTTP_CODE" != "200" ]; then
  fail tarball \
    "取 $tarball 返回 HTTP $HTTP_CODE，期望 200。" \
    'registry 能回答元数据但供不了包体；npm ci 会在这一步失败。' \
    "若该版本已不存在，用 REGISTRY_PREFLIGHT_PACKAGE 与 REGISTRY_PREFLIGHT_VERSION 换一个探测包。"
fi

echo "$MARK_OK registry=$REGISTRY package=$PACKAGE@$VERSION"
echo '[registry-preflight] packument 与 tarball 均真实取到，未经 npm 缓存。'
