import { t } from "../language/language.js";
import { state } from "./state.js";

// index.html 里的静态文案：元素 id -> 文案键。
const TEXT = {
  "skip": "skip",
  "open-adv": "adv",
  "adv-title": "adv",
  "ver-title": "verTitle",
  "board-title": "boardTitle",
  "board-hint": "boardHint",
  "write-title": "writeOpts",
  "erase-label": "erase",
  "erase-hint": "eraseHint",
  "logs-title": "logs",
  "copy-log": "copy",
  "foot-note": "footNote",
  "foot-src": "source",
};

export function renderPageText() {
  // 中文写成 zh-CN：浏览器据此挑简体字形（上游只写 zh）
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : state.lang;
  for (const [id, key] of Object.entries(TEXT)) {
    document.getElementById(id).textContent = t(key);
  }
  document.getElementById("close-adv").setAttribute("aria-label", t("close"));
  document.title = t("pageTitle");
  document.querySelector('meta[name="description"]')?.setAttribute("content", t("meta"));
}
