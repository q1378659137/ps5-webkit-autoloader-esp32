import { ESPLoader, Transport } from "https://unpkg.com/esptool-js@0.7.0/bundle.js";
import { state } from "../app/state.js";
import { CHIP_OF, isChip } from "../firmware/catalog.js";
import { t } from "../language/language.js";
import { logLine } from "../log/log.js";

const USB_VENDORS = [0x303a, 0x10c4, 0x1a86, 0x0403]; // Espressif, CP210x, CH34x, FTDI

export const serialOk = typeof navigator !== "undefined" && "serial" in navigator;

export const session = {
  port: null,
  transport: null,
  loader: null,
  nativeUsb: false,
  chipName: "",
  chipDesc: "",
  mac: "",
  chip: "",
};

// 原生 USB 的板子不接受 DTR/RTS，这对我们不算错误。
function ignoreMissingSignals(transport) {
  const wrap = (fn) => async function (...args) {
    try { return await fn.apply(this, args); }
    catch (err) {
      if (String(err).includes("control signals")) return;
      throw err;
    }
  };
  transport.setRTS = wrap(transport.setRTS);
  transport.setDTR = wrap(transport.setDTR);
  transport.setSignals = wrap(transport.setSignals);
}

// esptool-js 只把芯片信息当日志行输出。
function capture(line) {
  const s = String(line).trim();
  const chip = s.match(/^Chip is (.+)$/i);
  if (chip) session.chipDesc = chip[1];
  const mac = s.match(/^MAC:\s*([0-9a-f:]+)/i);
  if (mac) session.mac = mac[1].toUpperCase();
}

async function requestPort() {
  try {
    return await navigator.serial.requestPort({
      filters: USB_VENDORS.map((usbVendorId) => ({ usbVendorId })),
    });
  } catch (err) {
    if (err?.name === "NotFoundError") throw Object.assign(new Error(t("noport")), { abort: true });
    throw err;
  }
}

export async function dropSession() {
  try { await session.transport?.disconnect(); } catch { /* already gone */ }
  Object.assign(session, {
    port: null, transport: null, loader: null, nativeUsb: false,
    chipName: "", chipDesc: "", mac: "", chip: "",
  });
}

export async function openSession() {
  await dropSession();
  const port = await requestPort();
  session.port = port;
  session.nativeUsb = port.getInfo().usbVendorId === 0x303a;
  session.transport = new Transport(port, false);
  ignoreMissingSignals(session.transport);
  session.loader = new ESPLoader({
    transport: session.transport,
    // USB 串口桥（CP2102、CH340）先按 115200 连，跑起 stub 后再升速：
    // 460800 写 4 MB 镜像大约快四倍，常见桥片都吃得下。
    // 原生 USB 不看波特率，所以那边保持不动。
    baudrate: session.nativeUsb ? 115200 : 460800,
    romBaudrate: 115200,
    terminal: {
      clean() {},
      writeLine: (d) => { capture(d); logLine(d); },
      write() {},
    },
  });

  if (session.nativeUsb) logLine(t("native"));
  let chip;
  try {
    chip = await session.loader.main(session.nativeUsb ? "no_reset" : "default_reset");
  } catch (err) {
    if (!String(err).includes("control signals")) throw err;
    logLine(t("native"));
    try { await session.transport.disconnect(); } catch { /* already closed */ }
    chip = await session.loader.main("no_reset");
  }
  const name = session.loader.chip?.CHIP_NAME || chip || CHIP_OF[state.board];
  session.chipName = name;
  session.chip = isChip(name) ? name : CHIP_OF[state.board];
  if (CHIP_OF[state.board] !== session.chip) logLine(t("mismatch"));
}
