// 用无头 Chrome 渲染 flasher/，断言中文界面真的画出来了。
// 不是靠肉眼看截图：每条断言都读 textContent / aria-pressed / 计算样式。
//
//   node tools/verify-zh-render.mjs
//
// 需要 puppeteer-core。把 PUPPETEER_DIR 指到装了它的目录，
// 或者先在该目录里 npm i puppeteer-core。
// Chrome：CHROME=/path/to/chrome，不设就按 Windows/macOS/Linux 的常见位置找。
//
// 页面会从 unpkg 引入 esptool-js，并向 GitHub 查最新发行版，所以这些请求
// 都在本地应答。这样离线也能跑，结果也稳定。
// 页面接真实网络时的行为完全不变。

import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, extname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { existsSync } from "node:fs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const SITE = join(ROOT, "flasher");
const SHOTS = join(ROOT, "tools", "shots");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".bin": "application/octet-stream",
};

function loadPuppeteer() {
  const dirs = [process.env.PUPPETEER_DIR,
    join(process.env.USERPROFILE || "", ".workbuddy", "binaries", "node", "workspace"),
    join(process.env.HOME || "", ".workbuddy", "binaries", "node", "workspace"),
    ROOT].filter((d) => d && existsSync(join(d, "package.json")));
  for (const d of dirs) {
    try {
      return createRequire(join(d, "package.json"))("puppeteer-core");
    } catch { /* 换下一个 */ }
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

const LATEST = {
  tag_name: "v9.9.9", name: "itsPLK 9.9.9 (f4fab6b)",
  published_at: "2026-11-01T00:00:00Z",
  html_url: "https://github.com/q1378659137/ps5-webkit-autoloader-esp32/releases/tag/v9.9.9",
};

const STUB_ESPTOOL = "export class ESPLoader {};export class Transport {};";

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
      res.writeHead(404, { "content-type": "text/plain" }).end("not found");
    }
  });
  return new Promise((ok) => server.listen(0, "127.0.0.1", () => ok(server)));
}

const results = [];
const check = (name, ok, detail = "") => {
  results.push({ name, ok, detail });
  console.log(`${ok ? "  ok  " : " FAIL "} ${name}${detail ? `  (${detail})` : ""}`);
};

const text = (page, sel) => page.$eval(sel, (n) => n.textContent.trim()).catch(() => null);

async function intercept(page) {
  await page.setRequestInterception(true);
  const cors = { "access-control-allow-origin": "*" };
  page.on("request", (req) => {
    const url = req.url();
    if (url.startsWith("https://unpkg.com/esptool-js")) {
      return req.respond({ status: 200, contentType: "text/javascript; charset=utf-8", headers: cors, body: STUB_ESPTOOL });
    }
    if (url.includes("api.github.com") && url.includes("/releases/latest")) {
      return req.respond({ status: 200, contentType: "application/json; charset=utf-8", headers: cors, body: JSON.stringify(LATEST) });
    }
    if (url.includes("api.github.com")) {
      return req.respond({ status: 200, contentType: "application/json; charset=utf-8", headers: cors, body: JSON.stringify({ stargazers_count: 1579 }) });
    }
    if (url.includes("fonts.googleapis.com") || url.includes("fonts.gstatic.com")) {
      return req.respond({ status: 204, headers: cors, body: "" });
    }
    return req.continue();
  });
}

const server = await serve();
const base = `http://127.0.0.1:${server.address().port}/`;

const puppeteer = loadPuppeteer();
await mkdir(SHOTS, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: chromePath(),
  headless: "new",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--lang=zh-CN"],
});

const errors = [];
const missing = [];
const page = await browser.newPage();
page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
page.on("console", (m) => { if (m.type() === "error" && !/Failed to load resource/.test(m.text())) errors.push(`console: ${m.text()}`); });
// bin/* 由 pages 工作流发布，不进仓库。本地没有，所以那里 404
// 是正常的，只报告不算失败。
page.on("response", (r) => {
  if (r.status() !== 404) return;
  const url = new URL(r.url());
  if (url.pathname.startsWith("/bin/")) missing.push(url.pathname);
  else errors.push(`404: ${url.pathname}`);
});
page.setViewport({ width: 1280, height: 900 });
await intercept(page);

const TITLE_ZH = "把 ESP32 插到这台电脑上";
const TITLE_EN = "Plug your ESP32 into this computer";
const TITLE_ES = "Conecta tu ESP32 a este ordenador";

// 1. ?lang=zh 生效，而且首屏可见文案都是中文。
await page.goto(`${base}?lang=zh&board=s2`, { waitUntil: "networkidle2" });
await page.waitForFunction((want) => document.getElementById("wiz-title")?.textContent.trim() === want, {}, TITLE_ZH);

check("html lang = zh-CN", (await page.evaluate(() => document.documentElement.lang)) === "zh-CN",
  await page.evaluate(() => document.documentElement.lang));
check("首屏标题", (await text(page, "#wiz-title")) === TITLE_ZH, await text(page, "#wiz-title"));
check("首屏正文含「USB 线」", ((await text(page, "#wiz-body")) || "").includes("USB 线"));
check("主按钮是「安装」", ((await text(page, "#wiz-actions")) || "").includes("安装"), await text(page, "#wiz-actions"));
check("跳过链接", (await text(page, "#skip")) === "跳到正文", await text(page, "#skip"));
check("页脚说明", ((await text(page, "#foot-note")) || "").includes("esptool-js"));
check("页脚「高级」按钮", (await text(page, "#open-adv")) === "高级", await text(page, "#open-adv"));
check("页脚源码链接指向汉化仓库",
  (await page.$eval("#foot-src", (a) => a.getAttribute("href"))) === "https://github.com/q1378659137/ps5-webkit-autoloader-esp32");
check("语言按钮 aria-pressed 指向 zh",
  (await page.$eval('[data-set-lang="zh"]', (b) => b.getAttribute("aria-pressed"))) === "true");
check("EN 按钮已取消选中",
  (await page.$eval('[data-set-lang="en"]', (b) => b.getAttribute("aria-pressed"))) === "false");
check("中文字形真的落到 CJK 字体",
  await page.$eval("#wiz-title", (n) => {
    const f = getComputedStyle(n).fontFamily;
    return /PingFang|YaHei|Noto Sans SC|Hiragino/.test(f);
  }));

// 2. 高级面板（dialog）里的每一段标题也都是中文。
await page.click("#open-adv");
await page.waitForFunction(() => document.getElementById("adv")?.open === true);
check("高级面板标题", (await text(page, "#adv-title")) === "高级", await text(page, "#adv-title"));
check("版本分组", (await text(page, "#ver-title")) === "版本", await text(page, "#ver-title"));
check("板型分组", (await text(page, "#board-title")) === "开发板");
check("擦除选项", (await text(page, "#erase-label")) === "先擦除闪存", await text(page, "#erase-label"));
check("日志分组", (await text(page, "#logs-title")) === "日志");
check("复制按钮", (await text(page, "#copy-log")) === "复制");
check("关闭按钮 aria-label", (await page.$eval("#close-adv", (b) => b.getAttribute("aria-label"))) === "关闭");
await page.screenshot({ path: join(SHOTS, "zh-advanced.png") });
await page.click("#close-adv");

// 3. 浏览器语言检测：zh-CN 的客户端不带 ?lang=zh 也进中文。
const auto = await browser.newPage();
await intercept(auto);
await auto.evaluateOnNewDocument(() => {
  Object.defineProperty(navigator, "language", { get: () => "zh-CN" });
  Object.defineProperty(navigator, "languages", { get: () => ["zh-CN", "zh"] });
});
await auto.goto(base, { waitUntil: "networkidle2" });
await auto.waitForFunction((want) => document.getElementById("wiz-title")?.textContent.trim() === want, {}, TITLE_ZH);
check("zh-CN 浏览器自动选中中文", (await auto.$eval('[data-set-lang="zh"]', (b) => b.getAttribute("aria-pressed"))) === "true");
check("zh-CN 下标题为中文", (await text(auto, "#wiz-title")) === TITLE_ZH);
await auto.close();

// 4. 切回英文仍然正常：原来的机制没被破坏。
await page.click('[data-set-lang="en"]');
await page.waitForFunction((want) => document.getElementById("wiz-title")?.textContent.trim() === want, {}, TITLE_EN);
check("切回 EN 生效", (await text(page, "#wiz-title")) === TITLE_EN);
check("切回 EN 后 aria-pressed 正确",
  (await page.$eval('[data-set-lang="en"]', (b) => b.getAttribute("aria-pressed"))) === "true");

// 5. 切到西班牙语也正常，说明第三套语言包没被注册表改动弄坏。
await page.click('[data-set-lang="es"]');
await page.waitForFunction((want) => document.getElementById("wiz-title")?.textContent.trim() === want, {}, TITLE_ES);
check("切到 ES 生效", (await text(page, "#wiz-title")) === TITLE_ES);

await page.click('[data-set-lang="zh"]');
await page.waitForFunction((want) => document.getElementById("wiz-title")?.textContent.trim() === want, {}, TITLE_ZH);
await page.screenshot({ path: join(SHOTS, "zh-desktop.png"), fullPage: false });

await page.setViewport({ width: 390, height: 844, isMobile: true });
await page.reload({ waitUntil: "networkidle2" });
await page.waitForFunction((want) => document.getElementById("wiz-title")?.textContent.trim() === want, {}, TITLE_ZH);
check("移动端仍是中文", (await text(page, "#wiz-title")) === TITLE_ZH);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
check("移动端无横向溢出（多一个语言按钮）", overflow <= 1, `overflow ${overflow}px`);
check("语言按钮不折行", (await page.$eval('[data-set-lang="zh"]', (b) => b.getBoundingClientRect().height)) <= 26);

await page.setViewport({ width: 320, height: 640, isMobile: true });
await page.reload({ waitUntil: "networkidle2" });
await page.waitForFunction((want) => document.getElementById("wiz-title")?.textContent.trim() === want, {}, TITLE_ZH);
check("320px 窄屏无横向溢出", (await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)) <= 1);
check("320px 品牌文字已收起",
  (await page.$eval(".brand span", (n) => getComputedStyle(n).display)) === "none");
await page.screenshot({ path: join(SHOTS, "zh-mobile.png") });

check("无 JS 报错", errors.length === 0, errors.slice(0, 3).join(" | "));
console.log(`  note  bin/ 404s (未提交的构建产物，属预期): ${missing.length ? [...new Set(missing)].join(", ") : "none"}`);

// 6. 深色主题：浅字深底下中文照样要画出来。
await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
await page.setViewport({ width: 1280, height: 900 });
await page.reload({ waitUntil: "networkidle2" });
await page.waitForFunction((want) => document.getElementById("wiz-title")?.textContent.trim() === want, {}, TITLE_ZH);
const tone = await page.$eval("#wiz-body", (n) => {
  const [r, g, b] = getComputedStyle(n).color.match(/\d+/g).map(Number);
  return { color: `${r},${g},${b}`, bg: getComputedStyle(document.body).backgroundColor };
});
check("深色主题下正文为浅色", Number(tone.color.split(",").reduce((a, v) => a + Number(v), 0)) / 3 > 120, `${tone.color} on ${tone.bg}`);
await page.screenshot({ path: join(SHOTS, "zh-dark.png") });

await browser.close();
server.close();

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} passed  ·  shots in tools/shots/`);
if (failed.length) process.exit(1);
