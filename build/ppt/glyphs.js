// 把 jinwen_svg 里的字形渲染成指定颜色的透明 PNG：node glyphs.js 颜色 字...
const sharp = require('sharp'); const fs = require('fs'); const path = require('path');
const [,, color, ...chars] = process.argv;
const SRC = path.join(__dirname, '..', '..', 'jinwen_svg');
(async () => {
  for (const ch of chars.join('').split('')) {
    const f = path.join(SRC, ch + '.svg');
    if (!fs.existsSync(f)) { console.error('missing', ch); continue; }
    let svg = fs.readFileSync(f, 'utf8');
    // 漢典 SVG 里水印是浅色 path，去掉；字形 path 改成指定颜色
    svg = svg.replace(/<path[^>]*fill="#([0-9a-fA-F]{6})"[^>]*\/>/g, (m, hex) => {
      const n = parseInt(hex, 16), lum = ((n >> 16) & 255) * 0.3 + ((n >> 8) & 255) * 0.59 + (n & 255) * 0.11;
      return lum > 200 ? '' : m;
    });
    svg = svg.replace(/fill="(?!none)[^"]*"/g, `fill="#${color}"`).replace(/<svg /, `<svg fill="#${color}" `);
    await sharp(Buffer.from(svg), { density: 400 }).resize(600, 600, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png().toFile(path.join(__dirname, 'assets', 'glyph', `${ch}_${color}.png`));
  }
})();
