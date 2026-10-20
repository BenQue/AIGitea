#!/usr/bin/env bash
# #397: deployment failure / rollback notifier template. A fake curl on PATH
# records each request; nothing leaves this machine.
# shellcheck disable=SC2016 # backticks and $(...) below are literal test data
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
notify="$root/templates/project/ci/deploy-notify.sh"

mkdir "$test_root/bin"
cat >"$test_root/bin/curl" <<EOF
#!/usr/bin/env bash
config="\$(cat)"
printf '%s\n' "\$config" >>"$test_root/config.log"
url=''
data=''
while ((\$#)); do
  case "\$1" in
    --data) data="\$2"; shift 2 ;;
    --config | --output | --request | --header) shift 2 ;;
    http*) url="\$1"; shift ;;
    *) shift ;;
  esac
done
printf '%s\t%s\n' "\$url" "\$data" >>"$test_root/requests.log"
[[ "\$url" != *"/issues/\${FAKE_CURL_FAIL_ISSUE:-0}/"* ]]
EOF
chmod +x "$test_root/bin/curl"

repo="$test_root/repo"
git init -q "$repo"
git -C "$repo" -c user.name=t -c user.email=t@example.invalid commit -q --allow-empty \
  -m 'Merge pull request #9 from change/41-thing' -m 'Closes #41' -m 'Closes #42' -m 'Closes #41'

run() {
  (cd "$repo" && PATH="$test_root/bin:$PATH" GITEA_URL=http://gitea.example/ GITEA_OWNER=admin \
    GITEA_REPO=app GITEA_TOKEN=fixture-token bash "$notify" "$@")
}

out="$(run --result failed --stage health-check --run-url 'http://gitea.example/admin/app/actions/runs/7')"
grep -Fxq 'notified: #41 failed' <<<"$out"
grep -Fxq 'notified: #42 failed' <<<"$out"
[[ "$(wc -l <"$test_root/requests.log" | tr -d ' ')" == "2" ]]
grep -Fq 'http://gitea.example/api/v1/repos/admin/app/issues/41/comments' "$test_root/requests.log"
body="$(head -1 "$test_root/requests.log" | cut -f2 | jq -r .body)"
grep -Fq '**Deployment failed**' <<<"$body"
grep -Fq -- '- stage: `health-check`' <<<"$body"
grep -Fq -- '- run: http://gitea.example/admin/app/actions/runs/7' <<<"$body"
# The token travels only on curl's stdin config, never in argv or the body.
grep -Fq 'Authorization: token fixture-token' "$test_root/config.log"
if grep -Fq 'fixture-token' "$test_root/requests.log"; then
  echo 'token leaked into a request argument' >&2
  exit 1
fi

# Rollback; free text in stage and URL is dropped, not forwarded.
: >"$test_root/requests.log"
out="$(run --result rolled-back --stage 'rm -rf; $(id)' --run-url 'javascript:alert(1)')"
grep -Fxq 'notified: #41 rolled-back' <<<"$out"
body="$(head -1 "$test_root/requests.log" | cut -f2 | jq -r .body)"
grep -Fq '**Deployment rolled back**' <<<"$body"
grep -Fq -- '- stage: `unspecified`' <<<"$body"
if grep -Fq -- '- run:' <<<"$body"; then
  echo 'unsafe run link was forwarded' >&2
  exit 1
fi

# A valid first line cannot carry a second one; userinfo, query and fragment
# links are dropped because that is where credentials travel.
for bad_url in 'http://user:secret@gitea.example/run/1' 'http://gitea.example/run/1?access_token=secret' \
  'http://gitea.example/run/1#secret' $'http://gitea.example/run/1\nsecret'; do
  : >"$test_root/requests.log"
  run --result failed --stage $'deploy\nsecret' --run-url "$bad_url" >/dev/null
  body="$(head -1 "$test_root/requests.log" | cut -f2 | jq -r .body)"
  grep -Fq -- '- stage: `unspecified`' <<<"$body"
  if grep -Fq secret "$test_root/requests.log"; then
    echo "unsafe text reached the request: $bad_url" >&2
    exit 1
  fi
done

# Subject fallback when no Closes line exists.
: >"$test_root/requests.log"
printf 'Merge change/77-x into main\n' >"$test_root/msg"
MERGE_MESSAGE_FILE="$test_root/msg" run --result failed --stage deploy >/dev/null
grep -Fq '/issues/77/comments' "$test_root/requests.log"

# Every prerequisite failure warns and exits 0 without a request.
: >"$test_root/requests.log"
for case_args in 'bad' 'missing-env' 'no-token' 'no-issue' 'request-fails'; do
  set +e
  case "$case_args" in
    bad) err="$(run --result maybe 2>&1 >/dev/null)" ;;
    missing-env) err="$(cd "$repo" && PATH="$test_root/bin:$PATH" GITEA_TOKEN=x bash "$notify" --result failed 2>&1 >/dev/null)" ;;
    no-token) err="$(cd "$repo" && PATH="$test_root/bin:$PATH" GITEA_URL=u GITEA_OWNER=o GITEA_REPO=r GITEA_TOKEN='' bash "$notify" --result failed 2>&1 >/dev/null)" ;;
    no-issue) printf 'chore: nothing\n' >"$test_root/msg2"; err="$(MERGE_MESSAGE_FILE="$test_root/msg2" run --result failed 2>&1 >/dev/null)" ;;
    request-fails) err="$(FAKE_CURL_FAIL_ISSUE=41 run --result failed 2>&1 >/dev/null)" ;;
  esac
  status=$?
  set -e
  [[ "$status" == "0" ]]
  grep -Fq 'WARN: deploy-notify:' <<<"$err" || { printf 'case %s: %s\n' "$case_args" "$err" >&2; exit 1; }
done
# Only the request-fails case reached curl (two Issues, one failed).
[[ "$(wc -l <"$test_root/requests.log" | tr -d ' ')" == "2" ]]

printf '%s\n' 'deploy notify tests passed'
