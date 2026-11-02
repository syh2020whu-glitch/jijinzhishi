// 决赛答辩 PPT（4 分钟，11 页，浅色宣纸版）。
// 素材顺序：shots.py → record.py → glyphs.js / clean_glyph.py / evo_glyphs.py → make_assets_light.py → node build/ppt/build_deck.js
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

// ── 配色：宣纸底、墨字、朱砂、铜绿 ──
const C = {
  paper: 'F4EFE4', panel: 'FBF8F1', panel2: 'EFE8D8', line: 'D9CFBB',
  ink: '2A2418', text: '3A3328', muted: '7A6E5C',
  cinnabar: 'A63A2C', patina: '4E8A7A', gold: 'B8913F',
};
const F = { body: '微软雅黑', en: 'Cambria' };
const SECTION = { 1: '封面', 2: '缘起', 3: '缘起', 4: '主线', 5: '源流与内涵', 6: '材料与模型', 7: '材料与模型', 8: '四个模块', 9: '四个模块', 10: '落地应用', 11: '结尾' };

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
['封面', '缘起', '主线', '源流与内涵', '材料与模型', '四个模块', '落地应用', '结尾'].forEach(t => pres.addSection({ title: t }));

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
function header(slide, n, seal, titleKey, en) {
  slide.addImage({ path: A(`seal_${seal}.png`), x: 0.6, y: 0.4, w: 0.66, h: 0.66, objectName: 'seal' });
  tximg(slide, titleKey, 1.42, 0.4, { scale: 1.05 });
  slide.addText(en, { x: 1.45, y: 0.98, w: 9, h: 0.26, fontFace: F.en, fontSize: 10.5, italic: true, color: C.muted, charSpacing: 2, margin: 0, isTextBox: true, objectName: 'title-en' });
  slide.addText('吉金智识 · ' + SECTION[n], { x: 0.6, y: 7.0, w: 4, h: 0.3, fontFace: F.body, fontSize: 10, color: C.muted, margin: 0, isTextBox: true, objectName: 'footer' });
}
function summary(slide, key) {
  const m = META[key];
  const w = m.w, x = (13.333 - w) / 2;
  slide.addShape(pres.shapes.RECTANGLE, { x: x - 0.32, y: 6.63 + m.h / 2 - 0.07, w: 0.14, h: 0.14, fill: { color: C.cinnabar }, line: { color: C.cinnabar, width: 0 }, rotate: 45, objectName: 'summary-mark' });
  tximg(slide, key, x, 6.63);
}
function card(slide, x, y, w, h, o = {}) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: o.r ?? 0.1,
    fill: { color: o.fill || C.panel }, line: { color: o.line || C.line, width: o.lw ?? 0.75 },
    shadow: o.shadow ? { type: 'outer', color: '6B5A3E', opacity: 0.18, blur: 10, offset: 3, angle: 90 } : undefined,
    objectName: o.name,
  });
}
const txt = (s, text, o) => s.addText(text, { fontFace: F.body, color: C.text, margin: 0, isTextBox: true, valign: 'top', lang: 'zh-CN', ...o });
const frame = (s, x, y, w, h) => s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { type: 'none' }, line: { color: C.line, width: 0.75 } });

(async () => {
  const ICON = A('icons'); fs.mkdirSync(ICON, { recursive: true });
  const ic = {};
  for (const [k, Comp] of Object.entries({ museum: fa.FaLandmark, db: fa.FaDatabase, scroll: fa.FaScroll, qr: fa.FaQrcode, phone: fa.FaMobileAlt, class: fa.FaChalkboardTeacher, box: fa.FaBoxOpen })) {
    ic[k] = await icon(Comp, C.paper, path.join(ICON, `${k}_light.png`));
  }
  ic.arrow = await icon(fa.FaChevronRight, C.gold, path.join(ICON, 'arrow_ink.png'));
  const iconDot = (s, icn, x, y, d = 0.62) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: C.patina }, line: { color: C.patina, width: 0 } });
    s.addImage({ path: icn, x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5 });
  };

  // ══ 1 封面 ══
  {
    const s = pres.addSlide({ masterName: 'COVER', sectionTitle: '封面' });
    txt(s, '第三届中国研究生“文化中国”两创大赛 · 赛题五 开放赛题', { x: 0.75, y: 0.5, w: 8, h: 0.35, fontSize: 13, color: C.muted });
    s.addImage({ path: A('title_art_ink.png'), x: 0.7, y: 1.55, w: 7.3, h: 2.05, objectName: 'title-art' });
    tximg(s, 'cover_sub', 0.78, 3.85, { maxW: 7.4 });
    tximg(s, 'cover_tag', 0.8, 4.65);
    s.addMedia({ type: 'audio', path: A('zhaizi.mp3'), x: 0.8, y: 5.45, w: 0.46, h: 0.46 });
    txt(s, '开场拟音：何尊铭文“宅兹中国”四字上古音（郑张尚芳构拟，仅供参考）', { x: 1.38, y: 5.5, w: 7, h: 0.36, fontSize: 12, color: C.muted, valign: 'middle' });
    txt(s, '吉金智识团队', { x: 0.8, y: 6.55, w: 6, h: 0.4, fontSize: 15, bold: true, color: C.ink });
    s.addImage({ path: A('hezun_vessel.png'), x: 8.55, y: 1.45, w: 4.1, h: 4.78, objectName: 'hezun' });
    txt(s, '何尊 · 西周早期 · 铭文有“宅兹中国”，是“中国”一词最早的文字记录', { x: 8.3, y: 6.35, w: 4.6, h: 0.5, fontSize: 11, color: C.muted, align: 'center' });
    s.addNotes('【约 15 秒｜先点左下播放键，放 3 秒拟音】\n刚才这四个音，是三千年前“宅兹中国”的构拟读音。我们是吉金智识，想用一个个古文字，把三千年连起来。');
  }

  // ══ 2 总书记 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '缘起' });
    header(s, 2, '中', 't2', 'GENERAL SECRETARY XI JINPING AND THE HE ZUN');
    frame(s, 0.57, 1.52, 6.36, 3.99);
    s.addImage({ path: path.join(ROOT, 'dl', 'xi_hezun_b.jpg'), x: 0.6, y: 1.55, w: 6.3, h: 3.93, objectName: 'photo-xi' });
    txt(s, '2024 年 9 月 10 日，习近平总书记在宝鸡青铜器博物院考察，在何尊前驻足察看。新华社记者 王晔 摄', { x: 0.6, y: 5.6, w: 6.3, h: 0.5, fontSize: 11, color: C.muted });
    s.addText('“', { x: 7.25, y: 1.3, w: 0.8, h: 0.8, fontFace: F.en, fontSize: 66, bold: true, color: C.cinnabar, margin: 0, isTextBox: true });
    txt(s, '“中国”二字镌刻在“何尊”底部，更铭刻在每个华夏儿女心中。', { x: 7.35, y: 1.9, w: 5.4, h: 1.15, fontSize: 21, bold: true, color: C.ink });
    txt(s, '—— 2025 年新年贺词', { x: 7.35, y: 3.05, w: 5.4, h: 0.3, fontSize: 12, color: C.cinnabar });
    txt(s, '要加强青铜器文物的保护研究和宣传阐释，更好激发全社会特别是青少年对伟大祖国和中华文明的热爱。', { x: 7.35, y: 3.6, w: 5.4, h: 0.95, fontSize: 15 });
    txt(s, '—— 2024 年 9 月，考察宝鸡青铜器博物院', { x: 7.35, y: 4.55, w: 5.4, h: 0.3, fontSize: 12, color: C.cinnabar });
    txt(s, '中国的汉文字非常了不起，中华民族的形成和发展离不开汉文字的维系。', { x: 7.35, y: 5.05, w: 5.4, h: 0.7, fontSize: 15 });
    txt(s, '—— 2022 年 10 月，考察安阳殷墟', { x: 7.35, y: 5.77, w: 5.4, h: 0.3, fontSize: 12, color: C.cinnabar });
    summary(s, 's2');
    s.addNotes('【约 20 秒】\n这四个字铸在何尊底部，是“中国”二字最早的文字记录。总书记说，“中国”二字镌刻在何尊底部，更铭刻在每个华夏儿女心中；还嘱咐要加强青铜器的宣传阐释，激发青少年对中华文明的热爱。\n\n来源：2025 年新年贺词；2024-09-10 考察宝鸡青铜器博物院（新华社）；2022-10-28 考察安阳殷墟（新华社）。照片：新华社记者王晔摄，转自中央网信办网站 2024-09-12。');
  }

  // ══ 3 国家重视，公众难亲近 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '缘起' });
    header(s, 3, '文', 't3', 'POLICY MOMENTUM AND THE PUBLIC GAP');
    // 左：课本 + 文件
    frame(s, 0.57, 1.47, 2.32, 2.84);
    s.addImage({ path: A('textbook_cover.jpg'), x: 0.6, y: 1.5, w: 2.26, h: 2.78, objectName: 'textbook' });
    txt(s, '2024 年秋', { x: 3.1, y: 1.55, w: 3.5, h: 0.4, fontSize: 20, bold: true, color: C.cinnabar });
    txt(s, '何尊登上人教版七年级上册《中国历史》封面，背景是甲骨文。全国初一学生拿到的第一本历史书，封面就是一件青铜器和一片古文字。', { x: 3.1, y: 2.0, w: 3.55, h: 2.3, fontSize: 13, color: C.text, lineSpacingMultiple: 1.2 });
    frame(s, 0.57, 4.52, 6.08, 1.55);
    s.addImage({ path: A('moe_doc.jpg'), x: 0.6, y: 4.55, w: 6.02, h: 1.49, objectName: 'moe-doc' });
    txt(s, '2025 年 12 月，教育部等七部门印发《关于深入推进中华优秀语言文化传承发展 提高全民语言文化素养的意见》（教语信〔2025〕3 号），明确“开展追溯甲骨文、金文、篆书等文字发展演变”。', { x: 0.6, y: 6.1, w: 6.1, h: 0.5, fontSize: 10.5, color: C.muted });
    // 右：三道门槛
    txt(s, '公众面前的三道门槛', { x: 7.1, y: 1.5, w: 5.6, h: 0.4, fontSize: 17, bold: true, color: C.ink });
    const pains = [
      [ic.museum, '博物馆里', '器物旁只有一行说明，看不懂铭文就匆匆走过'],
      [ic.db, '数据库里', '一个个孤立的单字，不会检索就进不去'],
      [ic.scroll, '研究里', '整张拓片逐字释读，仍要专家一字一字看'],
    ];
    pains.forEach(([icn, head, body], i) => {
      const y = 2.05 + i * 1.4;
      card(s, 7.1, y, 5.63, 1.2, { name: `pain-${i}` });
      iconDot(s, icn, 7.3, y + 0.29);
      txt(s, head, { x: 8.15, y: y + 0.2, w: 4.4, h: 0.38, fontSize: 16, bold: true, color: C.ink });
      txt(s, body, { x: 8.15, y: y + 0.6, w: 4.45, h: 0.45, fontSize: 13, color: C.text });
    });
    summary(s, 's3');
    s.addNotes('【约 12 秒】\n何尊上了初中历史课本封面，七部门又发文要求追溯甲骨文、金文、篆书的演变。可对公众来说，古文字还是很远：博物馆里一行说明，数据库里一个个单字。材料不缺，缺的是路。\n\n来源：陕西新闻网 2024-08-28（教材封面照片）；教育部网站 2026-01-15 公布，教语信〔2025〕3 号。');
  }

  // ══ 4 主线：以字为桥 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '主线' });
    header(s, 4, '連', 't4', 'OUR THROUGH-LINE: CHARACTERS AS A BRIDGE');
    // 桥面
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1.75, y: 2.75, w: 9.85, h: 0.34, rectRadius: 0.17, fill: { color: C.patina }, line: { color: C.patina, width: 0 }, objectName: 'deck' });
    s.addText('三 千 年', { x: 1.75, y: 2.75, w: 9.85, h: 0.34, align: 'center', valign: 'middle', fontFace: F.body, fontSize: 11, color: C.paper, margin: 0, isTextBox: true });
    // 两端
    [[0.6, '古', '器上的字', '三千年前铸在青铜器上'], [11.2, '今', '身边的人', '公众 · 课堂 · 研究']].forEach(([x, ch, head, sub]) => {
      s.addShape(pres.shapes.OVAL, { x, y: 2.15, w: 1.55, h: 1.55, fill: { color: C.cinnabar }, line: { color: C.cinnabar, width: 0 }, shadow: { type: 'outer', color: '6B5A3E', opacity: 0.25, blur: 8, offset: 3, angle: 90 } });
      s.addImage({ path: A('text', `big_${ch}.png`), x: x + 0.3, y: 2.3, w: 0.95, h: 1.25, sizing: { type: 'contain', w: 0.95, h: 1.25 } });
      s.addText(head, { x: x - 0.3, y: 3.85, w: 2.15, h: 0.4, align: 'center', fontFace: F.body, fontSize: 15, bold: true, color: C.ink, margin: 0, isTextBox: true });
      s.addText(sub, { x: x - 0.4, y: 4.25, w: 2.35, h: 0.35, align: 'center', fontFace: F.body, fontSize: 11, color: C.muted, margin: 0, isTextBox: true });
    });
    // 四座桥墩
    const piers = [
      ['一', '字的源流与内涵', '一个字怎样演变到今天，\n字形里留着先人的世界观'],
      ['二', '材料与模型', '整理的字形、拓片、目录，\n和在此之上训练的识读模型'],
      ['三', '四个模块', '看 · 听 · 写 · 考，\n公众、课堂、研究同一套字库'],
      ['四', '落地应用', '明信片 PDF、小红书小工具、\n课堂一节课、离线包'],
    ];
    piers.forEach(([n, head, body], i) => {
      const w = 1.95, x = 2.5 + i * 2.15, y = 3.09;
      s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 2.35, fill: { color: C.panel }, line: { color: C.line, width: 0.75 }, shadow: { type: 'outer', color: '6B5A3E', opacity: 0.15, blur: 8, offset: 2, angle: 90 }, objectName: `pier-${i}` });
      s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.5, fill: { color: C.cinnabar }, line: { color: C.cinnabar, width: 0 } });
      s.addText(n, { x, y, w, h: 0.5, align: 'center', valign: 'middle', fontFace: F.body, fontSize: 16, bold: true, color: C.paper, margin: 0, isTextBox: true });
      s.addText(head, { x: x + 0.1, y: y + 0.65, w: w - 0.2, h: 0.55, align: 'center', valign: 'middle', fontFace: F.body, fontSize: 16, bold: true, color: C.ink, margin: 0, isTextBox: true, lang: 'zh-CN' });
      txt(s, body, { x: x + 0.12, y: y + 1.25, w: w - 0.24, h: 1.05, fontSize: 11, color: C.text, align: 'center', lineSpacingMultiple: 1.2 });
    });
    summary(s, 's4');
    s.addNotes('【约 12 秒】\n所以我们的主线是“以字为桥”：一头是器上的字，一头是身边的人，中间四个环节——字的源流与内涵、材料与模型、四个模块、落地应用。\n\n（回应“连起来是什么意思”：后面每一页对应一个环节。）');
  }

  // ══ 5 源流与内涵 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '源流与内涵' });
    header(s, 5, '古', 't5', 'LINEAGE AND MEANING OF THE CHARACTERS');
    // 左：两行源流
    const rows = [
      ['中', 'zhong', ['甲骨文', '金文', '秦文字', '小篆', '隶书', '楷书']],
      ['国', 'guo', ['金文「或」', '金文「國」', '小篆', '隶书', '楷书', '简化字']],
    ];
    rows.forEach(([ch, key, labels], r) => {
      const y = 1.5 + r * 2.0;
      s.addImage({ path: A('text', `big_${ch}.png`), x: 0.6, y: y + 0.12, w: 0.95, h: 1.0, sizing: { type: 'contain', w: 0.95, h: 1.0 } });
      labels.forEach((lab, i) => {
        const x = 1.75 + i * 1.08, t = 0.96;
        card(s, x, y, t, t, { fill: C.panel, name: `evo-${key}-${i}` });
        s.addImage({ path: A('evo', `${key}_${i}.png`), x: x + 0.08, y: y + 0.08, w: t - 0.16, h: t - 0.16 });
        s.addText(lab, { x: x - 0.1, y: y + 1.0, w: t + 0.2, h: 0.3, align: 'center', fontFace: F.body, fontSize: 10, color: C.text, margin: 0, isTextBox: true });
      });
    });
    txt(s, '“中”本是立在中央的一面旗，“国”在何尊上写作“或”，以戈守城，后加“囗”为“國”，今简化为“国”。', { x: 0.6, y: 5.55, w: 7.5, h: 0.8, fontSize: 12, color: C.muted, lineSpacingMultiple: 1.2 });
    // 右：四字内涵
    const cards = [
      ['中', A('glyph', '中_2A2418.png'), '天地之中', '立旗于中央，四方来聚'],
      ['家', A('glyph', '家_2A2418.png'), '安居之和', '屋下有豕，有居有畜才成家'],
      ['孝', A('glyph', '孝_2A2418.png'), '长幼之和', '子在下承托老人，《说文》“子承老也”'],
      ['龢', A('evo', 'he_4.png'), '声乐之和', '从龠，众管齐鸣，《说文》“龢，调也”'],
    ];
    cards.forEach(([ch, img, head, body], i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = 8.45 + col * 2.2, y = 1.5 + row * 2.45, w = 2.08, h = 2.3;
      card(s, x, y, w, h, { shadow: true, name: `harmony-${ch}` });
      s.addImage({ path: img, x: x + 0.62, y: y + 0.12, w: 0.85, h: 0.85 });
      s.addText(`${ch} · ${head}`, { x: x + 0.1, y: y + 1.02, w: w - 0.2, h: 0.4, align: 'center', fontFace: F.body, fontSize: 13, bold: true, color: C.cinnabar, margin: 0, isTextBox: true });
      txt(s, body, { x: x + 0.15, y: y + 1.45, w: w - 0.3, h: 0.8, fontSize: 10.5, color: C.text, align: 'center' });
    });
    summary(s, 's5');
    s.addNotes('【约 25 秒】\n第一个环节，字的源流与内涵。“中”字，甲骨文、金文画的是立在中央的一面旗，到隶书、楷书收成今天的“中”；“国”在何尊上写作“或”，以戈守城，后来加框成“國”，今天简化为“国”。字形之外还有字义：“家”是屋下养猪，有居才安家；“孝”是孩子托着老人；“龢”是竹管齐鸣。先人把对天地、家庭、长幼和礼乐的理解，写进了一笔一画。\n\n字形来源：甲骨文取自殷契文渊，金文、秦文字、小篆、隶书取自汉典字形库（经我们的字形库汇编），楷书、简化字为楷体排印。【第 5 页字形解说请老师过目】');
  }

  // ══ 6 我们整理的材料 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '材料与模型' });
    header(s, 6, '書', 't6', 'WHAT WE HAVE COMPILED');
    const stats = [
      ['58 万', '张古文字字形图', '汇编甲骨、金文、小篆等 10 个字形来源'],
      ['25,285', '条自建金文数据库目录', '器名、释文、时代、著录号逐条整理，对上拓片编号'],
      ['6,236', '张真拓片', '61,268 个字逐框标注，按隶定清洗重标'],
      ['5,930', '个金文变体', '1,690 个字头，标出时代与出土器物'],
      ['24.6 万', '条上古、中古音韵记录', '覆盖 7,909 个字，听音室据此构拟'],
      ['242', '个百家姓见于金文', '宋本《百家姓》408 个单姓逐一核对'],
    ];
    stats.forEach(([num, unit, note], i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = 0.6 + col * 3.55, y = 1.5 + row * 1.6, w = 3.35, h = 1.42;
      card(s, x, y, w, h, { name: `stat-${i}` });
      s.addText(num, { x: x + 0.2, y: y + 0.1, w: w - 0.4, h: 0.62, fontFace: F.en, fontSize: 32, bold: true, color: C.cinnabar, margin: 0, isTextBox: true, fit: 'shrink' });
      txt(s, unit, { x: x + 0.2, y: y + 0.72, w: w - 0.3, h: 0.32, fontSize: 13, bold: true, color: C.ink });
      txt(s, note, { x: x + 0.2, y: y + 1.03, w: w - 0.3, h: 0.34, fontSize: 10.5, color: C.muted });
    });
    const books = [
      ['殷周金文集成', '1727', '8C4A3C', 4.25], ['商周青铜器铭文暨图像集成续编', '998', '4E7A6C', 4.45], ['商周青铜器铭文暨图像集成', '785', '9A7A3A', 4.45],
      ['三代吉金文存', '455', '6E5B48', 3.75], ['汉金文录', '394', 'A65A44', 3.45], ['小校经阁金文拓本', '256', '5C7A72', 3.95],
      ['古镜聚英', '86', '8A7246', 3.3], ['商周青铜器铭文选', '59', '7C4A40', 3.25],
    ];
    const bx0 = 7.85, base = 6.1;
    books.forEach(([name, n, col, h], i) => {
      const x = bx0 + i * 0.6, w = 0.52, y = base - h;
      s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: col }, line: { color: col, width: 0 }, shadow: { type: 'outer', color: '6B5A3E', opacity: 0.2, blur: 6, offset: 2, angle: 90 }, objectName: `spine-${i}` });
      s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.16, w, h: 0.04, fill: { color: C.paper, transparency: 35 }, line: { color: C.paper, width: 0 } });
      s.addText(name, { x, y: y + 0.3, w, h: h - 0.95, vert: 'eaVert', align: 'center', valign: 'top', fontFace: F.body, fontSize: name.length > 9 ? 9.5 : 11.5, color: C.paper, margin: 0, isTextBox: true });
      s.addText(n, { x: x - 0.05, y: base - 0.52, w: w + 0.1, h: 0.38, align: 'center', fontFace: F.en, fontSize: 10, bold: true, color: C.paper, margin: 0, isTextBox: true });
    });
    s.addShape(pres.shapes.RECTANGLE, { x: bx0 - 0.15, y: base, w: 8 * 0.6 + 0.22, h: 0.09, fill: { color: C.ink }, line: { color: C.ink, width: 0 } });
    txt(s, '拓片出自 150 余种著录与期刊（书脊下为数据集中的拓片张数）', { x: 7.7, y: 1.45, w: 5.1, h: 0.3, fontSize: 10.5, color: C.muted });
    summary(s, 's6');
    s.addNotes('【约 18 秒】\n第二个环节，材料与模型。我们整理了五十八万张古文字字形、两万五千多条自建数据库目录、六千多张真拓片，拓片出自一百五十多种著录，每个字都能追到出处。\n\n口径：58 万 = jinwen-data 10 个字形来源图片合计 582,527；24.6 万 = 古音小镜音韵记录 246,485 条；书脊张数按 6,236 张拓片文件名前缀统计。');
  }

  // ══ 7 识读模型的训练 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '材料与模型' });
    header(s, 7, '智', 't7', 'HOW THE RECOGNITION MODEL WAS TRAINED');
    const steps = [
      ['01', '备数据', ['6,236 张真拓 · 61,268 个字框', '4,114 类字，2,031 类只有 1 个样本', '按隶定统一标注']],
      ['02', '找字', ['4 个检测器融合', 'RF-DETR + DINOv3 视觉大模型', '检测 mAP50 达 0.946']],
      ['03', '认字', ['7 个识别器集成', 'ConvNeXt / ViT-L / ViT-H+', '每个字给出前五个候选']],
      ['04', '交给学者', ['金框是初稿，灰框是存疑', '辞例、字形、释读意见辅助', '学者最后定稿']],
    ];
    steps.forEach(([n, head, lines], i) => {
      const x = 0.6 + i * 3.1, y = 1.5, w = 2.8, h = 2.35;
      card(s, x, y, w, h, { name: `step-${n}` });
      s.addText(n, { x: x + 0.22, y: y + 0.18, w: 0.9, h: 0.55, fontFace: F.en, fontSize: 26, bold: true, color: C.cinnabar, margin: 0, isTextBox: true });
      s.addText(head, { x: x + 1.05, y: y + 0.22, w: 1.6, h: 0.5, fontFace: F.body, fontSize: 18, bold: true, color: C.ink, margin: 0, isTextBox: true, valign: 'middle' });
      s.addText(lines.map((t, k) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: k < lines.length - 1 } })),
        { x: x + 0.2, y: y + 0.92, w: w - 0.3, h: 1.7, fontFace: F.body, fontSize: 12.5, color: C.text, paraSpaceAfter: 6, margin: 0, isTextBox: true, valign: 'top', lang: 'zh-CN' });
      if (i < 3) s.addImage({ path: ic.arrow, x: x + w + 0.06, y: y + 1.25, w: 0.18, h: 0.18 });
    });
    s.addImage({ path: A('rec_crop.png'), x: 0.6, y: 4.15, w: 2.59, h: 1.91, objectName: 'rec-shot' });
    frame(s, 0.6, 4.15, 2.59, 1.91);
    txt(s, '金框初稿 · 灰框存疑', { x: 0.6, y: 6.08, w: 2.59, h: 0.25, fontSize: 10, color: C.muted, align: 'center' });
    card(s, 3.45, 4.15, 9.28, 1.91, { fill: C.panel2, name: 'score' });
    s.addText('F1 0.803', { x: 3.7, y: 4.3, w: 3.3, h: 0.9, fontFace: F.en, fontSize: 44, bold: true, color: C.cinnabar, margin: 0, isTextBox: true });
    txt(s, '世界科学智能大赛 · 古文字识别赛道 二等奖\n第一名 0.8071；单字框对且字对才算对', { x: 3.72, y: 5.2, w: 3.8, h: 0.75, fontSize: 12, color: C.ink });
    txt(s, '训练：RTX 3090 / RTX 5090\n底座模型：DINOv3 视觉大模型\n网站展示的是 20 张验证集拓片的单模型离线结果', { x: 7.7, y: 4.4, w: 4.9, h: 1.5, fontSize: 12, color: C.text, lineSpacingMultiple: 1.3 });
    summary(s, 's7');
    s.addNotes('【约 22 秒】\n在这批拓片上，我们训练了识读模型：四个检测器找字，七个识别器认字，每个字给五个候选。这套系统拿了世界科学智能大赛古文字识别赛道的二等奖，F1 零点八零三，和第一名只差千分之四。机器给初稿，学者定稿。\n\n口径：决赛 F1 0.8030，第一名 0.8071；检测 mAP50 0.946 为 RF-DETR + DINOv3 ViT-L 单检测器本地验证值。被问网站准确率时：网站是单模型离线结果，不要把相合率当准确率。');
  }

  // ══ 8 四个模块：录屏 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '四个模块' });
    header(s, 8, '見', 't8', 'FOUR MODULES: SEE, HEAR, WRITE, STUDY');
    frame(s, 0.57, 1.47, 8.06, 4.56);
    s.addMedia({ type: 'video', path: A('demo.mp4'), cover: 'data:image/png;base64,' + fs.readFileSync(A('demo_poster.png')).toString('base64'), x: 0.6, y: 1.5, w: 8.0, h: 4.5, objectName: 'demo-video' });
    txt(s, '演示录屏（约 45 秒，无声）：寻姓 → 听音 → 铸辞 → 识图。点击播放。', { x: 0.6, y: 6.08, w: 8, h: 0.3, fontSize: 10.5, color: C.muted });
    const rows = [
      ['看', '寻姓 · 方格墙', '输入姓氏，看它三千年前的写法；408 个单姓，242 个见于金文'],
      ['听', '古音听音室', '按郑张尚芳构拟听上古音，四选一认字'],
      ['写', '铸辞坊', '选一件器、挑几个吉字，铸一句金文祝福，标明是戏仿'],
      ['考', '识图 · 释读辅助', '拓片框出每个字，辞例、字形帮学者释读'],
    ];
    rows.forEach(([ch, name, body], i) => {
      const y = 1.5 + i * 1.15, x = 8.95;
      s.addImage({ path: A('text', `big_${ch}.png`), x, y: y + 0.05, w: 0.75, h: 0.85, sizing: { type: 'contain', w: 0.75, h: 0.85 } });
      txt(s, name, { x: x + 0.9, y: y + 0.05, w: 2.95, h: 0.35, fontSize: 13, bold: true, color: C.cinnabar });
      txt(s, body, { x: x + 0.9, y: y + 0.4, w: 2.9, h: 0.65, fontSize: 10.5, color: C.text });
    });
    summary(s, 's8');
    s.addNotes('【约 45 秒，压着录屏说】\n第三个环节，四个模块。看：输入一个姓，比如“周”，看它三千年前的写法，四百零八个单姓里有二百四十二个能在金文里找到。听：按郑张尚芳的构拟，听它的上古音，四选一认字。写：到铸辞坊，先选一件器，再挑几个吉字，连成一句金文祝福，可以生成明信片；页面标明这是戏仿，不冒充出土铭文。考：打开一张拓片，模型框出每个字，金框是初稿，灰框是存疑，旁边列出辞例和字形，帮学者释读。');
  }

  // ══ 9 在趣味互动中记住金文 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '四个模块' });
    header(s, 9, '樂', 't9', 'MINI-GAMES THAT HELP MEMORY');
    const games = [
      ['连连看', 'match.png', '左边金文，右边今字，连对有编钟声'],
      ['描红', 'trace.png', '顺着淡底描一笔，记住字的结构'],
      ['汉字方格墙', 'wall_zhou.png', '翻开一格，认一个字，看一处出处'],
    ];
    games.forEach(([name, img, body], i) => {
      const x = 0.6 + i * 4.1, y = 1.55, w = 3.9, h = 2.19;
      card(s, x - 0.06, y - 0.06, w + 0.12, 3.25, { shadow: true, name: `game-${i}` });
      s.addImage({ path: A('shots', img), x, y, w, h });
      txt(s, name, { x: x + 0.1, y: y + 2.3, w: w - 0.2, h: 0.4, fontSize: 17, bold: true, color: C.ink });
      txt(s, body, { x: x + 0.1, y: y + 2.72, w: w - 0.2, h: 0.4, fontSize: 12, color: C.text });
    });
    txt(s, '看一眼，连一连，描一笔。小红书版还能存分数、晒成绩。', { x: 0.6, y: 5.3, w: 12.1, h: 0.45, fontSize: 15, color: C.cinnabar, align: 'center' });
    summary(s, 's9');
    s.addNotes('【约 8 秒，一句带过】\n连连看、描红这些小游戏，只做一件事：多动一次手，多记住一个字。');
  }

  // ══ 10 落地应用 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '落地应用' });
    header(s, 10, '手', 't10', 'FROM SCREEN TO HANDS');
    s.addImage({ path: A('postcard_shadow_light.png'), x: 0.75, y: 1.35, w: 3.55, h: 4.83, objectName: 'postcard' });
    txt(s, '铸辞坊生成的金文明信片（样张）', { x: 0.6, y: 6.12, w: 3.9, h: 0.3, fontSize: 11, color: C.muted, align: 'center' });
    const rows = [
      [ic.qr, '展位', '扫码体验 → 铸一句吉辞 → 领取 PDF 明信片，回家可自行打印'],
      [ic.phone, '小红书', '手机小工具：听音、描红、连连看，存分数、晒成绩'],
      [ic.class, '课堂', '一节 15 分钟古文字入门课，课前课后同一套题\n【11/7 试用：N 人，正确率 X% → Y%】'],
      [ic.box, '离线包', '没有网络的教室，解压即用'],
    ];
    rows.forEach(([icn, head, body], i) => {
      const x = 4.75, y = 1.45 + i * 1.22, w = 7.98, h = 1.07;
      card(s, x, y, w, h, { name: `land-${i}` });
      iconDot(s, icn, x + 0.25, y + 0.22);
      txt(s, head, { x: x + 1.15, y: y + 0.12, w: 1.4, h: 0.8, fontSize: 17, bold: true, color: C.ink, valign: 'middle' });
      txt(s, body, { x: x + 2.5, y: y + 0.12, w: w - 2.7, h: 0.85, fontSize: 13, color: C.text, valign: 'middle' });
    });
    summary(s, 's10');
    s.addNotes('【约 20 秒】\n第四个环节，落地应用。观众扫码就能生成金文明信片，领走 PDF；手机上有小红书小工具；课堂上，【N】名同学听了一节十五分钟的古文字入门课，答对率从【X】%升到【Y】%。\n\n【11/7 课堂试用后填数字；没测到就删掉课堂那半句】');
  }

  // ══ 11 结尾 ══
  {
    const s = pres.addSlide({ masterName: 'COVER', sectionTitle: '结尾' });
    tximg(s, 'end_1', 0.8, 2.0);
    tximg(s, 'end_2', 0.82, 3.05);
    s.addImage({ path: A('title_art_ink.png'), x: 0.75, y: 4.5, w: 4.3, h: 1.21 });
    tximg(s, 'end_thanks', 0.85, 5.95);
    s.addImage({ path: A('hezun_vessel.png'), x: 8.55, y: 1.45, w: 4.1, h: 4.78 });
    s.addNotes('【约 8 秒】\n字在器上，已经三千年。今天，它也在眼前、在耳边、在手里。请各位老师批评指正。');
  }

  await pres.writeFile({ fileName: OUT });
  console.log('wrote', OUT);
})();
