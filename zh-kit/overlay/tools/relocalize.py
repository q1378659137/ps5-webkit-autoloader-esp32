#!/usr/bin/env python3
"""按"重新克隆上游 → 覆盖汉化套件 → 重放补丁 → 验收"的顺序，重建一份干净的中文版。

本项目跟踪 https://github.com/percdotdev/ps5-webkit-autoloader-esp32 。
上游一更新，**不要在上一次的树上 merge/patch**，而是用这个脚本从上游最新代码重新铺一遍：

    python tools/relocalize.py                      # 重建到默认目录（会先备份再清空）
    python tools/relocalize.py --check              # 只克隆+比对，不动本地，报告上游改了哪些文件
    python tools/relocalize.py --into D:/tmp/zh     # 建到别的目录，本地原封不动（推荐先这么试）
    python tools/relocalize.py --source D:/clone    # 用已经克隆好的树，不再联网
    python tools/relocalize.py --ref v0.8.4         # 指定 tag / 分支

汉化内容全部放在 `zh-kit/` 里：

* `zh-kit/overlay/…` —— 整份归我们的文件（中文 README、`zh.js`、PS5 侧两个模板、
  那四个工具脚本、串口工具、这份说明），直接覆盖到新树。
* `zh-kit/comments.json` —— "英文注释整行 → 中文整行"的对照，覆盖 `flasher/`、`tools/`、
  `pack/`、`install-deps.sh`。上游改过措辞的注释会匹配不上，脚本会把它们列成"注释漂移"。
* 下面 `PATCHES` —— 只改几行的文件（`language.js` 注册语言、`index.html` 加按钮、
  字体栈、`nowrap`、品牌省略、`README.es.md` 语言链），一条一条断言"锚点出现且只出现一次"。
* 固件那 60 条不在这里，仍然由 `tools/zh-firmware-strings.py` 应用（它本身就是对照表）。

安全网：动本地目录之前先整份 zip 备份到 `<dest>_bak_<时间戳>.zip`；任何一步断言失败就停，
不会留下半成品（`--into` 模式下失败只影响临时目录）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent / "zh-kit"
DEFAULT_UPSTREAM = "https://github.com/percdotdev/ps5-webkit-autoloader-esp32"
DEFAULT_DEST = Path(os.environ.get("ZH_DEST") or Path(__file__).resolve().parent.parent)

# 整份归我们的文件：relocalize 直接用 zh-kit/overlay 里的版本覆盖上游同名文件。
OVERLAY = [
    "README.md",
    "LOCALIZATION.zh-CN.md",
    "flasher/language/zh.js",
    "host/installer/index.html",
    "host/installer/cache.html",
    "tools/check-i18n.mjs",
    "tools/verify-zh-render.mjs",
    "tools/verify-zh-console-pages.mjs",
    "tools/sync-payload-pages.py",
    "tools/zh-firmware-strings.py",
    "tools/zh-app-shell.py",
    "tools/zh-installer-page.py",
    "tools/audit-zh-leftovers.mjs",
    "tools/verify-zh-installer-page.mjs",
    "tools/pack-source-zip.py",
    "tools/relocalize.py",
    "tools/refresh-zh-kit.py",
    "debug/serial_timestamp.py",
]

# 只改几行的文件：整块原文 → 整块译文。全部按"归一化成 LF 再比"来匹配。
PATCHES: list[dict] = [
    {
        "file": "flasher/language/language.js",
        "why": "注册 zh 语言包（insert@4）",
        "old": "import { en } from \"./en.js\";\nimport { es } from \"./es.js\";\n\nconst STRINGS = { en, es };\n",
        "new": "import { en } from \"./en.js\";\nimport { es } from \"./es.js\";\nimport { zh } from \"./zh.js\";\n\nconst STRINGS = { en, es, zh };\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（replace@2）",
        "old": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n",
        "new": "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n  <meta charset=\"utf-8\">\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（replace@9）",
        "old": "  <meta name=\"theme-color\" content=\"#141415\">\n  <title>PS5 WebKit Autoloader</title>\n  <meta name=\"description\" content=\"Write the PS5 WebKit Autoloader firmware to an ESP32, then join ESP32_PORTAL on the console and open the User’s Guide.\">\n  <link rel=\"canonical\" href=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/\">\n  <meta property=\"og:type\" content=\"website\">\n",
        "new": "  <meta name=\"theme-color\" content=\"#141415\">\n  <title>PS5 WebKit Autoloader</title>\n  <meta name=\"description\" content=\"在浏览器里把 PS5 WebKit Autoloader 固件写入 ESP32，然后在 PS5 上打开使用说明书。\">\n  <link rel=\"canonical\" href=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/\">\n  <meta property=\"og:type\" content=\"website\">\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（replace@12）",
        "old": "  <link rel=\"canonical\" href=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/\">\n  <meta property=\"og:type\" content=\"website\">\n  <meta property=\"og:locale\" content=\"en_US\">\n  <meta property=\"og:site_name\" content=\"PS5 WebKit Autoloader\">\n  <meta property=\"og:title\" content=\"PS5 WebKit Autoloader\">\n",
        "new": "  <link rel=\"canonical\" href=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/\">\n  <meta property=\"og:type\" content=\"website\">\n  <meta property=\"og:locale\" content=\"zh_CN\">\n  <meta property=\"og:site_name\" content=\"PS5 WebKit Autoloader\">\n  <meta property=\"og:title\" content=\"PS5 WebKit Autoloader\">\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（replace@15）",
        "old": "  <meta property=\"og:site_name\" content=\"PS5 WebKit Autoloader\">\n  <meta property=\"og:title\" content=\"PS5 WebKit Autoloader\">\n  <meta property=\"og:description\" content=\"Write the PS5 WebKit Autoloader firmware to an ESP32, then join ESP32_PORTAL on the console and open the User’s Guide.\">\n  <meta property=\"og:url\" content=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/\">\n  <meta property=\"og:image\" content=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/share/og.png?v=2\">\n",
        "new": "  <meta property=\"og:site_name\" content=\"PS5 WebKit Autoloader\">\n  <meta property=\"og:title\" content=\"PS5 WebKit Autoloader\">\n  <meta property=\"og:description\" content=\"在浏览器里把 PS5 WebKit Autoloader 固件写入 ESP32，然后在 PS5 上打开使用说明书。\">\n  <meta property=\"og:url\" content=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/\">\n  <meta property=\"og:image\" content=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/share/og.png?v=2\">\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（replace@21）",
        "old": "  <meta property=\"og:image:width\" content=\"1200\">\n  <meta property=\"og:image:height\" content=\"630\">\n  <meta property=\"og:image:alt\" content=\"PS5 WebKit Autoloader for ESP32 — flash, join ESP32_PORTAL, open User’s Guide.\">\n  <meta name=\"twitter:card\" content=\"summary_large_image\">\n  <meta name=\"twitter:title\" content=\"PS5 WebKit Autoloader\">\n",
        "new": "  <meta property=\"og:image:width\" content=\"1200\">\n  <meta property=\"og:image:height\" content=\"630\">\n  <meta property=\"og:image:alt\" content=\"适用于 ESP32 的 PS5 WebKit Autoloader —— 刷写、连 ESP32_PORTAL、打开使用说明书。\">\n  <meta name=\"twitter:card\" content=\"summary_large_image\">\n  <meta name=\"twitter:title\" content=\"PS5 WebKit Autoloader\">\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（replace@24）",
        "old": "  <meta name=\"twitter:card\" content=\"summary_large_image\">\n  <meta name=\"twitter:title\" content=\"PS5 WebKit Autoloader\">\n  <meta name=\"twitter:description\" content=\"Write the PS5 WebKit Autoloader firmware to an ESP32, then join ESP32_PORTAL on the console and open the User’s Guide.\">\n  <meta name=\"twitter:image\" content=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/share/og.png?v=2\">\n  <meta name=\"twitter:image:alt\" content=\"PS5 WebKit Autoloader for ESP32 — flash, join ESP32_PORTAL, open User’s Guide.\">\n",
        "new": "  <meta name=\"twitter:card\" content=\"summary_large_image\">\n  <meta name=\"twitter:title\" content=\"PS5 WebKit Autoloader\">\n  <meta name=\"twitter:description\" content=\"在浏览器里把 PS5 WebKit Autoloader 固件写入 ESP32，然后在 PS5 上打开使用说明书。\">\n  <meta name=\"twitter:image\" content=\"https://percdotdev.github.io/ps5-webkit-autoloader-esp32/share/og.png?v=2\">\n  <meta name=\"twitter:image:alt\" content=\"适用于 ESP32 的 PS5 WebKit Autoloader —— 刷写、连 ESP32_PORTAL、打开使用说明书。\">\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（replace@47）",
        "old": "</head>\n<body>\n  <a class=\"skip\" href=\"#main\" id=\"skip\">Skip to content</a>\n\n  <header class=\"top\">\n",
        "new": "</head>\n<body>\n  <a class=\"skip\" href=\"#main\" id=\"skip\">跳到正文</a>\n\n  <header class=\"top\">\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（replace@55）",
        "old": "    </a>\n    <div class=\"top-tools\">\n      <div class=\"seg\" role=\"group\" aria-label=\"Language\">\n        <button type=\"button\" data-set-lang=\"en\" aria-pressed=\"true\">EN</button>\n        <button type=\"button\" data-set-lang=\"es\" aria-pressed=\"false\">ES</button>\n",
        "new": "    </a>\n    <div class=\"top-tools\">\n      <div class=\"seg\" role=\"group\" aria-label=\"语言\">\n        <button type=\"button\" data-set-lang=\"en\" aria-pressed=\"true\">EN</button>\n        <button type=\"button\" data-set-lang=\"es\" aria-pressed=\"false\">ES</button>\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（insert@58）",
        "old": "        <button type=\"button\" data-set-lang=\"en\" aria-pressed=\"true\">EN</button>\n        <button type=\"button\" data-set-lang=\"es\" aria-pressed=\"false\">ES</button>\n      </div>\n      <button type=\"button\" class=\"icon-btn\" id=\"theme\" aria-label=\"Toggle theme\"></button>\n",
        "new": "        <button type=\"button\" data-set-lang=\"en\" aria-pressed=\"true\">EN</button>\n        <button type=\"button\" data-set-lang=\"es\" aria-pressed=\"false\">ES</button>\n        <button type=\"button\" data-set-lang=\"zh\" aria-pressed=\"false\">中文</button>\n      </div>\n      <button type=\"button\" class=\"icon-btn\" id=\"theme\" aria-label=\"切换主题\"></button>\n",
    },
    {
        "file": "flasher/index.html",
        "why": "静态文案/语言按钮/链接改成中文与汉化仓库（replace@84）",
        "old": "    <nav>\n      <button type=\"button\" class=\"foot-btn\" id=\"open-adv\"></button>\n      <a id=\"foot-src\" href=\"https://github.com/percdotdev/ps5-webkit-autoloader-esp32\"></a>\n      <a href=\"https://github.com/itsPLK/ps5-webkit-autoloader\">itsPLK</a>\n    </nav>\n  </footer>\n",
        "new": "    <nav>\n      <button type=\"button\" class=\"foot-btn\" id=\"open-adv\"></button>\n      <a id=\"foot-src\" href=\"https://github.com/q1378659137/ps5-webkit-autoloader-esp32\"></a>\n      <a href=\"https://github.com/q1378659137/ps5-webkit-autoloader\">Payload</a>\n    </nav>\n  </footer>\n",
    },
    {
        "file": "flasher/app/base.css",
        "why": "正文字体栈补 CJK 回退（replace@1）",
        "old": "/* Tokens, reset, shared keyframes.\n   A night workbench: ink neutrals keep the chrome quiet, copper from the board traces is\n   the one accent, and the board in the middle is the only rich colour on screen. */\n",
        "new": "/* 变量、reset、共用的关键帧。\n   A night workbench: ink neutrals keep the chrome quiet, copper from the board traces is\n   the one accent, and the board in the middle is the only rich colour on screen. */\n",
    },
    {
        "file": "flasher/app/base.css",
        "why": "正文字体栈补 CJK 回退（replace@26）",
        "old": "  --radius-sm: 10px;\n  --ease: cubic-bezier(0.22, 1, 0.36, 1);\n  --sans: \"Instrument Sans\", ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", sans-serif;\n  --mono: \"Geist Mono\", ui-monospace, \"Cascadia Mono\", Consolas, monospace;\n  color-scheme: dark;\n",
        "new": "  --radius-sm: 10px;\n  --ease: cubic-bezier(0.22, 1, 0.36, 1);\n  --sans: \"Instrument Sans\", ui-sans-serif, system-ui, -apple-system, \"Segoe UI\",\n    \"PingFang SC\", \"Microsoft YaHei\", \"Noto Sans SC\", \"Source Han Sans SC\", sans-serif;\n  --mono: \"Geist Mono\", ui-monospace, \"Cascadia Mono\", Consolas, monospace;\n  color-scheme: dark;\n",
    },
    {
        "file": "flasher/ui/controls.css",
        "why": "语言按钮不断行（「中文」两个字）（replace@1）",
        "old": "/* Buttons, the language switch, icon buttons, the GitHub link, checkboxes. */\n.btn {\n  display: inline-flex; align-items: center; justify-content: center; gap: 8px;\n",
        "new": "/* 按钮、语言切换、图标按钮、GitHub 链接、复选框。 */\n.btn {\n  display: inline-flex; align-items: center; justify-content: center; gap: 8px;\n",
    },
    {
        "file": "flasher/ui/controls.css",
        "why": "语言按钮不断行（「中文」两个字）（replace@19）",
        "old": ".seg { display: flex; padding: 2px; border: 1px solid var(--line); border-radius: var(--radius-sm); }\n.seg button {\n  border: 0; background: none; height: 24px; padding: 0 8px; border-radius: 6px;\n  font-size: 12px; color: var(--dim); cursor: pointer; transition: color 150ms var(--ease), background-color 150ms var(--ease);\n}\n",
        "new": ".seg { display: flex; padding: 2px; border: 1px solid var(--line); border-radius: var(--radius-sm); }\n.seg button {\n  border: 0; background: none; height: 24px; padding: 0 8px; border-radius: 6px; white-space: nowrap;\n  font-size: 12px; color: var(--dim); cursor: pointer; transition: color 150ms var(--ease), background-color 150ms var(--ease);\n}\n",
    },
    {
        "file": "flasher/app/layout.css",
        "why": "品牌名可省略；窄屏隐藏品牌文字（replace@1）",
        "old": "/* Page frame: a quiet top bar, one centred step, a footer line. Fits one screen. */\n.top {\n  height: 56px; padding: 0 24px; flex: none;\n",
        "new": "/* 页面骨架：安静的顶栏、居中一步、一行页脚，一屏放得下。 */\n.top {\n  height: 56px; padding: 0 24px; flex: none;\n",
    },
    {
        "file": "flasher/app/layout.css",
        "why": "品牌名可省略；窄屏隐藏品牌文字（replace@6）",
        "old": "  display: flex; align-items: center; gap: 12px;\n}\n.brand { display: inline-flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 500; text-decoration: none; }\n.mark { width: 20px; height: 20px; flex: none; }\n.mark rect { fill: var(--fg); }\n",
        "new": "  display: flex; align-items: center; gap: 12px;\n}\n.brand { display: inline-flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 500; text-decoration: none; min-width: 0; }\n.brand span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.mark { width: 20px; height: 20px; flex: none; }\n.mark rect { fill: var(--fg); }\n",
    },
    {
        "file": "flasher/app/layout.css",
        "why": "品牌名可省略；窄屏隐藏品牌文字（insert@29）",
        "old": "@media (max-width: 560px) {\n  .top { padding: 0 16px; }\n  main { padding: 0 16px 8px; }\n  .foot { padding: 12px 16px 16px; justify-content: center; }\n",
        "new": "@media (max-width: 560px) {\n  .top { padding: 0 16px; }\n  .brand span { display: none; }\n  main { padding: 0 16px 8px; }\n  .foot { padding: 12px 16px 16px; justify-content: center; }\n",
    },
    {
        "file": "flasher/firmware/release.js",
        "why": "兜底 API 指向汉化仓库，避免误装上游英文固件（replace@3）",
        "old": "import { state } from \"../app/state.js\";\n\n// The pages workflow writes bin/channels.json next to the images:\n//   { \"stable\": { tag, name, date, url }, \"pre\": { ... } | null }\n// pre is only set while the newest pre-release is newer than stable.\n",
        "new": "import { state } from \"../app/state.js\";\n\n// pages 工作流会在镜像旁边写一个 bin/channels.json：\n//   { \"stable\": { tag, name, date, url }, \"pre\": { ... } | null }\n// 只有最新的预发行版比稳定版新时，pre 才有值。\n",
    },
    {
        "file": "flasher/firmware/release.js",
        "why": "兜底 API 指向汉化仓库，避免误装上游英文固件（replace@7）",
        "old": "// 只有最新的预发行版比稳定版新时，pre 才有值。\nconst CHANNELS = \"bin/channels.json\";\nconst API = \"https://api.github.com/repos/percdotdev/ps5-webkit-autoloader-esp32/releases/latest\";\nconst KEY = \"release:v1\";\n\n",
        "new": "// 只有最新的预发行版比稳定版新时，pre 才有值。\nconst CHANNELS = \"bin/channels.json\";\nconst API = \"https://api.github.com/repos/q1378659137/ps5-webkit-autoloader-esp32/releases/latest\";\nconst KEY = \"release:v1\";\n\n",
    },
    {
        "file": "flasher/firmware/release.js",
        "why": "兜底 API 指向汉化仓库，避免误装上游英文固件（replace@14）",
        "old": "}\n\n// Fallback for a local preview without channels.json: stable only, from the API.\n// GitHub allows 60 anonymous calls an hour, so reuse one answer per tab.\nasync function loadLatest() {\n  try {\n",
        "new": "}\n\n// 本地预览没有 channels.json 时的退路：只取稳定版，走 API。\n// GitHub 匿名调用每小时限 60 次，所以每个标签页复用同一个结果。\nasync function loadLatest() {\n  try {\n",
    },
    {
        "file": "flasher/firmware/release.js",
        "why": "兜底 API 指向汉化仓库，避免误装上游英文固件（replace@46）",
        "old": "}\n\n// The release the Install button writes: undefined while loading, null when unknown.\nexport function selected() {\n  const c = state.channels;\n",
        "new": "}\n\n// 安装按钮要写入的发行版：加载中是 undefined，未知是 null。\nexport function selected() {\n  const c = state.channels;\n",
    },
    {
        "file": "flasher/firmware/release.js",
        "why": "兜底 API 指向汉化仓库，避免误装上游英文固件（replace@53）",
        "old": "}\n\n// \"itsPLK 0.7.1(f4fab6b)\" -> \"itsPLK 0.7.1 (f4fab6b)\"\nexport function payloadLabel(name) {\n  return String(name || \"\").replace(/\\s*\\(/, \" (\").trim();\n",
        "new": "}\n\n// 把 \"itsPLK 0.7.1(f4fab6b)\" 规整成 \"itsPLK 0.7.1 (f4fab6b)\"\nexport function payloadLabel(name) {\n  return String(name || \"\").replace(/\\s*\\(/, \" (\").trim();\n",
    },
    {
        "file": "flasher/app/stars.js",
        "why": "星标 API 跟随汉化仓库（replace@1）",
        "old": "const API = \"https://api.github.com/repos/percdotdev/ps5-webkit-autoloader-esp32\";\nconst KEY = \"stars:v1\";\n\n",
        "new": "const API = \"https://api.github.com/repos/q1378659137/ps5-webkit-autoloader-esp32\";\nconst KEY = \"stars:v1\";\n\n",
    },
    {
        "file": "flasher/app/stars.js",
        "why": "星标 API 跟随汉化仓库（replace@4）",
        "old": "const KEY = \"stars:v1\";\n\n// GitHub allows 60 anonymous calls an hour, so ask once per tab.\nasync function loadStars() {\n  try {\n",
        "new": "const KEY = \"stars:v1\";\n\n// GitHub 匿名调用每小时限 60 次，所以每个标签页只问一次。\nasync function loadStars() {\n  try {\n",
    },
    {
        "file": "flasher/app/stars.js",
        "why": "星标 API 跟随汉化仓库（replace@29）",
        "old": "}\n\n// Fills the count next to the GitHub icon; leaves the icon alone when GitHub is unreachable.\nexport async function showStars(link, lang) {\n  const n = await loadStars();\n",
        "new": "}\n\n// 把星标数填到 GitHub 图标旁边；连不上 GitHub 就只留图标。\nexport async function showStars(link, lang) {\n  const n = await loadStars();\n",
    },
    {
        "file": "flasher/app/page-text.js",
        "why": "中文按 zh-CN 输出，浏览器据此挑简体字形（replace@4）",
        "old": "import { state } from \"./state.js\";\n\n// Static copy in index.html: element id -> string key.\nconst TEXT = {\n  \"skip\": \"skip\",\n",
        "new": "import { state } from \"./state.js\";\n\n// index.html 里的静态文案：元素 id -> 文案键。\nconst TEXT = {\n  \"skip\": \"skip\",\n",
    },
    {
        "file": "flasher/app/page-text.js",
        "why": "中文按 zh-CN 输出，浏览器据此挑简体字形（replace@22）",
        "old": "\nexport function renderPageText() {\n  document.documentElement.lang = state.lang;\n  for (const [id, key] of Object.entries(TEXT)) {\n    document.getElementById(id).textContent = t(key);\n",
        "new": "\nexport function renderPageText() {\n  // 中文写成 zh-CN：浏览器据此挑简体字形（上游只写 zh）\n  document.documentElement.lang = state.lang === \"zh\" ? \"zh-CN\" : state.lang;\n  for (const [id, key] of Object.entries(TEXT)) {\n    document.getElementById(id).textContent = t(key);\n",
    },
]


def log(msg: str = "") -> None:
    print(msg, flush=True)


def run(cmd: list[str], cwd: Path, env: dict | None = None, label: str = "") -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          env={**os.environ, **(env or {})})
    out = (proc.stdout or "") + (proc.stderr or "")
    if label:
        log(f"$ {label}")
    return proc.returncode, out


def find_node() -> str | None:
    cand = [os.environ.get("NODE"), shutil.which("node")]
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "")
    cand += [str(p) for p in sorted((home / ".workbuddy" / "binaries" / "node" / "versions").glob("*/node.exe"))]
    cand += [r"C:\Program Files\nodejs\node.exe"]
    for c in cand:
        if c and Path(c).is_file():
            return str(c)
    return None


def normalise(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    crlf = "\r\n" in text
    return text.replace("\r\n", "\n"), crlf


def write_back(path: Path, text: str, crlf: bool) -> None:
    data = text.replace("\n", "\r\n") if crlf else text
    path.write_bytes(data.encode("utf-8"))


def purge(path: Path) -> None:
    """删掉目录里的所有东西。

    故意不用 shutil.rmtree：某些受管环境会给 rmtree 套"移到回收站"的实现，
    在大目录上会失败（SHFileOperationW 0x78）。这里从最深的文件开始逐个删。
    """
    if not path.exists():
        return
    entries = sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for entry in entries:
        try:
            if entry.is_dir() and not entry.is_symlink():
                entry.rmdir()
            else:
                entry.unlink()
        except OSError as err:
            log(f"  [warn] 删不掉 {entry}: {err}")
    try:
        path.rmdir()
    except OSError as err:
        log(f"  [warn] 删不掉 {path}: {err}")


def backup(dest: Path) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = dest.parent / f"{dest.name}_bak_{stamp}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in dest.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(dest))
    return target


def clone(upstream: str, ref: str | None) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="zh-upstream-"))
    repo = tmp / "repo"
    cmd = ["git", "clone", "--depth", "1"]
    if ref:
        cmd += ["--branch", ref]
    cmd += [upstream, str(repo)]
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        cmd = ["git", "-c", f"http.proxy={proxy}", "-c", f"https.proxy={proxy}", *cmd[1:]]
    log(f"$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode:
        log(proc.stdout)
        log(proc.stderr)
        raise SystemExit("克隆上游失败。网络不通时先设 HTTPS_PROXY（本项目常用 http://127.0.0.1:10808）。")
    head = subprocess.run(["git", "log", "-1", "--format=%h %ad %s", "--date=short"],
                          cwd=str(repo), capture_output=True, text=True).stdout.strip()
    log(f"上游版本：{head}")
    return repo


def copy_tree(src: Path, dst: Path) -> None:
    # 就地重建时 dst 就是仓库根、已经存在，必须允许合并写入
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git"))


def apply_overlay(dest: Path) -> int:
    n = 0
    for src in sorted((KIT / "overlay").rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(KIT / "overlay")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        n += 1
    log(f"覆盖汉化文件：{n} 个")
    return n


def apply_patches(dest: Path) -> tuple[int, list[str]]:
    done = 0
    problems = []
    for patch in PATCHES:
        path = dest / patch["file"]
        if not path.is_file():
            problems.append(f"{patch['file']}：文件不存在（上游可能改名/删了）")
            continue
        text, crlf = normalise(path)
        if patch["new"] in text:
            done += 1
            continue
        hits = text.count(patch["old"])
        if hits != 1:
            problems.append(f"{patch['file']}：锚点命中 {hits} 次（应 1 次）— {patch['why']}")
            continue
        text = text.replace(patch["old"], patch["new"], 1)
        write_back(path, text, crlf)
        done += 1
    log(f"补丁：{done}/{len(PATCHES)} 条已就位")
    return done, problems


def apply_comments(dest: Path) -> tuple[int, list[str]]:
    table = json.loads((KIT / "comments.json").read_text("utf-8"))
    applied = 0
    drift: list[str] = []
    for rel, pairs in table.items():
        path = dest / rel
        if not path.is_file():
            drift.append(f"{rel}：文件不存在")
            continue
        text, crlf = normalise(path)
        lines = text.split("\n")
        misses = []
        for en, zh in pairs.items():
            hit = False
            for i, line in enumerate(lines):
                if line.strip() == en:
                    indent = line[: len(line) - len(line.lstrip())]
                    lines[i] = indent + zh
                    hit = True
            if hit:
                applied += 1
            else:
                misses.append(en)
        write_back(path, "\n".join(lines), crlf)
        if misses:
            drift.append(f"{rel}：{len(misses)} 条注释对不上（上游改过措辞）")
    log(f"注释：{applied}/{sum(len(v) for v in table.values())} 条替换成功")
    return applied, drift


def make_english_readme(repo: Path, dest: Path) -> None:
    """README.en.md = 上游 README.md 原文 + 首行语言链加一个中文入口。

    注意必须从**上游**那份取，不能从 dest 取：dest 的 README.md 已经被换成中文了。
    """
    src = repo / "README.md"
    if not src.is_file():
        return
    text, crlf = normalise(src)
    lines = text.split("\n")
    for i, line in enumerate(lines[:4]):
        if line.startswith("English"):
            lines[i] = "English · [Español](README.es.md) · [中文](README.md)"
            break
    write_back(dest / "README.en.md", "\n".join(lines), crlf)
    log("README.en.md：由上游 README.md 生成（只改首行语言链）")


# 仓库地址统一指向汉化分支（只在这几个文件里改，避免动到 third_party 与许可声明）
REF_FILES = ["README.en.md", "README.es.md", "pack/pack_payload.py", "pack/pack_payload.sh"]
REF_PAIRS = [("itsPLK/ps5-webkit-autoloader", "q1378659137/ps5-webkit-autoloader")]


def rewrite_refs(dest: Path) -> int:
    n = 0
    for rel in REF_FILES:
        path = dest / rel
        if not path.is_file():
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        crlf = "\r\n" in text
        body = text.replace("\r\n", "\n")
        before = body
        for old, new in REF_PAIRS:
            body = body.replace(old, new)
        if body != before:
            path.write_bytes((body.replace("\n", "\r\n") if crlf else body).encode("utf-8"))
            n += 1
    log(f"仓库引用：{n} 个文件指向汉化分支")
    return n


def compare_trees(a: Path, b: Path) -> list[str]:
    """列出两棵树的差异（不含 .git），用来实现 --check。"""
    out = []
    skip = {".git", "__pycache__"}
    fa = {p.relative_to(a).as_posix(): p for p in a.rglob("*")
          if p.is_file() and not (set(p.relative_to(a).parts) & skip)}
    fb = {p.relative_to(b).as_posix(): p for p in b.rglob("*")
          if p.is_file() and not (set(p.relative_to(b).parts) & skip)} if b.is_dir() else {}
    for rel in sorted(set(fa) | set(fb)):
        if rel not in fb:
            out.append(f"只有上游有：{rel}")
        elif rel not in fa:
            out.append(f"只有本地有：{rel}")
        elif fa[rel].read_bytes() != fb[rel].read_bytes():
            out.append(f"两边不同：{rel}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upstream", default=DEFAULT_UPSTREAM)
    ap.add_argument("--ref", default=None, help="分支 / tag，默认上游默认分支")
    ap.add_argument("--dest", default=str(DEFAULT_DEST), help="要重建的目录")
    ap.add_argument("--into", default=None, help="建到这个目录（本地原封不动）")
    ap.add_argument("--source", default=None, help="用已有的克隆，不联网")
    ap.add_argument("--check", action="store_true", help="只克隆并比对，不改任何文件")
    ap.add_argument("--skip-verify", action="store_true")
    args = ap.parse_args()

    dest = Path(args.into or args.dest).resolve()
    kit_ok = (KIT / "overlay").is_dir() and (KIT / "comments.json").is_file()
    if not kit_ok:
        raise SystemExit(f"zh-kit 不完整：{KIT}")

    repo = Path(args.source).resolve() if args.source else clone(args.upstream, args.ref)
    if not (repo / "flasher" / "index.html").is_file():
        raise SystemExit(f"{repo} 看起来不是这个项目的源码树")

    if args.check:
        log("\n--check：只报告，不写任何文件")
        diffs = compare_trees(repo, dest)
        if not diffs:
            log("（与本地完全一致）")
        for line in diffs[:80]:
            log("  " + line)
        if len(diffs) > 80:
            log(f"  …共 {len(diffs)} 条")
        return 0

    if args.into:
        if dest.exists():
            purge(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        log(f"目标目录：{dest}（新目录）")
    else:
        if dest.is_dir():
            zpath = backup(dest)
            log(f"已备份：{zpath}")
            # zh-kit 是重放要用的东西、out 是打包产物，都不能跟着清掉
            keep = {KIT.resolve(), (dest / "out").resolve()}
            for child in dest.iterdir():
                if child.resolve() in keep:
                    continue
                if child.is_dir() and not child.is_symlink():
                    purge(child)
                else:
                    child.unlink()
        else:
            dest.mkdir(parents=True, exist_ok=True)

    copy_tree(repo, dest)
    # .git 一并带走：这样 `git status` 能看出汉化改了哪些文件，
    # zh-firmware-strings.py --verify 的第 4 条（协议串检查）也才有 diff 可看。
    if (repo / ".git").is_dir() and not (dest / ".git").exists():
        shutil.copytree(repo / ".git", dest / ".git")
    log("上游代码已铺好")
    vendor = dest / "vendor"
    if vendor.is_dir() and not any(vendor.iterdir()):
        log("  [注意] vendor/ 是空的：上游克隆没带子模块。")
        log("         先跑 git submodule update --init --recursive --depth 1，")
        log("         否则 make 会找不到 mklittlefs / ps5-unified-autoloader。")

    apply_overlay(dest)
    _, patch_problems = apply_patches(dest)
    _, drift = apply_comments(dest)
    make_english_readme(repo, dest)
    rewrite_refs(dest)

    py = sys.executable
    log("\n应用固件文案表：")
    code, out = run([py, "tools/zh-firmware-strings.py"], dest)
    tail = [l for l in out.splitlines() if l.startswith("[FAIL]") or l.startswith("[MISS]")]
    log(f"  退出码 {code}" + ("" if not tail else f"，失败 {len(tail)} 条"))
    for line in tail[:10]:
        log("  " + line)

    code, out = run([py, "tools/sync-payload-pages.py"], dest)
    log("同步 PS5 侧产物：")
    for line in out.strip().splitlines():
        log("  " + line)

    code, out = run([py, "tools/zh-app-shell.py"], dest)
    log("Payload Manager 外壳文案：")
    for line in out.strip().splitlines()[-2:]:
        log("  " + line)

    problems = patch_problems + drift
    if problems:
        log("\n需要人工看一眼：")
        for p in problems:
            log("  - " + p)

    if not args.skip_verify:
        log("\n验收：")
        node = find_node()
        checks = [
            ([py, "tools/zh-firmware-strings.py", "--check"], "固件表 0 漂移"),
            ([py, "tools/zh-firmware-strings.py", "--verify"], "固件结构校验"),
            ([py, "tools/zh-app-shell.py", "--check"], "Payload Manager 外壳 0 漂移"),
            ([py, "debug/serial_timestamp.py", "--self-test"], "串口工具自检"),
        ]
        if node:
            checks = [([node, "tools/check-i18n.mjs"], "i18n 键一致性")] + checks + [
                ([node, "tools/verify-zh-render.mjs"], "刷写页渲染 30 条"),
                ([node, "tools/verify-zh-console-pages.mjs"], "PS5 侧页面 17 条"),
            ]
        else:
            log("  跳过渲染断言：没找到 node（设 NODE= 或装到默认位置）")
        failed = 0
        for cmd, label in checks:
            code, out = run(cmd, dest)
            if code != 0 and node and cmd[0] == node:
                # 连着起两个 Chrome 偶尔会撞上一次导航失败，重试一次再判
                log(f"  [retry] {label}：第一次没过，重试一次")
                code, out = run(cmd, dest)
            last = [l for l in out.strip().splitlines() if l.strip()]
            log(f"  [{'OK' if code == 0 else 'FAIL'}] {label}" + (f"  · {last[-1].strip()}" if last else ""))
            if code != 0:
                failed += 1
                for line in out.strip().splitlines()[-6:]:
                    log("        " + line)
        if failed:
            log(f"\n{failed} 项验收没过，别急着发布。")
            return 1

    log("\n完成。下一步："
        "\n  cd " + str(dest) +
        "\n  git status --short          # 看这次汉化改了哪些文件"
        "\n  git diff --stat              # 汉化改动的规模")
    return 0


if __name__ == "__main__":
    sys.exit(main())
