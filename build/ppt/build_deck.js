// 决赛答辩 PPT（4 分钟，11 页，浅色宣纸版，第三轮：为什么做 → 核心场景 → 我们的积累 → 更多场景）。
// 素材顺序：shots.py → record.py → fetch_hezun.py / make_guanju.py / make_evo_gif.py → make_assets_light.py → node build/ppt/build_deck.js
const path = require('path');
const fs = require('fs');
const pptxgen = require('pptxgenjs');
const sharp = require('sharp');
const React = require('react');
const ReactDOMServer = require('react-dom/server');
const fa = require('react-icons/fa');

const ROOT = __dirname;
const A = (...p) => path.join(ROOT, 'assets', ...p);
const OUT = path.join(ROOT, '..', '..', '吉金智识-决赛答辩-v2.pptx');
const META = JSON.parse(fs.readFileSync(A('text', 'meta.json'), 'utf8'));

// ── 配色：宣纸底、墨字、朱砂、铜绿、金 ──
const C = {
  paper: 'F4EFE4', panel: 'FBF8F1', panel2: 'EFE8D8', line: 'D9CFBB',
  ink: '2A2418', text: '3A3328', muted: '7A6E5C',
  cinnabar: 'A63A2C', patina: '4E8A7A', gold: 'B8913F',
};
const F = { body: '微软雅黑', en: 'Cambria' };
const SECTION = { 1: '封面', 2: '为什么做', 3: '为什么做', 4: '核心场景', 5: '我们的积累', 6: '我们的积累', 7: '我们的积累', 8: '更多场景', 9: '更多场景', 10: '落地应用', 11: '结尾' };

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';            // 13.333 × 7.5 in
pres.title = '吉金智识 · 决赛答辩';
pres.theme = { headFontFace: F.body, bodyFontFace: F.body };

// 两个 logo：系列大赛（矢量转的 PNG，1.6:1）和"文化中国"印章
const logos = (x, y, h) => [
  { image: { path: A('ref', 'cpipc_logo.png'), x, y, w: h * 1.6, h } },
  { image: { path: A('ref', 'image3.png'), x: x + h * 1.6 + 0.18, y: y + h * 0.04, w: h * 0.92, h: h * 0.92 } },
];
pres.defineSlideMaster({ title: 'COVER', background: { path: A('bg_light_cover.jpg') }, objects: logos(10.85, 0.42, 0.78) });
pres.defineSlideMaster({
  title: 'CONTENT',
  background: { path: A('bg_light.jpg') },
  objects: logos(11.25, 0.38, 0.56),
  slideNumber: { x: 12.15, y: 7.0, w: 0.6, h: 0.3, fontFace: F.en, fontSize: 10, color: C.muted, align: 'right' },
});
['封面', '为什么做', '核心场景', '我们的积累', '更多场景', '落地应用', '结尾'].forEach(t => pres.addSection({ title: t }));

// ── 小工具 ──
async function icon(Comp, color, file) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: '#' + color, size: 256 }));
  fs.writeFileSync(file, await sharp(Buffer.from(svg)).png().toBuffer());
  return file;
}
// 文字图：make_assets_light.py 渲染好的 PNG，按 meta 里的英寸尺寸放
function tximg(slide, key, x, y, opts = {}) {
  const m = META[key]; const k = opts.scale || 1;
  let w = m.w * k, h = m.h * k;
  if (opts.maxW && w > opts.maxW) { h *= opts.maxW / w; w = opts.maxW; }
  const xx = opts.align === 'center' ? x - w / 2 : opts.align === 'right' ? x - w : x;
  slide.addImage({ path: A('text', `${key}.png`), x: xx, y, w, h, objectName: key });
  return { w, h };
}
// 标题：印章 + 标题图 + 英文小字 + 金色短线和通栏细线
function header(slide, n, seal, titleKey, en) {
  slide.addImage({ path: A(`seal_${seal}.png`), x: 0.6, y: 0.4, w: 0.66, h: 0.66, objectName: 'seal' });
  tximg(slide, titleKey, 1.42, 0.4, { scale: 1.05 });
  slide.addText(en, { x: 1.45, y: 0.98, w: 9, h: 0.26, fontFace: F.en, fontSize: 10.5, italic: true, color: C.muted, charSpacing: 2, margin: 0, isTextBox: true, objectName: 'title-en' });
  slide.addShape(pres.shapes.LINE, { x: 0.6, y: 1.3, w: 12.13, h: 0, line: { color: C.line, width: 0.5 } });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.28, w: 0.66, h: 0.045, fill: { color: C.gold }, line: { color: C.gold, width: 0 } });
  slide.addText('吉金智识 · ' + SECTION[n], { x: 0.6, y: 7.0, w: 4, h: 0.3, fontFace: F.body, fontSize: 10, color: C.muted, margin: 0, isTextBox: true, objectName: 'footer' });
}
function summary(slide, key) {
  const m = META[key];
  const w = m.w, x = (13.333 - w) / 2;
  slide.addShape(pres.shapes.RECTANGLE, { x: x - 0.32, y: 6.63 + m.h / 2 - 0.07, w: 0.14, h: 0.14, fill: { color: C.cinnabar }, line: { color: C.cinnabar, width: 0 }, rotate: 45, objectName: 'summary-mark' });
  tximg(slide, key, x, 6.63);
}
// 直角细线框（不再用圆角卡片）
function card(slide, x, y, w, h, o = {}) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: o.fill || C.panel }, line: { color: o.line || C.line, width: o.lw ?? 0.75 },
    shadow: o.shadow ? { type: 'outer', color: '6B5A3E', opacity: 0.16, blur: 10, offset: 3, angle: 90 } : undefined,
    objectName: o.name,
  });
}
const txt = (s, text, o) => s.addText(text, { fontFace: F.body, color: C.text, margin: 0, isTextBox: true, valign: 'top', lang: 'zh-CN', ...o });
const frame = (s, x, y, w, h, color = C.line, width = 0.75) => s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { type: 'none' }, line: { color, width } });
// 图片按比例放进框里（居中，不裁）
async function fit(s, file, x, y, w, h, o = {}) {
  const m = await sharp(file).metadata();
  const r = Math.min(w / m.width, h / m.height);
  const iw = m.width * r, ih = m.height * r;
  const ix = x + (w - iw) / 2, iy = o.top ? y : y + (h - ih) / 2;
  s.addImage({ path: file, x: ix, y: iy, w: iw, h: ih, objectName: o.name });
  return { x: ix, y: iy, w: iw, h: ih };
}
// 一个字 + 构拟（第 1、8 页）
function charIpa(s, ch, ipaKey, cx, y, k = 0.62) {
  const m = META['big_' + ch], w = m.w * k, h = m.h * k;
  s.addImage({ path: A('text', `big_${ch}.png`), x: cx - w / 2, y, w, h });
  tximg(s, 'ipa_' + ipaKey, cx, y + h - 0.02, { scale: 0.62, align: 'center' });
}

// 中山王篆书标题 + 每字下方一个常用字释文（像展签）。fade=true 时释文命名为 fadein-*，autoplay.ps1 给它们加逐字淡入
const ART_COLS = [[17, 439], [1060, 1465], [2099, 2512], [3105, 3607]];
function titleArt(s, x, y, w, fade) {
  const h = w * 1017 / 3627, k = w / 3627;
  s.addImage({ path: A('title_art_ink.png'), x, y, w, h, objectName: 'title-art' });
  const gs = w / 7.3;
  [...'吉金智识'].forEach((ch, i) => {
    const cx = x + (ART_COLS[i][0] + ART_COLS[i][1]) / 2 * k;
    s.addShape(pres.shapes.LINE, { x: cx - 0.28 * gs, y: y + h + 0.12 * gs, w: 0.56 * gs, h: 0, line: { color: C.gold, width: 1 } });
    const m = META['gloss_' + ch], gw = m.w * 0.62 * gs, gh = m.h * 0.62 * gs;
    s.addImage({ path: A('text', `gloss_${ch}.png`), x: cx - gw / 2, y: y + h + 0.2 * gs, w: gw, h: gh, objectName: fade ? `fadein-${i}` : `gloss-${i}` });
  });
  return y + h + 0.2 * gs + META['gloss_吉'].h * 0.62 * gs;
}

(async () => {
  const ICON = A('icons'); fs.mkdirSync(ICON, { recursive: true });
  const ic = {};
  for (const [k, Comp] of Object.entries({ museum: fa.FaLandmark, db: fa.FaDatabase, scroll: fa.FaScroll, qr: fa.FaQrcode, phone: fa.FaMobileAlt, class: fa.FaChalkboardTeacher, box: fa.FaBoxOpen, globe: fa.FaGlobeEurope, paper: fa.FaFileAlt, trophy: fa.FaTrophy, camera: fa.FaCamera })) {
    ic[k] = await icon(Comp, C.paper, path.join(ICON, `${k}_light.png`));
  }
  ic.arrow = await icon(fa.FaChevronRight, C.gold, path.join(ICON, 'arrow_ink.png'));
  const iconDot = (s, icn, x, y, d = 0.62, color = C.patina) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color, width: 0 } });
    s.addImage({ path: icn, x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5 });
  };
  const numDot = (s, n, x, y, d = 0.5) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: C.cinnabar }, line: { color: C.paper, width: 1.5 } });
    s.addText(String(n), { x, y, w: d, h: d, align: 'center', valign: 'middle', fontFace: F.en, fontSize: 16, bold: true, color: C.paper, margin: 0, isTextBox: true });
  };

  // ══ 1 封面 ══
  {
    const s = pres.addSlide({ masterName: 'COVER', sectionTitle: '封面' });
    txt(s, '第三届中国研究生“文化中国”两创大赛　赛题五：开放赛题', { x: 0.75, y: 0.5, w: 8, h: 0.35, fontSize: 13, color: C.muted });
    titleArt(s, 0.7, 1.2, 7.3, true);
    tximg(s, 'cover_sub', 0.78, 4.45, { maxW: 7.4 });
    tximg(s, 'cover_tag', 0.8, 5.2);
    txt(s, '吉金智识团队', { x: 0.8, y: 6.65, w: 6, h: 0.4, fontSize: 15, bold: true, color: C.ink });
    s.addImage({ path: A('hezun_vessel.png'), x: 8.75, y: 1.45, w: 3.9, h: 4.55, objectName: 'hezun' });
    txt(s, '何尊（西周早期），铭文“宅兹中国”是“中国”一词目前所见最早的文字记录', { x: 8.5, y: 6.2, w: 4.4, h: 0.5, fontSize: 10.5, color: C.muted, align: 'center' });
    s.addNotes('【约 8 秒｜进页后篆书标题下的常用字逐字淡入，约 3 秒】\n各位评委老师好，我们是吉金智识团队，作品是金文数字化传承与互动体验平台。');
  }

  // ══ 2 为什么做：文明之源 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '为什么做' });
    header(s, 2, '中', 't2', 'WHY WE DO THIS');
    frame(s, 0.57, 1.52, 5.06, 3.18);
    s.addImage({ path: path.join(ROOT, 'dl', 'xi_hezun_b.jpg'), x: 0.6, y: 1.55, w: 5.0, h: 3.12, objectName: 'photo-xi' });
    txt(s, '2024 年 9 月，习近平总书记在宝鸡青铜器博物院何尊前驻足察看（新华社记者 王晔 摄）', { x: 0.6, y: 4.75, w: 5.0, h: 0.35, fontSize: 9.5, color: C.muted });
    frame(s, 0.57, 5.17, 1.2, 1.42);
    s.addImage({ path: A('textbook_cover.jpg'), x: 0.6, y: 5.2, w: 1.14, h: 1.36, objectName: 'textbook' });
    txt(s, '2024 年秋季起，人教版初中《中国历史》七年级上册以何尊为封面。', { x: 1.95, y: 5.35, w: 3.65, h: 0.9, fontSize: 12.5, color: C.text, lineSpacingMultiple: 1.25 });
    // 何尊拓片大图 + "中或"框 + 放大
    const rub = { x: 6.0, y: 1.55, h: 4.6 }; rub.w = rub.h * 1000 / 932;
    s.addImage({ path: A('hezun_rubbing.jpg'), x: rub.x, y: rub.y, w: rub.w, h: rub.h, objectName: 'rubbing' });
    const k = rub.w / 1000, bx = rub.x + 405 * k, by = rub.y + 180 * k, bw = 110 * k, bh = 235 * k;
    s.addShape(pres.shapes.RECTANGLE, { x: bx, y: by, w: bw, h: bh, fill: { type: 'none' }, line: { color: C.cinnabar, width: 2.5 } });
    const zx = 11.3, zy = 1.55, zh = 3.4, zw = zh * 330 / 705;
    s.addShape(pres.shapes.LINE, { x: bx + bw, y: zy, w: zx - bx - bw, h: by - zy, flipV: true, line: { color: C.cinnabar, width: 1, dashType: 'dash' } });
    s.addShape(pres.shapes.LINE, { x: bx + bw, y: by + bh, w: zx - bx - bw, h: zy + zh - by - bh, line: { color: C.cinnabar, width: 1, dashType: 'dash' } });
    s.addImage({ path: A('hezun_zhongguo.png'), x: zx, y: zy, w: zw, h: zh, objectName: 'zhongguo-zoom' });
    frame(s, zx, zy, zw, zh, C.cinnabar, 2.5);
    txt(s, '中或', { x: zx - 0.2, y: zy + zh + 0.12, w: zw + 0.4, h: 0.5, fontSize: 22, bold: true, color: C.cinnabar, align: 'center' });
    txt(s, '即“中国”', { x: zx - 0.2, y: zy + zh + 0.62, w: zw + 0.4, h: 0.3, fontSize: 12, color: C.text, align: 'center' });
    txt(s, '何尊铭文拓片，采自《中国青铜器全集》', { x: rub.x, y: rub.y + rub.h + 0.05, w: rub.w, h: 0.28, fontSize: 9.5, color: C.muted });
    summary(s, 's2');
    s.addNotes('【约 25 秒】\n何尊上的“宅兹中或”，是“中国”一词目前所见最早的文字记录。这些文字离我们很遥远，却是中华文明的源头。实现民族复兴，需要追溯文明的根脉；追溯根脉，首先要读懂青铜器上的铭文。那么，怎样才能读懂？\n\n照片：新华社记者王晔摄，转自中央网信办网站 2024-09-12；教材封面照：陕西新闻网 2024-08-28；拓片：维基共享资源 File:He_zun_inscription.jpg（公有领域，原出《中国青铜器全集》）。');
  }

  // ══ 3 为什么做：教育部 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '为什么做' });
    header(s, 3, '文', 't3', 'NATIONAL POLICY');
    txt(s, '教育部等七部门《关于深入推进中华优秀语言文化传承发展 提高全民语言文化素养的意见》明确提出', { x: 1.2, y: 1.6, w: 10.9, h: 0.4, fontSize: 15, color: C.muted, align: 'center' });
    const q = tximg(s, 'quote_moe', 6.67, 2.2, { align: 'center' });
    const qx = 6.67 - q.w / 2;
    s.addText('“', { x: qx - 0.8, y: 1.95, w: 0.8, h: 1.0, fontFace: F.en, fontSize: 80, bold: true, color: C.gold, margin: 0, isTextBox: true });
    s.addText('”', { x: qx + q.w * 0.83, y: 2.2 + q.h - 0.75, w: 0.8, h: 1.0, fontFace: F.en, fontSize: 80, bold: true, color: C.gold, margin: 0, isTextBox: true });  // 第二行较短，引号贴着“演变”
    s.addShape(pres.shapes.RECTANGLE, { x: 6.37, y: 4.25, w: 0.6, h: 0.045, fill: { color: C.gold }, line: { color: C.gold, width: 0 } });
    frame(s, 3.62, 4.52, 6.08, 1.55);
    s.addImage({ path: A('moe_doc.jpg'), x: 3.65, y: 4.55, w: 6.02, h: 1.49, objectName: 'moe-doc' });
    txt(s, '教语信〔2025〕3 号\n2025 年 12 月印发', { x: 9.95, y: 5.0, w: 2.6, h: 0.7, fontSize: 12, color: C.muted, lineSpacingMultiple: 1.3 });
    summary(s, 's3');
    s.addNotes('【约 15 秒｜引文放慢，一字一字读】\n总书记高度重视古文字的传承，教育部等七部门也明确提出：开展——追溯——甲骨文、金文、篆书——等文字发展演变。可是走进博物馆，大多数观众面对展柜里的铭文，仍然一个字也认不出来。\n\n文件：教育部网站 2026-01-15 公布。');
  }

  // ══ 4 核心场景：走进博物馆 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '核心场景' });
    header(s, 4, '見', 't4', 'CORE SCENARIO: READING INSCRIPTIONS IN THE MUSEUM');
    const W = 2.85, Hh = 2.85, y = 1.6;
    const steps = [
      ['拍下铭文', '观众在展柜前扫码，拍下器物上的铭文'],
      ['拆成单字', '模型找出铭文中的每一个字，逐个切分'],
      ['匹配今字', '到字库中逐字匹配，给出对应的现代汉字'],
      ['读懂历史', '连字成句、配上白话，读懂铭文记载的历史'],
    ];
    for (let i = 0; i < 4; i++) {
      const x = 0.6 + i * 3.1;
      card(s, x, y, W, Hh, { fill: i === 0 || i === 3 ? C.panel2 : '2B2620', shadow: true, name: `story-${i}` });
      if (i === 0) {
        await fit(s, A('hezun_vessel.png'), x + 0.2, y + 0.15, W - 0.4, Hh - 0.3);
        iconDot(s, ic.camera, x + W - 0.8, y + Hh - 0.8, 0.62, C.cinnabar);
      } else if (i === 1) {
        await fit(s, A('story_split.png'), x, y, W, Hh);
      } else if (i === 2) {
        await fit(s, A('story_match.png'), x, y, W, Hh);
      } else {
        txt(s, '余其宅兹中国，\n自之乂民。', { x: x + 0.25, y: y + 0.3, w: W - 0.5, h: 1.0, fontSize: 19, bold: true, color: C.ink, lineSpacingMultiple: 1.2 });
        s.addShape(pres.shapes.RECTANGLE, { x: x + 0.25, y: y + 1.38, w: 0.5, h: 0.04, fill: { color: C.gold }, line: { color: C.gold, width: 0 } });
        txt(s, '我要定居在天下的中心，从这里治理百姓。', { x: x + 0.25, y: y + 1.55, w: W - 0.5, h: 0.7, fontSize: 12.5, color: C.text, lineSpacingMultiple: 1.25 });
        txt(s, '周武王灭商后的誓言', { x: x + 0.25, y: y + 2.3, w: W - 0.5, h: 0.3, fontSize: 10.5, color: C.muted });
      }
      numDot(s, i + 1, x - 0.12, y - 0.15);
      if (i < 3) s.addImage({ path: ic.arrow, x: x + W + 0.04, y: y + Hh / 2 - 0.09, w: 0.18, h: 0.18 });
      txt(s, steps[i][0], { x, y: y + Hh + 0.15, w: W, h: 0.4, fontSize: 17, bold: true, color: C.ink, align: 'center' });
      txt(s, steps[i][1], { x: x + 0.1, y: y + Hh + 0.55, w: W - 0.2, h: 0.6, fontSize: 12, color: C.text, align: 'center' });
    }
    tximg(s, 'slogan', 6.67, 5.95, { align: 'center', scale: 0.9 });
    summary(s, 's4');
    s.addNotes('【约 30 秒】\n我们的作品，核心就是帮观众读懂铭文。在博物馆的展柜前，观众扫码拍下铭文，模型会找出其中的每一个字，到我们的字库里逐一匹配，给出对应的现代汉字，再连成句子、配上白话。比如何尊上的“余其宅兹中国”，意思就是“我要定居在天下的中心”。让青铜铭文可观、可识、可读、可感。');
  }

  // ══ 5 我们的积累：资料 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '我们的积累' });
    header(s, 5, '書', 't5', 'DATA RESOURCES');
    const stats = [
      ['58 万', '张古文字字形图', '汇集甲骨文、金文、小篆等 10 类字形来源'],
      ['25,285', '条自建金文数据库目录', '逐条录入器名、释文、时代、著录号'],
      ['6,236', '张拓片', '逐字标注 61,268 个字框，统一校订'],
      ['5,930', '个金文变体', '分属 1,690 个字头，注明时代与器物'],
      ['24.6 万', '条上古、中古音韵记录', '覆盖 7,909 个字，用于听古音'],
      ['242', '个百家姓见于金文', '宋本《百家姓》408 个单姓逐一核对'],
    ];
    stats.forEach(([num, unit, note], i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = 0.6 + col * 3.55, y = 1.6 + row * 1.6, w = 3.35, h = 1.42;
      card(s, x, y, w, h, { name: `stat-${i}` });
      s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h, fill: { color: C.cinnabar }, line: { color: C.cinnabar, width: 0 } });
      s.addText(num, { x: x + 0.25, y: y + 0.1, w: w - 0.4, h: 0.62, fontFace: F.en, fontSize: 32, bold: true, color: C.cinnabar, margin: 0, isTextBox: true, fit: 'shrink' });
      txt(s, unit, { x: x + 0.25, y: y + 0.72, w: w - 0.3, h: 0.32, fontSize: 13, bold: true, color: C.ink });
      txt(s, note, { x: x + 0.25, y: y + 1.03, w: w - 0.3, h: 0.34, fontSize: 10.5, color: C.muted });
    });
    const books = [
      ['殷周金文集成', '1727', '8C4A3C', 4.25], ['商周青铜器铭文暨图像集成续编', '998', '4E7A6C', 4.45], ['商周青铜器铭文暨图像集成', '785', '9A7A3A', 4.45],
      ['三代吉金文存', '455', '6E5B48', 3.75], ['汉金文录', '394', 'A65A44', 3.45], ['小校经阁金文拓本', '256', '5C7A72', 3.95],
      ['古镜聚英', '86', '8A7246', 3.3], ['商周青铜器铭文选', '59', '7C4A40', 3.25],
    ];
    const bx0 = 7.85, base = 6.2;
    books.forEach(([name, n, col, h], i) => {
      const x = bx0 + i * 0.6, w = 0.52, y = base - h;
      s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: col }, line: { color: col, width: 0 }, shadow: { type: 'outer', color: '6B5A3E', opacity: 0.2, blur: 6, offset: 2, angle: 90 }, objectName: `spine-${i}` });
      s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.16, w, h: 0.04, fill: { color: C.paper, transparency: 35 }, line: { color: C.paper, width: 0 } });
      s.addText(name, { x, y: y + 0.3, w, h: h - 0.95, vert: 'eaVert', align: 'center', valign: 'top', fontFace: F.body, fontSize: name.length > 9 ? 9.5 : 11.5, color: C.paper, margin: 0, isTextBox: true });
      s.addText(n, { x: x - 0.05, y: base - 0.52, w: w + 0.1, h: 0.38, align: 'center', fontFace: F.en, fontSize: 10, bold: true, color: C.paper, margin: 0, isTextBox: true });
    });
    s.addShape(pres.shapes.RECTANGLE, { x: bx0 - 0.15, y: base, w: 8 * 0.6 + 0.22, h: 0.09, fill: { color: C.ink }, line: { color: C.ink, width: 0 } });
    txt(s, '拓片出自 150 余种著录与期刊（书脊下为数据集中的拓片张数）', { x: 7.7, y: 1.5, w: 5.1, h: 0.3, fontSize: 10.5, color: C.muted });
    summary(s, 's5');
    s.addNotes('【约 15 秒】\n为此，我们做了大量积累。我们汇集整理了五十八万张古文字字形图、两万五千多条自建金文数据库目录和六千多张拓片，每个字都可以查到出处。');
  }

  // ══ 6 我们的积累：模型 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '我们的积累' });
    header(s, 6, '智', 't6', 'MODEL TRAINING');
    const steps = [
      ['01', '数据准备', ['6,236 张拓片，61,268 个字框', '4,114 类字，其中 2,031 类仅 1 个样本', '统一标注规范']],
      ['02', '字符检测', ['4 个检测器融合', 'RF-DETR + DINOv3 视觉大模型', '检测 mAP50 为 0.946']],
      ['03', '字符识别', ['7 个识别器集成', 'ConvNeXt、ViT-L、ViT-H+', '每个字给出 5 个候选']],
      ['04', '辅助释读', ['金框为初稿，灰框为存疑', '提供辞例和字形参考', '由专家审定']],
    ];
    steps.forEach(([n, head, lines], i) => {
      const x = 0.6 + i * 3.1, y = 1.6, w = 2.8, h = 2.3;
      card(s, x, y, w, h, { name: `step-${n}` });
      s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.05, fill: { color: C.cinnabar }, line: { color: C.cinnabar, width: 0 } });
      s.addText(n, { x: x + 0.22, y: y + 0.18, w: 0.9, h: 0.55, fontFace: F.en, fontSize: 26, bold: true, color: C.cinnabar, margin: 0, isTextBox: true });
      s.addText(head, { x: x + 1.05, y: y + 0.22, w: 1.6, h: 0.5, fontFace: F.body, fontSize: 18, bold: true, color: C.ink, margin: 0, isTextBox: true, valign: 'middle' });
      s.addText(lines.map((t, k) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: k < lines.length - 1 } })),
        { x: x + 0.2, y: y + 0.92, w: w - 0.3, h: 1.3, fontFace: F.body, fontSize: 12.5, color: C.text, paraSpaceAfter: 6, margin: 0, isTextBox: true, valign: 'top', lang: 'zh-CN' });
      if (i < 3) s.addImage({ path: ic.arrow, x: x + w + 0.06, y: y + 1.05, w: 0.18, h: 0.18 });
    });
    s.addImage({ path: A('rec_crop.png'), x: 0.6, y: 4.2, w: 2.59, h: 1.91, objectName: 'rec-shot' });
    frame(s, 0.6, 4.2, 2.59, 1.91);
    card(s, 3.45, 4.2, 9.28, 1.91, { fill: C.panel2, name: 'score' });
    s.addText('F1 0.803', { x: 3.7, y: 4.35, w: 3.3, h: 0.9, fontFace: F.en, fontSize: 44, bold: true, color: C.cinnabar, margin: 0, isTextBox: true });
    txt(s, '世界科学智能大赛古文字识别赛道二等奖\n第一名 F1 为 0.8071\n评测要求字的位置与释文同时正确', { x: 3.72, y: 5.25, w: 3.8, h: 0.8, fontSize: 12, color: C.ink });
    txt(s, '训练设备：RTX 3090、RTX 5090\n基础模型：DINOv3 视觉大模型', { x: 7.7, y: 4.45, w: 4.9, h: 1.5, fontSize: 12, color: C.text, lineSpacingMultiple: 1.3 });
    summary(s, 's6');
    s.addNotes('【约 20 秒】\n在这些资料上，我们训练了古文字识读模型。这套系统在世界科学智能大赛古文字识别赛道获得二等奖，F1 值为 0.803。模型给出的是初稿，最终释读仍由专家审定。');
  }

  // ══ 7 我们的积累：研究与测评 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '我们的积累' });
    header(s, 7, '古', 't7', 'RESEARCH AND EVALUATION');
    // 左：论文
    iconDot(s, ic.paper, 0.6, 1.6, 0.56, C.cinnabar);
    txt(s, '论文', { x: 1.3, y: 1.65, w: 4, h: 0.45, fontSize: 19, bold: true, color: C.ink });
    for (let i = 0; i < 3; i++) {
      const y = 2.35 + i * 1.32;
      card(s, 0.6, y, 6.0, 1.14, { name: `paper-${i}` });
      s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y, w: 0.06, h: 1.14, fill: { color: C.gold }, line: { color: C.gold, width: 0 } });
      txt(s, `【论文题目 ${i + 1}】`, { x: 0.9, y: y + 0.18, w: 5.5, h: 0.4, fontSize: 15, bold: true, color: C.ink });
      txt(s, '【期刊或会议】，【已发表 / 待刊】', { x: 0.9, y: y + 0.62, w: 5.5, h: 0.35, fontSize: 12, color: C.muted });
    }
    // 右：测评
    iconDot(s, ic.trophy, 7.0, 1.6, 0.56, C.cinnabar);
    txt(s, '学术评测', { x: 7.7, y: 1.65, w: 4, h: 0.45, fontSize: 19, bold: true, color: C.ink });
    [['CCL【届次】【评测任务名称】', '【名次 / 成绩】'],
     ['世界科学智能大赛 古文字识别赛道', '二等奖，F1 0.803']].forEach(([head, body], i) => {
      const y = 2.35 + i * 1.32;
      card(s, 7.0, y, 5.73, 1.14, { name: `eval-${i}` });
      s.addShape(pres.shapes.RECTANGLE, { x: 7.0, y, w: 0.06, h: 1.14, fill: { color: C.gold }, line: { color: C.gold, width: 0 } });
      txt(s, head, { x: 7.3, y: y + 0.18, w: 5.3, h: 0.4, fontSize: 15, bold: true, color: C.ink });
      txt(s, body, { x: 7.3, y: y + 0.62, w: 5.3, h: 0.35, fontSize: 12.5, color: C.cinnabar, bold: true });
    });
    summary(s, 's7');
    s.addNotes('【约 15 秒】\n围绕古文字识读，团队还完成了【N】篇论文，参加了 CCL【届次】【评测任务】，获得【名次】。\n\n【待填：论文题目、刊物、状态；CCL 届次、任务、名次。PPT 上不写作者姓名】');
  }

  // ══ 8 更多场景：一库多用 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '更多场景' });
    header(s, 8, '樂', 't8', 'MORE USES OF ONE CHARACTER DATABASE');
    const T = [[0.6, 1.55], [6.75, 1.55], [0.6, 4.08], [6.75, 4.08]], TW = 5.98, TH = 2.38;
    T.forEach(([x, y], i) => card(s, x, y, TW, TH, { shadow: true, name: `use-${i}` }));
    const head = (x, y, t, b, w = 3.2) => {
      txt(s, t, { x, y, w, h: 0.42, fontSize: 18, bold: true, color: C.cinnabar });
      txt(s, b, { x, y: y + 0.48, w, h: 1.4, fontSize: 12, color: C.text, lineSpacingMultiple: 1.25 });
    };
    // 认源流：GIF
    s.addImage({ path: A('evo_zhong.gif'), x: 0.75, y: 1.62, w: 2.13, h: 2.27, objectName: 'evo-gif' });
    head(3.2, 1.85, '认源流', '一个字从甲骨文、金文、小篆、隶书到楷书，怎样一步步演变成今天的样子。');
    // 听古音：关关雎鸠
    txt(s, '听古音', { x: 6.95, y: 1.68, w: 2, h: 0.42, fontSize: 18, bold: true, color: C.cinnabar });
    txt(s, '《诗经》首句的上古音拟读（郑张尚芳构拟）', { x: 8.2, y: 1.74, w: 4.4, h: 0.35, fontSize: 11, color: C.muted });
    s.addMedia({ type: 'audio', path: A('guanju.mp3'), x: 12.15, y: 1.66, w: 0.42, h: 0.42 });
    [['關', 'guan'], ['關', 'guan'], ['雎', 'ju'], ['鳩', 'jiu'], ['在', 'zai'], ['河', 'he'], ['之', 'zhi'], ['洲', 'zhou']]
      .forEach(([ch, k], i) => charIpa(s, ch, k, 7.25 + i * 0.66 + (i >= 4 ? 0.25 : 0), 2.4, 0.52));
    // 练书写
    await fit(s, A('trace_crop.png'), 0.8, 4.23, 1.95, 2.08);
    await fit(s, A('postcard_shadow_light.png'), 2.6, 4.18, 1.4, 2.18);
    head(4.2, 4.35, '练书写', '描红古文字，再挑几个吉字，铸一句金文祝福，生成明信片。', 2.2);
    // 助研究
    s.addShape(pres.shapes.RECTANGLE, { x: 6.9, y: 4.2, w: 1.95, h: 2.14, fill: { color: '2B2620' }, line: { color: '2B2620', width: 0 } });
    await fit(s, A('assist_panel.png'), 6.9, 4.2, 1.95, 2.14);
    head(9.1, 4.35, '助研究', '为研究者列出候选字、辞例和字形，辅助释读整篇拓片。');
    summary(s, 's8');
    s.addNotes('【约 30 秒｜进页先自动播放 7 秒《关雎》拟音，放完再开口】\n刚才听到的，是《诗经》“关关雎鸠，在河之洲”在上古的读法。同一套字库，还能用在更多场景：看一个字从甲骨文到楷书怎样演变；听古人怎样读诗；描红古文字，铸一句金文祝福；也能为研究者列出候选字和辞例，辅助释读。\n\n构拟据韵典网“上古音系”栏（郑张尚芳），仅供参考。');
  }

  // ══ 9 更多场景：网站演示 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '更多场景' });
    header(s, 9, '連', 't9', 'LIVE DEMO');
    const vw = 8.9, vh = vw * 9 / 16, vx = (13.333 - vw) / 2, vy = 1.5;
    frame(s, vx - 0.04, vy - 0.04, vw + 0.08, vh + 0.08, C.gold, 1.25);
    s.addMedia({ type: 'video', path: A('demo_fast.mp4'), cover: 'data:image/png;base64,' + fs.readFileSync(A('demo_poster.png')).toString('base64'), x: vx, y: vy, w: vw, h: vh, objectName: 'demo-video' });
    summary(s, 's9');
    s.addNotes('【约 32 秒｜录屏进页自动播放，边播边讲】\n请看网站演示：输入姓氏“周”，查看它的金文写法；听这个字的上古音；选一件青铜器，铸一句金文祝福，生成明信片；最后打开一张拓片，模型框出每个字，给出识读结果。');
  }

  // ══ 10 落地应用 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '落地应用' });
    header(s, 10, '手', 't10', 'APPLICATIONS');
    s.addImage({ path: A('postcard_shadow_light.png'), x: 0.75, y: 1.45, w: 3.45, h: 4.69, objectName: 'postcard' });
    txt(s, '铸辞坊生成的金文明信片（样张）', { x: 0.6, y: 6.12, w: 3.9, h: 0.3, fontSize: 11, color: C.muted, align: 'center' });
    const rows = [
      [ic.qr, '展位', '观众扫码体验，生成金文明信片，下载 PDF 后可自行打印'],
      [ic.phone, '小红书', '手机端小工具，包含听古音、描红、连连看，可保存和分享成绩'],
      [ic.class, '课堂', '15 分钟古文字入门课，课前、课后使用同一套测试题\n【11/7 试用：N 人，正确率由 X% 提高到 Y%】'],
      [ic.globe, '孔子学院', '服务巴黎西岱大学孔子学院中文教学\n【具体内容待填】'],
      [ic.box, '离线包', '无网络环境下解压即可使用'],
    ];
    rows.forEach(([icn, head, body], i) => {
      const x = 4.75, y = 1.55 + i * 0.98, w = 7.98, h = 0.86;
      card(s, x, y, w, h, { name: `land-${i}` });
      iconDot(s, icn, x + 0.22, y + 0.15, 0.56);
      txt(s, head, { x: x + 1.0, y: y + 0.08, w: 1.5, h: 0.7, fontSize: 16, bold: true, color: C.ink, valign: 'middle' });
      txt(s, body, { x: x + 2.5, y: y + 0.06, w: w - 2.7, h: 0.74, fontSize: 12.5, color: C.text, valign: 'middle' });
    });
    summary(s, 's10');
    s.addNotes('【约 20 秒】\n目前，作品已经可以在多个场景中使用：观众在展位扫码，生成金文明信片带走；手机上有小红书小工具；作品还服务于巴黎西岱大学孔子学院的中文教学【内容待填】；在课堂试用中，【N】名同学参加了十五分钟的入门课，答题正确率从【X】%提高到【Y】%。');
  }

  // ══ 11 结尾 ══
  {
    const s = pres.addSlide({ masterName: 'COVER', sectionTitle: '结尾' });
    tximg(s, 'end_1', 0.8, 2.3, { maxW: 7.5 });
    titleArt(s, 0.75, 3.45, 4.3, false);
    tximg(s, 'end_thanks', 0.85, 5.75);
    s.addImage({ path: A('hezun_vessel.png'), x: 8.55, y: 1.45, w: 4.1, h: 4.78 });
    s.addNotes('【约 10 秒】\n最后，我们希望通过这个作品，让书写在青铜器上的文字活起来。汇报完毕，敬请各位老师批评指正。');
  }

  await pres.writeFile({ fileName: OUT });
  console.log('wrote', OUT);
  // pptxgenjs 的媒体只能单击播放；Windows 上接着用 PowerPoint 设成进页自动播放
  if (process.platform === 'win32') {
    require('child_process').execFileSync('powershell', ['-ExecutionPolicy', 'Bypass', '-File', path.join(ROOT, 'autoplay.ps1'), '-Pptx', OUT], { stdio: 'inherit' });
  }
})();
