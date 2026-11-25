#include <Arduino.h>
#include "esp_arduino_version.h"
#include "esp_idf_version.h"
#include "config.h"
#include "led.h"
#include "host_files.h"
#include "wifi_ap.h"
#include "http_server.h"
#include "https_server.h"

#if !USB_DEBUG && (CONFIG_IDF_TARGET_ESP32S3 || CONFIG_IDF_TARGET_ESP32C3)
#include "soc/soc.h"
#include "soc/usb_serial_jtag_reg.h"
#endif

void setup()
{
#if !USB_DEBUG && (CONFIG_IDF_TARGET_ESP32S3 || CONFIG_IDF_TARGET_ESP32C3)
    CLEAR_PERI_REG_MASK(
        USB_SERIAL_JTAG_CONF0_REG,
        USB_SERIAL_JTAG_USB_PAD_ENABLE
    );
#endif

    portalLedBegin();
    Serial.begin(115200);
    delay(1000);
    portalPrepareHttpsDebug();

    Serial.printf(
        "Arduino ESP32 版本: %d.%d.%d\n",
        ESP_ARDUINO_VERSION_MAJOR,
        ESP_ARDUINO_VERSION_MINOR,
        ESP_ARDUINO_VERSION_PATCH
    );
    Serial.print("IDF 版本: ");
    Serial.println(IDF_VER);
    Serial.printf("闪存容量: %d MB\n", ESP.getFlashChipSize()/1024/1024);
    Serial.println();
    Serial.println("启动完成，开始初始化");

    portalMountStorage();
    portalStartAccessPoint();
    portalStartDns();
    portalSeedManifestVersion();

    Serial.println("正在启动 Web 服务");
    portalStartHttp();
    Serial.println("正在启动 HTTPS 服务");
    portalStartHttps();
    Serial.println("准备就绪");
    portalLedReady();
}

void loop()
{
    portalProcessDns();
    portalProcessHttp();
    portalLedUpdate();
    delay(2);
}
