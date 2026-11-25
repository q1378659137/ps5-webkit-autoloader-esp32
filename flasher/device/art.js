import { boardArt } from "../boards/art.js";

// 开发板绘图。只在换板时重画，这样正在跑的动画不会断。
export function renderArt(root, board) {
  if (root.dataset.board === board) return;
  root.dataset.board = board;
  root.innerHTML = boardArt(board);
}
