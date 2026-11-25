// 写入期间保持屏幕常亮，免得笔记本在刷写中途睡着。
let lock = null;

export async function holdAwake() {
  try {
    if ("wakeLock" in navigator) lock = await navigator.wakeLock.request("screen");
  } catch { /* not allowed here; the write still works */ }
}

export async function releaseAwake() {
  try { await lock?.release(); } catch { /* already released */ }
  lock = null;
}
