#!/usr/bin/env bash
# Puts the images the web flasher installs into flasher/bin:
#   bin/*.merged.bin      stable, from GitHub's "Latest" release
#   bin/pre/*.merged.bin  the newest pre-release, only while it is newer than stable
#   bin/channels.json     what the version switch shows
set -euo pipefail
: "${REPO:?}"
OUT=flasher/bin
mkdir -p "$OUT"

FIELDS='{tag: .tag_name, name: .name, date: .published_at, url: .html_url}'
stable=$(gh api "repos/$REPO/releases/latest" --jq "$FIELDS")
stable_tag=$(jq -r .tag <<< "$stable")
stable_date=$(jq -r .date <<< "$stable")

# 发布流程先建 release、再逐个上传镜像。pages 的 push 触发和 firmware 同时起跑，
# 撞进这个窗口就只看到一部分镜像（常是 0 个），`gh release download` 于是非零退出。
# 这里等一会儿补齐，不让一次竞态把整次部署判死。
BOARDS="pico devkit s2 s3 c3"

fetch_images() {
  local tag=$1 dir=$2 attempt missing b
  for attempt in 1 2 3 4 5 6; do
    gh release download "$tag" --repo "$REPO" --pattern '*.merged.bin' --dir "$dir" --clobber \
      >/dev/null 2>&1 || true
    missing=""
    for b in $BOARDS; do
      [ -s "$dir/esp32-arduino.$b.merged.bin" ] || missing="$missing $b"
    done
    [ -z "$missing" ] && return 0
    echo "release $tag 还缺:$missing（第 $attempt/6 次），等镜像传完…"
    sleep 15
  done
  echo "release $tag 等满 90 秒仍缺:$missing"
  return 1
}

fetch_images "$stable_tag" "$OUT" || {
  echo "稳定版 $stable_tag 的镜像没齐，本次不发布 flasher/bin。"
  exit 1
}

pre=$(gh api "repos/$REPO/releases?per_page=30" --jq \
  "[.[] | select(.prerelease and (.draft | not) and .published_at > \"$stable_date\")] | sort_by(.published_at) | last // empty | $FIELDS")
if [ -n "$pre" ]; then
  pre_tag=$(jq -r .tag <<< "$pre")
  mkdir -p "$OUT/pre"
  # Only offer it when every board's image is there.
  if ! fetch_images "$pre_tag" "$OUT/pre"; then
    echo "预发行版 $pre_tag 不完整，这次不提供"
    rm -rf "$OUT/pre"
    pre=""
  fi
fi

jq -n --argjson stable "$stable" --argjson pre "${pre:-null}" '{stable: $stable, pre: $pre}' > "$OUT/channels.json"
cat "$OUT/channels.json"
ls -lhR "$OUT"
