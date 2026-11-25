"""用安装器模板重新生成已提交的 payload 页面。

`host/packed/index.html` 和 `host/packed/cache.html` 是构建产物：pack_payload.py
会把 `host/installer/<name>` 复制过去，并填上 `[[VERSION_PLACEHOLDER]]` /
`[[BUILD_TIME_PLACEHOLDER]]`。它们之所以提交进仓库，是为了能离线编固件，
所以改完模板必须把它们也刷新一遍 —— 否则开发板发出去的页面
还是英文。

    python tools/sync-payload-pages.py

版本号和构建时间取自 `host/packed/cache.appcache`（打包步骤写下的清单），
所以数字仍然是当前 payload 构建时的那两个。这一步不会动 payload 本身，
只改写这两个 HTML 文件。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "host" / "installer"
DST = ROOT / "host" / "packed"
MANIFEST = DST / "cache.appcache"
PAGES = ("index.html", "cache.html")


def read_version() -> tuple[str, str]:
    lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    header = next((l for l in lines if l.startswith("# WebKit Autoloader")), "")
    match = re.search(r"v(\S+) \(built ([^)]+)\)", header)
    if not match:
        raise SystemExit(f"cannot read version/build time from {MANIFEST}")
    return match.group(1), match.group(2)


def main() -> int:
    version, build_time = read_version()
    for name in PAGES:
        source = SRC / name
        text = source.read_text(encoding="utf-8")
        for token in ("[[VERSION_PLACEHOLDER]]", "[[BUILD_TIME_PLACEHOLDER]]"):
            if token not in text:
                raise SystemExit(f"{source} lost {token}; refusing to write a half-filled page")
        filled = (text
                  .replace("[[VERSION_PLACEHOLDER]]", version)
                  .replace("[[APP_DIR_PLACEHOLDER]]", version)
                  .replace("[[BUILD_TIME_PLACEHOLDER]]", build_time))
        # 仓库里这些文件是 CRLF，而 read_text() 会读成 LF。
        data = filled.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
        target = DST / name
        before = target.stat().st_size if target.exists() else 0
        target.write_bytes(data)
        print(f"{name:12} {before} -> {len(data)} bytes  v{version} built {build_time}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
