import { isBoard } from "../firmware/catalog.js";
import { pickLang } from "../language/language.js";
import { state } from "./state.js";

// ?lang=es&board=s3&channel=pre 这样的链接能直接打开到指定语言和板型。
// 上次选过的板型也会记住，下次打开还在。
export function readUrl() {
  const q = new URLSearchParams(location.search);
  let saved = null;
  try { saved = localStorage.getItem("board"); } catch { /* storage blocked */ }
  state.lang = pickLang(q.get("lang"), navigator.language);
  state.board = [q.get("board"), saved].find(isBoard) || "s2";
  state.channel = q.get("channel") === "pre" ? "pre" : "stable";
}

export function writeUrl() {
  const q = new URLSearchParams({ lang: state.lang, board: state.board });
  if (state.channel === "pre") q.set("channel", "pre");
  history.replaceState(null, "", `?${q}`);
  try { localStorage.setItem("board", state.board); } catch { /* storage blocked */ }
}
