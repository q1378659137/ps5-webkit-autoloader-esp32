#!/usr/bin/env python3
"""改过中文文案之后，用它把 zh-kit 刷成本地这份的样子。

`tools/relocalize.py` 的输入是 `zh-kit/`：整份覆盖的文件在 `overlay/`，注释对照在
`comments.json`。**如果你改了中文措辞却没刷 kit，下一次重建就会把旧译文盖回来**。
所以只要动过这些文件，就顺手跑一次：

    python tools/refresh-zh-kit.py --source F:/daima/ps5-upstream

`--source` 指着一份**干净的上游克隆**（`git clone --depth 1 <上游>` 即可）：
overlay 直接抄本地当前文件，注释对照靠"本地 vs 上游逐行比对"现算出来。

判定规则：
* `overlay/` 里的文件不走注释对照（它们本来就是中文）。
* 只改几行的文件（`language.js`、`index.html`、`layout.css`、`controls.css`）由
  `relocalize.PATCHES` 负责，行数都对不上，跳过。
* 其余文件按行配对：英文行里带 `//` `/*` `*/` 的才算注释；`.py` / `.sh` 的
  docstring 行没有标记，整份接受（这两个语言里我们只动注释和文档串）。
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relocalize import OVERLAY, PATCHES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "zh-kit"

# 行数会变（增删行）的文件交给 PATCHES，逐行配对无意义
PATCH_ONLY = {"flasher/language/language.js", "flasher/index.html",
              "flasher/app/layout.css", "flasher/ui/controls.css", "README.es.md",
              "flasher/app/base.css", "flasher/app/page-text.js",
              "flasher/firmware/release.js", "flasher/app/stars.js"}

COMMENT_FILES = (
    [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "flasher").rglob("*.js"))]
    + [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "flasher").rglob("*.css"))]
    + ["install-deps.sh", "pack/check_packed.sh", "pack/prepare-data.sh",
       "pack/pack_payload.py", "pack/externalize_autoloader.py", "Makefile"]
    + [f for f in OVERLAY if f.endswith((".mjs", ".py"))]
)


def main() -> int:
    src_arg = None
    for i, a in enumerate(sys.argv):
        if a == "--source" and i + 1 < len(sys.argv):
            src_arg = sys.argv[i + 1]
    if not src_arg:
        print("用法：python tools/refresh-zh-kit.py --source <干净的上游克隆>")
        return 2
    upstream = Path(src_arg).resolve()
    if not (upstream / "flasher" / "index.html").is_file():
        print(f"{upstream} 看起来不是上游源码树")
        return 2

    if KIT.exists():
        for child in sorted(KIT.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            child.rmdir() if child.is_dir() else child.unlink()
        KIT.rmdir()
    (KIT / "overlay").mkdir(parents=True)

    for rel in OVERLAY:
        dst = KIT / "overlay" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    print(f"overlay：{len(OVERLAY)} 个文件")

    patch_lines = {line for p in PATCHES for line in p["new"].split("\n") if line.strip()}
    pairs: dict[str, dict[str, str]] = {}
    skipped: list[str] = []
    for rel in dict.fromkeys(COMMENT_FILES):
        if rel in OVERLAY or rel in PATCH_ONLY or "/language/" in rel:
            continue
        up, loc = upstream / rel, ROOT / rel
        if not up.is_file() or not loc.is_file():
            skipped.append(f"{rel}（缺文件）")
            continue
        a = up.read_text("utf-8").replace("\r\n", "\n").split("\n")
        b = loc.read_text("utf-8").replace("\r\n", "\n").split("\n")
        if len(a) != len(b):
            skipped.append(f"{rel}（行数 {len(a)} vs {len(b)}）")
            continue
        table = {}
        in_block = False  # 跨行 /* … */ 的续行本身没有标记，靠状态判断
        for old, new in zip(a, b):
            was_in_block = in_block
            if "/*" in old and "*/" not in old.split("/*", 1)[1]:
                in_block = True
            if "*/" in old:
                in_block = False
            if old == new:
                continue
            en, zh = old.strip(), new.strip()
            if not en or not zh:
                continue
            if zh in patch_lines:
                continue
            marked = any(m in en for m in ("//", "/*", "*/")) or was_in_block
            if not marked and loc.suffix not in (".py", ".sh"):
                skipped.append(f"{rel}（非注释行：{en[:40]}）")
                continue
            table[en] = zh
        if table:
            pairs[rel] = table

    (KIT / "comments.json").write_text(
        json.dumps(pairs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    total = sum(len(v) for v in pairs.values())
    print(f"comments.json：{len(pairs)} 个文件，{total} 条对照")
    for s in skipped:
        print("  跳过 " + s)
    print("\n下一步：python tools/relocalize.py --into D:/tmp/zh  先试一遍再动本地目录")
    return 0


if __name__ == "__main__":
    sys.exit(main())
