#!/usr/bin/env python3
"""把这份源码打成一个 zip，放到 out/ 下。

    python tools/pack-source-zip.py

包名带版本号和日期，取的是 `host/packed/cache.appcache` 里那一行
（`# WebKit Autoloader v0.8.4 (built …)`），所以不会和实际 payload 版本对不上。

排除掉的东西：版本库元数据（`.git`、子模块的 gitlink）、`__pycache__`/`*.pyc`、
构建产物（`build/ data/ dist/ dist-ci/`）、`out/` 自己、`*.bak`、`*.zip`。
zip 里有一个顶层目录，解压不会散一地。
"""

from __future__ import annotations

import re
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"

SKIP_DIRS = {".git", "__pycache__", "out", "build", "data", "dist", "dist-ci", "node_modules"}
SKIP_SUFFIX = {".pyc", ".bak", ".zip"}


def version() -> str:
    head = (ROOT / "host" / "packed" / "cache.appcache").read_text("utf-8").splitlines()[1]
    match = re.search(r"v(\S+) \(built", head)
    if not match:
        raise SystemExit("读不到 payload 版本，检查 host/packed/cache.appcache 第 2 行")
    return match.group(1)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    name = f"ps5-webkit-autoloader-esp32-zh_v{version()}_{date.today():%Y%m%d}"
    target = OUT / f"{name}.zip"

    files = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name == ".git":            # 子模块是指针文件，不是目录
            continue
        if not path.is_file() or path.suffix in SKIP_SUFFIX:
            continue
        files.append((path, rel))

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path, rel in files:
            zf.write(path, f"{name}/{rel.as_posix()}")

    with zipfile.ZipFile(target) as zf:
        bad = zf.testzip()

    print(f"输出：{target}")
    print(f"文件数：{len(files)}   大小：{target.stat().st_size / 1024:.1f} KB   CRC：{'OK' if bad is None else bad}")
    return 0 if bad is None else 1


if __name__ == "__main__":
    sys.exit(main())
