import { session } from "../device/session.js";
import { md5Hex } from "./verify.js";

// 通过已打开的 esptool-js 会话，把合并镜像写到 0x0。
export async function writeImage(data, { eraseAll, onProgress }) {
  await session.loader.writeFlash({
    fileArray: [{ data: new Uint8Array(data), address: 0 }],
    flashSize: "4MB",
    flashMode: "keep",
    flashFreq: "keep",
    eraseAll,
    // 传输时先用 Deflate 压：空闪存几乎压没了，所以 4 MB 的镜像
    // 实际只发约 2.7 MB，由芯片上的 stub 解压。
    compress: true,
    calculateMD5Hash: md5Hex,
    reportProgress(_i, written, total) {
      onProgress(written / total);
    },
  });
}

// 让芯片直接重启进新固件，省得人去插拔。
// - S2 的原生 USB（USB-OTG CDC）：RTS 不起作用，于是触发 RTC 看门狗，
//   和 esptool.py 在这个模式下用的招一样。
// - C3/S3 的 USB-Serial/JTAG 和 USB-UART 桥：通过 RTS 硬复位。
// 板子重启时会从 USB 上掉下去，所以请求发出后掉线算成功。
// 发出复位返回 true，需要用户自己按 RST 返回 false。
export async function startFirmware() {
  const { loader } = session;
  try {
    const otg = await loader.usesUsbOtg();
    if (otg && typeof loader.chip.watchdogReset === "function") {
      await loader.chip.watchdogReset(loader);
    } else {
      await loader.after("hard_reset", otg);
    }
    return true;
  } catch (err) {
    return /lost|disconnect|closed|NetworkError|read/i.test(String(err?.message || err));
  }
}
