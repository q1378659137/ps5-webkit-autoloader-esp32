// 把译好的 installer 页面真跑一遍，走到"安装完成"那条分支，断言是中文。
//
//   node tools/verify-zh-installer-page.mjs --page <那份 index.html>
//
// 做法：本地起个服务把页面发出去，把 `/app/<v>/__complete__` 和 `/install` 都做成 200，
// 再用 evaluateOnNewDocument 塞一个假的 window.applicationCache 并手动触发 `cached`，
// 这样页面就会走 install() → 成功分支，显示"安装完成"。
//
// 这一页正常是 installer ELF 在 PS5 的 127.0.0.1:18181 上发出来的，本仓库改不到它；
// 这个脚本只是证明"译文放进页面后能正确渲染"。

import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { existsSync } from "node:fs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const SHOTS = join(ROOT, "tools", "shots");
const VERSION = "0.8.4";

const argPage = (() => {
  const i = process.argv.indexOf("--page");
  return i > 0 ? process.argv[i + 1] : null;
})();

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

const pagePath = argPage || join(ROOT, "zh-kit", "upstream", "installer-page", "index.html");
const html = (await readFile(pagePath, "utf8"))
  .replaceAll("[[VERSION_PLACEHOLDER]]", VERSION)
  .replaceAll("[[BUILD_TIME_PLACEHOLDER]]", "2026-11-23 00:59:37 UTC");

const server = createServer((req, res) => {
  const url = req.url.split("?")[0];
  if (url === "/" || url === "/index.html") {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" }).end(html);
    return;
  }
  if (url.endsWith("/__complete__")) {
    res.writeHead(200, { "content-type": "text/plain; charset=utf-8" }).end(VERSION);
    return;
  }
  if (url === "/install" || url === "/clear-webkit-data") {
    res.writeHead(200, { "content-type": "text/plain; charset=utf-8" }).end("ok");
    return;
  }
  if (url === "/cache.appcache") {
    res.writeHead(200, { "content-type": "text/cache-manifest; charset=utf-8" }).end("CACHE MANIFEST\n");
    return;
  }
  if (url === "/logo.svg") {
    res.writeHead(200, { "content-type": "image/svg+xml" }).end("<svg xmlns='http://www.w3.org/2000/svg'/>");
    return;
  }
  res.writeHead(404, { "content-type": "text/plain; charset=utf-8" }).end("404");
});
await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
const base = `http://127.0.0.1:${server.address().port}`;

const puppeteer = loadPuppeteer();
await mkdir(SHOTS, { recursive: true });
const browser = await puppeteer.launch({ executablePath: chromePath(), headless: "new", args: ["--no-sandbox"] });
const page = await browser.newPage();
await page.setViewport({ width: 1000, height: 780 });

// 假的 applicationCache：记录监听器，稍后手动触发 cached
await page.evaluateOnNewDocument(() => {
  const handlers = {};
  window.applicationCache = {
    status: 0, UNCACHED: 0, IDLE: 1, CHECKING: 2, DOWNLOADING: 3, UPDATEREADY: 4, OBSOLETE: 5,
    swapCache() {},
    addEventListener(name, fn) { (handlers[name] = handlers[name] || []).push(fn); },
    __fire(name) { for (const fn of handlers[name] || []) fn({}); },
  };
});

const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(`${base}/index.html`, { waitUntil: "load" });
await page.evaluate(() => window.applicationCache.__fire("cached"));
await page.waitForFunction(() => document.getElementById("status")?.textContent.includes("安装"), { timeout: 8000 })
  .catch(() => {});

const status = await page.$eval("#status", (n) => n.textContent.trim());
const detail = await page.$eval("#detail", (n) => n.textContent.trim());
const title = await page.title();
const lang = await page.evaluate(() => document.documentElement.lang);
const charset = await page.evaluate(() => document.characterSet);
const garbled = await page.evaluate(() => document.body.innerText.includes("\uFFFD"));
const shot = join(SHOTS, "installer-page-zh.png");
await page.screenshot({ path: shot });
await browser.close();
server.close();

const checks = [
  ["状态行 = 安装完成", status === "安装完成", status],
  ["提示行是中文", detail.includes("重启主机"), detail],
  ["标题中文 + 版本号", title.includes("安装器") && title.includes(VERSION), title],
  ["lang = zh-CN", lang === "zh-CN", lang],
  ["UTF-8 且无乱码", charset.toUpperCase() === "UTF-8" && !garbled, charset],
  ["无 JS 报错", errors.length === 0, errors.slice(0, 2).join(" | ")],
];

let bad = 0;
for (const [name, pass, got] of checks) {
  console.log(`${pass ? "  ok  " : " FAIL "} ${name}${got ? `  (${String(got).slice(0, 70)})` : ""}`);
  if (!pass) bad++;
}
console.log(`\n${checks.length - bad}/${checks.length} passed  ·  截图 ${shot}`);
process.exit(bad ? 1 : 0);
