import { s2Mini } from "./s2-mini.js";
import { s3DevKitC } from "./s3-devkitc.js";
import { c3SuperMini } from "./c3-super-mini.js";
import { picoKit } from "./pico-kit.js";
import { devkit } from "./devkit.js";

const BOARDS = { s2: s2Mini, devkit, s3: s3DevKitC, c3: c3SuperMini, pico: picoKit };

// USB 插头与线缆，默认垂在接口下方；插上时滑进接口。
function cable(b) {
  const { cx, y, kind } = b.usb;
  const pw = kind === "c" ? 10.6 : 9.4;
  const top = y + (kind === "c" ? 3.4 : 3.2);
  const bottom = b.h + 46;
  const path = `M${cx} ${top + 11} C ${cx} ${top + 22}, ${cx + 10} ${top + 24}, ${cx + 10} ${bottom}`;
  return `<g class="cable">` +
    `<path d="${path}" fill="none" stroke="#2c2f36" stroke-width="3.4" stroke-linecap="round"/>` +
    `<path class="flow" d="${path}" fill="none" stroke-width="1.1" stroke-linecap="round"/>` +
    `<rect x="${cx - pw / 2}" y="${top}" width="${pw}" height="9" rx="1.8" fill="#3a3e47"/>` +
    `<rect x="${cx - pw / 2 + 0.6}" y="${top + 0.6}" width="${pw - 1.2}" height="1.6" rx="0.8" fill="#4d525d"/>` +
    `<rect x="${cx - 2.4}" y="${top + 9}" width="4.8" height="3.2" rx="1" fill="#2c2f36"/>` +
    `</g>`;
}

function wifi(b) {
  const cx = b.w / 2, y = -3;
  return `<g class="wifi">` + [5, 9, 13].map((r, i) =>
    `<path class="wave" style="--i:${i}" d="M${cx - r * 0.86} ${y - r * 0.5 + r * 0.5} A ${r} ${r} 0 0 1 ${cx + r * 0.86} ${y}" fill="none" stroke-width="1.3" stroke-linecap="round"/>`,
  ).join("") + `</g>`;
}

// 元件下方的铜箔走线，以及沿线跑的信号脉冲。
// 形如 "M1 2 V3 L4 5 H6" 的路径终点：按 M/L/H/V 逐条跟笔。
function endOf(d) {
  let x = 0, y = 0;
  for (const [, cmd, args] of d.matchAll(/([MLHV])\s*([-\d.\s]+)/g)) {
    const n = args.trim().split(/\s+/).map(Number);
    if (cmd === "H") x = n[0];
    else if (cmd === "V") y = n[0];
    else [x, y] = n;
  }
  return [x, y];
}

// 阻焊层下的铜箔。换层的走线以过孔收尾。
function copper(b) {
  const lines = b.traces.map(([, d]) =>
    `<path d="${d}" fill="none" stroke="${b.trace}" stroke-width="0.34" stroke-linecap="round" stroke-linejoin="round"/>`);
  const vias = b.traces.filter(([kind]) => kind === "io" || kind === "power").map(([, d]) => {
    const [x, y] = endOf(d);
    return `<circle cx="${x}" cy="${y}" r="0.34" fill="${b.trace}"/><circle cx="${x}" cy="${y}" r="0.15" fill="#0b0b0c"/>`;
  });
  return `<g class="traces">${lines.join("")}${vias.join("")}</g>`;
}

function signals(b) {
  return `<g class="signals">` + b.traces.map(([kind, d, delay = 0]) =>
    `<path class="sig sig-${kind}" d="${d}" pathLength="100" style="--d:${delay}s" fill="none" stroke-width="0.5" stroke-linecap="round"/>`).join("") + `</g>`;
}

// 大图：开发板、状态灯、BOOT 提示、线缆和 Wi-Fi 波纹。
export function boardArt(id) {
  const b = BOARDS[id] || s2Mini;
  const [lx, ly] = b.led;
  const [bx, by] = b.boot;
  // 取景框收紧，让开发板占满舞台；波纹和线缆允许溢出。
  const side = 4, top = 15, bottom = 14;
  return `<svg class="art" viewBox="${-side} ${-top} ${b.w + side * 2} ${b.h + top + bottom}" aria-hidden="true">` +
    `<ellipse class="art-shadow" cx="${b.w / 2}" cy="${b.h + 5}" rx="${b.w * 0.55}" ry="2.4"/>` +
    wifi(b) +
    cable(b) +
    `<g class="art-board">${b.pcb}${copper(b)}${signals(b)}${b.body}` +
    `<circle class="led" cx="${lx}" cy="${ly}" r="0.95"/>` +
    `<circle class="boot-ring" cx="${bx}" cy="${by}" r="3.2"/>` +
    `</g></svg>`;
}

// 板型选择器里的小图。
export function boardThumb(id) {
  const b = BOARDS[id] || s2Mini;
  return `<svg class="thumb" viewBox="-1 -1 ${b.w + 2} ${b.h + 2}" aria-hidden="true">${b.pcb}${copper(b)}${b.body}</svg>`;
}
