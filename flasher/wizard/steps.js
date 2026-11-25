import { state } from "../app/state.js";
import { serialOk } from "../device/session.js";
import { BOARD_NAME } from "../firmware/catalog.js";
import { t } from "../language/language.js";

// 五屏，按顺序排。LED 就按这张表逐个点亮。
export const VIEWS = ["plug", "install", "move", "wifi", "guide"];

const PAYLOAD = "https://github.com/itsPLK/ps5-webkit-autoloader#readme";

// 一屏显示什么：开发板场景、文案，最多一个主按钮。
// `go` 里放动作：install、next、back、again、help、log、copyLink。
export function step(go) {
  const v = state.view;
  if (!serialOk) {
    return {
      scene: "pick", title: t("noSerialTitle"), body: t("noSerialBody"),
      primary: { label: t("copyLink"), run: go.copyLink },
    };
  }
  if (v === "plug") {
    return {
      scene: "plug", title: t("plugTitle"), body: t("plugBody"),
      primary: { label: state.localFile ? t("installFile") : t("install"), run: go.install },
      links: [{ label: t("help"), run: go.help }],
    };
  }
  if (v === "install") {
    const p = state.phase;
    if (p === "error") {
      return {
        scene: "error", title: t("errTitle"), body: state.error || t("fail"),
        primary: { label: t("retry"), run: go.install },
        links: [{ label: t("help"), run: go.help }, { label: t("showLog"), run: go.log }],
      };
    }
    if (p === "installing") {
      return { scene: "writing", title: t("writeTitle2"), body: t("writeBody").replace("{board}", BOARD_NAME[state.board]) };
    }
    return { scene: "connecting", title: t("connTitle"), body: t("connBody") };
  }
  if (v === "move") {
    return {
      scene: state.started ? "portal" : "press",
      title: state.started ? t("moveTitle") : t("pressTitle"),
      body: state.started ? t("moveBody") : t("pressBody"),
      primary: { label: t("next"), run: go.next },
      links: [{ label: t("again"), run: go.again }],
    };
  }
  if (v === "wifi") {
    return {
      scene: "portal", title: t("wifiTitle"), body: t("wifiBody"),
      primary: { label: t("next"), run: go.next },
      links: [{ label: t("back"), run: go.back }],
    };
  }
  return {
    scene: "portal", title: t("guideTitle"), body: t("guideBody"),
    links: [{ label: t("payloadLink"), href: PAYLOAD }, { label: t("back"), run: go.back }],
  };
}
