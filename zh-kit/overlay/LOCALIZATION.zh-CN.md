# 汉化记录（简体中文）

这份文件是给"下次同步上游"用的。上游是
<https://github.com/percdotdev/ps5-webkit-autoloader-esp32>，
本仓库是 <https://github.com/q1378659137/ps5-webkit-autoloader-esp32>。
`upstream` remote 已配好（`git remote -v` 可见）。

**更新上游只做一件事**（2026-11-23 起）：

```sh
python tools/relocalize.py          # 克隆上游 → 备份 → 清空 → 重放汉化 → 跑验收
```

它读 `zh-kit/`（汉化套件）。改过中文措辞就补一句
`python tools/refresh-zh-kit.py --source <上游克隆>`，否则下次重建会盖回旧译文。
细节在 §4，套件怎么维护在 §9。

---

## 1. 汉化范围（改了哪些文件，各自为什么）

| 文件 | 改动 | 性质 |
| --- | --- | --- |
| `flasher/language/zh.js` | **新文件**，整份中文语言包（78 键，与 `en.js` 一一对应） | 纯新增 |
| `flasher/language/language.js` | `import { zh }` + `const STRINGS = { en, es, zh }` | 两行注册 |
| `flasher/index.html` | 语言切换组加一枚 `<button data-set-lang="zh">中文</button>` | 一处按钮 |
| `flasher/app/base.css` | `--sans` 字体栈补 `PingFang SC / Hiragino Sans GB / Microsoft YaHei / Noto Sans SC` | 字形回退 |
| `flasher/ui/controls.css` | `.seg button` 加 `white-space: nowrap` | 防「中文」竖排断行 |
| `flasher/app/layout.css` | `.brand` 加 `min-width:0` + 文字省略；≤560px 隐藏品牌文字、只留图标 | 三个语言按钮在窄屏会挤掉品牌名 |
| `README.md` | 换成中文版 | 全文重写 |
| `README.en.md` | **新文件**，原样保存上游英文 README（只改首行语言链） | 原文备份 |
| `README.es.md` | 首行语言链指向 `README.en.md`，补中文入口 | 一行 |
| `host/installer/index.html` | 开发板发给 PS5 的过渡页，文案换成中文 + `<html lang="zh-CN">` + CJK 字体栈 | 源模板，**会被下次打包读走** |
| `host/installer/cache.html` | 同上（缓存进度页），含 JS 里的 9 条状态/错误文案 | 源模板 |
| `host/packed/index.html`、`cache.html` | 上面两个模板 + 版本占位符填充后的**已提交产物**（固件就吃这一份） | 由 `tools/sync-payload-pages.py` 生成 |
| `firmware/esp32/*.ino`、`*.cpp` | 串口日志文案（启动横幅、AP、LittleFS、HTTP/HTTPS/TLS）；404 正文改中文并补 `charset=utf-8` | 原地替换，60 处 |
| `firmware/esp8266/*.ino`、`routes.h` | 同上（ESP8266 变体） | 同上 |
| `debug/serial_timestamp.py` | 串口监视器：Windows 切 65001、按 UTF-8 解码、坏字节降级为 `?`；新增 `--self-test` | 防乱码 |
| `tools/check-i18n.mjs` | **新文件**，键集合 / 数组长度 / `{s}` 占位符比对 | 同步用 |
| `tools/verify-zh-render.mjs` | **新文件**，刷写页的无头 Chrome 渲染断言 + 截图 | 验收用 |
| `tools/verify-zh-console-pages.mjs` | **新文件**，PS5 侧两个页面的渲染断言 + 截图 | 验收用 |
| `tools/sync-payload-pages.py` | **新文件**，把 `host/installer/` 的两个模板填成 `host/packed/` 的两个产物（沿用现有版本号/构建时间） | 改完模板就跑 |
| `tools/zh-firmware-strings.py` | **新文件**，固件那 60 处文案的**对照表**；`--check` 报告漂移、`--verify` 校验编码/结构 | 同步+验收 |
| `flasher/**/*.js`、`flasher/**/*.css`、`tools/*`、`pack/*`、`debug/*`、`install-deps.sh` | 代码**注释**与脚本 docstring 换成中文 | 2026-11-23 第二轮加做；代码零改动，见 §8 |
| `zh-kit/overlay/**`、`zh-kit/comments.json` | **新目录**，汉化套件：整份归我们的文件 + 注释英中对照。上游每次更新都靠它重放 | 见 §4.0 |
| `tools/relocalize.py` | **新文件**，一条命令：克隆上游 → 备份 → 清空 → 覆盖套件 → 打补丁 → 应用固件表 → 同步产物 → 跑验收 | 日常更新只用这个 |
| `tools/refresh-zh-kit.py` | **新文件**，改过中文措辞后把 `zh-kit/` 刷成本地现在的样子 | 改完文案就跑 |
| `tools/zh-app-shell.py` | **新文件**，Payload Manager（`host/packed/app/**`）外壳文案的对照表；`--check` 报漂移 | 打包产物，随 payload 更新 |
| `tools/audit-zh-leftovers.mjs` | **新文件**，无头 Chrome 跑四个页面，列出还带英文的可见文本（带"已知保留"理由） | 验收 |
| `tools/pack-source-zip.py` | **新文件**，把源码打 `out/*.zip` | 交付 |

**只动文案，不动逻辑**：所有 `id`、`class`、`data-*`、正则、键名、变量名、文件名保持原样。
进度 UI 依赖的正则（`/^Wrote (\d+) bytes…/`、`/^Chip is /` 等）一个字没改——改了就匹配不上、
界面会卡在「准备中」。PS5 侧两个页面同理：`/PlayStation 5\/(\d+\.\d+)/`、`marker.trim() !== version`、
`location.replace('/app/index.html')` 一个字符都不能动。

## 2. 术语表（改文案时按这个来，别自创同义词）

| English | 本仓库统一译法 | 备注 |
| --- | --- | --- |
| board | **开发板** | 用户指定。全仓库统一，不用「板子」「电路板」「开发板子」 |
| chip | 芯片 | |
| firmware | 固件 | |
| flash / flashing | 刷写 / 刷写工具 | 名词用「网页刷写工具」，动词用「刷写」 |
| download mode | 下载模式 | |
| bootloader / BOOT | BOOT | 按键名不译，`rich()` 会包成 `<kbd>` |
| hotspot | 热点 | |
| portal | 门户页 | 指开发板提供的那个网页 |
| release | 发行版 | 具体版本号（如 `v0.8.4`）保留原文 |
| stable / pre-release | 稳定版 / 预发行版 | |
| payload | payload | 专有名词，不译；`Payload Manager` 是程序名，保留 |
| exploit | 漏洞利用 | 链名（poops / Relapse）保留原文 |
| User's Guide | **用户指南** | PS5 中文界面里的叫法 |
| Settings / Media / Guide and Tips | 设定 / 媒体 / 指南与提示 | 按 PS5 简中菜单 |
| guide（步骤 4 标题） | 在 PS5 上设置 | |
| serial port / COM | 串口 / COM 口 | |
| verify / verified | 校验 / 校验通过 | |
| erase flash | 擦除闪存 | |
| ESP32-S2 Mini 等 | 原样保留 | 商品名，印在板子上，译了反而对不上 |

固件串口日志另外几条（这几条只影响 `firmware/` 与 `debug/serial_timestamp.py`）：

| English | 译法 | 备注 |
| --- | --- | --- |
| `BOOT` / `READY` | 启动 / 准备就绪 | 只是给人看的阶段标记，仓库里没有脚本 grep 它们（已确认） |
| `Starting …` | 正在启动 … | |
| `LittleFS mounted` / `mount failed` | LittleFS 已挂载 / 挂载失败 | |
| `softAPConfig` / `softAP` | AP 参数配置 / 热点启动 | 后面的 `OK` / `FAILED` 保留英文 |
| `AP IP` / `Channel` | AP 地址 / 信道 | `SSID`、`MAC`、`DNS` 保留原样 |
| `cert len` / `key len` | 证书长度 / 密钥长度 | `last: %02X` → `末字节: %02X` |
| `handshake` | 握手 | `[TLS] 握手成功: fd=3` |
| `manifest`（日志里） | 清单 | 对应 AppCache manifest |
| `404 Not Found`（**正文**） | 404：页面不存在 | 状态行仍是英文 |

## 3. 中文语言包的结构

`flasher/language/zh.js` 和 `en.js` **键名完全一致**，只是值换成中文。层级扁平（只有
`pill` 一个嵌套对象），`helpItems / prepItems / gWifiItems / gGuideItems` 是字符串数组，
**长度必须和英文一致**——`guide.js` 按数组逐条渲染，少一条就少一行步骤。

字符串里的 `{s}` 是占位符（`left: "剩余 {s} 秒"`），`flow.js` 用 `.replace("{s}", n)` 填秒数。
占位符丢了会显示「剩余 秒」。

`rich()`（`flasher/ui/dom.js`）会把 `ESP32_PORTAL`、`12345678`、`BOOT`、`autoload.txt`
这四个词换成 `<code>` / `<kbd>`。所以中文译文里**这四个词必须按原样出现**，否则那段就不再是
等宽/按键样式。

## 4. 下次更新上游的做法

**从 2026-11-23 起不再用 merge：每次都从上游重新克隆一份，删掉本地代码，再重放汉化。**
这样本地永远等于「上游最新 + 我们这一层汉化」，不会积累补丁债。

```sh
# 0) 先看上游这次动了什么（只克隆+比对，不动本地）
python tools/relocalize.py --check

# 1) 试跑：建到临时目录，本地原封不动
python tools/relocalize.py --into D:/tmp/zh-try

# 2) 正式重建（会先把当前目录打包成 <目录名>_bak_<时间戳>.zip，再清空）
python tools/relocalize.py

# 3) 要指定版本就加 --ref
python tools/relocalize.py --ref v0.8.5
```

顺序是固定的，任何一步断言失败都会停，不会留半成品：

| 步 | 动作 | 失败时 |
| --- | --- | --- |
| 1 | `git clone --depth 1` 上游（走 `HTTPS_PROXY`，本机是 `http://127.0.0.1:10808`） | 报错退出，本地没动 |
| 2 | 备份当前目录 → 清空 | — |
| 3 | 铺上游代码（含 `.git`，方便 `git status` 看汉化改了什么） | — |
| 4 | 覆盖 `zh-kit/overlay/` 里的**整份文件**（清单见 §9） | 缺文件即报错 |
| 5 | 打 `relocalize.PATCHES` 的 20 条小补丁（锚点必须命中 1 次） | 列入「需要人工看一眼」 |
| 6 | 按 `zh-kit/comments.json` 换 113 条注释 | 对不上的列成「注释漂移」 |
| 7 | 由上游 `README.md` 生成 `README.en.md`（只改首行语言链） | — |
| 8 | `tools/zh-firmware-strings.py` 应用 60 条固件文案 | 列出 `[FAIL]` 条目 |
| 9 | `tools/sync-payload-pages.py` 重新生成 `host/packed/` 两页 | — |
| 10 | `tools/zh-app-shell.py` 把 Payload Manager 外壳文案换成中文 | 列出 `[FAIL]` 条目 |
| 11 | 7 项验收：i18n / 固件表 / 固件结构 / app 外壳 / 串口自检 / 30 条渲染 / 17 条渲染 | 任一项失败退出码 1 |

### 4.0 上游改了什么，看这几处提示

- **注释漂移**：`comments.json` 匹配不上，说明上游改了注释措辞。看 `git diff` 把新英文行译好，
  再 `python tools/refresh-zh-kit.py --source <上游克隆>` 重刷套件。
- **补丁锚点失败**：上游动了 `language.js` / `index.html` / 那几行 CSS。按 `PATCHES` 里的
  `why` 字段找到位置，更新锚点。
- **固件表 `CHANGED UPSTREAM`**：改 `tools/zh-firmware-strings.py` 的 `TABLE`（细节见 §4.2.2）。
- **i18n `missing:`**：`en.js` 加了新键，补进 `zh.js`，再刷套件。
- **PS5 侧两页**：`host/installer/` 是整页覆盖，上游改文案不会自动跟进。
  `--check` 的差异清单里出现这两页时，人工把新文案译进 overlay。

**改过中文措辞之后**（`zh.js`、README、注释都算），一定跑一次
`python tools/refresh-zh-kit.py --source <上游克隆>`，否则下一次重建会把旧译文盖回来。

---

> 下面 4.1–4.3 是 2026-11-23 之前的**旧 merge 流程**，已经不用了。
> 但里面「哪些地方一定会冲突、冲突了怎么解」的判断仍然有效，出问题时可以照着排查。

### 4.1 `README.md` 一定会冲突

我们在自己的仓库里把 `README.md` 换成了中文，上游改的也是 `README.md`。处理办法：

```sh
# 取上游最新英文，覆盖我们的英文备份
git show upstream/main:README.md > README.en.md
# 然后把 README.en.md 里新增/改动过的段落，按第 2 节术语表译进 README.md
```

上游改了 `README.es.md` 时，别忘了它的首行语言链要重新指到 `README.en.md`。

另外两处容易被合并冲掉的细节：

- 中文 `README.md` 里指向刷写工具的两个链接写的是**本仓库的 Pages**：
  `https://q1378659137.github.io/ps5-webkit-autoloader-esp32/?lang=zh`。
  上游用的是 `percdotdev.github.io`，那边没有中文包，`?lang=zh` 会静默回退英文。
  合并时保留本仓库地址；仓库改名或没开 Pages 的话就改这两处。
- 中文 `README.md` 末尾的「关于中文界面」整节是我们加的，上游没有，合并后要补回来。

### 4.2 `flasher/` 一般只在两处冲突

1. `language/language.js` —— 上游若加了新语言，`const STRINGS = {...}` 那行取并集，
   务必把 `zh` 留着：`const STRINGS = { en, es, zh }`。
2. `index.html` —— 语言按钮组。上游加了语言就跟着加，`data-set-lang="zh"` 那枚不能丢。

### 4.2.1 `host/installer/` 是**整页重写**，上游一改就冲突

那两个文件没有 i18n，我们是原地换成中文，所以上游任何文案改动都会撞。处理办法：
拿上游版本填进英文习惯的措辞、再按第 2 节术语表译一遍，然后：

```sh
python tools/sync-payload-pages.py     # 重新生成 host/packed 的两个产物
node tools/verify-zh-console-pages.mjs # 17 条断言
```

容易漏的三处：`cache.html` 里 `fail('…')` 的内联字符串、`obsolete` 分支的提示、
以及 `aria-label="缓存下载进度"`（上游是 `Cache download`）。`host/packed/` 每次合完
都当成"产物"重新生成，别手工改它。

### 4.2.2 上游改了固件日志：`--check` 会告诉你哪几条漂了

```sh
python tools/zh-firmware-strings.py --check
```

状态含义：

- `applied` —— 已是中文，没事。
- `pending` —— 还是英文原文，跑一次不带 `--check` 的就补上了。
- `CHANGED UPSTREAM` —— 上游动过这一行（改了措辞、加了参数、调了缩进），
  **表里那条的原文对不上了**。这种情况不要硬跑：对着 `git diff upstream/main -- firmware`
  看一眼上游改了什么，把表里那条的"原文"更新成新版本，再重新译一遍译文，然后跑
  `--verify` 确认格式占位符没变。

上游加了一条全新的日志行，`--check` 不会报它（它不在表里）。所以合完上游顺手
`git diff upstream/main -- firmware | grep '^+.*Serial\.'` 扫一眼新增的 `Serial` 行，
有新的就往 `TABLE` 里加一条。

`zh.js` 是新文件，不会冲突，但**上游往 `en.js` 加的新键不会自动出现在 `zh.js` 里**，
界面会静默回退成英文。所以合完必须跑：

```sh
node tools/check-i18n.mjs
```

期望输出：

```
en: 78 keys (en.js, es.js, zh.js)
[ OK ] es: 78/78
[ OK ] zh: 78/78

All language files match en.js.
```

`[FAIL] zh:` 后面列出的 `missing:` 就是这次要补的键；`extra:` 是上游删掉的键，从 `zh.js`
里删掉即可；`array length differs` 说明数组条数变了，要对着英文补/删；
`placeholder differs` 说明 `{s}` 之类的占位符译丢了。

### 4.3 验收（必须做，别靠眼睛）

```sh
node tools/verify-zh-render.mjs          # 网页刷写工具
node tools/verify-zh-console-pages.mjs   # 开发板发给 PS5 的两个页面
```

期望输出最后一行：`30/30 passed` 和 `17/17 passed`，截图都落在 `tools/shots/`：
`zh-desktop.png`、`zh-mobile.png`、`zh-dark.png`、`console-index.png`、
`console-unsupported.png`、`console-cache.png`。

`verify-zh-render.mjs` 断言的是 `textContent` / `aria-pressed` / 计算样式，不是"看截图觉得像中文"：
标题、首段、状态胶囊、四个步骤标题、安装按钮（带版本号）、PS5 指南条数、语言按钮选中态、
`zh-CN` 浏览器自动命中中文、切回 EN/ES 仍然生效、移动端无横向溢出、深色主题正文为浅色。
它把 unpkg 的 esptool-js 和 GitHub API 都在本地应答了，所以离线也能跑
（`bin/*` 会 404，那是 pages 工作流才发布的构建产物，脚本单独列出不算失败）。

`verify-zh-console-pages.mjs` 把 `host/packed/` 当站点根，用假 PS5 UA 跑两条分支：
支持范围内（走 `正在准备缓存…`，重定向被 204 挡掉停在原地）和超出范围（走 `不支持的固件`），
再单独跑一遍 `cache.html`；断言标题/状态行/页脚/`aria-label`/`characterSet`/无 `\uFFFD`。

**断言里不要写死版本号**：payload 版本每次发布都会变。要断版本就从仓库里读
（本项目的版本和构建时间在 `host/packed/cache.appcache` 第 2 行），否则每次 bump 都要改脚本，
还会把"页面是对的"误报成"汉化坏了"。（2026-11-23 同步时就踩了这一下，见第 7 节。）

依赖：`puppeteer-core`（用 `PUPPETEER_DIR` 指到装了它的目录）+ 本机 Chrome（`CHROME` 覆盖）。

### 4.3.1 改过 PS5 侧模板，一定要同步产物

`host/packed/index.html`、`cache.html` 是 `host/installer/` 两个模板填完 `[[VERSION_PLACEHOLDER]]`
`[[BUILD_TIME_PLACEHOLDER]]` 的结果。固件吃的是 packed 那一份，所以只改模板等于没改：

```sh
python tools/sync-payload-pages.py
```

版本号和构建时间从 `host/packed/cache.appcache` 第 2 行读（`# WebKit Autoloader v0.8.x (built …)`），
不会瞎编。跑完自己核一下两边只差占位符填充：

```sh
python -c "import re,pathlib as p;m=re.search(r'v(\S+) \(built ([^)]+)\)',p.Path('host/packed/cache.appcache').read_text('utf-8').splitlines()[1]);v,b=m.groups();print([p.Path('host/installer/'+n).read_text('utf-8').replace('[[VERSION_PLACEHOLDER]]',v).replace('[[BUILD_TIME_PLACEHOLDER]]',b)==p.Path('host/packed/'+n).read_text('utf-8') for n in ('index.html','cache.html')])"
```

CI 每次发布都会用 `host/installer/` 重新打包并把结果写回 `host/packed/`，所以只要模板是中文，
产物迟早也是中文；这一步只是让你**本地这份**立刻可用、且能离线编固件。

### 4.3.2 固件文案：一张对照表，两个开关

`firmware/` 里的中文不是硬改完就算，全部集中在 `tools/zh-firmware-strings.py` 的 `TABLE`
（60 条，逐条给**整行原文 → 整行译文**）。三种用法：

```sh
python tools/zh-firmware-strings.py            # 应用（幂等，已改过的会显示 already applied）
python tools/zh-firmware-strings.py --check     # 只报告：applied / pending / CHANGED UPSTREAM
python tools/zh-firmware-strings.py --verify    # 结构校验，见下
```

用整行匹配而不是替换字符串是有原因的：`"404 Not Found"` 在 `https_server.cpp` 里出现两次，
一次是 **HTTP 状态行**（必须英文），一次是**正文**（可以中文）。整行匹配只会命中正文那一行。

`--verify` 断言四件事，任何一条不满足就退出码 1：

1. 表里每一条都是"纯字符串编辑"——把引号内容抹掉后，新旧两行的代码骨架必须完全相同
   （所以不可能改出编译错误：`Serial.printf(` 的参数、括号、分号一个没动）。
2. 所有固件源文件是 UTF-8、**无 BOM**、仍然是 CRLF。
3. 中文只出现在 `Serial.` / `logTlsMemory(` / `portalLogHeap(` / 404 正文这四类行上；
   用中英混写的方式往路由、头字段、状态行里塞中文会立刻被抓出来。
4. `git diff` 里没有任何一行**含协议串**被删改：`Success`、`Microsoft Connect Test`、
   `Microsoft NCSI`、`"incomplete"`、`ESP32_PORTAL`、`12345678`、`text/html; charset=utf-8`、
   `application/octet-stream`、`no-cache`。

第 4 条是最重要的护栏：这几种串译了不是"看着别扭"，是**真坏**——
`Success`/`Microsoft NCSI` 是系统判断"这个 Wi-Fi 能不能上网"的约定应答，
`"incomplete"` 是 `strcmp` 的另一半，SSID 写错了 PS5 连不上，`charset` 写错就乱码。

### 4.3.3 防乱码的三道闸

1. **源文件编码**：UTF-8 无 BOM（`--verify` 检查）。带 BOM 的文件 gcc 能过，但别的工具链
   （尤其是 `.ino` 交给 arduino-cli 预处理的路径）容易出怪问题，统一不带。
2. **线上编码**：凡是中文要经过 HTTP 出去的，`Content-Type` 必须显式带 `charset=utf-8`。
   这次只改了 404 正文，所以顺手把 `text/plain` 改成了 `text/plain; charset=utf-8`；
   页面本身早就是 `text/html; charset=utf-8`（`host_files.cpp` 里写死的）。
3. **终端编码**：串口日志是 UTF-8 字节流，`debug/serial_timestamp.py` 会先
   `SetConsoleOutputCP(65001)` 再按 UTF-8 解码，坏字节降级成 `\ufffd` 而不是抛异常。
   自检：`python debug/serial_timestamp.py --self-test`（三条样例，含被截断的多字节字符）。

顺带一条**别踩**的：不要把中文塞进 `char buf[N]` / `vsnprintf` 那类定长缓冲。
中文一个字 3 字节，按字节截断会把一个字符切成两半 → 输出非法 UTF-8 → 乱码。
`https_server.cpp` 里 `tlsDebugVprintf` 的 256 字节缓冲就属于这类，所以 `esp_log` 的话一个字都没动。

### 4.4 改完后自检清单

- [ ] `node tools/check-i18n.mjs` 全 OK
- [ ] `node tools/verify-zh-render.mjs` 全 passed
- [ ] `node tools/verify-zh-console-pages.mjs` 全 passed
- [ ] 改过 `host/installer/` 就跑过 `tools/sync-payload-pages.py`
- [ ] 改过 `firmware/` 就跑过 `python tools/zh-firmware-strings.py --check`（0 drifted）和 `--verify`（OK）
- [ ] `python debug/serial_timestamp.py --self-test` 三条全 OK
- [ ] 中文界面上没有半中半英的句子
- [ ] `?lang=zh` 和浏览器语言两条路都能进中文
- [ ] EN / ES 切回去没坏

## 5. 刻意没汉化的部分（不是漏了）

| 位置 | 为什么 |
| --- | --- |
| esptool-js 日志行（`Chip is ESP32-S2 …`、`MAC: …`、`Writing at 0x…`） | 是工具输出，且被 `log/format-line.js` 的正则逐行匹配；译了会匹配不上。只有 `Wrote … / Hash of data verified / Chip is` 三种行被 `t()` 包装成中文前缀，芯片描述本身仍是英文 |
| 固件里的联网探测应答：`Success` / `Microsoft Connect Test` / `Microsoft NCSI` / `OK` | 系统拿这几个字面量判断"这个 Wi-Fi 通不通"，改一个字就没法自动弹登录页，PS5 也进不到用户指南 |
| 固件里的 `strcmp(sni, "incomplete")` | 比较的另一半，改了 TLS 探测的循环就永远提前 break |
| SSID `ESP32_PORTAL`、密码 `12345678` | README、刷写页、PS5 连接步骤全都在用这串常量 |
| 固件的 HTTP 状态行、header 值、MIME、路由路径 | 协议。`charset=utf-8` 反而必须显式存在，否则中文乱码 |
| 固件里的字段式日志（`[HTTP] 404: %s`、`[HEAP] … free=%u`、`MAC: %s`、`SSID: %s`、`[MANIFEST] version=%s`） | 键名留着方便 grep 和对照上游；译了反而不好定位 |
| `esp_log` / TLS 调试那 256 字节缓冲里的内容 | 定长缓冲按字节截断会把中文字符切半 → 非法 UTF-8 → 乱码。ESP-IDF 自己的日志也本来就是英文 |
| 芯片型号、开发板商品名（`ESP32-S2 Mini`、`ESP32-C3 Super Mini` 等） | 印在实物和商品页上，译了用户反而对不上；`catalog.js` 里也是 path 拼装的一部分 |
| `flasher/share/og.html` → `og.png` | 社交分享用的静态图，改文案要重新出图，收益低 |
| `host/packed/app/**`（itsPLK 的 Payload Manager 界面） | **外壳已汉化**（标题、页脚、HUD、进度条状态，见 `tools/zh-app-shell.py`）。剩下没译的是 `vendor/wobkot/**` 的步骤日志和 `[*] Starting Wobkot userland` —— 后者被 `app.js` 的进度正则按字面匹配，译了进度条就不动 |
| `flasher/index.html` 的 `<title>`、品牌名 `WebKit Autoloader` | 产品名（PS5 侧两个页面同理，`WebKit Autoloader` 保留，只把 `Installer` 译成「安装器」） |
| 语言按钮组的 `aria-label="Language"` | 只给读屏软件用，`en.js` 里没有对应的键；为了不弄出「比英文多键」的情况，故意没加 |
| 代码注释 | **不是没汉化，是 2026-11-23 才补的**：`flasher/`、`tools/`、`pack/`、`debug/`、`install-deps.sh` 的注释与 docstring 都已换成中文（见 §8）。`firmware/` 的 C/C++ 源码本来就没有注释 |

> PS5 侧那两页的中文字形依赖控制台自带的 CJK 回退字体。真机上若出现方块，
> 说明该固件版本没有可用字形，`git checkout -- host/installer host/packed` 即可退回英文。
> 固件日志同理：终端不支持 UTF-8 时看到的是 `?` 而不是乱码，不会崩。

## 6. 一句话版本

网页刷写工具：`zh.js` 纯新增，`language.js` 和 `index.html` 各一行，其余是字体/换行的小修补。
PS5 侧两页：`host/installer/` 原地换中文，再跑 `tools/sync-payload-pages.py` 生成 `host/packed/`。
固件：`tools/zh-firmware-strings.py` 里的 60 条对照表 + `debug/serial_timestamp.py` 的 UTF-8 输出。
同步上游后依次跑 `check-i18n` / `verify-zh-render` / `verify-zh-console-pages` /
`zh-firmware-strings.py --check --verify` / `serial_timestamp.py --self-test`，全绿就算完事。

## 7. 同步记录（照着上一条的做法复现）

### 2026-11-23 · 上游 `f5b16a0 → 5cb13d2`（6 个提交，payload 0.8.3 → 0.8.4）

实际发生的事情，可以当成后续同步的模板：

| 步骤 | 结果 |
| --- | --- |
| `git fetch upstream`（走 `http://127.0.0.1:10808`） | 快进 6 个提交，新增 tag `0.8.4` |
| 上游改了什么 | 只有 `.github/**`、`install-deps.sh`、`host/packed/**`（payload 换 0.8.4）；**`flasher/`、`firmware/`、`README*`、`host/installer/` 一个都没动** |
| `git merge upstream/main` | 冲突只有两个：`host/packed/index.html`、`host/packed/cache.html`（我改了文案、上游改了版本号） |
| 解冲突 | `git checkout --theirs` 取上游（英文 + 0.8.4）→ `python tools/sync-payload-pages.py` 按模板重新生成中文（自动读到 `v0.8.4 / 2026-11-23 00:47:38 UTC`） |
| 验收 | 固件表 0 drifted、固件结构 OK、i18n 78/78、刷写页 30/30；**PS5 侧页 16/17** |

那 1 条失败是校验脚本自己的问题，不是页面坏了：`index：标题中文 + 版本号` 里写死了
`v0.8.3`，而页面正确显示 `v0.8.4`。**教训：校验脚本里不要写死版本号**，
改成从 `host/packed/cache.appcache` 读，之后每次 bump 都不用改脚本。
顺手把 `verify-zh-render.mjs` 里那个假的 GitHub release 从 `v0.8.3` 换成 `v9.9.9`
（明显是合成值，不会跟真实版本混淆），`debug/serial_timestamp.py` 自检样例里的
`/app/0.8.3/x.js` 也换成不含版本号的 `/app/x.js`。

**没冲突不等于不用检查**：这一轮 `flasher/`、`firmware/` 上游都没碰，但如果哪天碰了，
`zh-firmware-strings.py --check` 会给出 `CHANGED UPSTREAM`，`check-i18n.mjs` 会给出 `missing:`，
两条命令分别守住固件和网页两块。

## 8. 第二轮：在一份干净的上游源码树上重放（2026-11-23）

这次拿到的目录**没有 `.git`**（是复制/解压出来的源码树，不是克隆的工作区）：
`zh.js` 不存在、`README.md` 是英文、`host/installer/` 两个模板是英文、`firmware/` 日志也是英文，
但 `tools/` 里那四个脚本（含 60 条对照表）还在。于是照着本文档从头重放一遍。

| 步骤 | 做了什么 | 结果 |
| --- | --- | --- |
| 1 | 新写 `flasher/language/zh.js`（78 键） | `check-i18n` → `zh: 78/78` |
| 2 | `language.js` 注册 `zh`、`index.html` 加中文按钮、三处 CSS（CJK 字体栈 / `nowrap` / 窄屏省略品牌名） | 940px 与 320px 都不溢出 |
| 3 | `README.md` 中文重写；`README.en.md` 存英文原文；`README.es.md` 首行语言链改指 `README.en.md` | 三条互相指得到 |
| 4 | `host/installer/{index,cache}.html` 原地换中文，再跑 `sync-payload-pages.py` | 产物 2889 / 6357 字节（v0.8.4） |
| 5 | `python tools/zh-firmware-strings.py` | 60 条应用，`--check` 0 drifted，`--verify` OK |
| 6 | `debug/serial_timestamp.py` 换 UTF-8 输出 + `--self-test` | 三条样例全 OK |
| 7 | 注释与 docstring 汉化（见下） | 49 个 flasher 文件"去注释后逐字节一致" |

### 8.1 注释汉化的做法

把"整行（去掉缩进后）原文 → 译文"写成一张表，脚本按**整行**匹配替换，然后拿替换前的快照
做断言：**两边去掉注释后必须逐字节相同**。这样"只动注释"是可证的，不靠眼睛。

踩到的坑（下次别再踩）：脚本按 `\n` 切开、替换完再拼回去时，**被替换那一行末尾的 `\r` 丢了** ——
缩进是从行首截的，行尾的 `\r` 跟着被替换内容一起消失，于是文件变成 LF/CRLF 混用，
`git diff` 看着像整个文件重写。修法只有两条：替换时保留每行的 `\r`，或者事后按原文件的换行约定
统一回来（本项目源码全是 CRLF）。比对脚本会把这种差异报成"去掉注释后代码不一致"，
所以这个坑不会静默通过。

### 8.2 这次为什么有 3 条断言会 FAIL

`verify-zh-render.mjs` 里有三处把中文原文写死了：

- 首屏标题 === `把 ESP32 插到这台电脑上`、高级面板各分组标题 === `版本`/`开发板`/`日志`
- `#device .stage-body` 含 `选一块和你手上一样的开发板`
- `#guide` 含 `设定 → 网络 → 设定互联网连接`

换个译法就 FAIL。这不是页面坏了，是**脚本在替你守术语**。要么按这三条译，要么同时改断言，
别只改一边（改了没同步，下次同步上游就会以为汉化坏了）。

### 8.3 没有 `.git` 时会少一条检查

`zh-firmware-strings.py --verify` 的第 4 条（"没有任何含协议串的行被删改"）靠 `git diff` 取改动行，
目录不是仓库时会打印 `[warn] git not usable here` 并跳过，其余三条照常。要完整跑就先 `git init`
或者从克隆下来的仓库里跑。

### 8.4 本轮验收输出

```
node tools/check-i18n.mjs                    en: 78 keys · [ OK ] es 78/78 · [ OK ] zh 78/78
python tools/zh-firmware-strings.py --check  0 entries drifted from the table.
python tools/zh-firmware-strings.py --verify OK
python debug/serial_timestamp.py --self-test 自检通过（英文行 / 中文行 / 截断的多字节字符）
node tools/verify-zh-render.mjs              30/30 passed
node tools/verify-zh-console-pages.mjs       17/17 passed
```

## 9. 汉化套件 `zh-kit/`

```
zh-kit/
  overlay/          "整份归我们"的文件（清单即 tools/relocalize.py 的 OVERLAY），重建时直接覆盖上游同名文件
  comments.json     39 个文件 / 113 条「英文注释整行 → 中文整行」对照
```

| 文件类别 | 放在哪 | 为什么 |
| --- | --- | --- |
| 我们写的 / 整页重写的（`zh.js`、中文 README、PS5 侧两页、串口工具、本文档、本仓库自己的工具脚本） | `overlay/` | 上游没有对应实现，或整页换语言，逐行合并没意义 |
| 只改几行的（`language.js` 注册语言、`index.html` 的按钮/静态文案/lang/og、字体栈、`nowrap`、品牌省略、`README.es.md` 语言链） | `tools/relocalize.py` 的 `PATCHES` | 每处都有「锚点必须命中一次」的断言，上游一改就报错，不会静默错位 |
| 只换注释的（`flasher/**`、`pack/*`、`install-deps.sh`） | `comments.json` | 与代码无关，按整行对照替换最安全 |
| 固件 60 条日志文案 | `tools/zh-firmware-strings.py` 的 `TABLE` | 本来就是对表 + 结构校验 |
| Payload Manager 外壳（标题/页脚/HUD/进度状态） | `tools/zh-app-shell.py` 的 `RULES` | 产物目录，随 payload 重打包，只能对表重放 |
| `host/packed/*.html`、`host/packed/app/**` 的其余部分 | **不进套件** | 是产物：前两个由 `sync-payload-pages.py` 生成，其余是上游 payload 原样搬运 |

### 9.1 什么时候必须刷套件

只要**改了会被套件覆盖的内容**，就刷：

- 改了 `zh.js`、中文 README、PS5 侧两页、工具脚本里的中文；
- 改了注释的译法（`comments.json` 里那 113 条）；
- 上游改了注释措辞、你重新译过之后。

```sh
python tools/refresh-zh-kit.py --source F:/daima/ps5-upstream
```

`--source` 只要一份**干净的上游克隆**（`git clone --depth 1` 即可），脚本靠
「本地 vs 上游逐行比对」重新算出注释对照，并按 OVERLAY 清单重新抄进 `overlay/`。

## 10. 第三轮：把"还剩什么没汉化"变成可复查的清单（2026-11-23 晚）

起因：**板子/刷写页**之外还有英文没被发现。这次不靠眼睛，做了一件工具，把"还剩什么英文"变成清单。
（PS5 上 `127.0.0.1:18181` 那一页不在这里 —— 它属于 installer ELF，见 §11。）

| 工具 | 作用 |
| --- | --- |
| `tools/audit-zh-leftovers.mjs` | 无头 Chrome 打开四个页面，取 `innerText` + `aria-label/title/placeholder/alt`，凡是含 3 个以上连续英文字母、又不在白名单里的就列出来。**白名单 = LOCALIZATION §5 的"故意不译"清单**，另有一组 `KNOWN` 带理由单独打印 |

审计后补上的汉化：

- `flasher/index.html` 的静态英文：`<html lang>`、`<meta description>`（3 处）、`og:locale`、
  两个 `image:alt`、跳到正文、状态胶囊初始文案、两个 `aria-label`（语言 / 切换主题）。
  这些都在 JS 跑起来之前可见或被读屏软件念出来。
- `host/packed/app/**`（Payload Manager）的外壳：页面标题、`STANDALONE.title`、页脚、
  HUD 的 `FW --`、进度条的全部状态文案（16 条）、`Firmware:` / `Agent:` 前缀 —— 见 `tools/zh-app-shell.py`。

审计结果（四个页面）：**待查 0 行**，`KNOWN` 里剩下的都有理由：

| 保留的英文 | 为什么 |
| --- | --- |
| 开发板丝印（`ESPRESSIF`、`POWER`、`AMS1117`、`USB Bridge`、`PICO-D4`、`Proant 440`…） | 是画在板子上的字，译了和实物对不上 |
| `[*] Starting Wobkot userland` | **被 `app.js` 的进度正则按字面匹配**（`/Starting Wobkot userland/i`），译了进度条就不动 —— 同 §1 那条"正则不能碰" |
| `[+] ===USERLAND===`、`[+] Initiate ARW...`、`[+] Agent: <UA>` | `vendor/wobkot/**` 的漏洞利用步骤日志 |
| `Object.defineProperty called on non-object` | JS 引擎自己的报错文本 |
| `WebKit Autoloader`、`Payload Manager`、`ESP32-S2 Mini` 等 | 产品名/型号 |

验收（本轮）：

```
python tools/zh-app-shell.py --check         0 条对不上
node tools/audit-zh-leftovers.mjs            待查 0 行（四个页面）
node tools/verify-zh-render.mjs              30/30 passed
node tools/verify-zh-console-pages.mjs       17/17 passed
```

## 11. PS5 上"安装完成"那一页：**不在本仓库里**

真机截图里那页——蓝底、地球图标、`WebKit Autoloader Installer` / `Installed successfully`，
地址 `127.0.0.1:18181`——**不是** `host/installer/` 里我们汉化的那两个门户页，也不是
`host/packed/` 里的任何文件。它是：

- 来源：itsPLK payload 仓库的 `frontend/installer-page/index.html`
- 打包：他们的 `tools/gen_file_registry.py` 把 `dist/` 里的文件做成**文件注册表（压缩）编进 installer ELF**
- 发出：ELF 在 PS5 自己开的 `127.0.0.1:18181` 上发这一页
- 本仓库的角色：`pack/pack_payload.py` 的 `download_installer()` 只负责把上游**发布好的 ELF** 下载下来塞进 payload

所以改本仓库任何文件都不会影响它；`.elf` 里也没有明文 HTML（`Installed successfully` 等串搜不到）。
`[WKAL]` / `[HTTP] Serving …` 那些日志行同样来自 ELF，不是页面。

### 11.1 已经做好的东西

| 文件 | 内容 |
| --- | --- |
| `tools/zh-installer-page.py` | 29 条对照表；`--source <itsPLK 克隆>` 就地译，`--into` 译到别处，`--check` 只报告 |
| `zh-kit/upstream/installer-page/index.html` | 译好的一份成品（可直接覆盖到 itsPLK 仓库的 `frontend/installer-page/index.html`） |
| `tools/verify-zh-installer-page.mjs` | 无头 Chrome 把"安装完成"分支真跑一遍（假 `applicationCache` + 200 的 `/install`），断言中文/无乱码/无报错并截图 |

验收：`node tools/verify-zh-installer-page.mjs --page zh-kit/upstream/installer-page/index.html`
→ **6/6 passed**，截图 `tools/shots/installer-page-zh.png`。

### 11.2 要让它真在 PS5 上显示中文

必须重建那个 ELF（本机没有 PS5 payload SDK）：

```sh
# 1) 取 itsPLK 仓库并翻译页面
git clone --depth 1 https://github.com/q1378659137/ps5-webkit-autoloader
python tools/zh-installer-page.py --source ./ps5-webkit-autoloader

# 2) 用它的工具链重建 ELF（需要 PS5 payload SDK，按它仓库的 README/Makefile）
#    产物：build/deps/webkit-autoloader-installer_<tag>.elf

# 3) 回到本仓库，让 pack 用这份本地 ELF 打包
python pack/pack_payload.py --web /path/to/ps5-webkit-autoloader
make
```

改 ELF 里的压缩资源行不通：长度一变，注册表的偏移就全乱，页面直接崩。

### 9.2 套件是否最新的判据

**重建出来的树要和你本地这份逐字节一致。** 具体做法：

```sh
python tools/relocalize.py --into D:/tmp/zh-check     # 别动本地
# 然后把 D:/tmp/zh-check 与本地逐文件比对，flasher/ firmware/ tools/ host/ debug/ pack/
# 以及 README*.md、LOCALIZATION.zh-CN.md 应当 0 差异（tools/shots、__pycache__ 除外）
```

2026-11-23 建套件时就是这么验收的：0 差异，且 6 项断言全绿。
如果哪天重建后出现差异，说明套件落后了 —— 先 `refresh-zh-kit.py`，别急着重建本地目录。

## 12. payload 侧也汉化了：引用统一指向 fork（2026-11-23 深夜）

payload 仓库（installer ELF / Payload Manager 的源码）已经在本地 fork 并汉化：

| 仓库 | 地址 | 汉化说明 |
| --- | --- | --- |
| 固件/刷写工具（本仓库） | `https://github.com/q1378659137/ps5-webkit-autoloader-esp32` | 本文档 |
| payload（itsPLK 的仓库） | `https://github.com/q1378659137/ps5-webkit-autoloader` | 见该仓库的 `LOCALIZATION.zh-CN.md` |

本仓库里凡是"去哪里拿 payload / 报 payload 的问题 / 看 payload 源码"的地方，都改指 fork：

- `pack/pack_payload.py`、`pack/pack_payload.sh`：下载与克隆地址
- `host/installer/{index,cache}.html` 页脚（再由 `sync-payload-pages.py` 同步到 `host/packed/`）
- `flasher/index.html` 页脚的 payload 链接（文案从 `itsPLK` 改成 `Payload`）
- `README.md` / `README.es.md` / `README.en.md`
- `tools/zh-installer-page.py` 的译文侧、`tools/zh-app-shell.py` 的 app.js 页脚链接规则

重建时由 `tools/relocalize.py` 的 `rewrite_refs()` 统一处理（`REF_FILES` / `REF_PAIRS`），
不散在各处手改。作者名 `PLK` / `itsPLK` 在产品文案里保留 —— 那是原作者，不是仓库地址。

**注意**：`README.en.md` 是"上游英文 README"的副本，重建时由上游生成后再改地址；
它天然更像上游文档，改动只有语言链和 payload 链接。

## 13. 刷写工具的兜底 API 也指向了汉化仓库

`flasher/firmware/release.js` 优先读同源的 `bin/channels.json`（Pages 工作流写的，指向本仓库 release）；
读不到时才退到 GitHub API。那条兜底原先写死 `percdotdev/...`，本地双击打开页面时会去拉**上游英文固件**，
属于会静默装错东西的隐患，已改指 `q1378659137/...`。`flasher/app/stars.js` 的星标 API 同样改指本仓库。
两条都记进了 `tools/relocalize.py` 的 `PATCHES`，重建不会丢。

## 14. 第四轮：上游重做 flasher（2026-11-25）

上游把一个提交推到了 `e0dd125`（*compress the image on the wire, a progress bar that replaces the button, fresh files on every deploy*），
把刷写页从"一页到底"改成了**五步向导**，顺带换掉了大半文件名。这一轮按规矩是**重克隆 → 清空 → 在新代码上重放汉化**，
不是在旧树上打补丁。

### 14.1 结构变了什么

| 旧 | 新 |
| --- | --- |
| `flasher/steps/`、`flasher/device/stage.js`、`flasher/guide/` | `flasher/wizard/{steps,wizard}.js`、`flasher/device/{art,session}.js` |
| `flasher/install/{button,progress}.js` | `flasher/install/{flow,help,write,verify,wake-lock}.js` |
| 没有 | `flasher/advanced/{sheet.js,advanced.css}`（右侧抽屉：版本/板型/擦除/自有 .bin/日志） |
| 5 块板 | 6 块板，新增 `flasher/boards/devkit.js`（ESP32 DevKit / WROOM-32） |
| `en.js` 101 键（`title/lead/s0Title…`） | `en.js` **78 键**（`plugTitle/connTitle/writeTitle2/moveTitle/wifiTitle/guideTitle…`） |

### 14.2 这轮怎么改的

- `flasher/language/zh.js`：按新键表整份重写（78 键，含 `helpItems` 三条数组、`{board}` / `{n}` 占位符）
- 静态文案：`index.html` 的 `lang`、三处 description、`og:locale`、两处 image:alt、跳过链接、两个 `aria-label`
- 样式：字体栈补 CJK、`.seg button` 加 `nowrap`、品牌名可省略、≤560px 收起品牌文字
- `flasher/app/page-text.js`：中文输出 `lang="zh-CN"`（上游只写 `zh`，浏览器挑字形会差一点）
- 注释：**113 条**（39 个文件），其中新增的 `advanced/`、`wizard/`、`boards/devkit.js` 全新翻译
- `README.md` 按新流程重写（五步向导、DevKit 板、LED 表、SHA256SUMS、Troubleshooting）

### 14.3 验收（本轮真实输出）

```
node tools/check-i18n.mjs                    en 78 · es 78/78 · zh 78/78
python tools/zh-firmware-strings.py --check   0 entries drifted
python tools/zh-firmware-strings.py --verify  OK
python debug/serial_timestamp.py --self-test  自检通过
python tools/zh-app-shell.py --check          0 条对不上
node tools/verify-zh-render.mjs               30/30 passed（新 UI 重写了断言）
node tools/verify-zh-console-pages.mjs        17/17 passed
```

重建判据同前：`relocalize.py --into` 出来的树与本仓库 **180 个文件 0 差异**。

### 14.4 教训

上游改结构时，`comments.json` 的"整行对照"会整片对不上（这轮一次报了 20 条漂移）。
正确做法不是逐条补，而是**在新树里重新译一遍，再 `refresh-zh-kit.py` 重新算对照**——
`comments.json` 是产物，不是手写的清单。补丁同理：这轮的 28 条补丁是按"上游 ↔ 汉化结果"的
逐行差异**自动生成**的，生成后先模拟重放一遍（必须逐字等于目标），再写进 `PATCHES`。

### 14.5 克隆上游别忘了子模块

上游把 `vendor/mklittlefs` 和 `vendor/ps5-unified-autoloader` 做成了 submodule。
`git clone --depth 1` 之后 `vendor/` 是空目录，重建出来的树里也是空的（这轮踩到了：
打完包只有 206 个文件，正常是 412 个）。先补一句再重建：

```sh
git -C <上游克隆> submodule update --init --recursive --depth 1
```

`relocalize.py` 现在会在铺完上游代码后检查这一点，空的话直接打印提示。
