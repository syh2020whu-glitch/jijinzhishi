"""「一个字的源流」用的字形：统一成透明底单色 PNG。楷书、简化字用系统楷体渲染。"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
SRC = ROOT / "dl" / "jwd"
OUT = ROOT / "assets" / "evo"
OUT.mkdir(parents=True, exist_ok=True)
INK = (232, 199, 122)   # 与 PPT 金色一致
KAI = "C:/Windows/Fonts/simkai.ttf"

CHAINS = {
    "zhong": [("中", "ayh_3.webp", "甲骨文"), ("中", "zdic_jinwen_31_E263.png", "金文"),
              ("中", "zdic_qinwenzi_71_E04A.png", "秦文字"), ("中", "zdic_xiaozhuan_27_4E2D.png", "小篆"),
              ("中", "zdic_lishu_91_E273.png", "隶书"), ("中", None, "楷书")],
    "guo": [("或", "zdic_jinwen_33_F3BF.png", "金文「或」"), ("國", "zdic_jinwen_32_EC7F.png", "金文「國」"),
            ("國", "zdic_xiaozhuan_27_570B.png", "小篆"), ("國", "zdic_lishu_92_EA88.png", "隶书"),
            ("國", None, "楷书"), ("国", None, "简化字")],
    "he": [("龢", f, "") for f in ("zdic_jinwen_31_EA50.png", "zdic_jinwen_31_EA51.png", "zdic_jinwen_31_EA52.png",
                                   "zdic_jinwen_31_EA57.png", "zdic_jinwen_31_EA5A.png")],
}


def to_alpha(path):
    im = Image.open(path).convert("RGBA")
    a = np.array(im).astype(np.float32)
    if a[..., 3].min() > 250:                       # 白底黑字：按亮度取墨
        alpha = 255 - a[..., :3].mean(axis=2)
    else:                                           # 透明底：用原 alpha，去掉浅色
        alpha = a[..., 3] * (a[..., :3].mean(axis=2) < 160)
    alpha = np.clip((alpha - 40) * 1.4, 0, 255)
    return alpha.astype(np.uint8)


def kai(ch, size=600):
    im = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(KAI, int(size * 0.82))
    d.text((size / 2, size / 2), ch, fill=255, font=f, anchor="mm")
    return np.array(im)


def save(alpha, out, size=600, pad=0.08):
    ys, xs = np.nonzero(alpha > 30)
    alpha = alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = alpha.shape
    s = (size * (1 - 2 * pad)) / max(h, w)
    g = Image.fromarray(alpha).resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(g, ((size - g.width) // 2, (size - g.height) // 2))
    rgba = Image.new("RGBA", (size, size), INK + (0,))
    rgba.putalpha(canvas)
    rgba.save(out)


for name, chain in CHAINS.items():
    for i, (ch, fn, _label) in enumerate(chain):
        alpha = kai(ch) if fn is None else to_alpha(SRC / ch / fn)
        save(alpha, OUT / f"{name}_{i}.png")
print("ok")
