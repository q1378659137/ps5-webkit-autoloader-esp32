#include <WiFi.h>
#include <DNSServer.h>
#include "wifi_ap.h"
#include "config.h"
#include "led.h"

static const IPAddress AP_IP(192, 168, 4, 1);
static const IPAddress AP_GATEWAY(192, 168, 4, 1);
static const IPAddress AP_SUBNET(255, 255, 255, 0);

static DNSServer dnsServer;

bool portalDnsAllowed(const String &domain)
{
    return domain == "manuals.playstation.net" ||
           domain == "ena.net.playstation.net" ||
           domain == "www.msftconnecttest.com";
}

void portalStartAccessPoint()
{
    WiFi.persistent(false);
    WiFi.mode(WIFI_OFF);
    delay(200);
    WiFi.mode(WIFI_AP);

    bool configResult = WiFi.softAPConfig(AP_IP, AP_GATEWAY, AP_SUBNET);
    Serial.printf("AP 参数配置: %s\n", configResult ? "OK" : "FAILED");

    bool apResult = WiFi.softAP(PORTAL_AP_SSID, PORTAL_AP_PASSWORD);
    Serial.printf("热点启动: %s\n", apResult ? "OK" : "FAILED");
    if (!apResult) {
        portalLedError();
        while (true) {
            portalLedUpdate();
            delay(10);
        }
    }

    Serial.print("AP 地址: ");
    Serial.println(WiFi.softAPIP());
    Serial.printf("SSID: %s\n", WiFi.softAPSSID().c_str());
    Serial.printf("信道: %d\n", WiFi.channel());
    Serial.printf("MAC: %s\n", WiFi.softAPmacAddress().c_str());
}

void portalStartDns()
{
    Serial.println("正在启动 DNS 劫持");
    dnsServer.setTTL(30);
    dnsServer.setErrorReplyCode(DNSReplyCode::NonExistentDomain);
    bool dnsResult = dnsServer.start(53, "*", AP_IP);
    Serial.printf("DNS: %s\n", dnsResult ? "OK" : "FAILED");
}

void portalProcessDns()
{
    dnsServer.processNextRequest();
}
