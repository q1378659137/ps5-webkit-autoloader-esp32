import { state } from "../app/state.js";
import { session, openSession, dropSession } from "../device/session.js";
import { IMAGE_OF, boardOf, imagePath } from "../firmware/catalog.js";
import { fetchImage } from "../firmware/image.js";
import { t } from "../language/language.js";
import { clearLog, logLine } from "../log/log.js";
import { fmtBytes } from "../ui/format.js";
import { showProgress, endProgress, hideProgress } from "./progress.js";
import { holdAwake, releaseAwake } from "./wake-lock.js";
import { writeImage, startFirmware } from "./write.js";

// 数据够估算了，就显示「大约还要 2 分钟」或「大约还要 40 秒」。
function timeLeft(started, f) {
  const spent = (Date.now() - started) / 1000;
  if (f < 0.05 || spent < 3) return t("phWrite");
  const left = Math.max(1, Math.round((spent / f) * (1 - f)));
  return left >= 90
    ? t("leftMin").replace("{n}", Math.round(left / 60))
    : t("leftSec").replace("{n}", Math.max(5, Math.round(left / 5) * 5));
}

function isAbort(err) {
  return Boolean(err?.abort) || err?.name === "NotFoundError";
}

function errorText(err) {
  if (isAbort(err)) return t("noport");
  if (err?.name === "InvalidStateError" || err?.name === "NetworkError") return t("busyPort");
  if (/md5/i.test(String(err?.message))) return t("badVerify");
  return t("fail");
}

// 连接、安装、断开。每次阶段变化后由 `render` 重绘页面。
export function createFlow(render) {
  async function attach() {
    state.phase = "connecting";
    render();
    await openSession();
    state.board = boardOf(session.chip, state.board);
    state.phase = "connected";
    render();
  }

  // 没选端口就退回第一屏；其他错误则提示该怎么办。
  async function fail(err) {
    await dropSession();
    logLine(String(err?.message || err), "bad");
    hideProgress();
    if (isAbort(err)) {
      state.phase = "idle";
      state.view = "plug";
      return;
    }
    state.phase = "error";
    state.error = errorText(err);
  }

  async function run(task) {
    if (state.busy) return;
    state.busy = true;
    try {
      await task();
    } catch (err) {
      await fail(err);
    } finally {
      state.busy = false;
      render();
    }
  }

  async function write() {
    let data = state.localFile?.data;
    const name = state.localFile?.name || IMAGE_OF[state.board];
    if (!data) {
      showProgress(t("phFetch"), null);
      data = await fetchImage(imagePath(state.board, state.channel));
    }
    logLine(`${name} · ${fmtBytes(data.byteLength)}`);

    showProgress(state.eraseAll ? t("phErase") : t("phWrite"), state.eraseAll ? null : 0);
    let started = 0;
    await writeImage(data, {
      eraseAll: state.eraseAll,
      onProgress: (f) => {
        started ||= Date.now();
        showProgress(timeLeft(started, f), f * 100);
      },
    });
  }

  const connect = () => run(async () => {
    clearLog();
    hideProgress();
    await attach();
  });

  const install = () => run(async () => {
    state.view = "install";
    state.error = "";
    await holdAwake();
    try {
      if (!session.loader) {
        clearLog();
        showProgress(t("phConnect"), null);
        await attach();
      }
      state.phase = "installing";
      render();
      await write();
      state.started = await startFirmware();
      const done = state.started ? t("phDone") : t("phDonePress");
      logLine(done, "hi");
      endProgress(done, "ok");
      state.phase = "done";
      state.view = "move";
      await dropSession();
    } finally {
      await releaseAwake();
    }
  });

  const disconnect = () => run(async () => {
    await dropSession();
    state.phase = "idle";
    hideProgress();
  });

  function reset() {
    state.phase = "idle";
    state.view = "plug";
    hideProgress();
    render();
  }

  // 空等的时候板子掉线了（被拔掉或自己重启了）。
  async function lost(port) {
    if (state.busy || port !== session.port) return;
    await dropSession();
    if (state.phase === "connected") state.phase = "idle";
    if (state.view === "install" && state.phase !== "error") state.view = "plug";
    render();
  }

  return { connect, install, disconnect, reset, lost };
}
