// 把 SVG 栅格化成 PNG：node svg2png.js in.svg out.png [size]
const sharp = require('sharp');
const [,, inp, out, size] = process.argv;
sharp(inp, { density: 300 }).resize(+(size || 400), +(size || 400), { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
  .png().toFile(out).then(() => {}).catch(e => { console.error(inp, e.message); process.exit(1); });
