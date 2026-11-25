#!/usr/bin/env python3
"""把 PS5 上那个"WebKit Autoloader Installer / 安装完成"页译成中文。

**这一页不在本仓库里。** 它是 itsPLK payload 仓库的
`frontend/installer-page/index.html`，编译时被 `tools/gen_file_registry.py` 打进
installer ELF 的文件注册表（压缩存），再由 ELF 在自己的 127.0.0.1:18181 上发出来。
本仓库只是把上游发布的 ELF 下载下来塞进 payload（`pack/pack_payload.py` 的
`download_installer`），所以改本仓库的文件对那一页没有任何影响。

真要让它在 PS5 上显示中文，只有两条路：

1. **正路**：用这个脚本把 itsPLK 仓库里的那份页面译好，再用他们的工具链重建 ELF
   （需要 PS5 payload SDK），然后 `python pack/pack_payload.py --web <itsPLK 仓库>` 打包。
2. 改 ELF 里的压缩资源 —— 长度一变就崩，不建议。

用法：

    python tools/zh-installer-page.py --source F:/daima/_itsplk            # 就地翻译
    python tools/zh-installer-page.py --source F:/daima/_itsplk --check     # 只报告
    python tools/zh-installer-page.py --source F:/daima/_itsplk --into D:/tmp/x   # 翻到别处

翻完想看效果：`node tools/verify-zh-installer-page.mjs --page <那份 index.html>`
（用无头 Chrome 把"安装完成"那条路径真的跑一遍）。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REL = "frontend/installer-page/index.html"

# 原文 → 译文。每一条都按"整段字面量"匹配，命中次数必须 ≥1。
TABLE: list[tuple[str, str]] = [
    ("<html lang=\"en\" manifest=\"/cache.appcache\">",
     "<html lang=\"zh-CN\" manifest=\"/cache.appcache\">"),
    ("font-family: -apple-system, \"Helvetica Neue\", Helvetica, Arial, sans-serif;",
     "font-family: -apple-system, \"Helvetica Neue\", Helvetica, Arial, \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", \"Noto Sans SC\", sans-serif;"),
    ("<title>WebKit Autoloader Installer v[[VERSION_PLACEHOLDER]] by PLK (built [[BUILD_TIME_PLACEHOLDER]])</title>",
     "<title>WebKit Autoloader 安装器 v[[VERSION_PLACEHOLDER]]（PLK 构建，[[BUILD_TIME_PLACEHOLDER]]）</title>"),
    ("<h1>WebKit Autoloader Installer</h1>", "<h1>WebKit Autoloader 安装器</h1>"),
    ("<p id=\"status\">Caching content...</p>", "<p id=\"status\">正在缓存内容…</p>"),
    ("<p id=\"detail\">Please wait a moment. Do not close this page yet!</p>",
     "<p id=\"detail\">请稍等片刻，先不要关闭这个页面！</p>"),
    ("aria-label=\"Cache download\"", "aria-label=\"缓存下载进度\""),
    ("<footer id=\"footer\">WebKit Autoloader Installer v[[VERSION_PLACEHOLDER]] by PLK (built [[BUILD_TIME_PLACEHOLDER]])<br />This project is free and open source: github.com/itsPLK/ps5-webkit-autoloader</footer>",
     "<footer id=\"footer\">WebKit Autoloader 安装器 v[[VERSION_PLACEHOLDER]]（PLK 构建，[[BUILD_TIME_PLACEHOLDER]]）<br />本项目免费开源：github.com/q1378659137/ps5-webkit-autoloader</footer>"),
    ("<h2 id=\"repairTitle\">WebKit cache appears corrupted</h2>",
     "<h2 id=\"repairTitle\">WebKit 缓存似乎已损坏</h2>"),
    ("<p id=\"repairMessage\">Clearing WebKit browser data may fix the issue. This removes AppCache, cookies, and local storage for the current user.</p>",
     "<p id=\"repairMessage\">清除 WebKit 的浏览器数据可能解决问题。这会删掉当前用户的 AppCache、Cookie 和本地存储。</p>"),
    ("Clear WebKit Data &amp; Retry", "清除 WebKit 数据并重试"),
    (">Cancel</button>", ">取消</button>"),
    ("'Installing homescreen shortcut...'", "'正在安装主屏幕快捷方式…'"),
    ("'The offline cache is ready. Keep this page open.'", "'离线缓存已就绪，请保持本页打开。'"),
    ("'Installed successfully'", "'安装完成'"),
    ("'Reboot, then open WebKit Autoloader from the homescreen. You can close this page.'",
     "'重启主机，然后从主屏幕打开 WebKit Autoloader。现在可以关闭本页了。'"),
    ("'Clear WebKit browser data and retry the installation?'",
     "'要清除 WebKit 浏览器数据并重试安装吗？'"),
    ("'Clearing WebKit data...'", "'正在清除 WebKit 数据…'"),
    ("'WebKit data cleared. The installer will reopen this page.'",
     "'WebKit 数据已清除，安装器会重新打开本页。'"),
    ("'Unsupported firmware '", "'不支持的固件 '"),
    ("'Supported: 3.00–13.60 via Wobkot Relapse and Poops.'",
     "'支持范围：3.00–13.60，走 Wobkot Relapse 和 Poops。'"),
    ("'This browser does not support offline AppCache.'", "'这个浏览器不支持离线 AppCache。'"),
    ("'Downloading...'", "'正在下载…'"),
    ("'The cached manifest was superseded. Re-run the installer to finish.'",
     "'缓存的清单已被更新取代，请重新运行安装器以完成。'"),
    ("'Caching is taking unusually long'", "'缓存耗时异常长'"),
    ("'Keep this page open or run the installer again.'", "'请保持本页打开，或者重新运行安装器。'"),
    ("'Cache incomplete. Run the installer again.'", "'缓存不完整，请重新运行安装器。'"),
    ("'Install failed. Run the installer again.'", "'安装失败，请重新运行安装器。'"),
    ("'Could not clear WebKit data. Run the installer again.'",
     "'无法清除 WebKit 数据，请重新运行安装器。'"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="itsPLK/ps5-webkit-autoloader 的克隆目录")
    ap.add_argument("--into", default=None, help="翻到别的路径（不就地改）")
    ap.add_argument("--check", action="store_true", help="只报告，不写")
    args = ap.parse_args()

    src = Path(args.source).resolve() / REL
    if not src.is_file():
        print(f"[MISS] {src} 不存在；确认 --source 指到了 itsPLK 仓库根目录")
        return 1

    if args.into:
        dst = Path(args.into)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        target = dst
    else:
        target = src

    raw = target.read_bytes()
    text = raw.decode("utf-8")
    crlf = "\r\n" in text
    text = text.replace("\r\n", "\n")

    pending = applied = drift = 0
    for old, new in TABLE:
        if new in text:
            applied += 1
            continue
        if old in text:
            pending += 1
            if not args.check:
                text = text.replace(old, new)
            continue
        drift += 1
        print(f"[CHANGED UPSTREAM] {old[:80]}")

    if not args.check and pending:
        target.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))

    if args.check:
        print(f"\n已有 {applied} 条 / 待译 {pending} 条 / 对不上 {drift} 条")
        return 1 if drift else 0
    print(f"\n译好 {applied + pending}/{len(TABLE)} 条（本来就有 {applied} 条），对不上 {drift} 条")
    print(f"文件：{target}")
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
