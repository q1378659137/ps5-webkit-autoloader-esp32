import SparkMD5 from "https://cdn.jsdelivr.net/npm/spark-md5@3.0.2/+esm";

// 镜像的 MD5，按 esptool-js 交过来的形态（补齐过的 Uint8Array）算，十六进制。
// esptool-js 会拿它和芯片对已写入闪存算出的 MD5 比对，
// 不一致就抛错。所以「已安装」代表校验过，不只是发过去了。
export function md5Hex(image) {
  const bytes = image instanceof Uint8Array ? image : new Uint8Array(image);
  return SparkMD5.ArrayBuffer.hash(bytes.slice().buffer);
}
