import { t } from "../language/language.js";

// 挡掉过小的文件，以及拿 HTML 错误页冒充二进制的响应。
export function checkImage(buf) {
  if (buf.length < 1024 || buf[0] === 0x3c) throw new Error(t("badbin"));
}

export async function fetchImage(path) {
  const res = await fetch(`${path}?v=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} (${res.status})`);
  const buf = new Uint8Array(await res.arrayBuffer());
  checkImage(buf);
  return buf;
}
