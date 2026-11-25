// 把 flasher/language/ 下每个 <lang>.js 和 en.js 比一遍。
// 合完上游（git merge upstream/main）立刻跑：上游新加的键会
// 以 "missing" 的形式列出来，一眼看得出还差哪些没译。
//
//   node tools/check-i18n.mjs
//
// 有问题时退出码为 1，可以直接卡住提交或 CI。

import { readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const DIR = join(ROOT, "flasher", "language");

const flat = (o, p = "") => Object.entries(o).flatMap(([k, v]) =>
  v && typeof v === "object" && !Array.isArray(v) ? flat(v, `${p}${k}.`) : [`${p}${k}`]);

const load = async (file) => {
  const mod = await import(pathToFileURL(join(DIR, file)).href);
  return mod[file.replace(/\.js$/, "")];
};

// {s} / {n} 这类占位符翻译时必须原样保留。
const slots = (s) => (String(s).match(/\{(\w+)\}/g) || []).sort().join(",");

const files = readdirSync(DIR).filter((f) => /^[a-z]{2}\.js$/.test(f)).sort();
const en = await load("en.js");
const base = new Set(flat(en));

let bad = 0;
console.log(`en: ${base.size} keys (${files.join(", ")})`);

for (const file of files) {
  const lang = file.replace(/\.js$/, "");
  if (lang === "en") continue;
  const dict = await load(file);
  if (!dict) {
    console.log(`[FAIL] ${lang}: module did not export '${lang}'`);
    bad++;
    continue;
  }
  const keys = new Set(flat(dict));
  const missing = [...base].filter((k) => !keys.has(k));
  const extra = [...keys].filter((k) => !base.has(k));
  const arrLen = Object.keys(en).filter((k) => Array.isArray(en[k]) && dict[k]?.length !== en[k].length);
  const slotBad = [...base].filter((k) => {
    const a = en[k], b = dict[k];
    return typeof a === "string" && typeof b === "string" && slots(a) !== slots(b);
  });

  const ok = !missing.length && !extra.length && !arrLen.length && !slotBad.length;
  console.log(`${ok ? "[ OK ]" : "[FAIL]"} ${lang}: ${keys.size}/${base.size}` +
    (missing.length ? `\n         missing: ${missing.join(", ")}` : "") +
    (extra.length ? `\n         extra: ${extra.join(", ")}` : "") +
    (arrLen.length ? `\n         array length differs: ${arrLen.join(", ")}` : "") +
    (slotBad.length ? `\n         placeholder differs: ${slotBad.join(", ")}` : ""));
  if (!ok) bad++;
}

if (bad) {
  console.log(`\n${bad} language file(s) need work.`);
  process.exit(1);
}
console.log("\nAll language files match en.js.");
