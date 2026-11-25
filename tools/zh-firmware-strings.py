"""固件里的中文文案，逐行精确对照的一张表。

直接运行就是应用；带 --check 只报告（合完上游马上跑最有用：
对不上的每一条都会列出来，而且一个字都不写）。

    python tools/zh-firmware-strings.py            # 应用
    python tools/zh-firmware-strings.py --check     # 只报告

这份表里写死了几条规矩，以及为什么：

* 只翻译 `Serial` / 日志文本和 404 的**正文**。其它一律保持英文，
  这是有意的：
  - "Success"、"Microsoft Connect Test"、"Microsoft NCSI"、"OK" 是强制门户的
    握手应答：系统会比对正文，译了网络检测就失效。
  - `strcmp(sni, "incomplete")` 是拿字面量和返回值比较。
  - SSID `ESP32_PORTAL` 和密码同时出现在 README、刷写工具和 PS5 上。
  - HTTP 状态行、header 值、MIME、路由是协议，不是文案。
* 格式占位符必须一比一保留，所以每条都断言了 `%d`/`%s` 的个数。
* 文件是 CRLF，按 "\\r\\n" 切分再拼回去，别的地方一个字节都不动。
* 全有或全无：只要有一条不对，整轮就中止，一个字节都不写。
* 写成 UTF-8 无 BOM。凡是中文要经 HTTP 出去的，都显式带上
  `charset=utf-8`，否则 PS5 上就是乱码。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import os

ROOT = Path(os.environ.get("ZH_ROOT") or Path(__file__).resolve().parent.parent)
NEWLINE = "\r\n"
SPEC = re.compile(r"%(?:[-+ 0#]*\d*(?:\.\d+)?(?:hh|h|ll|l|j|z|t|L)?[diouxXeEfgGaAcspn%])")

# （文件，原行，新行）
TABLE: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
    # ---- ESP32：启动横幅 -----------------------------------------------------
    ("firmware/esp32/esp32-arduino.ino", (
        '        "Arduino ESP32: %d.%d.%d\\n",',
    ), (
        '        "Arduino ESP32 版本: %d.%d.%d\\n",',
    )),
    ("firmware/esp32/esp32-arduino.ino", (
        '    Serial.print("IDF version: ");',
    ), (
        '    Serial.print("IDF 版本: ");',
    )),
    ("firmware/esp32/esp32-arduino.ino", (
        '    Serial.printf("Flash size: %d MB\\n", ESP.getFlashChipSize()/1024/1024);',
    ), (
        '    Serial.printf("闪存容量: %d MB\\n", ESP.getFlashChipSize()/1024/1024);',
    )),
    ("firmware/esp32/esp32-arduino.ino", (
        '    Serial.println("BOOT");',
    ), (
        '    Serial.println("启动完成，开始初始化");',
    )),
    ("firmware/esp32/esp32-arduino.ino", (
        '    Serial.println("Starting WebServer");',
    ), (
        '    Serial.println("正在启动 Web 服务");',
    )),
    ("firmware/esp32/esp32-arduino.ino", (
        '    Serial.println("Starting HTTPS Server");',
    ), (
        '    Serial.println("正在启动 HTTPS 服务");',
    )),
    ("firmware/esp32/esp32-arduino.ino", (
        '    Serial.println("READY");',
    ), (
        '    Serial.println("准备就绪");',
    )),

    # ---- ESP32：HTTP 服务 -----------------------------------------------------
    ("firmware/esp32/http_server.cpp", (
        '    portalLogHeap("HTTP network test");',
    ), (
        '    portalLogHeap("网络连通性测试");',
    )),
    ("firmware/esp32/http_server.cpp", (
        '    portalLogHeap("HTTP file begin");',
    ), (
        '    portalLogHeap("开始发送文件");',
    )),
    ("firmware/esp32/http_server.cpp", (
        '        portalLogHeap("HTTP manifest end");',
    ), (
        '        portalLogHeap("清单发送完成");',
    )),
    ("firmware/esp32/http_server.cpp", (
        '    portalLogHeap("HTTP file end");',
    ), (
        '    portalLogHeap("文件发送完成");',
    )),
    ("firmware/esp32/http_server.cpp", (
        '            webServer.send(404, "text/plain", "404 Not Found");',
    ), (
        '            webServer.send(404, "text/plain; charset=utf-8", "404：页面不存在");',
    )),
    ("firmware/esp32/http_server.cpp", (
        '    Serial.println("HTTP: OK");',
    ), (
        '    Serial.println("HTTP 已启动");',
    )),

    # ---- ESP32：HTTPS 服务 + TLS 调试 -----------------------------------------
    ("firmware/esp32/https_server.cpp", (
        '    Serial.printf("[TLS] handshake OK: fd=%d\\n", event->tls->sockfd);',
    ), (
        '    Serial.printf("[TLS] 握手成功: fd=%d\\n", event->tls->sockfd);',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    logTlsMemory("after handshake");',
    ), (
        '    logTlsMemory("握手完成");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    Serial.printf("[TLS] ClientHello fd=%d sni=%s\\n", sockfd, sni);',
    ), (
        '    Serial.printf("[TLS] 收到 ClientHello fd=%d sni=%s\\n", sockfd, sni);',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    logTlsMemory("before handshake");',
    ), (
        '    logTlsMemory("握手前");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    Serial.printf("[TLS] handshake fd=%d sni=%s result=%d\\n", sockfd, sni, result);',
    ), (
        '    Serial.printf("[TLS] 握手 fd=%d sni=%s result=%d\\n", sockfd, sni, result);',
    )),
    ("firmware/esp32/https_server.cpp", (
        '        logTlsMemory("handshake failed");',
    ), (
        '        logTlsMemory("握手失败");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    portalLogHeap("HTTPS file begin");',
    ), (
        '    portalLogHeap("开始发送文件");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    portalLogHeap("HTTPS fixed URL");',
    ), (
        '    portalLogHeap("固定探测路径");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    portalLogHeap("HTTPS network test");',
    ), (
        '    portalLogHeap("网络连通性测试");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '        portalLogHeap("HTTPS manifest end");',
    ), (
        '        portalLogHeap("清单发送完成");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    portalLogHeap("HTTPS file end");',
    ), (
        '    portalLogHeap("文件发送完成");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    logTlsMemory("before HTTPS start");',
    ), (
        '    logTlsMemory("HTTPS 启动前");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '        logTlsMemory("HTTPS start failed");',
    ), (
        '        logTlsMemory("HTTPS 启动失败");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    logTlsMemory("HTTPS listening");',
    ), (
        '    logTlsMemory("HTTPS 监听中");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    Serial.printf("cert len: %u, last: %02X\\n",',
        '                  (unsigned)server_crt_len, server_crt[server_crt_len - 1]);',
    ), (
        '    Serial.printf("证书长度: %u, 末字节: %02X\\n",',
        '                  (unsigned)server_crt_len, server_crt[server_crt_len - 1]);',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    Serial.printf("key len: %u, last: %02X\\n",',
        '                  (unsigned)server_key_len, server_key[server_key_len - 1]);',
    ), (
        '    Serial.printf("密钥长度: %u, 末字节: %02X\\n",',
        '                  (unsigned)server_key_len, server_key[server_key_len - 1]);',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    Serial.println("Starting httpd_ssl_start...");',
    ), (
        '    Serial.println("正在启动 httpd_ssl_start…");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '        Serial.printf("HTTPS start failed: %s\\n", esp_err_to_name(err));',
    ), (
        '        Serial.printf("HTTPS 启动失败: %s\\n", esp_err_to_name(err));',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    Serial.println("HTTPS socket started");',
    ), (
        '    Serial.println("HTTPS 套接字已启动");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '                "HTTPS route registration failed: method=%d uri=%s error=%s\\n",',
    ), (
        '                "HTTPS 路由注册失败: method=%d uri=%s error=%s\\n",',
    )),
    ("firmware/esp32/https_server.cpp", (
        '    Serial.println("HTTPS: OK");',
    ), (
        '    Serial.println("HTTPS 已启动");',
    )),
    ("firmware/esp32/https_server.cpp", (
        '        httpd_resp_set_status(req, "404 Not Found");',
        '        httpd_resp_set_type(req, "text/plain");',
        '        httpd_resp_send(req, "404 Not Found", HTTPD_RESP_USE_STRLEN);',
    ), (
        '        httpd_resp_set_status(req, "404 Not Found");',
        '        httpd_resp_set_type(req, "text/plain; charset=utf-8");',
        '        httpd_resp_send(req, "404：页面不存在", HTTPD_RESP_USE_STRLEN);',
    )),

    # ---- ESP32：热点与存储 -----------------------------------------------------
    ("firmware/esp32/wifi_ap.cpp", (
        '    Serial.printf("softAPConfig: %s\\n", configResult ? "OK" : "FAILED");',
    ), (
        '    Serial.printf("AP 参数配置: %s\\n", configResult ? "OK" : "FAILED");',
    )),
    ("firmware/esp32/wifi_ap.cpp", (
        '    Serial.printf("softAP: %s\\n", apResult ? "OK" : "FAILED");',
    ), (
        '    Serial.printf("热点启动: %s\\n", apResult ? "OK" : "FAILED");',
    )),
    ("firmware/esp32/wifi_ap.cpp", (
        '    Serial.print("AP IP: ");',
    ), (
        '    Serial.print("AP 地址: ");',
    )),
    ("firmware/esp32/wifi_ap.cpp", (
        '    Serial.printf("Channel: %d\\n", WiFi.channel());',
    ), (
        '    Serial.printf("信道: %d\\n", WiFi.channel());',
    )),
    ("firmware/esp32/wifi_ap.cpp", (
        '    Serial.println("Starting DNS");',
    ), (
        '    Serial.println("正在启动 DNS 劫持");',
    )),
    ("firmware/esp32/host_files.cpp", (
        '        Serial.println("LittleFS mount failed");',
    ), (
        '        Serial.println("LittleFS 挂载失败");',
    )),
    ("firmware/esp32/host_files.cpp", (
        '    Serial.println("LittleFS mounted");',
    ), (
        '    Serial.println("LittleFS 已挂载");',
    )),

    # ---- ESP8266 ---------------------------------------------------------------
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.println("\\nBOOT ESP8266");',
    ), (
        '    Serial.println("\\nESP8266 启动");',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.printf("Core: %s, SDK: %s\\n", ESP.getCoreVersion().c_str(), ESP.getSdkVersion());',
    ), (
        '    Serial.printf("内核: %s, SDK: %s\\n", ESP.getCoreVersion().c_str(), ESP.getSdkVersion());',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.printf("Reset: %s\\n", ESP.getResetReason().c_str());',
    ), (
        '    Serial.printf("复位原因: %s\\n", ESP.getResetReason().c_str());',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.printf("Flash: configured=%u MB, detected=%u MB, CPU=%u MHz\\n",',
    ), (
        '    Serial.printf("闪存: 配置=%u MB, 检测=%u MB, CPU=%u MHz\\n",',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '        Serial.println("LittleFS: FAILED");',
    ), (
        '        Serial.println("LittleFS: 挂载失败");',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '        Serial.printf("LittleFS: OK, total=%u, used=%u bytes\\n", info.totalBytes, info.usedBytes);',
    ), (
        '        Serial.printf("LittleFS: 已挂载, 总计=%u, 已用=%u 字节\\n", info.totalBytes, info.usedBytes);',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.printf("softAPConfig: %s\\n",',
    ), (
        '    Serial.printf("AP 参数配置: %s\\n",',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.printf("softAP: %s\\n", ap ? "OK" : "FAILED");',
    ), (
        '    Serial.printf("热点启动: %s\\n", ap ? "OK" : "FAILED");',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.printf("AP IP: %s\\n", WiFi.softAPIP().toString().c_str());',
    ), (
        '    Serial.printf("AP 地址: %s\\n", WiFi.softAPIP().toString().c_str());',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.printf("Channel: %d\\n", WiFi.channel());',
    ), (
        '    Serial.printf("信道: %d\\n", WiFi.channel());',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.println("Starting HTTP");',
    ), (
        '    Serial.println("正在启动 HTTP 服务");',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.println("Starting HTTPS");',
    ), (
        '    Serial.println("正在启动 HTTPS 服务");',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    portalLogHeap("HTTP ready");',
    ), (
        '    portalLogHeap("HTTP 就绪");',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    portalLogHeap("HTTPS ready");',
    ), (
        '    portalLogHeap("HTTPS 就绪");',
    )),
    ("firmware/esp8266/esp8266-arduino.ino", (
        '    Serial.println("READY");',
    ), (
        '    Serial.println("准备就绪");',
    )),
    ("firmware/esp8266/routes.h", (
        '    portalLogHeap("file begin");',
    ), (
        '    portalLogHeap("开始发送文件");',
    )),
    ("firmware/esp8266/routes.h", (
        '            server.send(404, "text/plain", "404 Not Found");',
    ), (
        '            server.send(404, "text/plain; charset=utf-8", "404：页面不存在");',
    )),
    ("firmware/esp8266/routes.h", (
        '    portalLogHeap("file end");',
    ), (
        '    portalLogHeap("文件发送完成");',
    )),
]


def specs(lines: tuple[str, ...]) -> list[str]:
    return sorted(SPEC.findall("\n".join(lines)))


LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"')
CJK = re.compile(r"[\u4e00-\u9fff\uff00-\uffef\u3000-\u303f]")


def skeleton(lines: tuple[str, ...]) -> str:
    """Code with the contents of every string literal removed."""
    return LITERAL.sub('""', "\n".join(lines))


# 这些行永远不能翻译：操作系统或 HTTP 栈会拿它们做比较。
PROTOCOL = re.compile(
    rb"Success|Microsoft Connect Test|Microsoft NCSI|\"incomplete\"|ESP32_PORTAL|"
    rb"12345678|text/html; charset=utf-8|application/octet-stream|no-cache")


def git_diff_lines() -> list[bytes]:
    """Lines removed by `git diff -U0 -- firmware`, so we can prove none held a protocol string."""
    try:
        out = subprocess.run(["git", "diff", "-U0", "--", "firmware"],
                             cwd=ROOT, check=True, capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError):
        print("[warn] git not usable here; the protocol-string check is skipped")
        return []
    return [l[1:] for l in out.splitlines()
            if l.startswith(b"-") and not l.startswith(b"---")]


def verify() -> int:
    bad = 0

    # 1. 表里每条都是纯字符串替换：周围的代码一个字没动。
    for rel, old, new in TABLE:
        if skeleton(old) != skeleton(new):
            print(f"[FAIL] table entry is not a pure string edit: {rel}: {old[0].strip()[:50]}")
            bad += 1

    # 2. 源文件是 UTF-8、无 BOM、CRLF，且中文只出现在给人看的字符串里。
    for path in sorted((ROOT / "firmware").rglob("*")):
        if path.suffix not in (".cpp", ".h", ".ino"):
            continue
        raw = path.read_bytes()
        rel = path.relative_to(ROOT).as_posix()
        if raw.startswith(b"\xef\xbb\xbf"):
            print(f"[FAIL] {rel}: has a UTF-8 BOM")
            bad += 1
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as err:
            print(f"[FAIL] {rel}: not valid UTF-8 ({err})")
            bad += 1
            continue
        if b"\r\n" not in raw:
            print(f"[FAIL] {rel}: line endings are no longer CRLF")
            bad += 1

        lines = text.split("\r\n")
        for i, line in enumerate(lines):
            if not CJK.search(line):
                continue
            allowed = ("Serial.", "logTlsMemory(", "portalLogHeap(", "404：页面不存在")
            # 跨多行的 `Serial.printf(` 会把字面量单独放到一行。
            window = lines[max(0, i - 3):i] + [line]
            if not any(a in "".join(window) for a in allowed):
                print(f"[FAIL] {rel}:{i + 1}: Chinese leaked outside a log/body string")
                print(f"        {line.strip()[:90]}")
                bad += 1

    # 3. 没有任何协议串被删除或改写，只有我们自己的改动例外。
    legit = {"\n".join(o).encode("utf-8") for _, o, _ in TABLE}
    for line in git_diff_lines():
        if PROTOCOL.search(line) and line not in legit:
            print(f"[FAIL] protocol string touched: {line.decode('utf-8', 'replace').strip()[:90]}")
            bad += 1

    print(f"\n{'OK' if not bad else str(bad) + ' problem(s)'}: "
          f"UTF-8 + no BOM + CRLF, Chinese only in log/body strings, "
          f"captive-portal and comparison strings untouched.")
    return 1 if bad else 0


def apply_one(path: Path, old: tuple[str, ...], new: tuple[str, ...]) -> tuple[bool, str]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return False, "file starts with a BOM"
    text = raw.decode("utf-8")
    if NEWLINE not in text:
        return False, "file is not CRLF"
    lines = text.split(NEWLINE)

    def count(seq: tuple[str, ...]) -> int:
        return sum(1 for i in range(len(lines) - len(seq) + 1) if tuple(lines[i:i + len(seq)]) == seq)

    # 可重复运行：已经是新内容的那行不算错。
    if count(new) == 1 and count(old) == 0:
        return True, "already applied"

    hits = count(old)
    if hits != 1:
        return False, f"expected 1 match, found {hits}"
    if specs(old) != specs(new):
        return False, f"format specifiers changed: {specs(old)} -> {specs(new)}"
    if "\n".join(old).count('"') != "\n".join(new).count('"'):
        return False, "quote count changed"

    i = next(i for i in range(len(lines) - len(old) + 1) if tuple(lines[i:i + len(old)]) == old)
    lines[i:i + len(old)] = list(new)
    path.write_bytes(NEWLINE.join(lines).encode("utf-8"))
    return True, "ok"


def main() -> int:
    if "--verify" in sys.argv:
        return verify()
    check = "--check" in sys.argv
    cache: dict[Path, str] = {}
    bad = 0
    done = 0

    for rel, old, new in TABLE:
        path = ROOT / rel
        if not path.is_file():
            print(f"[MISS] {rel}: file not found")
            bad += 1
            continue
        # 以文件当前内容为准逐条应用（各条之间互不依赖）。
        if check:
            text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
            state = "applied" if "\n".join(new).replace("\r\n", "\n") in text else (
                "pending" if "\n".join(old) in text else "CHANGED UPSTREAM")
            print(f"[{state:>14}] {rel}: {old[0].strip()[:60]}")
            if state == "CHANGED UPSTREAM":
                bad += 1
            continue

        ok, why = apply_one(path, old, new)
        print(f"{'[ OK ]' if ok else '[FAIL]'} {rel}: {old[0].strip()[:60]}  {why}")
        if ok:
            done += 1
        else:
            bad += 1

    if check:
        print(f"\n{bad} entr{'y' if bad == 1 else 'ies'} drifted from the table.")
        return 1 if bad else 0

    if bad:
        print(f"\n{bad} entr{'y' if bad == 1 else 'ies'} failed. Files already written keep their change;"
              "\nre-run after `git checkout -- firmware` to start from a clean tree.")
        return 1
    print(f"\n{done} lines localised. Now verify: python tools/zh-firmware-strings.py --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
