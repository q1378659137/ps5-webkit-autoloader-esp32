import { t } from "../language/language.js";
import { fmtBytes, fmtSec } from "../ui/format.js";

// 对用户毫无信息量的 esptool-js 噪声。
const SKIP = /^(Writing at 0x|Compressed \d|Uploading stub|Running stub|Stub running|Changing baud|Hard resetting|Connecting\.\.\.|Detecting chip|Leaving\.\.\.|Staying in)/i;

// 把一行原始 esptool-js 输出变成 { text, kind }，返回 null 表示丢弃。
export function formatLine(raw) {
  const s = String(raw).replace(/\r/g, "").replace(/\s+/g, " ").trim();
  if (!s || SKIP.test(s)) return null;
  const wrote = s.match(/^Wrote (\d+) bytes.*?in ([\d.]+) seconds/i);
  if (wrote) return { text: `${t("wrote")} ${fmtBytes(+wrote[1])} · ${fmtSec(+wrote[2])}`, kind: "hi" };
  if (/^Hash of data verified/i.test(s)) return { text: t("verified"), kind: "hi" };
  if (/^Chip is /i.test(s)) return { text: s.replace(/^Chip is /i, `${t("chip")}  `), kind: "hi" };
  if (/^MAC:/i.test(s)) return { text: s.replace(/^MAC:\s*/i, "MAC  ") };
  if (/^Features:/i.test(s)) return { text: s.replace(/^Features:\s*/i, "") };
  if (/^Crystal is /i.test(s)) return { text: s.replace(/^Crystal is /i, "") };
  return { text: s };
}
