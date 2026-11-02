// 决赛答辩 PPT（4 分钟，12 页）。先跑 shots.py / make_assets.py / evo_glyphs.py 备好素材，再：node build/ppt/build_deck.js
const path = require('path');
const fs = require('fs');
const pptxgen = require('pptxgenjs');
const sharp = require('sharp');
const React = require('react');
const ReactDOMServer = require('react-dom/server');
const fa = require('react-icons/fa');

const ROOT = __dirname;
const A = (...p) => path.join(ROOT, 'assets', ...p);
const OUT = path.join(ROOT, '..', '..', '吉金智识-决赛答辩-v1.pptx');

// ── 配色：墨褐底、金字、朱印、铜绿点缀 ──
const C = {
  bg: '15110C', panel: '231C14', panel2: '2E251A',
  gold: 'E8C77A', goldDeep: 'B8913F', goldLight: 'F4E3B5',
  text: 'EFE6D2', muted: 'A89A7E', cinnabar: 'A63A2C', patina: '5E9C88', paper: 'F4EFE4',
};
const F = { title: '华文中宋', body: '微软雅黑', en: 'Cambria' };
const TOTAL = 12;

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';            // 13.333 × 7.5 in
pres.title = '吉金智识 · 决赛答辩';
pres.theme = { headFontFace: F.title, bodyFontFace: F.body };

// ── 版式：封面 / 内容页 ──
const logoObjs = (x, y, s) => [
  { rect: { x, y, w: s * 2.35, h: s, fill: { color: C.paper, transparency: 6 }, rectRadius: 0.08 } },
  { image: { path: A('ref', 'image2.png'), x: x + s * 0.1, y: y + s * 0.06, w: s * 0.92, h: s * 0.88 } },
  { image: { path: A('ref', 'image3.png'), x: x + s * 1.28, y: y + s * 0.06, w: s * 0.88, h: s * 0.88 } },
];
pres.defineSlideMaster({
  title: 'COVER',
  background: { path: A('bg_cover.jpg') },
  objects: logoObjs(10.75, 0.42, 0.8),
});
pres.defineSlideMaster({
  title: 'CONTENT',
  background: { path: A('bg_dark.jpg') },
  objects: [
    ...logoObjs(11.3, 0.4, 0.6),
    { text: { text: '吉金智识 · 以字为桥', options: { x: 0.6, y: 7.0, w: 4, h: 0.3, fontFace: F.body, fontSize: 10, color: C.muted, margin: 0 } } },
  ],
  slideNumber: { x: 12.15, y: 7.0, w: 0.6, h: 0.3, fontFace: F.en, fontSize: 10, color: C.muted, align: 'right' },
});

// ── 小工具 ──
async function icon(Comp, color, file) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: '#' + color, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  fs.writeFileSync(file, buf);
  return file;
}
function header(slide, seal, title, en) {
  slide.addImage({ path: A(`seal_${seal}.png`), x: 0.6, y: 0.4, w: 0.68, h: 0.68, objectName: 'seal' });
  slide.addText(title, { x: 1.45, y: 0.33, w: 9.6, h: 0.62, fontFace: F.title, fontSize: 28, bold: true, color: C.goldLight, margin: 0, isTextBox: true, objectName: 'title', lang: 'zh-CN' });
  slide.addText(en, { x: 1.47, y: 0.93, w: 9.4, h: 0.28, fontFace: F.en, fontSize: 11, italic: true, color: C.muted, charSpacing: 2, margin: 0, isTextBox: true, objectName: 'title-en' });
}
function takeaway(slide, text) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 1.67, y: 6.5, w: 10.0, h: 0.5, rectRadius: 0.25,
    fill: { color: C.panel2, transparency: 15 }, line: { color: C.goldDeep, width: 0.75, transparency: 40 }, objectName: 'takeaway-bg',
  });
  slide.addText(text, { x: 1.67, y: 6.5, w: 10.0, h: 0.5, align: 'center', valign: 'middle', fontFace: F.title, fontSize: 16, color: C.goldLight, margin: 0, isTextBox: true, objectName: 'takeaway', lang: 'zh-CN' });
}
function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: opts.r ?? 0.12,
    fill: { color: opts.fill || C.panel, transparency: opts.t ?? 10 },
    line: { color: opts.line || C.goldDeep, width: 0.75, transparency: opts.lt ?? 55 },
    shadow: opts.shadow ? { type: 'outer', color: '000000', opacity: 0.45, blur: 8, offset: 3, angle: 90 } : undefined,
    objectName: opts.name,
  });
}
const txt = (slide, text, o) => slide.addText(text, { fontFace: F.body, color: C.text, margin: 0, isTextBox: true, valign: 'top', lang: 'zh-CN', ...o });

(async () => {
  const ICON = A('icons'); fs.mkdirSync(ICON, { recursive: true });
  const ic = {
    museum: await icon(fa.FaLandmark, C.gold, path.join(ICON, 'museum.png')),
    db: await icon(fa.FaDatabase, C.gold, path.join(ICON, 'db.png')),
    scroll: await icon(fa.FaScroll, C.gold, path.join(ICON, 'scroll.png')),
    qr: await icon(fa.FaQrcode, C.gold, path.join(ICON, 'qr.png')),
    phone: await icon(fa.FaMobileAlt, C.gold, path.join(ICON, 'phone.png')),
    class: await icon(fa.FaChalkboardTeacher, C.gold, path.join(ICON, 'class.png')),
    box: await icon(fa.FaBoxOpen, C.gold, path.join(ICON, 'box.png')),
    book: await icon(fa.FaBookOpen, C.gold, path.join(ICON, 'book.png')),
    arrow: await icon(fa.FaChevronRight, C.goldDeep, path.join(ICON, 'arrow.png')),
  };
  // 桥拱：金色描线
  const archSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="520" viewBox="0 0 1800 520">
    <path d="M60 470 Q900 -120 1740 470" fill="none" stroke="#E8C77A" stroke-width="10" stroke-linecap="round"/>
    <path d="M60 470 L1740 470" fill="none" stroke="#B8913F" stroke-width="6" stroke-dasharray="2 22" stroke-linecap="round"/></svg>`;
  await sharp(Buffer.from(archSvg)).png().toFile(A('arch.png'));

  ['开场', '缘起', '主线', '一 源流', '二 内涵', '三 底座', '四 体验', '五 落地', '结尾'].forEach(t => pres.addSection({ title: t }));

  // ══ 1 封面 ══
  {
    const s = pres.addSlide({ masterName: 'COVER', sectionTitle: '开场' });
    ['宅', '茲', '中', '或'].forEach((ch, i) => {
      s.addImage({ path: A('glyph', `${ch}_E8C77A.png`), x: 0.95, y: 0.95 + i * 1.42, w: 1.3, h: 1.3, objectName: `cover-glyph-${ch}` });
    });
    s.addText('何尊 · 宅兹中国', { x: 2.35, y: 2.2, w: 0.45, h: 3.2, vert: 'eaVert', fontFace: F.title, fontSize: 14, color: C.muted, margin: 0, isTextBox: true });
    s.addImage({ path: A('title_art.png'), x: 3.55, y: 1.65, w: 7.7, h: 2.16, objectName: 'title-art' });
    s.addText('以字为桥，连起三千年', { x: 3.65, y: 4.05, w: 8.6, h: 0.75, fontFace: F.title, fontSize: 34, bold: true, color: C.goldLight, margin: 0, isTextBox: true });
    s.addText('让金文可看 · 可听 · 可写 · 可考', { x: 3.67, y: 4.85, w: 8.6, h: 0.5, fontFace: F.title, fontSize: 20, color: C.gold, margin: 0, isTextBox: true });
    s.addText('第三届中国研究生“文化中国”两创大赛 · 赛题五 开放赛题 · 吉金智识团队', { x: 3.67, y: 6.35, w: 8.8, h: 0.4, fontFace: F.body, fontSize: 13, color: C.muted, margin: 0, isTextBox: true });
    // 「宅茲中國」四字拟音（assets/audio/ipa 拼接），开场点一下播放
    s.addMedia({ type: 'audio', path: A('zhaizi.mp3'), x: 3.67, y: 5.5, w: 0.5, h: 0.5 });
    s.addText('▶ 点此播放“宅兹中国”上古拟音（郑张尚芳构拟，仅供参考）', { x: 4.25, y: 5.55, w: 8, h: 0.4, fontFace: F.body, fontSize: 12, color: C.muted, margin: 0, isTextBox: true, valign: 'middle' });
    s.addNotes('【约 15 秒｜先放 3 秒“宅兹中国”上古拟音】\n刚才这四个音，是三千年前“宅兹中国”的构拟读音。我们是吉金智识，想用一个个金文字，把三千年连起来。');
  }

  // ══ 2 总书记 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '缘起' });
    header(s, '中', '最早的“中国”，写在何尊上', 'GENERAL SECRETARY XI JINPING AND THE HE ZUN');
    s.addShape(pres.shapes.RECTANGLE, { x: 0.56, y: 1.46, w: 6.38, h: 4.01, fill: { color: C.goldDeep }, line: { color: C.goldDeep, width: 0 } });
    s.addImage({ path: path.join(ROOT, 'dl', 'xi_hezun_b.jpg'), x: 0.6, y: 1.5, w: 6.3, h: 3.93, objectName: 'photo-xi' });
    txt(s, '2024 年 9 月 10 日，习近平总书记在宝鸡青铜器博物院考察，在何尊前驻足察看。新华社记者 王晔 摄', { x: 0.6, y: 5.55, w: 6.3, h: 0.5, fontSize: 11, color: C.muted });
    s.addText('“', { x: 7.25, y: 1.25, w: 0.8, h: 0.8, fontFace: F.title, fontSize: 60, color: C.gold, margin: 0, isTextBox: true });
    s.addText('“中国”二字镌刻在“何尊”底部，更铭刻在每个华夏儿女心中。', { x: 7.35, y: 1.85, w: 5.4, h: 1.15, fontFace: F.title, fontSize: 22, bold: true, color: C.goldLight, margin: 0, isTextBox: true, valign: 'top' });
    txt(s, '—— 2025 年新年贺词', { x: 7.35, y: 3.0, w: 5.4, h: 0.3, fontSize: 12, color: C.gold });
    txt(s, '要加强青铜器文物的保护研究和宣传阐释，更好激发全社会特别是青少年对伟大祖国和中华文明的热爱。', { x: 7.35, y: 3.55, w: 5.4, h: 0.95, fontSize: 15 });
    txt(s, '—— 2024 年 9 月，考察宝鸡青铜器博物院', { x: 7.35, y: 4.5, w: 5.4, h: 0.3, fontSize: 12, color: C.gold });
    txt(s, '中国的汉文字非常了不起，中华民族的形成和发展离不开汉文字的维系。', { x: 7.35, y: 5.0, w: 5.4, h: 0.7, fontSize: 15 });
    txt(s, '—— 2022 年 10 月，考察安阳殷墟', { x: 7.35, y: 5.72, w: 5.4, h: 0.3, fontSize: 12, color: C.gold });
    takeaway(s, '让青少年读懂何尊上的字，是我们做这件事的起点');
    s.addNotes('【约 20 秒】\n这四个字铸在何尊底部，是“中国”二字最早的文字记录。总书记说，“中国”二字镌刻在何尊底部，更铭刻在每个华夏儿女心中；还嘱咐要加强青铜器的宣传阐释，激发青少年对中华文明的热爱。\n\n来源：2025 年新年贺词；2024-09-10 考察宝鸡青铜器博物院（新华社）；2022-10-28 考察安阳殷墟（新华社）。照片：新华社记者王晔摄，转自中央网信办网站 2024-09-12。');
  }

  // ══ 3 时代与痛点 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '缘起' });
    header(s, '文', '时代在推，公众却走不近', 'WHY BRONZE INSCRIPTIONS, WHY NOW');
    txt(s, '政策与课堂', { x: 0.6, y: 1.5, w: 5.8, h: 0.4, fontFace: F.title, fontSize: 18, bold: true, color: C.gold });
    const items = [
      ['2024', '秋季', '何尊登上人教版七年级上册《中国历史》封面，背景是甲骨文。'],
      ['2026', '1 月', '教育部等七部门印发意见：开展追溯甲骨文、金文、篆书等文字发展演变。'],
    ];
    items.forEach(([yr, mo, body], i) => {
      const y = 2.05 + i * 2.15;
      card(s, 0.6, y, 5.8, 1.95, { name: `policy-${yr}` });
      s.addText(yr, { x: 0.85, y: y + 0.22, w: 1.6, h: 0.75, fontFace: F.en, fontSize: 40, bold: true, color: C.gold, margin: 0, isTextBox: true });
      txt(s, mo, { x: 0.87, y: y + 1.0, w: 1.5, h: 0.35, fontSize: 13, color: C.muted });
      txt(s, body, { x: 2.55, y: y + 0.3, w: 3.65, h: 1.4, fontSize: 15, valign: 'middle' });
    });
    txt(s, '可在现实里，金文离公众最远', { x: 6.9, y: 1.5, w: 5.8, h: 0.4, fontFace: F.title, fontSize: 18, bold: true, color: C.gold });
    const pains = [
      [ic.museum, '博物馆里', '器物旁一行说明，扫一眼就走'],
      [ic.db, '数据库里', '一个个孤立的单字，不会查就进不去'],
      [ic.scroll, '研究里', '整张拓片逐字释读，全靠专家一字字看'],
    ];
    pains.forEach(([icn, head, body], i) => {
      const y = 2.05 + i * 1.37;
      card(s, 6.9, y, 5.83, 1.17, { name: `pain-${i}` });
      s.addShape(pres.shapes.OVAL, { x: 7.12, y: y + 0.24, w: 0.7, h: 0.7, fill: { color: C.panel2 }, line: { color: C.gold, width: 1 } });
      s.addImage({ path: icn, x: 7.29, y: y + 0.41, w: 0.36, h: 0.36 });
      txt(s, head, { x: 8.05, y: y + 0.2, w: 4.5, h: 0.38, fontSize: 16, bold: true, color: C.goldLight });
      txt(s, body, { x: 8.05, y: y + 0.6, w: 4.5, h: 0.4, fontSize: 14, color: C.text });
    });
    takeaway(s, '材料不缺，缺一座从三千年前走到今天的桥');
    s.addNotes('【约 12 秒】\n何尊上了初中历史课本封面，今年七部门又要求追溯金文等文字的演变。可金文离公众仍然最远：博物馆里一行说明，数据库里一个个单字。缺的是一座桥。\n\n来源：人民网陕西频道 2024-08-30；教育部网站 2026-01-15《教育部等七部门关于深入推进中华优秀语言文化传承发展 提高全民语言文化素养的意见》。');
  }

  // ══ 4 主线：以字为桥 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '主线' });
    header(s, '連', '以字为桥：把三千年连起来', 'OUR THROUGH-LINE: CHARACTERS AS A BRIDGE');
    s.addImage({ path: A('arch.png'), x: 1.55, y: 1.55, w: 10.2, h: 2.95, objectName: 'arch' });
    // 两端
    [[0.6, '古', '器上的字', '三千年前铸在青铜器上'], [11.15, '今', '手边的人', '公众 · 课堂 · 研究']].forEach(([x, ch, head, sub]) => {
      s.addShape(pres.shapes.OVAL, { x, y: 3.25, w: 1.55, h: 1.55, fill: { color: C.cinnabar }, line: { color: C.gold, width: 1.5 } });
      s.addText(ch, { x, y: 3.25, w: 1.55, h: 1.55, align: 'center', valign: 'middle', fontFace: F.title, fontSize: 44, bold: true, color: C.paper, margin: 0, isTextBox: true });
      s.addText(head, { x: x - 0.3, y: 4.9, w: 2.15, h: 0.4, align: 'center', fontFace: F.title, fontSize: 16, bold: true, color: C.goldLight, margin: 0, isTextBox: true });
      s.addText(sub, { x: x - 0.35, y: 5.3, w: 2.25, h: 0.35, align: 'center', fontFace: F.body, fontSize: 11, color: C.muted, margin: 0, isTextBox: true });
    });
    const piers = [
      ['一', '源流', '一个字怎样\n变成今天的样子'],
      ['二', '内涵', '字里的天地\n家国与人伦'],
      ['三', '底座', '字形、拓片、书目\n与识读模型'],
      ['四', '体验', '看 · 听 · 写 · 考\n玩中记住'],
      ['五', '落地', '带得走的明信片\n进得去的课堂'],
    ];
    piers.forEach(([n, head, body], i) => {
      const x = 2.45 + i * 1.75, y = 3.15;
      card(s, x, y, 1.55, 2.2, { fill: C.panel2, t: 5, lt: 35, name: `pier-${i}` });
      s.addText(n, { x, y: y + 0.15, w: 1.55, h: 0.4, align: 'center', fontFace: F.title, fontSize: 14, color: C.gold, margin: 0, isTextBox: true });
      s.addText(head, { x, y: y + 0.55, w: 1.55, h: 0.55, align: 'center', fontFace: F.title, fontSize: 22, bold: true, color: C.goldLight, margin: 0, isTextBox: true });
      s.addText(body, { x: x + 0.08, y: y + 1.2, w: 1.39, h: 1.2, align: 'center', fontFace: F.body, fontSize: 12, color: C.text, margin: 0, isTextBox: true, valign: 'top' });
    });
    takeaway(s, '一头是器上的字，一头是手边的人，中间五座桥墩');
    s.addNotes('【约 12 秒】\n所以我们的主线是“以字为桥”：一头是器上的字，一头是手边的人，中间五座桥墩。\n\n（回应“连起来是什么意思”：后面每一页都对应一座桥墩，顺序是 源流 → 内涵 → 底座 → 体验 → 落地。）');
  }

  // ══ 5 源流 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '一 源流' });
    header(s, '古', '一个字，三千年', 'FROM A STATIC GLYPH TO A LIVING LINEAGE');
    const rows = [
      ['中', 'zhōng', 'zhong', ['甲骨文', '金文', '秦文字', '小篆', '隶书', '楷书'], ['商', '商周', '战国 · 秦', '秦', '汉', '魏晋以后']],
      ['国', 'guó', 'guo', ['金文「或」', '金文「國」', '小篆', '隶书', '楷书', '简化字'], ['西周 · 何尊', '外加「囗」', '秦', '汉', '魏晋以后', '1956 年']],
    ];
    rows.forEach(([ch, py, key, labels, eras], r) => {
      const y = 1.55 + r * 2.35;
      s.addText(ch, { x: 0.6, y: y + 0.12, w: 1.3, h: 1.0, align: 'center', fontFace: F.title, fontSize: 54, bold: true, color: C.goldLight, margin: 0, isTextBox: true });
      s.addText(py, { x: 0.6, y: y + 1.12, w: 1.3, h: 0.35, align: 'center', fontFace: F.en, fontSize: 14, italic: true, color: C.muted, margin: 0, isTextBox: true });
      labels.forEach((lab, i) => {
        const x = 2.15 + i * 1.78;
        card(s, x, y, 1.38, 1.38, { fill: C.panel, t: 0, lt: 50, name: `evo-${key}-${i}` });
        s.addImage({ path: A('evo', `${key}_${i}.png`), x: x + 0.14, y: y + 0.14, w: 1.1, h: 1.1 });
        s.addText(lab, { x: x - 0.2, y: y + 1.45, w: 1.78, h: 0.32, align: 'center', fontFace: F.body, fontSize: 13, bold: true, color: C.goldLight, margin: 0, isTextBox: true });
        s.addText(eras[i], { x: x - 0.2, y: y + 1.76, w: 1.78, h: 0.3, align: 'center', fontFace: F.body, fontSize: 11, color: C.muted, margin: 0, isTextBox: true });
        if (i < labels.length - 1) s.addImage({ path: ic.arrow, x: x + 1.47, y: y + 0.58, w: 0.22, h: 0.22 });
      });
    });
    txt(s, '何尊写作“宅兹中或”：“或”从口从戈，以戈守城；后来外加“囗”表示疆域，成了“國”。', { x: 2.15, y: 6.0, w: 10.4, h: 0.4, fontSize: 14, color: C.text });
    takeaway(s, '字不是一张静态的图：从甲骨到简化字，一脉相承三千年');
    s.addNotes('【约 22 秒】\n第一是源流。“中”字，甲骨文、金文画的是立在中央的一面旗，到隶书、楷书收成今天的“中”。“国”在何尊上写作“或”，以戈守城，后来加框成“國”，今天简化为“国”。静态的字，就成了一条活的源流。\n\n字形来源：甲骨文取自殷契文渊，金文、秦文字、小篆、隶书取自汉典字形库（经我们的字形库 jinwen-data 汇编），楷书、简化字为楷体排印。时代按字体大类标注，不对应具体器物。');
  }

  // ══ 6 内涵 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '二 内涵' });
    header(s, '和', '先人造字，字里有“和”', 'HARMONY WRITTEN INTO EVERY STROKE');
    const cards = [
      ['中', A('glyph', '中_E8C77A.png'), '天地之中', '一面旗立在中央，四方来聚。“中”是不偏不倚的位置，也是何尊上的“中国”。'],
      ['家', A('glyph', '家_E8C77A.png'), '安居之和', '屋顶下养着猪。有屋可住、有畜可养，人才安定成家。'],
      ['孝', A('glyph', '孝_E8C77A.png'), '长幼之和', '上面是长发老人，下面是孩子。《说文》：“子承老也。”'],
      ['龢', A('evo', 'he_4.png'), '声乐之和', '从“龠”，一排竹管合在一起吹。《说文》：“龢，调也。”今写作“和”。'],
    ];
    cards.forEach(([ch, img, head, body], i) => {
      const x = 0.6 + i * 3.07, y = 1.5, w = 2.85, h = 4.55;
      card(s, x, y, w, h, { fill: C.panel, t: 5, shadow: true, name: `harmony-${ch}` });
      s.addImage({ path: img, x: x + 0.62, y: y + 0.25, w: 1.6, h: 1.6 });
      s.addText(ch, { x: x + 0.2, y: y + 1.95, w: 0.8, h: 0.7, fontFace: F.title, fontSize: 32, bold: true, color: C.goldLight, margin: 0, isTextBox: true });
      s.addText(head, { x: x + 1.0, y: y + 2.08, w: 1.7, h: 0.5, fontFace: F.title, fontSize: 17, bold: true, color: C.gold, margin: 0, isTextBox: true, valign: 'middle' });
      txt(s, body, { x: x + 0.22, y: y + 2.75, w: w - 0.4, h: 1.7, fontSize: 15, color: C.text, lineSpacingMultiple: 1.15 });
    });
    takeaway(s, '天地、家庭、长幼、礼乐：先人把对和谐的理解，写进了一笔一画');
    s.addNotes('【约 22 秒】\n第二是内涵。“中”是立旗聚众；“家”是屋下养猪，有居才安家；“孝”是孩子托着老人；“龢”是竹管齐鸣、众声调和。先人把对天地、家庭、长幼和礼乐的理解，写进了一笔一画。\n\n【请老师审定】字形解说取通行说法：中（唐兰旗帜说）、家（宀下豕）、孝（《说文》子承老也）、龢（《说文》调也，从龠禾声）。');
  }

  // ══ 7 家底 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '三 底座' });
    header(s, '書', '我们的家底：每个字都有出处', 'WHAT WE HAVE COMPILED');
    const stats = [
      ['58 万', '张古文字字形图', '汇编甲骨、金文、小篆等 10 个字形来源'],
      ['25,285', '条《中华字库》金文目录', '6 卷著录逐条整理成表，对上拓片编号'],
      ['6,236', '张真拓片', '61,268 个字逐框标注，我们按隶定清洗重标'],
      ['5,930', '个金文变体', '1,690 个字头，标出时代与出土器物'],
      ['24.6 万', '条上古、中古音韵记录', '覆盖 7,909 个字，听音室据此构拟'],
      ['242', '个百家姓见于金文', '宋本《百家姓》408 个单姓逐一核对'],
    ];
    stats.forEach(([num, unit, note], i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = 0.6 + col * 3.55, y = 1.5 + row * 1.62, w = 3.35, h = 1.45;
      card(s, x, y, w, h, { name: `stat-${i}` });
      s.addText(num, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.62, fontFace: F.en, fontSize: 32, bold: true, color: C.gold, margin: 0, isTextBox: true, fit: 'shrink' });
      txt(s, unit, { x: x + 0.2, y: y + 0.74, w: w - 0.3, h: 0.32, fontSize: 13, bold: true, color: C.goldLight });
      txt(s, note, { x: x + 0.2, y: y + 1.05, w: w - 0.3, h: 0.32, fontSize: 11, color: C.muted });
    });
    // 书墙：拓片出处（数据集内拓片张数）
    const books = [
      ['殷周金文集成', '1727', '5A2E22', 4.25], ['商周青铜器铭文暨图像集成续编', '998', '2F4A40', 4.45], ['商周青铜器铭文暨图像集成', '785', '6B5326', 4.45],
      ['三代吉金文存', '455', '3D3024', 3.75], ['汉金文录', '394', '7A3B2A', 3.45], ['小校经阁金文拓本', '256', '35473F', 3.95],
      ['古镜聚英', '86', '5C4A2A', 3.3], ['中华字库 · 金文目录', '6 卷', '4A2A22', 3.95],
    ];
    const bx0 = 7.85, base = 6.1;
    books.forEach(([name, n, col, h], i) => {
      const x = bx0 + i * 0.6, w = 0.52, y = base - h;
      s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: col }, line: { color: C.goldDeep, width: 0.5, transparency: 30 }, objectName: `spine-${i}` });
      s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.18, w, h: 0.05, fill: { color: C.gold, transparency: 30 }, line: { color: C.gold, width: 0 } });
      s.addText(name, { x, y: y + 0.32, w, h: h - 0.95, vert: 'eaVert', align: 'center', valign: 'top', fontFace: F.title, fontSize: name.length > 9 ? 10 : 12, color: C.paper, margin: 0, isTextBox: true });
      s.addText(n, { x: x - 0.05, y: base - 0.55, w: w + 0.1, h: 0.4, align: 'center', fontFace: F.en, fontSize: 10, bold: true, color: C.goldLight, margin: 0, isTextBox: true });
    });
    s.addShape(pres.shapes.RECTANGLE, { x: bx0 - 0.15, y: base, w: 8 * 0.6 + 0.22, h: 0.08, fill: { color: C.goldDeep }, line: { color: C.goldDeep, width: 0 } });
    txt(s, '拓片出自 150 余种著录与期刊（书脊下为数据集中的拓片张数）', { x: 7.7, y: 1.45, w: 5.1, h: 0.3, fontSize: 11, color: C.muted });
    takeaway(s, '数量是底气：每一个字，都能追到出处');
    s.addNotes('【约 18 秒】\n第三是底座。我们整理了五十八万张古文字字形、两万五千多条《中华字库》金文目录、六千多张真拓片，拓片出自一百五十多种著录，每个字都能追到出处。\n\n口径：58 万 = jinwen-data 10 个字形来源图片合计 582,527（KAOM、殷契文渊、汉典、比赛拓片切字、EVOBC、Chronicles、说文、故宫甲骨、HUST-OBC、qxk）；24.6 万 = 古音小镜音韵记录 246,485 条；书脊张数按 6,236 张拓片文件名前缀统计。');
  }

  // ══ 8 模型 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '三 底座' });
    header(s, '智', '模型怎么练成：拓片进，初稿出', 'HOW THE RECOGNITION MODEL WAS TRAINED');
    const steps = [
      ['01', '备数据', ['6,236 张真拓 · 61,268 个字框', '4,114 类字，2,031 类只有 1 个样本', '按隶定统一标注']],
      ['02', '找字', ['4 个检测器融合', 'RF-DETR + DINOv3 视觉大模型', '检测 mAP50 达 0.946']],
      ['03', '认字', ['7 个识别器集成', 'ConvNeXt / ViT-L / ViT-H+', '每个字给出前五个候选']],
      ['04', '交给学者', ['金框是初稿，灰框是存疑', '辞例、字形、释读意见辅助', '学者最后定稿']],
    ];
    steps.forEach(([n, head, lines], i) => {
      const x = 0.6 + i * 3.1, y = 1.5, w = 2.8, h = 2.75;
      card(s, x, y, w, h, { name: `step-${n}` });
      s.addText(n, { x: x + 0.22, y: y + 0.18, w: 0.9, h: 0.55, fontFace: F.en, fontSize: 26, bold: true, color: C.gold, margin: 0, isTextBox: true });
      s.addText(head, { x: x + 1.05, y: y + 0.22, w: 1.6, h: 0.5, fontFace: F.title, fontSize: 19, bold: true, color: C.goldLight, margin: 0, isTextBox: true, valign: 'middle' });
      s.addText(lines.map((t, k) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: k < lines.length - 1 } })),
        { x: x + 0.2, y: y + 0.92, w: w - 0.3, h: 1.7, fontFace: F.body, fontSize: 12.5, color: C.text, paraSpaceAfter: 6, margin: 0, isTextBox: true, valign: 'top', lang: 'zh-CN' });
      if (i < 3) s.addImage({ path: ic.arrow, x: x + w + 0.06, y: y + 1.25, w: 0.18, h: 0.18 });
    });
    // 下排：识图截图 + 成绩
    s.addImage({ path: A('rec_crop.png'), x: 0.6, y: 4.45, w: 2.59, h: 1.91, objectName: 'rec-shot' });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 4.45, w: 2.59, h: 1.91, fill: { type: 'none' }, line: { color: C.goldDeep, width: 0.75 } });
    txt(s, '金框初稿 · 灰框存疑', { x: 0.6, y: 6.38, w: 2.59, h: 0.25, fontSize: 10, color: C.muted, align: 'center' });
    card(s, 3.45, 4.45, 9.28, 1.91, { fill: C.panel2, t: 5, lt: 35, name: 'score' });
    s.addText('F1 0.80', { x: 3.7, y: 4.62, w: 3.3, h: 0.9, fontFace: F.en, fontSize: 44, bold: true, color: C.gold, margin: 0, isTextBox: true });
    txt(s, '世界科学智能大赛 · 古文字识别赛道\n决赛系统（单字框对且字对才算对）', { x: 3.72, y: 5.5, w: 3.6, h: 0.75, fontSize: 12, color: C.goldLight });
    txt(s, '训练：RTX 3090 / RTX 5090\n底座模型：DINOv3 视觉大模型\n网站展示的是 20 张验证集拓片的单模型离线结果', { x: 7.6, y: 4.72, w: 4.95, h: 1.5, fontSize: 12, color: C.text, lineSpacingMultiple: 1.3 });
    takeaway(s, '机器先给初稿和疑字，释读的最后一笔留给学者');
    s.addNotes('【约 22 秒】\n在这批拓片上，我们训练了识读模型：四个检测器找字，七个识别器认字，每个字给五个候选。这套系统在世界科学智能大赛古文字识别赛道决赛中，F1 达到 0.80。机器给初稿，学者定稿。\n\n【定稿前确认】F1 0.80 的赛事名称、赛段、名次口径；检测 mAP50 0.946 为 RF-DETR + DINOv3 ViT-L 单检测器本地验证值。被问网站准确率时：网站是单模型离线结果，不要把相合率当准确率。');
  }

  // ══ 9 体验：看听写考 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '四 体验' });
    header(s, '見', '看 · 听 · 写 · 考：一座桥，四条路', 'FOUR WAYS TO MEET A CHARACTER');
    const cells = [
      ['看', '寻姓', 'wall_zhou.png', '输入姓氏，看它三千年前的写法；408 个单姓，242 个见于金文。'],
      ['听', '古音听音室', 'listen.png', '按郑张尚芳构拟听上古音，四选一认字，标明仅供参考。'],
      ['写', '铸辞坊', 'ritual_card.png', '选一件器、挑几个吉字，铸一句金文祝福，标明是戏仿。'],
      ['考', '识图 · 释读辅助', 'rec_assist.png', '拓片框出每个字，辞例、字形帮学者释读。'],
    ];
    cells.forEach(([ch, name, img, body], i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = 0.6 + col * 6.12, y = 1.45 + row * 2.5, iw = 4.0, ih = 2.25;
      card(s, x, y, 5.95, ih + 0.1, { fill: C.panel, t: 5, name: `way-${ch}` });
      s.addImage({ path: A('shots', img), x: x + 0.05, y: y + 0.05, w: iw, h: ih });
      s.addText(ch, { x: x + 4.2, y: y + 0.12, w: 1.0, h: 0.8, fontFace: F.title, fontSize: 40, bold: true, color: C.gold, margin: 0, isTextBox: true });
      txt(s, name, { x: x + 4.22, y: y + 0.92, w: 1.65, h: 0.35, fontSize: 13, bold: true, color: C.goldLight });
      txt(s, body, { x: x + 4.22, y: y + 1.3, w: 1.62, h: 1.0, fontSize: 11, color: C.text });
    });
    takeaway(s, '公众、课堂、研究走同一座桥，只是走得深浅不同');
    s.addNotes('【约 25 秒】\n第四是体验，四条路：看，输入姓氏看它的金文；听，听构拟的上古音；写，选器择字，铸一句金文祝福；考，打开拓片，模型框出每个字，辅助释读。\n\n（如有 60 秒录屏，可在这一页嵌入，替换四张截图。）');
  }

  // ══ 10 小游戏 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '四 体验' });
    header(s, '樂', '玩一遍，就记住了', 'MINI-GAMES THAT HELP MEMORY');
    const games = [
      ['连连看', 'match.png', '左边金文，右边今字，连对有编钟声'],
      ['描红', 'trace.png', '顺着淡底描一笔，记住字的结构'],
      ['汉字方格墙', 'wall_zhou.png', '翻开一格，认一个字，看一处出处'],
    ];
    games.forEach(([name, img, body], i) => {
      const x = 0.6 + i * 4.1, y = 1.6, w = 3.9, h = 2.19;
      card(s, x - 0.05, y - 0.05, w + 0.1, 3.4, { fill: C.panel, t: 5, name: `game-${i}` });
      s.addImage({ path: A('shots', img), x, y, w, h });
      txt(s, name, { x: x + 0.1, y: y + 2.35, w: w - 0.2, h: 0.42, fontFace: F.title, fontSize: 19, bold: true, color: C.goldLight });
      txt(s, body, { x: x + 0.1, y: y + 2.82, w: w - 0.2, h: 0.6, fontSize: 13, color: C.text });
    });
    txt(s, '看一眼 → 连一连 → 描一笔：从认得，到记得', { x: 0.6, y: 5.5, w: 12.1, h: 0.45, fontFace: F.title, fontSize: 18, color: C.gold, align: 'center' });
    takeaway(s, '游戏只是手段：多动一次手，就多记住一个字');
    s.addNotes('【约 8 秒，一句带过】\n连连看、描红这些小游戏，只做一件事：多动一次手，多记住一个字。');
  }

  // ══ 11 落地 ══
  {
    const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: '五 落地' });
    header(s, '手', '带得走，用得上', 'FROM SCREEN TO HANDS');
    s.addImage({ path: A('postcard_shadow.png'), x: 0.75, y: 1.35, w: 3.55, h: 4.83, objectName: 'postcard' });
    txt(s, '铸辞坊生成的金文明信片（样张）', { x: 0.6, y: 6.12, w: 3.9, h: 0.3, fontSize: 11, color: C.muted, align: 'center' });
    const rows = [
      [ic.qr, '展位', '扫码体验 → 铸一句吉辞 → 领取 PDF 明信片，回家可自行打印'],
      [ic.phone, '小红书', '手机小工具：听音、描红、连连看，存分数、晒成绩'],
      [ic.class, '课堂', '一节 15 分钟金文入门课，课前课后同一套题\n【11/7 试用：N 人，正确率 X% → Y%】'],
      [ic.box, '离线包', '没有网络的教室，解压即用'],
    ];
    rows.forEach(([icn, head, body], i) => {
      const x = 4.75, y = 1.45 + i * 1.22, w = 7.98, h = 1.07;
      card(s, x, y, w, h, { name: `land-${i}` });
      s.addShape(pres.shapes.OVAL, { x: x + 0.22, y: y + 0.18, w: 0.7, h: 0.7, fill: { color: C.panel2 }, line: { color: C.gold, width: 1 } });
      s.addImage({ path: icn, x: x + 0.39, y: y + 0.35, w: 0.36, h: 0.36 });
      txt(s, head, { x: x + 1.15, y: y + 0.12, w: 1.4, h: 0.8, fontFace: F.title, fontSize: 18, bold: true, color: C.goldLight, valign: 'middle' });
      txt(s, body, { x: x + 2.5, y: y + 0.12, w: w - 2.7, h: 0.85, fontSize: 13, color: C.text, valign: 'middle' });
    });
    takeaway(s, '从屏幕上的字，到手里的明信片、课堂上的一节课');
    s.addNotes('【约 20 秒】\n第五是落地。观众扫码就能生成金文明信片，领走 PDF；手机上有小红书小工具；课堂上，【N】名同学听了一节十五分钟的入门课，答对率从【X】%升到【Y】%。\n\n【11/7 课堂试用后填数字；没测到就删掉课堂那半句】');
  }

  // ══ 12 结尾 ══
  {
    const s = pres.addSlide({ masterName: 'COVER', sectionTitle: '结尾' });
    ['宅', '茲', '中', '或'].forEach((ch, i) => {
      s.addImage({ path: A('glyph', `${ch}_E8C77A.png`), x: 0.95, y: 0.95 + i * 1.42, w: 1.3, h: 1.3 });
    });
    s.addText('字在器上，已经三千年。', { x: 3.6, y: 2.0, w: 9.0, h: 0.9, fontFace: F.title, fontSize: 40, bold: true, color: C.goldLight, margin: 0, isTextBox: true });
    s.addText('今天，它也在眼前、在耳边、在手里。', { x: 3.6, y: 2.95, w: 9.0, h: 0.8, fontFace: F.title, fontSize: 30, color: C.gold, margin: 0, isTextBox: true });
    s.addImage({ path: A('title_art.png'), x: 3.6, y: 4.25, w: 4.6, h: 1.29 });
    s.addText('谢谢各位老师', { x: 8.7, y: 4.55, w: 3.8, h: 0.7, fontFace: F.title, fontSize: 26, color: C.goldLight, margin: 0, isTextBox: true });
    s.addNotes('【约 8 秒】\n字在器上，已经三千年。今天，它也在眼前、在耳边、在手里。谢谢各位老师。');
  }

  await pres.writeFile({ fileName: OUT });
  console.log('wrote', OUT);
})();
