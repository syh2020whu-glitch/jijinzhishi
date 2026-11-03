""""中"字演变动图：甲骨文 → 金文 → 秦文字 → 小篆 → 隶书 → 楷书，逐个淡入，循环。→ assets/evo_zhong.gif
python build/ppt/make_evo_gif.py"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
A = ROOT / "assets"
BG = (251, 248, 241)
INK = (42, 36, 24)
MUTED = (160, 148, 128)
CINNABAR = (166, 58, 44)
FONT = "C:/Windows/Fonts/msyh.ttc"
LABELS = ["甲骨文", "金文", "秦文字", "小篆", "隶书", "楷书"]
W, H = 600, 640
GLYPH = 400
HOLD, FADE = 10, 4          # 每 0.1 秒一帧：停 1 秒，淡入 0.4 秒

glyphs = [Image.open(A / "evo" / f"zhong_{i}.png").convert("RGBA").resize((GLYPH, GLYPH), Image.LANCZOS) for i in range(6)]
f_label = ImageFont.truetype(FONT, 34)
f_step = ImageFont.truetype(FONT, 20)


def frame(i, j=None, t=0.0):
    """第 i 个字形；若给 j，则按 t 从 i 淡到 j。"""
    im = Image.new("RGBA", (W, H), BG + (255,))
    g = glyphs[i] if j is None else Image.blend(glyphs[i], glyphs[j], t)
    im.alpha_composite(g, ((W - GLYPH) // 2, 30))
    cur = i if j is None or t < 0.5 else j
    d = ImageDraw.Draw(im)
    lab = LABELS[cur]
    d.text(((W - d.textlength(lab, font=f_label)) / 2, 450), lab, font=f_label, fill=CINNABAR)
    # 底部时间轴
    y = 560
    x0, x1 = 60, W - 60
    d.line((x0, y, x1, y), fill=MUTED, width=2)
    for k, name in enumerate(LABELS):
        x = x0 + (x1 - x0) * k / 5
        r = 9 if k == cur else 5
        d.ellipse((x - r, y - r, x + r, y + r), fill=CINNABAR if k == cur else MUTED)
        d.text((x - d.textlength(name, font=f_step) / 2, y + 16), name, font=f_step, fill=INK if k == cur else MUTED)
    return im.convert("RGB")


frames = []
for i in range(6):
    frames += [frame(i)] * HOLD
    j = (i + 1) % 6
    if j:
        frames += [frame(i, j, (k + 1) / (FADE + 1)) for k in range(FADE)]
frames += [frame(5)] * HOLD          # 楷书多停一会儿再回到甲骨文
pal = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
pal[0].save(A / "evo_zhong.gif", save_all=True, append_images=pal[1:], duration=100, loop=0, optimize=True)
print("frames", len(frames), (A / "evo_zhong.gif").stat().st_size // 1024, "KB")
