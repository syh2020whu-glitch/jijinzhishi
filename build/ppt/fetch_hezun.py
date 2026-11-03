"""何尊铭文拓片（中国青铜器全集，经维基共享资源，公有领域）→ 整张图 + "中或"局部放大。
python build/ppt/fetch_hezun.py"""
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).parent
URL = "https://upload.wikimedia.org/wikipedia/commons/4/48/He_zun_inscription.jpg"
RAW = ROOT / "dl" / "hezun_rubbing.jpg"
ZHONGGUO = (405, 180, 515, 415)   # Commons 页面注释框 x=415 y=188 w=89 h=218，四周各放宽一点

if not RAW.exists():
    RAW.parent.mkdir(exist_ok=True)
    req = urllib.request.Request(URL, headers={"User-Agent": "jijinzhishi-ppt/1.0 (education)"})
    RAW.write_bytes(urllib.request.urlopen(req).read())

im = Image.open(RAW).convert("RGB")
im.save(ROOT / "assets" / "hezun_rubbing.jpg", quality=92)
crop = im.crop(ZHONGGUO)
crop = crop.resize((crop.width * 3, crop.height * 3), Image.LANCZOS)
ImageOps.autocontrast(crop, cutoff=1).save(ROOT / "assets" / "hezun_zhongguo.png")
print("ok", im.size, crop.size)
