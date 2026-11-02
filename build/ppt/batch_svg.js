const sharp = require('sharp'); const fs = require('fs'); const path = require('path');
const dir = process.argv[2];
(async () => {
  for (const ch of fs.readdirSync(dir)) {
    const d = path.join(dir, ch); if (!fs.statSync(d).isDirectory()) continue;
    for (const f of fs.readdirSync(d)) if (f.endsWith('.svg')) {
      try { await sharp(path.join(d, f), { density: 300 }).resize(300, 300, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toFile(path.join(d, f.replace(/\.svg$/, '.png'))); }
      catch (e) { console.error(f, e.message); }
    }
  }
})();
