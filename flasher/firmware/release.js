import { state } from "../app/state.js";

// pages 工作流会在镜像旁边写一个 bin/channels.json：
//   { "stable": { tag, name, date, url }, "pre": { ... } | null }
// 只有最新的预发行版比稳定版新时，pre 才有值。
const CHANNELS = "bin/channels.json";
const API = "https://api.github.com/repos/q1378659137/ps5-webkit-autoloader-esp32/releases/latest";
const KEY = "release:v1";

function pickFields(j) {
  return j?.tag ? { tag: j.tag, name: j.name, date: j.date, url: j.url } : null;
}

// 本地预览没有 channels.json 时的退路：只取稳定版，走 API。
// GitHub 匿名调用每小时限 60 次，所以每个标签页复用同一个结果。
async function loadLatest() {
  try {
    const hit = sessionStorage.getItem(KEY);
    if (hit) return JSON.parse(hit);
  } catch { /* storage blocked */ }
  try {
    const res = await fetch(API, { headers: { Accept: "application/vnd.github+json" } });
    if (!res.ok) return null;
    const j = await res.json();
    const rel = { tag: j.tag_name, name: j.name, date: j.published_at, url: j.html_url };
    try { sessionStorage.setItem(KEY, JSON.stringify(rel)); } catch { /* storage blocked */ }
    return rel;
  } catch {
    return null;
  }
}

export async function loadChannels() {
  try {
    const res = await fetch(`${CHANNELS}?v=${Date.now()}`, { cache: "no-store" });
    if (res.ok) {
      const j = await res.json();
      const stable = pickFields(j?.stable);
      if (stable) return { stable, pre: pickFields(j?.pre) };
    }
  } catch { /* missing or not JSON */ }
  const stable = await loadLatest();
  return stable ? { stable, pre: null } : null;
}

// 安装按钮要写入的发行版：加载中是 undefined，未知是 null。
export function selected() {
  const c = state.channels;
  if (c === undefined) return undefined;
  return c?.[state.channel] ?? c?.stable ?? null;
}

// 把 "itsPLK 0.7.1(f4fab6b)" 规整成 "itsPLK 0.7.1 (f4fab6b)"
export function payloadLabel(name) {
  return String(name || "").replace(/\s*\(/, " (").trim();
}
