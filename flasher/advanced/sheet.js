import { ICON } from "../ui/icons.js";

const $ = (id) => document.getElementById(id);

// 高级面板：用原生 <dialog>，Esc 关闭、焦点管理和遮罩都是白送的。
export function wireSheet() {
  const sheet = $("adv");
  $("close-adv").innerHTML = ICON.close;
  $("open-adv").addEventListener("click", () => sheet.showModal());
  $("close-adv").addEventListener("click", () => sheet.close());
  sheet.addEventListener("click", (e) => { if (e.target === sheet) sheet.close(); });
}

export function openSheet() {
  $("adv").showModal();
}
