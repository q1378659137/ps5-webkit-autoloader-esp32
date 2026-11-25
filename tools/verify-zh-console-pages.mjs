// 渲染开发板发给 PS5 的那两个页面，断言它们确实是中文。
// 这两页没有语言开关（文案是写死的），所以唯一靠谱的证据是渲染。
//
//   node tools/verify-zh-console-pages.mjs
//
// 用固件同样的 Content-Type（text/html; charset=utf-8）提供 host/packed/
// （真正进固件的那份产物），并伪造 PS5 的 UA，让页面里那段固件判断的两条分支
// 都能走一遍。
//
// 需要 puppeteer-core + Chrome，和 verify-zh-render.mjs 一样（PUPPETEER_DIR / CHROME）。

import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, extname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { existsSync } from "node:fs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const SITE = join(ROOT, "host", "packed");
const SHOTS = join(ROOT, "tools", "shots");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".json": "application/json; charset=utf-8",
};

function loadPuppeteer() {
  const dirs = [process.env.PUPPETEER_DIR,
    join(process.env.USERPROFILE || "", ".workbuddy", "binaries", "node", "workspace"),
    join(process.env.HOME || "", ".workbuddy", "binaries", "node", "workspace"),
    ROOT].filter((d) => d && existsSync(join(d, "package.json")));
  for (const d of dirs) {
    try {
      return createRequire(join(d, "package.json"))("puppeteer-core");
    } catch { /* next */ }
  }
  throw new Error("puppeteer-core not found. Set PUPPETEER_DIR to a directory that has it.");
}

function chromePath() {
  const list = [process.env.CHROME,
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome", "/usr/bin/chromium"].filter(Boolean);
  const hit = list.find((p) => existsSync(p));
  if (!hit) throw new Error("Chrome not found. Set CHROME=/path/to/chrome.");
  return hit;
}

// 页面从 user agent 里读自己的固件版本。
const PS5_UA = (fw) => `Mozilla/5.0 (PlayStation; PlayStation 5/${fw}) AppleWebKit/605.1.15 (KHTML, like Gecko)`;

// 页面必须显示的版本号和构建时间取自打包步骤写下的清单。写死在这里的话，
// 每次 bump payload 都会变成一次假失败。
async function payloadVersion() {
  const head = (await readFile(join(SITE, "cache.appcache"), "utf8"))
    .split("\n").find((l) => l.startsWith("# WebKit Autoloader"));
  const m = /v(\S+) \(built ([^)]+)\)/.exec(head || "");
  if (!m) throw new Error("cannot read version from host/packed/cache.appcache");
  return { version: m[1], built: m[2] };
}

function serve() {
  const server = createServer(async (req, res) => {
    const url = decodeURIComponent(req.url.split("?")[0]);
    const path = join(SITE, url === "/" ? "index.html" : url);
    if (!path.startsWith(SITE)) { res.writeHead(403).end(); return; }
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

const results = [];
const ok = (name, pass, detail = "") => {
  results.push({ name, pass });
  console.log(`${pass ? "  ok  " : " FAIL "} ${name}${detail ? `  (${detail})` : ""}`);
};

const text = (page, sel) => page.$eval(sel, (n) => n.textContent.trim()).catch(() => null);

const server = await serve();
const base = `http://127.0.0.1:${server.address().port}`;
const puppeteer = loadPuppeteer();
await mkdir(SHOTS, { recursive: true });
const browser = await puppeteer.launch({ executablePath: chromePath(), headless: "new", args: ["--no-sandbox"] });
const errors = [];

async function newPage(fw) {
  const page = await browser.newPage();
  page.on("pageerror", (e) => errors.push(`${fw}: ${e.message}`));
  await page.setUserAgent(PS5_UA(fw));
  await page.setViewport({ width: 900, height: 640 });
  return page;
}

// 1. 支持范围内的固件：页面准备缓存并跳转。把跳转拦在原地。
const a = await newPage("8.00");
await a.setRequestInterception(true);
a.on("request", (req) => {
  if (req.url().endsWith("/cache.html")) return req.respond({ status: 204, body: "" });
  return req.continue();
});
await a.goto(`${base}/`, { waitUntil: "networkidle2" });
await a.waitForFunction(() => document.getElementById("status")?.textContent.includes("准备"));

const { version, built } = await payloadVersion();
ok("index：<html lang>", (await a.evaluate(() => document.documentElement.lang)) === "zh-CN");
ok("index：标题中文 + 版本号",
  (await a.title()) === `WebKit Autoloader 安装器 v${version}（PLK 构建，${built}）`, await a.title());
ok("index：h1", (await text(a, "h1")) === "WebKit Autoloader 安装器", await text(a, "h1"));
ok("index：状态行", (await text(a, "#status")) === "正在准备缓存…", await text(a, "#status"));
ok("index：提示行", (await text(a, "#detail")) === "请稍等片刻，先不要关闭这个页面！");
ok("index：页脚开源说明", ((await text(a, "#footer")) || "").includes("本项目免费开源"));
ok("index：CJK 字体在字体栈里",
  /PingFang SC|Microsoft YaHei|Noto Sans SC/.test(await a.$eval("body", (n) => getComputedStyle(n).fontFamily)));
ok("index：UTF-8 解码无乱码",
  await a.evaluate(() => document.characterSet === "UTF-8" && !document.body.innerText.includes("\uFFFD")));
await a.screenshot({ path: join(SHOTS, "console-index.png") });
await a.close();

// 2. 超出支持范围的固件：报错分支也是中文。
const b = await newPage("6.00");
await b.goto(`${base}/`, { waitUntil: "networkidle2" });
await b.waitForFunction(() => document.getElementById("status")?.textContent.includes("不支持"));
ok("index：不支持固件时状态行", (await text(b, "#status")) === "不支持的固件 6.00", await text(b, "#status"));
ok("index：错误态样式", (await b.$eval("#status", (n) => n.className)) === "error");
ok("index：支持范围说明", ((await text(b, "#detail")) || "").includes("7.00–12.00 走 Poops"));
await b.screenshot({ path: join(SHOTS, "console-unsupported.png") });
await b.close();

// 3. 缓存页。Chrome 已经移除 AppCache，所以这里走的是 !cache 分支 ——
//    这也顺带证明改写之后内联脚本还能跑。
const c = await newPage("8.00");
await c.goto(`${base}/cache.html`, { waitUntil: "networkidle2" });
ok("cache：初始/降级状态为中文",
  ["正在缓存内容…", "这个浏览器不支持离线 AppCache。"].includes(await text(c, "#status")), await text(c, "#status"));
ok("cache：h1", (await text(c, "h1")) === "WebKit Autoloader 安装器");
ok("cache：进度条 aria-label", (await c.$eval("#progress", (n) => n.getAttribute("aria-label"))) === "缓存下载进度");
ok("cache：页脚", ((await text(c, "#footer")) || "").includes("本项目免费开源"));
ok("cache：UTF-8 解码无乱码",
  await c.evaluate(() => document.characterSet === "UTF-8" && !document.body.innerText.includes("\uFFFD")));
await c.screenshot({ path: join(SHOTS, "console-cache.png") });
await c.close();

ok("无 JS 报错", errors.length === 0, errors.slice(0, 3).join(" | "));

await browser.close();
server.close();

const failed = results.filter((r) => !r.pass);
console.log(`\n${results.length - failed.length}/${results.length} passed  ·  shots in tools/shots/`);
if (failed.length) process.exit(1);
