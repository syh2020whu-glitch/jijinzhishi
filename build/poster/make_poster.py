"""决赛现场展示海报：套组委会模板（竖版 800×1800 mm），出 72 dpi jpg（2268×5102）。

python build/poster/make_poster.py                  # 两个主标题方案各出一张
python build/poster/make_poster.py --title A        # 只出方案 A
python build/poster/make_poster.py --prep          # 重新生成 build/poster/assets/（证明材料脱敏图 + VR 截图）

模板 jpg 不入库，默认读仓库根目录的“文化中国”总决赛现场展示海报设计模板.jpg（4724×10628，150 dpi）。
版面在模板原尺寸上排，最后缩到 72 dpi。配色、字体、素材与 build/ppt 同一套。
全稿不放本队校名、人名；文案不拿金文和其他古文字比较。
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
A = REPO / "build" / "ppt" / "assets"
OUT = ROOT / "out"
TEMPLATE = REPO / "“文化中国”总决赛现场展示海报设计模板.jpg"
Image.MAX_IMAGE_PIXELS = None

# ── 配色：与 PPT 相同（宣纸、墨、朱砂、铜绿、金），另加模板标签的藏青 ──
PAPER = (244, 239, 228)
PANEL = (251, 248, 241)
PANEL2 = (239, 232, 216)
LINE = (217, 207, 187)
INK = (42, 36, 24)
TEXT = (58, 51, 40)
MUTED = (122, 110, 92)
CINNABAR = (166, 58, 44)
PATINA = (78, 138, 122)
GOLD = (184, 145, 63)
DARK = (43, 38, 32)
NAVY = (11, 61, 86)   # 模板“参赛队伍名称：”的颜色

FONTS = "C:/Windows/Fonts/"
F_TITLE = FONTS + "STZHONGS.TTF"   # 华文中宋：标题（PPT 标题图同款）
F_BODY = FONTS + "msyh.ttc"        # 微软雅黑：正文
F_BOLD = FONTS + "msyhbd.ttc"
F_NUM = FONTS + "cambriab.ttf"     # Cambria：数字、英文
F_EN = FONTS + "cambriai.ttf"

TITLES = {
    "A": "“中国”二字，最早写在这件青铜器上",
    "B": "以字为桥，连起三千年",
}

W = 4724                      # 模板宽（150 dpi）
PX0, PX1 = 300, W - 300       # 内容面板左右
CX0, CX1 = 470, W - 470       # 面板内文字区
CW = CX1 - CX0
OUT_SIZE = (2268, 5102)       # 800×1800 mm @ 72 dpi

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


NO_LINE_START = set("，。、；：？！”’）》」』…·%")


def wrap(text, f, max_w):
    """按宽度折行，标点不放行首。"""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if cur and f.getlength(cur + ch) > max_w and ch not in NO_LINE_START:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines


class Poster:
    def __init__(self, template):
        self.im = Image.open(template).convert("RGB").convert("RGBA")
        assert self.im.width == W, f"模板宽应为 {W}，实际 {self.im.width}"
        self.d = ImageDraw.Draw(self.im)

    # ── 基础绘制 ──
    def text(self, xy, s, path, size, color, anchor="la", bold=0, spacing=0):
        f = font(path, size)
        if spacing:
            x, y = xy
            total = sum(f.getlength(c) for c in s) + spacing * (len(s) - 1)
            if anchor[0] == "m":
                x -= total / 2
            elif anchor[0] == "r":
                x -= total
            for c in s:
                self.d.text((x, y), c, font=f, fill=color, anchor="l" + anchor[1], stroke_width=bold, stroke_fill=color)
                x += f.getlength(c) + spacing
            return total
        self.d.text(xy, s, font=f, fill=color, anchor=anchor, stroke_width=bold, stroke_fill=color)
        return f.getlength(s)

    def para(self, x, y, s, size, color, max_w, path=F_BODY, lh=1.6, align="left"):
        f = font(path, size)
        lines = wrap(s, f, max_w)
        for i, l in enumerate(lines):
            if align == "center":
                self.d.text((x + max_w / 2, y + i * size * lh), l, font=f, fill=color, anchor="ma")
            else:
                self.d.text((x, y + i * size * lh), l, font=f, fill=color)
        return y + len(lines) * size * lh

    def rect(self, box, fill=None, outline=None, width=1, radius=0):
        if radius:
            self.d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=width)

    def shadow_box(self, box, radius=0, blur=28, offset=12, alpha=60):
        x0, y0, x1, y1 = (round(v) for v in box)
        pad = blur * 3
        m = Image.new("L", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), radius=radius, fill=alpha)
        m = m.filter(ImageFilter.GaussianBlur(blur))
        sh = Image.new("RGBA", m.size, (90, 72, 46, 0))
        sh.putalpha(m)
        self.im.alpha_composite(sh, (x0 - pad, y0 - pad + offset))

    def paste(self, src, box, mode="contain", align="center"):
        """把图片放进框里：contain 等比缩放居中不裁；cover 等比铺满后裁切。返回实际位置。"""
        img = src if isinstance(src, Image.Image) else Image.open(src)
        img = img.convert("RGBA")
        x0, y0, x1, y1 = (round(v) for v in box)
        bw, bh = x1 - x0, y1 - y0
        r = (min if mode == "contain" else max)(bw / img.width, bh / img.height)
        img = img.resize((max(1, round(img.width * r)), max(1, round(img.height * r))), Image.LANCZOS)
        if mode == "cover":
            l, t = (img.width - bw) // 2, (img.height - bh) // 2
            img = img.crop((l, t, l + bw, t + bh))
        ix = x0 + (bw - img.width) // 2
        iy = y0 + ((bh - img.height) // 2 if align == "center" else 0)
        self.im.alpha_composite(img, (ix, iy))
        return ix, iy, ix + img.width, iy + img.height

    def dashed_line(self, p0, p1, color, width=4, dash=26, gap=18):
        (x0, y0), (x1, y1) = p0, p1
        n = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        t = 0.0
        while t < n:
            t1 = min(t + dash, n)
            self.d.line((x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n, x0 + (x1 - x0) * t1 / n, y0 + (y1 - y0) * t1 / n), fill=color, width=width)
            t += dash + gap

    def tri(self, cx, cy, s, direction):
        if direction == "right":
            pts = [(cx - s / 2, cy - s * 0.6), (cx + s / 2, cy), (cx - s / 2, cy + s * 0.6)]
        else:
            pts = [(cx - s * 0.6, cy - s / 2), (cx + s * 0.6, cy - s / 2), (cx, cy + s / 2)]
        self.d.polygon(pts, fill=GOLD)

    def dot(self, cx, cy, d, color, icon=None, label=None, label_size=None):
        self.d.ellipse((cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2), fill=color, outline=PAPER, width=max(3, d // 30))
        if icon:
            s = int(d * 0.52)
            self.paste(icon, (int(cx - s / 2), int(cy - s / 2), int(cx + s / 2), int(cy + s / 2)))
        if label:
            self.text((cx, cy), label, F_NUM, label_size or int(d * 0.55), PAPER, anchor="mm")

    # ── PPT 同款版块标题：印章 + 中宋标题 + 英文小字 + 金色短线和通栏细线 ──
    def header(self, y, seal, title, en):
        s = 170
        self.paste(A / f"seal_{seal}.png", (CX0, y, CX0 + s, y + s))
        self.text((CX0 + s + 50, y + s * 0.42), title, F_TITLE, 120, INK, anchor="lm", bold=2)
        self.text((CX0 + s + 54, y + s * 0.42 + 95), en, F_EN, 46, MUTED, anchor="lm", spacing=6)
        ly = y + s + 40
        self.d.line((CX0, ly, CX1, ly), fill=LINE, width=3)
        self.rect((CX0, ly - 4, CX0 + s, ly + 5), fill=GOLD)
        return ly + 70


PA = ROOT / "assets"            # 海报专用素材（已去掉姓名、校名，入库）
PROOF = A / "proof" / "png"      # 证明材料的脱敏图（不入库），只在 --prep 时读
VR_BRANCH = "claude/vr-galaxy-fb0eec"


def prep_assets():
    """从证明材料和 VR 分支截图生成 build/poster/assets/。一般不用重跑，素材已入库。"""
    import subprocess
    from io import BytesIO
    PA.mkdir(exist_ok=True)
    # VR 截图（1920×1080）：取中间 1440×810，去掉四周空黑
    for key, n in [("vr_carve", "03-carve"), ("vr_pour", "05-pour"), ("vr_open", "06-open"), ("vr_rise", "08-rise")]:
        raw = subprocess.run(["git", "show", f"{VR_BRANCH}:build/vr-slide/out/{n}.png"], cwd=REPO, capture_output=True, check=True).stdout
        Image.open(BytesIO(raw)).convert("RGB").crop((240, 100, 1680, 910)).resize((1080, 608), Image.LANCZOS).save(PA / f"{key}.jpg", quality=90)
    # 证书：世界科学智能大赛裁到赛道名为止（不露队名、姓名、主办方校名）；CCL 已转正并遮掉高校校徽
    s = Image.open(PROOF / "sais_award_crop.png").convert("RGB")
    s.crop((0, 0, s.width, 1535)).resize((900, round(900 * 1535 / s.width)), Image.LANCZOS).save(PA / "award_sais.jpg", quality=90)
    for key, src in [("award_ccl", "ccl2026_award_crop.png"), ("cert_confucius", "confucius_cert_crop.png")]:
        c = Image.open(PROOF / src).convert("RGB")
        c.resize((1200, round(1200 * c.height / c.width)), Image.LANCZOS).save(PA / f"{key}.jpg", quality=90)
    # 论文首页：只取上半页（题目 + 摘要），作者栏已涂掉 / 本是匿名稿
    for key, src in [("paper_lt4hala", "paper_lt4hala2026_p1_anon.png"), ("paper_arr", "paper_arr2026-10_p1.png")]:
        c = Image.open(PROOF / src).convert("RGB")
        c = c.crop((0, int(c.height * 0.05), c.width, int(c.height * 0.50)))
        c.resize((1000, round(1000 * c.height / c.width)), Image.LANCZOS).save(PA / f"{key}.jpg", quality=90)
    print("prepared", sorted(f.name for f in PA.iterdir()))


def build(key, template):
    p = Poster(template)
    d = p.d

    # ── 模板上的“参赛队伍名称：”后面填队名，同一行右侧补赛题（同色同字号） ──
    p.text((1385, 2691), "吉金智识", F_TITLE, 150, NAVY, anchor="lm", bold=2)
    p.text((2560, 2691), "所属赛题：赛题五 开放赛题", F_TITLE, 112, NAVY, anchor="lm", bold=1)

    # ── 内容面板：半透明宣纸色圆角大板，底部露出模板山水 ──
    PY0, PY1 = 2900, 10240
    p.shadow_box((PX0, PY0, PX1, PY1), radius=80, blur=40, offset=16, alpha=70)
    panel = Image.new("RGBA", p.im.size, (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle((PX0, PY0, PX1, PY1), radius=80, fill=PANEL + (236,))
    p.im.alpha_composite(panel)
    d.rounded_rectangle((PX0 + 28, PY0 + 28, PX1 - 28, PY1 - 28), radius=60, outline=(214, 192, 140), width=4)

    # ══ 主标题 ══
    y = 3050
    title = TITLES[key]
    size = 200 if key == "A" else 230
    th = 215                    # 两个方案的标题行同高，后面版面不动
    tw = font(F_TITLE, size).getlength(title)
    seal = int(size * 0.95)
    tx = (W - tw - seal - 60) / 2
    p.text((tx, y + th / 2), title, F_TITLE, size, INK, anchor="lm", bold=4)
    p.paste(A / "seal_中.png", (int(tx + tw + 60), int(y + th / 2 - seal / 2), int(tx + tw + 60 + seal), int(y + th / 2 + seal / 2)))
    y += th + 60
    p.rect((W / 2 - 90, y, W / 2 + 90, y + 8), fill=GOLD)
    y += 50
    p.text((W / 2, y), "吉金智识　金文数字化传承与互动体验平台", F_TITLE, 96, CINNABAR, anchor="ma", bold=1, spacing=8)
    y += 96 + 100

    # ══ 何尊 + 项目简介 ══
    hy0, hh = y, 720
    p.paste(A / "hezun_vessel.png", (CX0, hy0, CX0 + 680, hy0 + hh))
    rx0 = CX0 + 710
    rw = int(hh * 1000 / 932)
    rb = p.paste(A / "hezun_rubbing.jpg", (rx0, hy0, rx0 + rw, hy0 + hh))
    k = rw / 1000
    bx, by, bw, bh = rb[0] + 405 * k, rb[1] + 180 * k, 110 * k, 235 * k
    d.rectangle((bx, by, bx + bw, by + bh), outline=CINNABAR, width=9)
    zx0 = rx0 + rw + 110
    zw = int(hh * 0.86 * 330 / 705)
    zb = (zx0, hy0, zx0 + zw, hy0 + int(hh * 0.86))
    p.dashed_line((bx + bw, by), (zb[0], zb[1]), CINNABAR, 4)
    p.dashed_line((bx + bw, by + bh), (zb[0], zb[3]), CINNABAR, 4)
    p.paste(A / "hezun_zhongguo.png", zb, mode="cover")
    d.rectangle(zb, outline=CINNABAR, width=9)
    p.text(((zb[0] + zb[2]) / 2, zb[3] + 14), "中或", F_TITLE, 80, CINNABAR, anchor="ma", bold=2)
    p.para(CX0, hy0 + hh + 25, "何尊（西周早期），铭文“宅兹中或”是“中国”一词目前所见最早的文字记录", 46, MUTED, zb[2] - CX0 + 200)

    ix0 = zb[2] + 120
    iw = CX1 - ix0
    p.text((ix0, hy0), "项目简介", F_TITLE, 104, INK, bold=2)
    p.text((ix0 + 450, hy0 + 62), "ABOUT", F_EN, 46, MUTED, anchor="ls", spacing=6)
    p.rect((ix0, hy0 + 140, ix0 + 140, hy0 + 148), fill=GOLD)
    p.para(ix0, hy0 + 185,
           "吉金智识是一个金文数字化传承与互动体验平台。我们整理古文字字形、自建金文数据库目录和拓片，"
           "训练古文字识读模型，帮助观众在博物馆里读懂青铜铭文。同一套字库，还能用来认源流、听古音、练书写、助研究，"
           "也能带观众用 VR 走进青铜器。",
           56, TEXT, iw, lh=1.58)
    y = hy0 + hh + 110

    # ══ 核心场景：博物馆四步 ══
    y = p.header(y, "見", "走进博物馆，读懂青铜铭文", "CORE SCENARIO")
    gap = 90
    cw = (CW - 3 * gap) // 4
    ch = 460
    cards = [("拍下铭文", "观众在展柜前扫码，\n拍下器物上的铭文"),
             ("拆成单字", "模型找出铭文中的每一个字，\n逐个切分"),
             ("匹配今字", "到字库中逐字匹配，\n给出对应的现代汉字"),
             ("读懂历史", "连字成句、配上白话，\n读懂铭文记载的历史")]
    for i, (head, body) in enumerate(cards):
        x = CX0 + i * (cw + gap)
        box = (x, y, x + cw, y + ch)
        p.shadow_box(box, blur=20, offset=10, alpha=55)
        p.rect(box, fill=PANEL2 if i in (0, 3) else DARK)
        if i == 0:
            p.paste(A / "hezun_rubbing.jpg", (x + 25, y + 25, x + cw - 25, y + ch - 25), mode="cover")
            p.dot(x + cw - 105, y + ch - 105, 150, CINNABAR, icon=A / "icons" / "camera_light.png")
        elif i == 1:
            p.paste(A / "story_split.png", box)
        elif i == 2:
            p.paste(A / "story_match.png", box)
        else:
            p.text((x + 55, y + 55), "余其宅兹中国，", F_TITLE, 74, INK, bold=2)
            p.text((x + 55, y + 160), "自之乂民。", F_TITLE, 74, INK, bold=2)
            p.rect((x + 55, y + 280, x + 175, y + 288), fill=GOLD)
            p.para(x + 55, y + 320, "我要定居在天下的中心，从这里治理百姓。", 48, TEXT, cw - 110, lh=1.45)
        p.dot(x - 10, y - 10, 110, CINNABAR, label=str(i + 1), label_size=60)
        if i < 3:
            p.tri(x + cw + gap / 2, y + ch / 2, 40, "right")
        p.text((x + cw / 2, y + ch + 40), head, F_TITLE, 80, INK, anchor="ma", bold=2)
        p.para(x + 20, y + ch + 150, body, 48, TEXT, cw - 40, lh=1.45, align="center")
    y += ch + 150 + 2 * 48 * 1.45 + 70

    # ══ 我们的积累：大数字（口径同 决赛讲稿-v3 第四节） ══
    y = p.header(y, "書", "我们的积累", "DATA AND MODEL")
    stats = [("58万", "张古文字字形图", "汇集 10 个字形来源"),
             ("25,285", "条自建金文数据库目录", "器名、释文、时代、著录号"),
             ("6,236", "张拓片", "逐字标注 61,268 个字框"),
             ("150余种", "拓片来源著录", "每张拓片都注明出处"),
             ("5,930", "个金文变体", "分属 1,690 个字头"),
             ("24.6万", "条音韵记录", "覆盖 7,909 个字"),
             ("242", "个百家姓见于金文", "宋本《百家姓》408 个单姓"),
             ("F1 0.803", "识读模型得分", "4 个检测器 + 7 个识别器集成")]
    sw, sh, sg = (CW - 3 * 60) // 4, 300, 60
    for i, (num, unit, note) in enumerate(stats):
        x = CX0 + (i % 4) * (sw + sg)
        yy = y + (i // 4) * (sh + 36)
        p.rect((x, yy, x + sw, yy + sh), fill=PANEL, outline=LINE, width=3)
        p.rect((x, yy, x + 14, yy + sh), fill=CINNABAR)
        nx = x + 55
        for part in _split_num(num):
            path = F_NUM if part.isascii() else F_TITLE
            sz = 130 if part.isascii() else 92
            p.text((nx, yy + 135), part, path, sz, CINNABAR, anchor="ls", bold=0 if part.isascii() else 2)
            nx += font(path, sz).getlength(part)
        p.text((x + 55, yy + 162), unit, F_BOLD, 52, INK)
        p.text((x + 55, yy + 236), note, F_BODY, 42, MUTED)
    y += 2 * sh + 36 + 80

    # ══ 更多场景：四可 + VR ══
    y = p.header(y, "樂", "更多场景：让古文字可看、可听、可写、可考", "MORE WAYS TO EXPERIENCE")
    four = [("看", "认源流", "看一个字怎样一步步\n演变成今天的样子"),
            ("听", "听古音", "听《诗经》“关关雎鸠”\n在上古的读法"),
            ("写", "练书写", "描红古文字，\n铸一句金文祝福"),
            ("考", "助研究", "模型框出拓片上的字，\n列出候选字和辞例")]
    cw4 = (CW - 3 * gap) // 4
    dd = 230
    for i, (c, head, body) in enumerate(four):
        cx = CX0 + i * (cw4 + gap) + cw4 / 2
        col = CINNABAR if i == 3 else PATINA
        d.ellipse((cx - dd / 2, y, cx + dd / 2, y + dd), fill=col)
        d.ellipse((cx - dd / 2 + 14, y + 14, cx + dd / 2 - 14, y + dd - 14), outline=PAPER, width=4)
        p.text((cx, y + dd / 2 + 5), c, F_TITLE, 140, PAPER, anchor="mm", bold=3)
        p.text((cx, y + dd + 35), head, F_TITLE, 72, INK, anchor="ma", bold=2)
        for j, l in enumerate(body.split("\n")):
            p.text((cx, y + dd + 135 + j * 66), l, F_BODY, 46, TEXT, anchor="ma")
    by = y + dd + 135 + 2 * 66 + 40
    # 看听写 = 创造性转化；考 = 创新性发展
    xa0, xa1 = CX0 + 40, CX0 + 3 * cw4 + 2 * gap - 40
    xb0, xb1 = CX0 + 3 * (cw4 + gap) + 40, CX1 - 40
    for x0, x1, col, lab in [(xa0, xa1, PATINA, "创造性转化"), (xb0, xb1, CINNABAR, "创新性发展")]:
        d.line((x0, by, x1, by), fill=col, width=6)
        d.line((x0, by - 28, x0, by), fill=col, width=6)
        d.line((x1, by - 28, x1, by), fill=col, width=6)
        mid = (x0 + x1) / 2
        lw = font(F_TITLE, 64).getlength(lab) + 80
        p.rect((mid - lw / 2, by - 42, mid + lw / 2, by + 42), fill=PANEL)
        p.text((mid, by), lab, F_TITLE, 64, col, anchor="mm", bold=1)
    y = by + 90

    # VR：化身工匠，走进何尊
    VRH = 1190
    p.rect((CX0, y, CX1, y + VRH), fill=DARK)
    p.text((CX0 + 70, y + 60), "VR", F_NUM, 96, GOLD, anchor="la")
    p.text((CX0 + 270, y + 66), "化身工匠，走进何尊", F_TITLE, 92, PAPER, anchor="la", bold=2)
    p.para(CX0 + 70, y + 200,
           "观众在博物馆看得到青铜器，却看不到铸在器内底的铭文。手机套上纸盒眼镜，坐进铸铜作坊，亲手刻铭、浇铸，再走进铸好的尊里读铭文。无需安装应用。",
           48, (226, 214, 190), CW - 140, lh=1.5)
    vr = [("vr_carve", "内范刻铭", "亲手反刻“宅兹中国”"),
          ("vr_pour", "合范浇铸", "铜液灌入范中"),
          ("vr_open", "脱范出器", "敲开外范，铜尊出范"),
          ("vr_rise", "入器读铭", "122 字从脚下升起，\n注视一字即显示今译和古音")]
    vg = 40
    vw = (CW - 140 - 3 * vg) // 4
    vh = int(vw * 608 / 1080)
    vy = y + 350
    for i, (f, head, body) in enumerate(vr):
        x = CX0 + 70 + i * (vw + vg)
        p.paste(PA / f"{f}.jpg", (x, vy, x + vw, vy + vh), mode="cover")
        d.rectangle((x, vy, x + vw, vy + vh), outline=GOLD, width=3)
        p.dot(x + 50, vy + 50, 76, CINNABAR, label=str(i + 1), label_size=42)
        p.text((x, vy + vh + 30), head, F_TITLE, 62, PAPER, bold=1)
        p.para(x, vy + vh + 115, body, 40, (206, 194, 170), vw, lh=1.4)
    p.text((CX0 + 70, y + VRH - 45), "三维模型为明尼阿波利斯美术馆 CC0 开放扫描的西周同类器；范铸过程为示意。",
           F_BODY, 36, (170, 158, 136), anchor="ls")
    y += VRH + 90

    # ══ 研究与应用成果（证书、论文、落地，参照往届海报的“实践成果”） ══
    y = p.header(y, "古", "研究与应用成果", "ACHIEVEMENTS AND APPLICATIONS")
    cg = 70
    colw = (CW - 2 * cg) // 3
    cols = [CX0 + i * (colw + cg) for i in range(3)]

    def col_head(x, t):
        tw = font(F_TITLE, 70).getlength(t)
        mid = x + colw / 2
        p.text((mid, y + 40), t, F_TITLE, 70, CINNABAR, anchor="mm", bold=2)
        for sgn in (-1, 1):
            a0 = mid + sgn * (tw / 2 + 30)
            a1 = mid + sgn * (colw / 2 - 10)
            d.line((a0, y + 40, a1, y + 40), fill=GOLD, width=4)
            d.ellipse((a1 - 9, y + 31, a1 + 9, y + 49), fill=GOLD)

    # 获奖与证书
    x = cols[0]
    col_head(x, "获奖与证书")
    iy = y + 120
    for f, lines in [("award_sais", ["第四届世界科学智能大赛", "古文字识别赛道", "二等奖"]),
                     ("award_ccl", ["CCL 2026 第二届", "古诗词赏析评测", "第三名"]),
                     ("cert_confucius", ["巴黎西岱大学孔子学院", "中文线上辅导项目", "实习证书"])]:
        img_w = 360
        b = p.paste(PA / f"{f}.jpg", (x, iy, x + img_w, iy + 400), align="top")
        d.rectangle(b, outline=LINE, width=3)
        ty = iy + 5
        for j, l in enumerate(lines):
            last = j == len(lines) - 1
            p.text((x + img_w + 36, ty), l, F_TITLE if last else F_BODY, 70 if last else 42,
                   CINNABAR if last else INK, bold=2 if last else 0)
            ty += 64
        iy = max(b[3], ty + 70) + 40

    # 学术论文
    x = cols[1]
    col_head(x, "学术论文")
    pw = (colw - 40) // 2
    papers = [("paper_lt4hala", "已发表", "LT4HALA 2026\n（LREC 2026）", "古籍 OCR 中视觉语言\n模型的多任务权衡"),
              ("paper_arr", "在审", "ACL Rolling Review\n2026 年 10 月", "字形能否为青铜器\n铭文断代")]
    for i, (f, status, venue, gist) in enumerate(papers):
        px = x + i * (pw + 40)
        b = p.paste(PA / f"{f}.jpg", (px, y + 120, px + pw, y + 120 + 620), align="top")
        d.rectangle(b, outline=LINE, width=3)
        sw2 = font(F_BOLD, 40).getlength(status) + 40
        p.rect((px, b[3] + 25, px + sw2, b[3] + 85), fill=CINNABAR if status == "已发表" else PATINA)
        p.text((px + sw2 / 2, b[3] + 55), status, F_BOLD, 40, PAPER, anchor="mm")
        p.para(px, b[3] + 110, venue, 38, MUTED, pw, lh=1.35)
        p.para(px, b[3] + 225, gist, 44, INK, pw, path=F_BOLD, lh=1.35)

    # 落地应用
    x = cols[2]
    col_head(x, "落地应用")
    apps = [("展位", "输入你的姓，铸一句金文祝福，\n领取 PDF 明信片"),
            ("小红书", "手机小工具：听古音、描红、连连看"),
            ("课堂", "15 分钟古文字入门课"),
            ("海外中文教学", "参与巴黎西岱大学孔子学院\n2025–2026 学年中文线上辅导"),
            ("离线包", "无网络环境解压即用")]
    ay = y + 120
    for head, body in apps:
        d.ellipse((x, ay + 16, x + 26, ay + 42), fill=PATINA)
        p.text((x + 50, ay), head, F_BOLD, 50, INK)
        ay = p.para(x + 50, ay + 72, body, 42, TEXT, colw - 50, lh=1.4) + 34
    end_y = max(iy, ay)

    OUT.mkdir(exist_ok=True)
    final = p.im.convert("RGB").resize(OUT_SIZE, Image.LANCZOS)
    path = OUT / f"吉金智识-决赛海报-{key}.jpg"
    final.save(path, quality=95, dpi=(72, 72), subsampling=0)
    print("wrote", path, final.size, "内容到底部 y =", int(end_y), "面板底 =", PY1)


def _split_num(s):
    """'58万' → ['58', '万']；'F1 0.803' 整段 ASCII。"""
    parts, cur = [], ""
    for ch in s:
        if cur and ch.isascii() != cur[-1].isascii():
            parts.append(cur)
            cur = ""
        cur += ch
    parts.append(cur)
    return parts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", choices=["A", "B", "both"], default="both", help="A：“中国”二字…  B：以字为桥…")
    ap.add_argument("--template", default=str(TEMPLATE))
    ap.add_argument("--prep", action="store_true", help="先重新生成 build/poster/assets/")
    a = ap.parse_args()
    if a.prep:
        prep_assets()
    for k in (["A", "B"] if a.title == "both" else [a.title]):
        build(k, a.template)
