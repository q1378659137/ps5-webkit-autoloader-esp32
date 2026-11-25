// 页面当前在做什么。串口对象放在 device/session.js。
// view:  plug | install | move | wifi | guide（当前显示的屏，见 wizard/steps.js）
// phase: idle | connecting | installing | done | error（串口链路状态）
export const state = {
  lang: "en",
  view: "plug",
  board: "s2",    // drawn before connecting; replaced by what the chip says it is
  phase: "idle",
  error: "",      // what went wrong, in words, while phase is "error"
  busy: false,
  started: false, // the board rebooted into the new firmware on its own
  eraseAll: false,
  localFile: null, // { name, data }
  channel: "stable", // stable | pre
  channels: undefined, // { stable, pre } releases; undefined while loading, null when unknown
};
