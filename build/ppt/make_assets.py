"""决赛 PPT 的背景、印章、标题字。python build/ppt/make_assets.py"""
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent
A = ROOT / "assets"
G = A / "glyph"
W, H = 1920, 1080
random.seed(7)


def radial(c_in, c_out, cx=0.5, cy=0.42, power=1.6):
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x / W - cx) * 1.25) ** 2 + (y / H - cy) ** 2)
    t = np.clip(d / 0.85, 0, 1) ** power
    img = np.zeros((H, W, 3))
    for k in range(3):
        img[..., k] = c_in[k] * (1 - t) + c_out[k] * t
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")


def sprinkle(base, glyphs, n, size_rng, alpha_rng, avoid=None):
    for _ in range(n):
        g = Image.open(random.choice(glyphs)).convert("RGBA")
        s = random.randint(*size_rng)
        g = g.resize((s, s), Image.LANCZOS)
        a = np.array(g)
        a[..., 3] = (a[..., 3] * random.uniform(*alpha_rng)).astype(np.uint8)
        g = Image.fromarray(a)
        x, y = random.randint(-s // 3, W - s // 2), random.randint(-s // 3, H - s // 2)
        if avoid and avoid(x + s / 2, y + s / 2):
            continue
        base.alpha_composite(g, (x, y))
    return base


gold = sorted(G.glob("*_E8C77A.png"))

# 内容页背景：墨褐，四周略暗，零星金文暗纹
bg = radial((40, 33, 24), (14, 11, 8))
bg = sprinkle(bg, gold, 70, (60, 150), (0.035, 0.07))
bg.convert("RGB").save(A / "bg_dark.jpg", quality=92)

# 封面背景：更暗，右侧大片金文字阵
cv = radial((34, 28, 20), (10, 8, 6), cx=0.35, cy=0.5)
cv = sprinkle(cv, gold, 160, (70, 210), (0.04, 0.10))
cv.convert("RGB").save(A / "bg_cover.jpg", quality=92)

# 印章：朱红圆角方块 + 白色金文
for f in G.glob("*_FFFFFF.png"):
    ch = f.name.split("_")[0]
    S = 320
    seal = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(seal)
    d.rounded_rectangle((8, 8, S - 8, S - 8), radius=36, fill=(166, 58, 44, 255))
    # 印泥的斑驳感
    noise = (np.random.rand(S, S) > 0.985)
    a = np.array(seal)
    a[noise & (a[..., 3] > 0), 3] = 150
    seal = Image.fromarray(a)
    g = Image.open(f).convert("RGBA").resize((236, 236), Image.LANCZOS)
    seal.alpha_composite(g, ((S - 236) // 2, (S - 236) // 2))
    seal.save(A / f"seal_{ch}.png")

# 标题字「吉金智識」：取初赛 PPT 的金色标题图，黑底转透明
t = Image.open(A / "semi" / "image2.jpeg").convert("RGB")
arr = np.array(t).astype(np.float32)
lum = arr.max(axis=2)
alpha = np.clip((lum - 30) * 2.2, 0, 255).astype(np.uint8)
rgba = np.dstack([arr.astype(np.uint8), alpha])
Image.fromarray(rgba, "RGBA").save(A / "title_art.png")

# 明信片：加一圈投影
pc = Image.open(A / "shots" / "postcard.png").convert("RGBA")
pad = 40
sh = Image.new("RGBA", (pc.width + pad * 2, pc.height + pad * 2), (0, 0, 0, 0))
m = Image.new("L", sh.size, 0)
ImageDraw.Draw(m).rectangle((pad, pad + 10, pad + pc.width, pad + pc.height + 10), fill=150)
m = m.filter(ImageFilter.GaussianBlur(16))
sh.putalpha(m)
sh.alpha_composite(pc, (pad, pad))
sh.save(A / "postcard_shadow.png")
print("ok")
