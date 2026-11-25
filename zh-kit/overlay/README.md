# 给 ESP32 用的 PS5 WebKit Autoloader

中文 · [English](README.en.md) · [Español](README.es.md)

[![网页刷写工具：插上板子，点安装](flasher/share/og.png)](https://q1378659137.github.io/ps5-webkit-autoloader-esp32/)

这块固件把一块便宜的 ESP32 开发板变成 Wi-Fi 热点。把开发板插到 PS5 上，连上这个热点，打开官方的**使用说明书**。说明书会从开发板（而不是互联网）加载一个页面，那个页面负责安装 [itsPLK/ps5-webkit-autoloader](https://github.com/itsPLK/ps5-webkit-autoloader)。之后从 **媒体 → WebKit Autoloader** 就能启动 Payload Manager。

请只在你自己拥有的主机上使用。自制软件与 WebKit 漏洞利用可能违反 Sony 的条款。这台主机一旦联网，主机或 PSN 账号都可能被封。本项目不会帮你躲过 Sony。

哪些 PS5 系统版本可用、每个版本跑哪个漏洞，由 payload 决定，见 [itsPLK 的 README](https://github.com/itsPLK/ps5-webkit-autoloader#readme)。

## 需要准备

- 一台 PS5，系统版本在 payload 支持范围内（[列表](https://github.com/itsPLK/ps5-webkit-autoloader#readme)）
- 一块带 USB 口的 ESP32 开发板：**ESP32-S2 Mini**（TENSTAR 之类）、ESP32-S3、ESP32-C3、ESP32 DevKit（WROOM-32 / ESP-32S，常见的 30 脚或 38 脚那种），或 ESP32-PICO
- 一根能传数据的 USB 线，只能充电的不行
- 电脑上的 Chrome 或 Edge，用来写固件（Firefox 和 Safari 不行）

## 刷写固件（只需一次）

开发板出厂是空的。你要在电脑上把我们的镜像写进去，然后把板子挪到 PS5 上。

### 网页刷写工具

1. 用 Chrome 或 Edge 打开[网页刷写工具](https://q1378659137.github.io/ps5-webkit-autoloader-esp32/)。
2. 把开发板插到电脑上，点 **安装**。Chrome 会问用哪个设备：选中那块 ESP32（一个 COM 口，或「USB JTAG/serial debug unit」）。工具会自己认出板型并写入对应镜像。写入过程中别关这个标签页。
3. 跟着接下来的几屏走，它会一步步带你完成 PS5 那一侧。

开发板没出现的话，换一根线，或者插的时候按住 **BOOT**。版本、板型、先擦除一遍、你自己的 `.bin` 以及日志，都在页面底部的**高级**里。

刷写工具会把写进去的固件和文件对一遍，然后直接让开发板重启并进入门户页，所以不用再插拔一次。如果开发板没法自己重启，页面会提示你：按一下 **RST**，或者拔下来再插回去。

开发板重启后可能会从 Windows 里消失，这是正常的：这些镜像启动后会关掉原生 USB，免得 PS5 和串口抢设备。

你也可以下载 [release](https://github.com/q1378659137/ps5-webkit-autoloader-esp32/releases/latest)，用 esptool 把对应的 `.merged.bin` 写到 `0x0`。payload 版本不变时直接原地更新 `latest`；payload 出了新版本才会单独发一个 release。itsPLK 发预发行版时这里也会跟着发一个对应的预发行版用于测试，而 `latest` 和网页刷写工具始终停在稳定版。每个 release 都带 `SHA256SUMS`：`sha256sum -c SHA256SUMS --ignore-missing` 可以校验你下载的文件。

| 开发板 | 文件 | 板载 LED |
| --- | --- | --- |
| ESP32-S2 | `esp32-arduino.s2.merged.bin` | GPIO 15 |
| ESP32-S3 | `esp32-arduino.s3.merged.bin` | GPIO 21 |
| ESP32 DevKit | `esp32-arduino.devkit.merged.bin` | GPIO 2 |
| ESP32-PICO | `esp32-arduino.pico.merged.bin` | GPIO 10 |
| ESP32-C3 | `esp32-arduino.c3.merged.bin` | GPIO 8 |

开发板启动期间 LED 常亮，热点起来之后每隔两秒短闪一次，每次有人请求页面也会闪一下。闪得很快说明 Wi-Fi 热点没起来。

## 在 PS5 上使用

1. 把开发板从电脑上拔下来，插到 PS5 的 USB 口上，以后就一直插在那儿。
2. 在 PS5 上：**设定 → 网络 → 设定 → 设定互联网连接**。连接 Wi-Fi **`ESP32_PORTAL`**，密码 **`12345678`**。
3. 就留在这个网络上。PS5 会提示没有互联网，这是正常的：确实没有，也不需要。
4. **设定 → 指南与提示 → 使用说明书**。等到缓存跑完。这个页面会执行漏洞利用并装好主屏幕快捷方式。
5. 重启 PS5。打开 **媒体 → WebKit Autoloader**。没有 `autoload.txt` 时会启动 Payload Manager。

以后只需要插着开发板、Wi-Fi 还连着 `ESP32_PORTAL`，然后从 **媒体 → WebKit Autoloader** 进入即可。

## 从源码构建

```sh
./install-deps.sh
python3 pack/pack_payload.py --web /path/to/ps5-webkit-autoloader
make
```

只支持 Arduino-ESP32 **2.0.11**。镜像输出到 `build/{pico,devkit,s2,s3,c3}/`。`make debug` / `make debug-s2` 会保留 USB 串口，方便看日志。

## 遇到问题

刷写工具、开发板或 `ESP32_PORTAL` 出问题？[提个 issue](https://github.com/q1378659137/ps5-webkit-autoloader-esp32/issues/new/choose)，把刷写工具的日志贴进去（安装 → 日志 → 复制）。payload 本身的问题请找 [itsPLK](https://github.com/itsPLK/ps5-webkit-autoloader/issues)。

## 致谢

Payload：[itsPLK](https://github.com/itsPLK/ps5-webkit-autoloader)。漏洞链：[slopkit](https://github.com/jordyidk/slopkit)、[Relapse](https://github.com/ntfargo/Relapse-Exploit)。刷写工具：[esptool-js](https://github.com/espressif/esptool-js)。

## 许可

固件与构建脚本：MIT。随包的 payload 各自遵循自己的条款。见 [LICENSE](LICENSE)。
