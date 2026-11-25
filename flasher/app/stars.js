const API = "https://api.github.com/repos/q1378659137/ps5-webkit-autoloader-esp32";
const KEY = "stars:v1";

// GitHub 匿名调用每小时限 60 次，所以每个标签页只问一次。
async function loadStars() {
  try {
    const hit = sessionStorage.getItem(KEY);
    if (hit !== null) return Number(hit);
  } catch { /* storage blocked */ }
  try {
    const res = await fetch(API, { headers: { Accept: "application/vnd.github+json" } });
    if (!res.ok) return null;
    const n = (await res.json()).stargazers_count;
    try { sessionStorage.setItem(KEY, String(n)); } catch { /* storage blocked */ }
    return n;
  } catch {
    return null;
  }
}

function compact(n, lang) {
  try {
    return new Intl.NumberFormat(lang, { notation: "compact", maximumFractionDigits: 1 }).format(n);
  } catch {
    return String(n);
  }
}

// 把星标数填到 GitHub 图标旁边；连不上 GitHub 就只留图标。
export async function showStars(link, lang) {
  const n = await loadStars();
  if (n == null) return;
  const count = link.querySelector(".gh-count") || link.appendChild(document.createElement("span"));
  count.className = "gh-count";
  count.textContent = compact(n, lang);
  link.setAttribute("aria-label", `GitHub, ${n} stars`);
}
