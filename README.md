# 宅兹中國 · 金文數字星河

> 何尊铭文里，"中国"两个字第一次被写下来。
> 三千年后，把先秦 1690 个可见金文放进一个可交互、可听闻、可考释的数字宇宙。

纯前端 · Three.js · 零构建。浏览器打开 `demo.html` 即可用。

---

## 项目形态

三入口 SPA（hash 路由，全部在 `demo.html` 里）：

| 入口 | 别名路由 | 面向 | 子板块 |
|---|---|---|---|
| **学习**（原「铭」） | `#/learn`，`#/ming` | 公众访客 | 漢字方格牆 / 古音聽音室 / 吉金字典 |
| **游玩**（原「篆」） | `#/play`，`#/zhuan` | 学生、爱好者 | 金文連連看 / 青銅器描紅 / 祭祀祝福生成器 |
| **铭见**（原「考」） | `#/work`，`#/kao` | 学者、师生 | 拓片識別 / 變體檢索 |

首页是 `index.html` 金文星河（`?embed=1` 参数支持 iframe 嵌入 + `postMessage` `focus-char` 桥接）。

---

## 快速开始

需要 Python 3（走 `http.server`，避免 file:// 下的 fetch/CORS 限制）：

```bat
:: Windows 双击
启动服务器.bat
```

或手动：

```bash
cd baijia-jinwen
python -m http.server 8000
```

打开 <http://localhost:8000/demo.html>。

**手机上**：`demo.html` 会检测低性能设备走 `lite` 模式（用几个 SVG 精灵替代完整 3D 星河）。

---

## 目录结构

```
baijia-jinwen/
├── demo.html               ← 三入口 SPA 主入口（~3700 行）
├── index.html              ← 独立金文星河（Three.js r128，~2000 行）
├── jinwen_svg/             ← 1690 个金文 SVG + index.json（朝代/器物元数据）
├── data/
│   ├── laoyin_seed.json    ← 郑张尚芳上古音种子数据（IPA）
│   └── similarity.json     ← 预计算的字形相似字对
├── assets/
│   ├── fonts/              ← 敬峰中山王篆（OFL）
│   └── seal/
├── js/vendor/              ← meSpeak.js WASM (~3 MB) + eSpeak config + en voice
├── _chars.json             ← zdic 字符元数据（3.7 MB，本地增量抓取，未入库）
├── _thumbs-meta.json       ← zdic 图像元数据（18.6 MB，未入库）
├── ocr-endpoint.json       ← 拓片识别后端 URL（本地，不入库）
├── pitch.md / pitch.html   ← 提案书
└── 启动服务器.bat / 启动识图.bat
```

未入库的本地资产（见 `.gitignore`）：`tools/`、`scripts/`、`dataset/`、`mingjian-ocr-shitu/`、`*.bat`、`*.pdf`、`_chars.json`、`_thumbs-meta.json`、`ocr-endpoint.json` 等。GitHub Pages 发布静态副本走 `_site/`。

---

## 数据

- **字形**：1690 SVG，来源 [zdic.net](https://www.zdic.net) / [darkscope.cn/jinwen-data](https://darkscope.cn/jinwen-data)，学术引用规范。
- **元数据** `jinwen_svg/index.json`：`{char: {cp, file, variants, src, period}}`，1127 条有朝代与出土器物。
- **朝代分布**：西周 589 / 商 162 / 春秋 142 / 战国 198 / 未标注 563，变体总数 5930。
- **上古音**：郑张尚芳《上古音系》(上海教育出版社, 2003) 构拟音（IPA），当前覆盖种子字集。
- **姓氏故事**：20 个大姓（王周殷吴楚秦宋曹蔡虢散毛虞曾黄朱林方金白）内嵌在 `index.html`。

---

## 关键技术点

### 金文星河（`index.html`）

- Three.js r128，CDN 加载，无构建工具。
- 1690 精灵按对数螺旋双臂银河布局，按朝代染色。
- 器形切换：银河 / 鼎 / 簋 / 尊 / 盘 / 爵，用二次贝塞尔轨迹（径向外爆点 P1 → 新目标 P2）分批 0–350 ms 出发。
- 采样按 **CDF · 2πr 表面积均匀**（早期按 y 均匀导致腹部稀疏）。
- 一键录制：`canvas.captureStream` → `MediaRecorder`（MP4 优先，回退 WebM），1080p buffer，Web Audio 合成宫商角徵羽 + 卷积混响。

### 上古音朗读（`demo.html`）

- 引擎：**meSpeak.js WASM** vendored 在 `js/vendor/`（3 MB，首次加载 5–10 s）。
- Unicode IPA → espeak Kirshenbaum ASCII IPA 映射表（ɢ/ɡ→g、ʷ→w、ŋ→N、ː→: 等 30+ 条）。
- 后处理：干路 + 湿路（卷积混响 + `BiquadFilterNode` lowpass 3 kHz Q 0.7）模拟"三千年回声"。
- 失败回退：`speechSynthesis`（系统语音，读现代普通话）。
- 已知取舍：espeak 是英语引擎，`ɢʷ` 退化 `gw`，非严格学术还原，但清晰可辨。

### 拓片识别（`demo.html` · 铭见 · 拓片識別）

- 契约：`POST /recognize`（multipart file）→ `{total, chars: {detections:[{bbox, text, confidence, top5}], recognitions, meta}}`。
- 端点通过 `ocr-endpoint.json` 或 UI ⚙ 按钮或 `?ocr=...` URL 参数配置，默认 `http://localhost:8000`。
- 状态机 `ok / down / unknown`，首次进入 tab 懒探测；真 API 失败自动 fallback mock，UI 顶部 badge 显示 ●已连接 / ○示例数据。
- 后端见 `2026-ancient-ocr`（FastAPI，RFDETR-2XLarge 检测 + ResNet50 识别）。启动 `启动识图.bat` 走本机 uvicorn（需 CUDA + 权重），一般让它打到远端 3090 就够。

### 相似字（`demo.html` · 铭见 · 變體檢索）

- `scripts/precompute_similarity.py`（本地，未入库）用 `resvg-py + PIL + imagehash` 输出 `data/similarity.json`。
- 前端 SIMILARITY 全局兜底：curated 表 + 同朝代随机。

---

## 与 pitch 的对照

`pitch.md` 里承诺的"新建 landing + 三独立 HTML"最终实现为 **单 SPA + hash 路由**。原 `pitch_思路.md` 的三入口命名（铭/篆/考）作为路由别名保留，UI 用了更贴近场景的措辞（学习/游玩/铭见）。

---

## 授权与引用

- 字形数据：zdic.net、darkscope.cn/jinwen-data，学术引用。
- 上古音：郑张尚芳《上古音系》(2003)。
- 篆字标题字：敬峰中山王篆（OFL，见 `assets/fonts/OFL.txt`）。
- meSpeak.js：foxdog-studios/meSpeak（GPLv3）。
- 视觉、代码：待作者补充。

底部固定免责："实际先秦发音已不可考，本站音值参考郑张尚芳《上古音系》(2003) 构拟，合成音仅供参考。"

---

## 部署

GitHub Pages 走 `_site/`（`.nojekyll` 已置顶）。任何静态托管均可（Netlify / Vercel / 自建 Nginx）。仅需确保 `jinwen_svg/`、`data/`、`js/vendor/`、`assets/` 在同域可访问。
