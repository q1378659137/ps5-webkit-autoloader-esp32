// 把站点在无头 Chrome 里跑一遍，列出**还带英文的可见文本**。
//
//   node tools/audit-zh-leftovers.mjs
//
// 判定方式很笨但很硬：取 document.body.innerText（真正画在屏幕上的文字），
// 再取 aria-label / title / placeholder / alt，凡是含 3 个以上连续英文字母、
// 又不在白名单（品牌名、芯片型号、协议串、单位、文件名）里的，就算残留。
//
// 白名单就是这项目的"故意不译"清单，见 LOCALIZATION.zh-CN.md §5。

import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { existsSync } from "node:fs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const SHOTS = join(ROOT, "tools", "shots");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".elf": "application/octet-stream",
};

// 这些是"故意不译"的东西，见 LOCALIZATION §5
const ALLOW = [
  /^(WebKit Autoloader|Payload Manager|PLK|itsPLK)$/i,
  /ESP32(-S2|-S3|-C3|-PICO|-PICO-KIT|-S3-DevKitC)?/i,
  /ESP8266|WROOM|TENSTAR|Lolin|Super Mini|DevKitC|PICO-KIT/i,
  /^(BOOT|RST|USB|MAC|SSID|GPIO|JTAG|COM|DNS|TLS|HTTP|HTTPS|IDF|AP|IP|LED|QFN|PCB|MD5|UI)$/i,
  /ESP32_PORTAL|12345678|autoload\.txt/,
  /\b(Success|Microsoft Connect Test|Microsoft NCSI)\b/,
  /\.(bin|elf|js|css|html|png|svg|json|crt|key)\b/i,
  /\b(MB|KB|GB|B|ms|s|fd)\b/,
  /\b(esptool-js|esptool|Wobkot|nxs|pako|unpkg|GitHub|Chrome|Edge|Firefox|Safari|Windows|macOS|Linux|Arduino|PlatformIO|LittleFS|AppCache|Payload)\b/,
  /\b(CP210x|CH340|CH34x|FTDI|Silabs|WCH)\b/i,
  /^[\x00-\x7F]*[0-9a-f]{6,}[\x00-\x7F]*$/i, // 纯哈希/编号
];

// 有明确理由保留英文的，单独列出来，别和"漏译"混在一起
const KNOWN = [
  [/^(ESPRESSIF|POWER|AMS1117|USB Bridge|RGB|UART|WiFi|Proant 440|PICO-D4|S2 Mini)$/i,
    "画在开发板上的丝印，译了反而和实物对不上"],
  [/^\[\*\] Agent:|^\[\+\] Agent:/, "漏洞利用打的 UA 日志，键名留着方便搜 issue"],
  [/^\[\+\] ===USERLAND===|^\[\+\] Initiate ARW/, "vendor/wobkot 的步骤日志"],
  [/^\[\*\] Starting Wobkot userland/, "app.js 的进度正则按这串匹配，译了进度条就不动"],
  [/^\[\*\] UA：/, "标签已译成「UA：」，后面本来就是浏览器的 UA 串"],
  [/Unsupported user agent/, "vendor/wobkot 抛的错，原文便于对照上游"],
  [/Object\.defineProperty called on non-object/, "JS 引擎自己的报错文本"],
];

const clean = (s) => s.replace(/\s+/g, " ").trim();

function leftovers(text) {
  const out = [];
  for (const raw of text.split(/\n+/)) {
    const line = clean(raw);
    if (!line) continue;
    if (!/[A-Za-z]{3,}/.test(line)) continue;
    if (/[\u4e00-\u9fff]/.test(line)) continue;          // 已经含中文，算混排
    if (ALLOW.some((re) => re.test(line))) continue;
    if (/^[\s\d\-–—:：·|/\\()[\].%,+*=<>#!?&"'`^~_]+$/.test(line)) continue;
    out.push(line);
  }
  return out;
}

function loadPuppeteer() {
  const dirs = [process.env.PUPPETEER_DIR,
    join(process.env.USERPROFILE || "", ".workbuddy", "binaries", "node", "workspace"),
    join(process.env.HOME || "", ".workbuddy", "binaries", "node", "workspace"),
    ROOT].filter((d) => d && existsSync(join(d, "package.json")));
  for (const d of dirs) {
    try { return createRequire(join(d, "package.json"))("puppeteer-core"); } catch { /* next */ }
  }
  throw new Error("puppeteer-core not found; set PUPPETEER_DIR");
}

function chromePath() {
  const list = [process.env.CHROME,
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome", "/usr/bin/chromium"].filter(Boolean);
  const hit = list.find((p) => existsSync(p));
  if (!hit) throw new Error("Chrome not found; set CHROME=");
  return hit;
}

// 一个服务器同时挂两份站点：/ → host/packed（开发板发给 PS5 的），/flasher/ → flasher
function serve() {
  const server = createServer(async (req, res) => {
    const url = decodeURIComponent(req.url.split("?")[0]);
    let base, rel;
    if (url === "/flasher" || url.startsWith("/flasher/")) {
      base = join(ROOT, "flasher");
      rel = url.slice("/flasher".length);
      if (rel === "" || rel === "/") rel = "/index.html";
    } else {
      base = join(ROOT, "host", "packed");
      rel = url === "/" ? "/index.html" : url;
    }
    const path = join(base, rel);
    if (!normalize(path).startsWith(normalize(ROOT))) { res.writeHead(403).end(); return; }
    try {
      const body = await readFile(path);
      res.writeHead(200, { "content-type": MIME[extname(path)] || "application/octet-stream" });
      res.end(body);
    } catch {
      res.writeHead(404, { "content-type": "text/plain; charset=utf-8" }).end("not found");
    }
  });
  return new Promise((ok) => server.listen(0, "127.0.0.1", () => ok(server)));
}

const PS5_UA = "Mozilla/5.0 (PlayStation; PlayStation 5/8.00) AppleWebKit/605.1.15 (KHTML, like Gecko)";

const server = await serve();
const base = `http://127.0.0.1:${server.address().port}`;
const puppeteer = loadPuppeteer();
await mkdir(SHOTS, { recursive: true });
const browser = await puppeteer.launch({ executablePath: chromePath(), headless: "new", args: ["--no-sandbox"] });

const pages = [
  { name: "flasher（刷写工具，中文）", url: `${base}/flasher/?lang=zh&board=s2`, shot: "audit-flasher.png" },
  { name: "PS5 侧：安装器过渡页", url: `${base}/`, ua: PS5_UA, shot: "audit-console-index.png" },
  { name: "PS5 侧：缓存进度页", url: `${base}/cache.html`, ua: PS5_UA, shot: "audit-console-cache.png" },
  { name: "PS5 侧：Payload Manager", url: `${base}/app/index.html`, ua: PS5_UA, shot: "audit-app.png" },
];

let total = 0;
for (const spec of pages) {
  const page = await browser.newPage();
  if (spec.ua) await page.setUserAgent(spec.ua);
  await page.setViewport({ width: 1100, height: 760 });
  await page.goto(spec.url, { waitUntil: "networkidle2", timeout: 20000 }).catch(() => {});
  await new Promise((r) => setTimeout(r, 600));

  const text = await page.evaluate(() => document.body?.innerText || "");
  const attrs = await page.evaluate(() => {
    const out = [];
    for (const el of document.querySelectorAll("[aria-label],[title],[placeholder],[alt]")) {
      for (const a of ["aria-label", "title", "placeholder", "alt"]) {
        const v = el.getAttribute(a);
        if (v) out.push(v);
      }
    }
    return out.join("\n");
  });

  const found = leftovers(text + "\n" + attrs);
  const known = [];
  const left = [];
  for (const line of found) {
    const hit = KNOWN.find(([re]) => re.test(line));
    if (hit) known.push(`${line}   ← ${hit[1]}`);
    else left.push(line);
  }

  console.log(`\n=== ${spec.name} ===`);
  console.log(`  URL: ${spec.url.replace(base, "")}   可见文本 ${text.length} 字符   待查 ${left.length} 行   已知保留 ${known.length} 行`);
  for (const line of left.slice(0, 25)) console.log("   · " + line.slice(0, 120));
  if (left.length > 25) console.log(`   …还有 ${left.length - 25} 行`);
  for (const line of known.slice(0, 6)) console.log("   - " + line.slice(0, 130));
  total += left.length;

  await page.screenshot({ path: join(SHOTS, spec.shot), fullPage: false });
  await page.close();
}

await browser.close();
server.close();
console.log(`\n合计可疑 ${total} 行。截图在 tools/shots/audit-*.png`);
