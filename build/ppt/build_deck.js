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
    txt(s, '第三届中国研究生“文化中国”两创大赛　赛题五：开放赛题', { x: 0.75, y: 0.5, w: 8, h: 0.35, fontSize: 13, color: C.muted });
    s.addImage({ path: A('title_art_ink.png'), x: 0.7, y: 1.55, w: 7.3, h: 2.05, objectName: 'title-art' });
    tximg(s, 'cover_sub', 0.78, 3.85, { maxW: 7.4 });
    tximg(s, 'cover_tag', 0.8, 4.65);
    s.addMedia({ type: 'audio', path: A('zhaizi.mp3'), x: 0.8, y: 5.45, w: 0.46, h: 0.46 });
    txt(s, '开场拟音：何尊铭文“宅兹中国”四字上古音（郑张尚芳构拟，仅供参考）', { x: 1.38, y: 5.5, w: 7, h: 0.36, fontSize: 12, color: C.muted, valign: 'middle' });
    txt(s, '吉金智识团队', { x: 0.8, y: 6.55, w: 6, h: 0.4, fontSize: 15, bold: true, color: C.ink });
    s.addImage({ path: A('hezun_vessel.png'), x: 8.55, y: 1.45, w: 4.1, h: 4.78, objectName: 'hezun' });
    txt(s, '何尊（西周早期），铭文“宅兹中国”是“中国”一词目前所见最早的文字记录', { x: 8.3, y: 6.35, w: 4.6, h: 0.5, fontSize: 11, color: C.muted, align: 'center' });
    s.addNotes('【约 12 秒｜先点左下播放键，放 3 秒拟音】\n各位评委老师好，我们是吉金智识团队。刚才播放的，是何尊铭文“宅兹中国”四个字的上古音构拟。');
  }

  // ══ 2 总书记 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '缘起' });
    header(s, 2, '中', 't2', 'BACKGROUND');
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
    s.addNotes('【约 20 秒】\n何尊上的“宅兹中国”，是“中国”一词目前所见最早的文字记录。总书记在新年贺词中说，“中国”二字镌刻在何尊底部，更铭刻在每个华夏儿女心中，并强调要激发青少年对中华文明的热爱。');
  }

  // ══ 3 国家重视，公众难亲近 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '缘起' });
    header(s, 3, '文', 't3', 'POLICY AND PUBLIC NEEDS');
    // 左：课本 + 文件
    frame(s, 0.57, 1.47, 2.32, 2.84);
    s.addImage({ path: A('textbook_cover.jpg'), x: 0.6, y: 1.5, w: 2.26, h: 2.78, objectName: 'textbook' });
    txt(s, '2024 年秋季', { x: 3.1, y: 1.55, w: 3.5, h: 0.4, fontSize: 20, bold: true, color: C.cinnabar });
    txt(s, '人教版七年级上册《中国历史》教材启用新封面，主体为何尊，背景为甲骨文。', { x: 3.1, y: 2.0, w: 3.55, h: 2.3, fontSize: 13, color: C.text, lineSpacingMultiple: 1.2 });
    frame(s, 0.57, 4.52, 6.08, 1.55);
    s.addImage({ path: A('moe_doc.jpg'), x: 0.6, y: 4.55, w: 6.02, h: 1.49, objectName: 'moe-doc' });
    txt(s, '2025 年 12 月，教育部等七部门印发《关于深入推进中华优秀语言文化传承发展 提高全民语言文化素养的意见》（教语信〔2025〕3 号），明确“开展追溯甲骨文、金文、篆书等文字发展演变”。', { x: 0.6, y: 6.1, w: 6.1, h: 0.5, fontSize: 10.5, color: C.muted });
    // 右：三道门槛
    txt(s, '公众接触古文字的三个难点', { x: 7.1, y: 1.5, w: 5.6, h: 0.4, fontSize: 17, bold: true, color: C.ink });
    const pains = [
      [ic.museum, '博物馆', '展品说明较简略，观众难以读懂铭文'],
      [ic.db, '数据库', '以单字检索为主，普通读者不易上手'],
      [ic.scroll, '研究', '整篇拓片的释读依赖专家逐字辨识，耗时较长'],
    ];
    pains.forEach(([icn, head, body], i) => {
      const y = 2.05 + i * 1.4;
      card(s, 7.1, y, 5.63, 1.2, { name: `pain-${i}` });
      iconDot(s, icn, 7.3, y + 0.29);
      txt(s, head, { x: 8.15, y: y + 0.2, w: 4.4, h: 0.38, fontSize: 16, bold: true, color: C.ink });
      txt(s, body, { x: 8.15, y: y + 0.6, w: 4.45, h: 0.45, fontSize: 13, color: C.text });
    });
    summary(s, 's3');
    s.addNotes('【约 20 秒】\n近年来，何尊登上了初中历史教材封面，教育部等七部门也提出，要追溯甲骨文、金文、篆书的发展演变。但对普通观众来说，古文字仍然比较陌生，博物馆里往往只有一行说明，数据库里也只能查到单个的字。');
  }

  // ══ 4 主线：以字为桥 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '主线' });
    header(s, 4, '連', 't4', 'FRAMEWORK');
    // 桥面
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1.75, y: 2.75, w: 9.85, h: 0.34, rectRadius: 0.17, fill: { color: C.patina }, line: { color: C.patina, width: 0 }, objectName: 'deck' });
    s.addText('三 千 年', { x: 1.75, y: 2.75, w: 9.85, h: 0.34, align: 'center', valign: 'middle', fontFace: F.body, fontSize: 11, color: C.paper, margin: 0, isTextBox: true });
    // 两端
    [[0.6, '古', '器上的字', '三千年前铸在青铜器上'], [11.2, '今', '身边的人', '公众、课堂与研究']].forEach(([x, ch, head, sub]) => {
      s.addShape(pres.shapes.OVAL, { x, y: 2.15, w: 1.55, h: 1.55, fill: { color: C.cinnabar }, line: { color: C.cinnabar, width: 0 }, shadow: { type: 'outer', color: '6B5A3E', opacity: 0.25, blur: 8, offset: 3, angle: 90 } });
      s.addImage({ path: A('text', `big_${ch}.png`), x: x + 0.3, y: 2.3, w: 0.95, h: 1.25, sizing: { type: 'contain', w: 0.95, h: 1.25 } });
      s.addText(head, { x: x - 0.3, y: 3.85, w: 2.15, h: 0.4, align: 'center', fontFace: F.body, fontSize: 15, bold: true, color: C.ink, margin: 0, isTextBox: true });
      s.addText(sub, { x: x - 0.4, y: 4.25, w: 2.35, h: 0.35, align: 'center', fontFace: F.body, fontSize: 11, color: C.muted, margin: 0, isTextBox: true });
    });
    // 四座桥墩
    const piers = [
      ['一', '字的源流与内涵', '梳理字形演变，\n阐释字中的文化内涵'],
      ['二', '材料与模型', '整理字形、拓片和目录，\n训练古文字识读模型'],
      ['三', '四个模块', '看、听、写、考，\n面向公众、课堂和研究'],
      ['四', '落地应用', '展位明信片、手机小工具、\n课堂教学、离线使用'],
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
    s.addNotes('【约 10 秒】\n因此，我们希望以字为桥，把青铜器上的文字带到今天的公众身边。整个作品分为四个部分。');
  }

  // ══ 5 源流与内涵 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '源流与内涵' });
    header(s, 5, '古', 't5', 'ORIGIN AND MEANING');
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
    txt(s, '“中”字象立于中央的旗帜；“国”在何尊上写作“或”，从戈守城，后加“囗”为“國”，今简化为“国”。', { x: 0.6, y: 5.55, w: 7.5, h: 0.8, fontSize: 12, color: C.muted, lineSpacingMultiple: 1.2 });
    // 右：四字内涵
    const cards = [
      ['中', A('glyph', '中_2A2418.png'), '居中', '象旗立于中央，引申为中心、中正'],
      ['家', A('glyph', '家_2A2418.png'), '安居', '屋下有豕，反映定居与家畜饲养'],
      ['孝', A('glyph', '孝_2A2418.png'), '敬老', '子在下承托老人，《说文》“子承老也”'],
      ['龢', A('evo', 'he_4.png'), '和谐', '从龠，象编管乐器，《说文》“龢，调也”'],
    ];
    cards.forEach(([ch, img, head, body], i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = 8.45 + col * 2.2, y = 1.5 + row * 2.45, w = 2.08, h = 2.3;
      card(s, x, y, w, h, { shadow: true, name: `harmony-${ch}` });
      s.addImage({ path: img, x: x + 0.62, y: y + 0.12, w: 0.85, h: 0.85 });
      s.addText(`${ch}：${head}`, { x: x + 0.1, y: y + 1.02, w: w - 0.2, h: 0.4, align: 'center', fontFace: F.body, fontSize: 13, bold: true, color: C.cinnabar, margin: 0, isTextBox: true });
      txt(s, body, { x: x + 0.15, y: y + 1.45, w: w - 0.3, h: 0.8, fontSize: 10.5, color: C.text, align: 'center' });
    });
    summary(s, 's5');
    s.addNotes('【约 25 秒】\n第一部分是字的源流与内涵。“中”字在甲骨文和金文中像一面立在中央的旗帜，后来逐渐演变成今天的写法；“国”字在何尊上写作“或”，后来外加方框成为“國”，现在简化为“国”。“家”“孝”“龢”这些字，也保存着古人对家庭、长幼和礼乐的理解。');
  }

  // ══ 6 我们整理的材料 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '材料与模型' });
    header(s, 6, '書', 't6', 'DATA RESOURCES');
    const stats = [
      ['58 万', '张古文字字形图', '汇集甲骨文、金文、小篆等 10 类字形来源'],
      ['25,285', '条自建金文数据库目录', '逐条录入器名、释文、时代、著录号'],
      ['6,236', '张拓片', '逐字标注 61,268 个字框，按隶定统一校订'],
      ['5,930', '个金文变体', '分属 1,690 个字头，注明时代与器物'],
      ['24.6 万', '条上古、中古音韵记录', '覆盖 7,909 个字，用于听音模块'],
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
    s.addNotes('【约 15 秒】\n第二部分是材料与模型。我们汇集整理了五十八万张古文字字形图、两万五千多条自建金文数据库目录和六千多张拓片，每个字都可以查到出处。');
  }

  // ══ 7 识读模型的训练 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '材料与模型' });
    header(s, 7, '智', 't7', 'MODEL TRAINING');
    const steps = [
      ['01', '数据准备', ['6,236 张拓片，61,268 个字框', '4,114 类字，其中 2,031 类仅 1 个样本', '按隶定统一标注']],
      ['02', '字符检测', ['4 个检测器融合', 'RF-DETR + DINOv3 视觉大模型', '检测 mAP50 为 0.946']],
      ['03', '字符识别', ['7 个识别器集成', 'ConvNeXt、ViT-L、ViT-H+', '每个字给出 5 个候选']],
      ['04', '辅助释读', ['金框为初稿，灰框为存疑', '提供辞例和字形参考', '由专家审定']],
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
    txt(s, '识图界面：金框为初稿，灰框为存疑', { x: 0.6, y: 6.08, w: 2.59, h: 0.25, fontSize: 10, color: C.muted, align: 'center' });
    card(s, 3.45, 4.15, 9.28, 1.91, { fill: C.panel2, name: 'score' });
    s.addText('F1 0.803', { x: 3.7, y: 4.3, w: 3.3, h: 0.9, fontFace: F.en, fontSize: 44, bold: true, color: C.cinnabar, margin: 0, isTextBox: true });
    txt(s, '世界科学智能大赛古文字识别赛道二等奖\n第一名 F1 为 0.8071\n评测要求字的位置与释文同时正确', { x: 3.72, y: 5.2, w: 3.8, h: 0.75, fontSize: 12, color: C.ink });
    txt(s, '训练设备：RTX 3090、RTX 5090\n基础模型：DINOv3 视觉大模型', { x: 7.7, y: 4.4, w: 4.9, h: 1.5, fontSize: 12, color: C.text, lineSpacingMultiple: 1.3 });
    summary(s, 's7');
    s.addNotes('【约 22 秒】\n在此基础上，我们训练了古文字识读模型，先定位每个字，再给出五个候选。这套系统在世界科学智能大赛古文字识别赛道获得二等奖，F1 值为 0.803。模型给出的是初稿，最终释读仍由学者确定。');
  }

  // ══ 8 四个模块：录屏 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '四个模块' });
    header(s, 8, '見', 't8', 'FOUR MODULES');
    frame(s, 0.57, 1.47, 8.06, 4.56);
    s.addMedia({ type: 'video', path: A('demo.mp4'), cover: 'data:image/png;base64,' + fs.readFileSync(A('demo_poster.png')).toString('base64'), x: 0.6, y: 1.5, w: 8.0, h: 4.5, objectName: 'demo-video' });
    txt(s, '演示录屏（约 47 秒，无声），依次为寻姓、听音、铸辞、识图', { x: 0.6, y: 6.08, w: 8, h: 0.3, fontSize: 10.5, color: C.muted });
    const rows = [
      ['看', '寻姓与方格墙', '输入姓氏，查看其金文写法；408 个单姓中有 242 个见于金文'],
      ['听', '古音听音室', '依郑张尚芳构拟播放上古音，并设听音辨字练习'],
      ['写', '铸辞坊', '选择器物和吉语，生成金文祝福明信片，注明为仿写'],
      ['考', '识图与释读辅助', '自动框出拓片中的字，提供辞例和字形参考'],
    ];
    rows.forEach(([ch, name, body], i) => {
      const y = 1.5 + i * 1.15, x = 8.95;
      s.addImage({ path: A('text', `big_${ch}.png`), x, y: y + 0.05, w: 0.75, h: 0.85, sizing: { type: 'contain', w: 0.75, h: 0.85 } });
      txt(s, name, { x: x + 0.9, y: y + 0.05, w: 2.95, h: 0.35, fontSize: 13, bold: true, color: C.cinnabar });
      txt(s, body, { x: x + 0.9, y: y + 0.4, w: 2.9, h: 0.65, fontSize: 10.5, color: C.text });
    });
    summary(s, 's8');
    s.addNotes('【约 35 秒，压着录屏说】\n第三部分是四个功能模块，请看录屏。“看”，输入一个姓氏，比如“周”，就能看到它在金文里的写法，宋本《百家姓》四百零八个单姓中，有二百四十二个可以在金文中找到；“听”，根据郑张尚芳先生的构拟，听这个字的上古音；“写”，选一件青铜器，挑几个吉祥字，生成一张金文祝福明信片，页面上注明这是仿写；“考”，打开一张拓片，模型会框出每个字，并列出相关辞例和字形，供研究参考。');
  }

  // ══ 9 在趣味互动中记住金文 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '四个模块' });
    header(s, 9, '樂', 't9', 'INTERACTIVE GAMES');
    const games = [
      ['连连看', 'match.png', '金文与楷书配对，答对时播放编钟音'],
      ['描红', 'trace.png', '沿字形描摹笔画，熟悉字的结构'],
      ['汉字方格墙', 'wall_zhou.png', '逐格查看汉字，每个字形附有出处'],
    ];
    games.forEach(([name, img, body], i) => {
      const x = 0.6 + i * 4.1, y = 1.55, w = 3.9, h = 2.19;
      card(s, x - 0.06, y - 0.06, w + 0.12, 3.25, { shadow: true, name: `game-${i}` });
      s.addImage({ path: A('shots', img), x, y, w, h });
      txt(s, name, { x: x + 0.1, y: y + 2.3, w: w - 0.2, h: 0.4, fontSize: 17, bold: true, color: C.ink });
      txt(s, body, { x: x + 0.1, y: y + 2.72, w: w - 0.2, h: 0.4, fontSize: 12, color: C.text });
    });
    txt(s, '连连看、描红也已做成小红书小工具，可保存和分享成绩', { x: 0.6, y: 5.3, w: 12.1, h: 0.45, fontSize: 15, color: C.cinnabar, align: 'center' });
    summary(s, 's9');
    s.addNotes('【约 8 秒】\n此外，我们还设计了连连看、描红等小游戏，帮助大家在互动中加深记忆。');
  }

  // ══ 10 落地应用 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '落地应用' });
    header(s, 10, '手', 't10', 'APPLICATIONS');
    s.addImage({ path: A('postcard_shadow_light.png'), x: 0.75, y: 1.35, w: 3.55, h: 4.83, objectName: 'postcard' });
    txt(s, '铸辞坊生成的金文明信片（样张）', { x: 0.6, y: 6.12, w: 3.9, h: 0.3, fontSize: 11, color: C.muted, align: 'center' });
    const rows = [
      [ic.qr, '展位', '观众扫码体验，生成金文明信片，下载 PDF 后可自行打印'],
      [ic.phone, '小红书', '手机端小工具，包含听音、描红、连连看，可保存和分享成绩'],
      [ic.class, '课堂', '15 分钟古文字入门课，课前、课后使用同一套测试题\n【11/7 试用：N 人，正确率由 X% 提高到 Y%】'],
      [ic.box, '离线包', '无网络环境下解压即可使用'],
    ];
    rows.forEach(([icn, head, body], i) => {
      const x = 4.75, y = 1.45 + i * 1.22, w = 7.98, h = 1.07;
      card(s, x, y, w, h, { name: `land-${i}` });
      iconDot(s, icn, x + 0.25, y + 0.22);
      txt(s, head, { x: x + 1.15, y: y + 0.12, w: 1.4, h: 0.8, fontSize: 17, bold: true, color: C.ink, valign: 'middle' });
      txt(s, body, { x: x + 2.5, y: y + 0.12, w: w - 2.7, h: 0.85, fontSize: 13, color: C.text, valign: 'middle' });
    });
    summary(s, 's10');
    s.addNotes('【约 22 秒】\n第四部分是落地应用。观众在展位扫码，就能生成自己的金文明信片，下载 PDF 带走；手机上可以使用小红书小工具。在课堂试用中，【N】名同学参加了十五分钟的入门课，答题正确率从【X】%提高到【Y】%。');
  }

  // ══ 11 结尾 ══
  {
    const s = pres.addSlide({ masterName: 'COVER', sectionTitle: '结尾' });
    tximg(s, 'end_1', 0.8, 2.3, { maxW: 7.5 });
    s.addImage({ path: A('title_art_ink.png'), x: 0.75, y: 3.75, w: 4.3, h: 1.21 });
    tximg(s, 'end_thanks', 0.85, 5.4);
    s.addImage({ path: A('hezun_vessel.png'), x: 8.55, y: 1.45, w: 4.1, h: 4.78 });
    s.addNotes('【约 10 秒】\n最后，我们希望通过这个作品，让书写在青铜器上的文字活起来。汇报完毕，敬请各位老师批评指正。');
  }

  await pres.writeFile({ fileName: OUT });
  console.log('wrote', OUT);
})();
