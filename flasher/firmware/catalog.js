// 板型 id -> 它用的芯片。两块板可能共用一颗芯片（DevKit 和 PICO-KIT 都是 ESP32）。
// 选择器顺序：最常见的板型排在前面。
export const CHIP_OF = { s2: "ESP32-S2", devkit: "ESP32", s3: "ESP32-S3", c3: "ESP32-C3", pico: "ESP32" };

// 这块板常见的售卖名称。
export const BOARD_NAME = {
  s2: "ESP32-S2 Mini", s3: "ESP32-S3 DevKitC", c3: "ESP32-C3 Super Mini",
  devkit: "ESP32 DevKit", pico: "ESP32 PICO-KIT",
};

// 板型 id -> pages 工作流发布的镜像。
export const IMAGE_OF = {
  s2: "esp32-arduino.s2.merged.bin",
  s3: "esp32-arduino.s3.merged.bin",
  c3: "esp32-arduino.c3.merged.bin",
  devkit: "esp32-arduino.devkit.merged.bin",
  pico: "esp32-arduino.pico.merged.bin",
};

// 稳定版镜像在 bin/，预发行版在 bin/pre/。
export function imagePath(board, channel) {
  return `bin/${channel === "pre" ? "pre/" : ""}${IMAGE_OF[board]}`;
}

export function isChip(name) {
  return Object.values(CHIP_OF).includes(name);
}

// 识别到芯片后该用哪块板：已选板型如果就是这颗芯片，就保留它。
export function boardOf(chip, picked) {
  if (CHIP_OF[picked] === chip) return picked;
  return Object.keys(CHIP_OF).find((id) => CHIP_OF[id] === chip) || "s2";
}

export function isBoard(id) {
  return Object.hasOwn(CHIP_OF, id ?? "");
}
