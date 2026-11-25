#!/usr/bin/env python3
"""把 PS5 侧 Payload Manager（`host/packed/app/**`）的**外壳文案**换成中文。

这个目录是 `pack_payload.py` 从上游 itsPLK 仓库生成的产物，本仓库只负责搬运，
所以汉化不能手改一份留着：上游一打包就没了。做法和固件那 60 条一样 ——
一张表，跑一遍就应用，`--check` 报漂移。

    python tools/zh-app-shell.py            # 应用
    python tools/zh-app-shell.py --check     # 只报告
    python tools/zh-app-shell.py --verify    # 结构校验

**只覆盖外壳**：页面标题、页脚、进度条状态文案、HUD 上的固件号。
`vendor/wobkot/**` 里那几百行是漏洞利用自己的诊断日志（`[*] Agent:`、
`===USERLAND===`、`Initiate ARW...` 之类），和 esptool-js 的输出同理，不译 ——
译了反而对不上上游日志、也搜不到 issue。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def app_dirs() -> list[Path]:
    """host/packed/app 下所有版本目录，外加 app 本身（入口页）。"""
    base = ROOT / "host" / "packed" / "app"
    if not base.is_dir():
        return []
    return [base, *sorted(p for p in base.iterdir() if p.is_dir())]


# (相对 app 目录的路径, 类型, 原文, 译文)
RULES: list[tuple[str, str, str, str]] = [
    # ---- 入口页 app/index.html ----
    ("index.html", "literal", '<html lang="en">', '<html lang="zh-CN">'),
    ("index.html", "literal", "<p id=\"status\">Loading...</p>", "<p id=\"status\">正在加载…</p>"),
    # ---- 版本目录里的页面 ----
    ("*/index.html", "literal", '<html lang="en">', '<html lang="zh-CN">'),
    ("*/index.html", "literal", '<div id="hud-fw">FW --</div>', '<div id="hud-fw">固件 --</div>'),
    # ---- 标题 / 页脚（版本号和构建时间每次打包都变，用正则）----
    ("index.html", "regex", r"v(\S+) by PLK \(built ([^)]+)\)", r"v\1（PLK 构建，\2）"),
    ("*/index.html", "regex", r"v(\S+) by PLK \(built ([^)]+)\)", r"v\1（PLK 构建，\2）"),
    # ---- app.js：进度文案 + 页脚 ----
    ("*/app.js", "literal", "' by PLK'", "'（PLK 构建'"),
    ("*/app.js", "literal", "' (built ' + config.buildTime + ')'", "'，' + config.buildTime + '）'"),
    ("*/app.js", "literal", "'This project is free and open source: '", "'本项目免费开源：'"),
    ("*/app.js", "literal", "'Starting WebKit exploit...'", "'正在启动 WebKit 漏洞利用…'"),
    ("*/app.js", "literal", "'Autoload failed. See the log above.'", "'自动加载失败，请看上面的日志。'"),
    ("*/app.js", "literal", "'Autoload finished.'", "'自动加载完成。'"),
    ("*/app.js", "literal", "'Payloads finished.'", "'payload 已全部完成。'"),
    ("*/app.js", "literal", "'Stopped. See the log above.'", "'已停止，请看上面的日志。'"),
    ("*/app.js", "literal", "'ELF loader already running. Nothing to do.'", "'ELF 加载器已在运行，无需操作。'"),
    ("*/app.js", "literal", "'An error occurred. See the log above.'", "'出错了，请看上面的日志。'"),
    ("*/app.js", "literal", "'Finishing autoload...'", "'正在完成自动加载…'"),
    ("*/app.js", "literal", "'Loading autoload payload...'", "'正在加载 autoload payload…'"),
    ("*/app.js", "literal", "'ELF loader ready...'", "'ELF 加载器就绪…'"),
    ("*/app.js", "literal", "'Privileges ready...'", "'权限就绪…'"),
    ("*/app.js", "literal", "'Kernel read/write ready...'", "'内核读写就绪…'"),
    ("*/app.js", "literal", "'Starting kernel exploit...'", "'正在启动内核漏洞利用…'"),
    ("*/app.js", "literal", "'WebKit ready...'", "'WebKit 就绪…'"),
    ("*/app.js", "literal", "'Preparing WebKit...'", "'正在准备 WebKit…'"),
    ("*/app.js", "literal", "'Running kernel exploit...'", "'正在运行内核漏洞利用…'"),
    ("*/app.js", "literal", "// Presentation only: runs through the standalone builder's awaited --js hook.",
     "// 只负责表现层：由 standalone 构建器的 --js 钩子执行。"),
    ("*/app.js", "literal", "// Keep the actual console, payloads and exploit in this document.",
     "// 真正的控制台、payload 和漏洞利用仍然留在本文档里。"),
    # ---- site.js：HUD 与日志前缀 ----
    ("*/src/site.js", "literal", "`FW ${hudState.fw}`", "`固件 ${hudState.fw}`"),
    ("*/src/site.js", "literal", "`Firmware: ${window.fw_str || \"detecting\"}`",
     "`固件：${window.fw_str || \"检测中\"}`"),
    ("*/src/site.js", "literal", "`Firmware: ${window.fw_str}`", "`固件：${window.fw_str}`"),
    ("*/src/site.js", "literal", "`Agent: ${navigator.userAgent}`", "`UA：${navigator.userAgent}`"),
    # 页脚里的仓库地址改成汉化分支
    ("*/app.js", "literal", "'https://github.com/itsPLK/ps5-webkit-autoloader'",
     "'https://github.com/q1378659137/ps5-webkit-autoloader'"),
]


def read(path: Path) -> tuple[str, bool]:
    text = path.read_bytes().decode("utf-8")
    crlf = "\r\n" in text
    return text.replace("\r\n", "\n"), crlf


# 正则规则没法用"译文整串"判断是否已应用，给一个稳定标记
REGEX_MARKERS = {
    r"v(\S+) by PLK \(built ([^)]+)\)": "（PLK 构建，",
}


def write(path: Path, text: str, crlf: bool) -> None:
    data = text.replace("\n", "\r\n") if crlf else text
    path.write_bytes(data.encode("utf-8"))


def targets() -> list[tuple[Path, str, str, str]]:
    """展开成 (文件, 类型, 原文, 译文)。"""
    out = []
    for app in app_dirs():
        is_root_page = app.name == "app"
        for pattern, kind, old, new in RULES:
            if pattern == "index.html" and not is_root_page:
                continue
            if pattern == "*/index.html" and is_root_page:
                continue
            rel = pattern.replace("*/", "")
            path = app / rel
            if path.is_file():
                out.append((path, kind, old, new))
    return out


def apply(check: bool, verify: bool) -> int:
    if not app_dirs():
        print("[MISS] host/packed/app 不存在，先跑 tools/sync-payload-pages.py")
        return 1

    bad = 0
    done = 0
    for path, kind, old, new in targets():
        text, crlf = read(path)
        rel = path.relative_to(ROOT).as_posix()

        if kind == "regex":
            pattern = re.compile(old)
            marker = REGEX_MARKERS.get(old, "")
            if marker and marker in text and not pattern.search(text):
                done += 1
                state = "applied"
            elif pattern.search(text):
                if not check and not verify:
                    text = pattern.sub(new, text)
                    write(path, text, crlf)
                done += 1
                state = "pending" if (check or verify) else "ok"
            else:
                state = "CHANGED UPSTREAM"
        else:
            if new in text and old not in text:
                done += 1
                state = "applied"
            elif old in text:
                if not check and not verify:
                    text = text.replace(old, new)
                    write(path, text, crlf)
                done += 1
                state = "pending" if (check or verify) else "ok"
            else:
                state = "CHANGED UPSTREAM"

        if check or verify:
            if state == "CHANGED UPSTREAM":
                bad += 1
                print(f"[{state:>15}] {rel}: {old[:70]}")
            else:
                print(f"[{state:>15}] {rel}: {old[:70]}")
        elif state == "CHANGED UPSTREAM":
            bad += 1
            print(f"[FAIL] {rel}: 原文对不上 — {old[:70]}")

    if check:
        print(f"\n{bad} 条对不上（上游改了这些文案）。")
        return 1 if bad else 0
    if verify:
        print(f"\n{bad} 条对不上。" if bad else "\nOK：app 外壳文案都是中文，结构没动。")
        return 1 if bad else 0
    print(f"\n{done} 条已就位。再跑 --check 确认 0 漂移。")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="只报告，不写文件")
    ap.add_argument("--verify", action="store_true", help="同 --check，外加结构断言")
    args = ap.parse_args()
    return apply(check=args.check, verify=args.verify)


if __name__ == "__main__":
    sys.exit(main())
