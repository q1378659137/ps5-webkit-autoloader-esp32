import { state } from "../app/state.js";
import { en } from "./en.js";
import { es } from "./es.js";
import { zh } from "./zh.js";

const STRINGS = { en, es, zh };

const LANGS = Object.keys(STRINGS);

export function t(key) {
  return STRINGS[state.lang]?.[key] ?? en[key];
}

export function pickLang(raw, nav) {
  if (LANGS.includes(raw)) return raw;
  const short = String(nav || "").slice(0, 2).toLowerCase();
  return LANGS.includes(short) ? short : "en";
}
