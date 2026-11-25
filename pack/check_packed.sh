#!/usr/bin/env bash
# 进镜像之前先对 host/packed 做体检，免得一次“成功”的构建
# 带着半截 payload 混进 release。
# 用法：pack/check_packed.sh <版本> <上游 tag>   例：0.8.0-pre-627ba8c v0.8.0-pre-627ba8c
set -euo pipefail
VER=$1
REF=$2
DIR="${PACKED_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/host/packed}"
fail() { echo "packed payload check failed: $*" >&2; exit 1; }

for f in index.html cache.html cache.appcache app/index.html "app/$VER/index.html"; do
  [ -s "$DIR/$f" ] || fail "missing $f"
done
elf="$DIR/app/$VER/webkit-autoloader-installer_${REF}.elf"
[ -f "$elf" ] || fail "missing installer $(basename "$elf")"
[ "$(stat -c %s "$elf")" -gt 100000 ] || fail "installer is too small"
grep -qF "$VER" "$DIR/app/index.html" || fail "app/index.html does not point at $VER"
grep -qF "$VER" "$DIR/cache.appcache" || fail "cache.appcache does not list $VER"
echo "packed payload $VER looks complete ($(du -sh "$DIR" | cut -f1))"
