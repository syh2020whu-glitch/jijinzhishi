"""决赛现场展示海报：套组委会模板（竖版 800×1800 mm），出 72 dpi jpg（2268×5102）。

python build/poster/make_poster.py                  # 定稿：B 版（以字为桥，连起三千年）
python build/poster/make_poster.py --title both     # A、B 两个主标题方案各出一张
python build/poster/make_poster.py --prep          # 重新生成 build/poster/assets/（证明材料脱敏图 + VR 截图）

模板 jpg 不入库，默认读仓库根目录的“文化中国”总决赛现场展示海报设计模板.jpg（4724×10628，150 dpi）。
版面在模板原尺寸上排，最后缩到 72 dpi。配色、字体、素材与 build/ppt 同一套。
全稿不放本队校名、人名；文案统称“古文字”，不突出金文，也不拿它和其他古文字比较。
"""
import argparse
import re
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
    """按宽度折行：中文逐字、英文按词，标点不放行首。"""
    lines = []
    for para in text.split("\n"):
        cur = ""
        # 数字/英文词连同后面紧跟的一个汉字算一段（“15 分”“58 万”不拆行）
        for tok in re.findall(r"[A-Za-z0-9.,:;?!'’–@()\-]+ ?[一-鿿]?|.", para):
            if cur and f.getlength((cur + tok).rstrip()) > max_w and tok[0] not in NO_LINE_START:
                lines.append(cur.rstrip())
                cur = tok.lstrip()
            else:
                cur += tok
        lines.append(cur.rstrip())
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

# ── 仿往届海报的绿色系（与模板青绿呼应），朱砂只用在印章和少量强调 ──
G_DARK = (38, 84, 58)        # 小节标题、竖签
G_MID = (86, 140, 98)
G_LIGHT = (214, 232, 206)
G_HL = (226, 232, 128)       # 标题下的黄绿高光（样本里的荧光笔效果）
F_BRUSH = FONTS + "STXINGKA.TTF"   # 华文行楷：主标题、小节标题、口号
F_SONG = FONTS + "STSONG.TTF"      # 华文宋体：正文
NUMS = "壹贰叁肆伍"


def prep_assets():
    """从证明材料、VR 分支截图生成 build/poster/assets/。一般不用重跑，素材已入库。
    小红书截图另见 shot_xhs.py；课堂照片放 assets/class_1.jpg 即可自动替换占位框。"""
    import subprocess
    from io import BytesIO
    PA.mkdir(exist_ok=True)
    # VR 截图（1920×1080）：取中间 1440×810，去掉四周空黑
    for key, n in [("vr_carve", "03-carve"), ("vr_pour", "05-pour"), ("vr_open", "06-open"), ("vr_rise", "08-rise")]:
        raw = subprocess.run(["git", "show", f"{VR_BRANCH}:build/vr-slide/out/{n}.png"], cwd=REPO, capture_output=True, check=True).stdout
        Image.open(BytesIO(raw)).convert("RGB").crop((240, 100, 1680, 910)).resize((1080, 608), Image.LANCZOS).save(PA / f"{key}.jpg", quality=90)
    # 论文首页整页：作者栏已涂掉 / 本是匿名稿（第三篇直接从投稿 PDF 渲染）
    for key, src in [("paper_p1_published", "paper_lt4hala2026_p1_anon.png"), ("paper_p1_glyph", "paper_arr2026-10_p1.png")]:
        c = Image.open(PROOF / src).convert("RGB")
        c.resize((800, round(800 * c.height / c.width)), Image.LANCZOS).save(PA / f"{key}.jpg", quality=90)
    import pymupdf
    pdf = Path.home() / "Desktop" / "When the Answer Key Is Online - Reference Retrievability and Metric Validity in Classical Chinese Poetry Evaluation" / "01_paper" / "paper.pdf"
    pix = pymupdf.open(pdf)[0].get_pixmap(dpi=150)
    c = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    c.resize((800, round(800 * c.height / c.width)), Image.LANCZOS).save(PA / "paper_p1_poetry.jpg", quality=90)
    # VR 看器页四件扫描器物 + 透视截图见 shot_vessels.py；文创样图见 make_wenchuang.py
    print("prepared", sorted(f.name for f in PA.iterdir()))


def cloud(d, cx, cy, s, color, flip=False):
    """简笔祥云：一大一小两个回旋，样本里小标题两侧的纹样。"""
    import math
    k = -1 if flip else 1
    for r0, ox, oy in [(s, 0, 0), (s * 0.6, s * 1.25, s * 0.35)]:
        pts = []
        for t in range(0, 300):
            th = t / 300 * 2.2 * math.pi
            r = r0 * (1 - th / (2.6 * math.pi))
            pts.append((cx + k * (ox + r * math.cos(th)), cy + oy - r * math.sin(th)))
        d.line(pts, fill=color, width=max(3, int(s / 9)), joint="curve")
    d.line((cx - k * s * 0.2, cy + s, cx + k * s * 3.6, cy + s), fill=color, width=max(3, int(s / 9)))


def build(key, template):
    p = Poster(template)
    d = p.d

    # ── 模板上的“参赛队伍名称：”后面填队名，同一行右侧补赛题（同色同字号） ──
    p.text((1385, 2691), "吉金智识", F_TITLE, 150, NAVY, anchor="lm", bold=2)
    p.text((2560, 2691), "所属赛题：赛题五 开放赛题", F_TITLE, 112, NAVY, anchor="lm", bold=1)

    # ── 内容面板：半透明浅绿白圆角大板（同往届海报），底部露出模板山水 ──
    PY0, PY1 = 2900, 10250
    p.shadow_box((PX0, PY0, PX1, PY1), radius=80, blur=40, offset=16, alpha=60)
    panel = Image.new("RGBA", p.im.size, (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle((PX0, PY0, PX1, PY1), radius=80, fill=(246, 251, 244, 226))
    p.im.alpha_composite(panel)
    d.rounded_rectangle((PX0 + 28, PY0 + 28, PX1 - 28, PY1 - 28), radius=60, outline=(196, 222, 190), width=4)

    def hl(x0, y0, x1):
        """标题下的黄绿高光条。"""
        p.rect((x0, y0, x1, y0 + 34), fill=G_HL)

    def section(y, title, pinyin):
        """样本式小节标题：行楷大字 + 拼音 + 一条通到右边的细线。"""
        tw = font(F_BRUSH, 128).getlength(title)
        hl(CX0 - 10, y + 104, CX0 + tw * 0.55)
        p.text((CX0, y), title, F_BRUSH, 128, G_DARK, bold=1)
        px = CX0 + tw + 60
        p.text((px, y + 98), pinyin, F_NUM, 60, G_DARK, anchor="ls", spacing=4)
        pw = font(F_NUM, 60).getlength(pinyin) + 4 * len(pinyin)
        d.line((px, y + 118, CX1, y + 118), fill=G_DARK, width=5)
        d.line((px + pw + 30, y + 98 - 22, CX1, y + 98 - 22), fill=G_MID, width=2)
        return y + 190

    # ══ 主标题（行楷，后半句绿色，句末印章） ══
    y = 3040
    head, tail = {"A": ("“中国”二字，", "最早写在这件青铜器上"), "B": ("以字为桥，", "连起三千年")}[key]
    size = 196 if key == "A" else 250
    fh = font(F_BRUSH, size)
    tw = fh.getlength(head + tail)
    seal = 170
    tx = (W - tw - seal - 50) / 2
    cy = y + 125
    p.text((tx, cy), head, F_BRUSH, size, INK, anchor="lm", bold=2)
    p.text((tx + fh.getlength(head), cy), tail, F_BRUSH, size, G_DARK, anchor="lm", bold=2)
    p.paste(A / "seal_中.png", (int(tx + tw + 50), int(cy - seal / 2), int(tx + tw + 50 + seal), int(cy + seal / 2)))
    y += 270
    p.text((W / 2, y), "吉金智识　古文字数字化传承与互动体验平台", F_TITLE, 92, CINNABAR, anchor="ma", bold=1, spacing=8)
    y += 92 + 100

    # ══ 项目简介 ══
    y = section(y, "项目简介", "XIANGMU JIANJIE")
    hy0, hh = y, 700
    p.paste(A / "hezun_vessel.png", (CX0, hy0, CX0 + 660, hy0 + hh))
    rx0 = CX0 + 690
    rw = int(hh * 1000 / 932)
    rb = p.paste(A / "hezun_rubbing.jpg", (rx0, hy0, rx0 + rw, hy0 + hh))
    k = rw / 1000
    bx, by, bw, bh = rb[0] + 405 * k, rb[1] + 180 * k, 110 * k, 235 * k
    d.rectangle((bx, by, bx + bw, by + bh), outline=CINNABAR, width=9)
    zx0 = rx0 + rw + 100
    zw = int(hh * 0.86 * 330 / 705)
    zb = (zx0, hy0, zx0 + zw, hy0 + int(hh * 0.86))
    p.dashed_line((bx + bw, by), (zb[0], zb[1]), CINNABAR, 4)
    p.dashed_line((bx + bw, by + bh), (zb[0], zb[3]), CINNABAR, 4)
    p.paste(A / "hezun_zhongguo.png", zb, mode="cover")
    d.rectangle(zb, outline=CINNABAR, width=9)
    p.text(((zb[0] + zb[2]) / 2, zb[3] + 12), "中或", F_TITLE, 76, CINNABAR, anchor="ma", bold=2)
    p.para(CX0, hy0 + hh + 22, "何尊（西周早期），铭文“宅兹中或”是“中国”一词目前所见最早的文字记录", 44, MUTED, zb[2] - CX0 + 300)
    ix0 = zb[2] + 110
    p.para(ix0, hy0 + 10,
           "吉金智识以字为桥，致力于古文字的数字化普及与传承。项目汇集 10 类来源的 58 万张古文字字形，"
           "自建 2.5 万条铭文数据库目录；基于 DINOv3 视觉大模型，集成 4 个检测器与 7 个识别器，"
           "在 6,236 张真实拓片上训练古文字识读模型，实现拓片自动框字、逐字释读。在此基础上，开设古文字入门课程；"
           "线上打造可看、可听、可写、可考的互动体验平台，借助三维扫描与 VR 再现“铸铭入尊”，以科技赋能文脉传承。",
           54, TEXT, CX1 - ix0, path=F_SONG, lh=1.58)
    y = hy0 + hh + 120

    # ══ 口号（两侧祥云） ══
    slogan = "让书写在青铜器上的文字活起来"
    sw_ = font(F_BRUSH, 120).getlength(slogan)
    p.text((W / 2, y + 60), slogan, F_BRUSH, 120, G_DARK, anchor="mm", bold=1)
    cloud(d, W / 2 - sw_ / 2 - 120, y + 50, 36, G_MID, flip=True)
    cloud(d, W / 2 + sw_ / 2 + 120, y + 50, 36, G_MID)
    y += 200

    # ══ 体验体系：四格，左侧竖签（仿样本“理念/技术/方法/模式创新”） ══
    y = section(y, "体验体系", "TIYAN TIXI")
    gx, gy = 70, 60
    cw = (CW - gx) // 2
    chh = 1300
    lab_w = 130

    def cell(ix, iy, label, heading):
        x0 = CX0 + ix * (cw + gx)
        y0 = y + iy * (chh + gy)
        # 竖签：深绿底、浅色内框、竖排四字
        p.rect((x0, y0 + 60, x0 + lab_w, y0 + 60 + 560), fill=G_DARK, radius=18)
        d.rounded_rectangle((x0 + 12, y0 + 72, x0 + lab_w - 12, y0 + 60 + 548), radius=12, outline=G_LIGHT, width=3)
        for j, ch in enumerate(label):
            p.text((x0 + lab_w / 2, y0 + 130 + j * 125), ch, F_BRUSH, 96, PAPER, anchor="mm")
        cx0 = x0 + lab_w + 50
        cwid = cw - lab_w - 50
        p.text((cx0 + cwid / 2, y0 + 10), heading, F_TITLE, 66, G_DARK, anchor="ma", bold=1, spacing=4)
        return cx0, y0 + 120, cwid

    # 1 核心场景：博物馆四步
    cx0, cy0, cwid = cell(0, 0, "核心场景", "走进博物馆，读懂青铜铭文")
    sw4 = (cwid - 3 * 30) // 4
    steps = [("拍下铭文", None), ("框出单字", "story_split.png"), ("逐字释读", "story_match.png"), ("读懂历史", None)]
    for i, (lab, img) in enumerate(steps):
        x = cx0 + i * (sw4 + 30)
        box = (x, cy0, x + sw4, cy0 + 760)
        p.rect(box, fill=DARK if img else PANEL2)
        if i == 0:
            # 博物馆实拍：观众隔着展柜举手机拍器物；横图里取以拍照者和展柜为中心的竖条
            mus = Image.open(PA / "museum_visitors.jpg")
            cw_ = int(mus.height * sw4 / 760)
            mx0 = max(0, min(mus.width - cw_, 900 - cw_ // 2))
            p.paste(mus.crop((mx0, 0, mx0 + cw_, mus.height)), box, mode="cover")
        elif img:
            p.paste(A / img, box)
        else:
            for j, l in enumerate(["余其宅", "兹中国，", "自之乂民。"]):
                p.text((x + 30, cy0 + 40 + j * 90), l, F_TITLE, 64, INK, bold=1)
            p.rect((x + 30, cy0 + 330, x + 130, cy0 + 337), fill=GOLD)
            p.para(x + 30, cy0 + 365, "我要定居在天下的中心，从这里治理百姓。", 40, TEXT, sw4 - 50, lh=1.4)
        p.dot(x + 6, cy0 + 6, 80, G_DARK, label=str(i + 1), label_size=44)
        p.text((x + sw4 / 2, cy0 + 795), lab, F_TITLE, 62, INK, anchor="ma", bold=1)
    p.para(cx0, cy0 + 920, "观众在展柜前拍摄铭文，检测模型定位每个单字，识别模型逐字给出释文及候选，连缀成句并附白话译文。",
           44, TEXT, cwid, path=F_SONG, lh=1.5)

    # 2 资料与模型：六个大数字
    cx0, cy0, cwid = cell(1, 0, "资料模型", "汇集整理资料，训练识读模型")
    stats = [("58万", "张古文字字形图"), ("25,285", "条自建铭文数据库目录"), ("6,236", "张拓片"),
             ("61,268", "个逐字标注的字框"), ("150余种", "拓片来源著录"), ("5,930", "个字形变体"),
             ("24.6万", "条音韵记录"), ("4,114", "类古文字"), ("F1 0.803", "单字识别（公开评测）")]
    sw3 = (cwid - 2 * 30) // 3
    for i, (num, unit) in enumerate(stats):
        x = cx0 + (i % 3) * (sw3 + 30)
        yy = cy0 + (i // 3) * 300
        p.rect((x, yy, x + sw3, yy + 270), fill=(255, 255, 255), outline=G_LIGHT, width=4)
        p.rect((x, yy, x + sw3, yy + 12), fill=G_MID)
        nx = x + (sw3 - sum(font(F_NUM if s.isascii() else F_TITLE, 104 if s.isascii() else 74).getlength(s) for s in _split_num(num))) / 2
        for part in _split_num(num):
            path = F_NUM if part.isascii() else F_TITLE
            sz = 104 if part.isascii() else 74
            p.text((nx, yy + 140), part, path, sz, G_DARK, anchor="ls", bold=0 if part.isascii() else 2)
            nx += font(path, sz).getlength(part)
        p.para(x + 20, yy + 175, unit, 40, TEXT, sw3 - 40, lh=1.3, align="center")
    p.para(cx0, cy0 + 920, "每个字形、每张拓片都注明出处；识读模型由 4 个检测器、7 个识别器集成，给出初稿，最终由专家审定。",
           44, TEXT, cwid, path=F_SONG, lh=1.5)

    # 3 四可体验
    cx0, cy0, cwid = cell(0, 1, "四可体验", "让古文字可看、可听、可写、可考")
    four = [("看", "认源流", "梳理字形源流，\n呈现演变脉络"), ("听", "听古音", "聆听上古读音，\n依据学界构拟"),
            ("写", "练书写", "描红书写古文字，\n集字生成吉语"), ("考", "助研究", "自动框字释读，\n提供候选与辞例")]
    q = cwid / 4
    for i, (c, head, body) in enumerate(four):
        mx = cx0 + q * i + q / 2
        col = CINNABAR if i == 3 else G_MID
        d.ellipse((mx - 150, cy0 + 30, mx + 150, cy0 + 330), fill=col)
        d.ellipse((mx - 132, cy0 + 48, mx + 132, cy0 + 312), outline=PAPER, width=5)
        p.text((mx, cy0 + 184), c, F_BRUSH, 200, PAPER, anchor="mm")
        p.text((mx, cy0 + 380), head, F_TITLE, 68, INK, anchor="ma", bold=1)
        for j, l in enumerate(body.split("\n")):
            p.text((mx, cy0 + 490 + j * 66), l, F_BODY, 46, TEXT, anchor="ma")
    by = cy0 + 720
    for x0, x1, col, lab in [(cx0 + 20, cx0 + 3 * q - 20, G_MID, "创造性转化"), (cx0 + 3 * q + 20, cx0 + cwid - 20, CINNABAR, "创新性发展")]:
        d.line((x0, by, x1, by), fill=col, width=6)
        d.line((x0, by - 26, x0, by), fill=col, width=6)
        d.line((x1, by - 26, x1, by), fill=col, width=6)
        lw = font(F_TITLE, 56).getlength(lab) + 60
        p.rect(((x0 + x1) / 2 - lw / 2, by - 38, (x0 + x1) / 2 + lw / 2, by + 38), fill=(246, 251, 244))
        p.text(((x0 + x1) / 2, by), lab, F_TITLE, 56, col, anchor="mm", bold=1)
    p.para(cx0, cy0 + 840, "看、听、写将古文字转化为可感知、可参与的体验；考将识读模型用于研究，辅助整篇拓片释读。",
           44, TEXT, cwid, path=F_SONG, lh=1.5)

    # 4 沉浸体验：VR
    cx0, cy0, cwid = cell(1, 1, "沉浸体验", "VR：化身工匠，走进青铜器")
    g = 24
    qw = (cwid - 3 * g) // 4
    for i, (f, lab) in enumerate([("zun", "尊"), ("ding", "鼎"), ("gui", "簋"), ("gu", "觚")]):
        x = cx0 + i * (qw + g)
        p.paste(PA / f"vessel_{f}.jpg", (x, cy0, x + qw, cy0 + qw), mode="cover")
        p.text((x + 26, cy0 + 20), lab, F_TITLE, 64, PAPER, bold=1)
    p.rect((cx0, cy0 + qw - 64, cx0 + cwid, cy0 + qw), fill=(30, 26, 20))
    p.text((cx0 + 26, cy0 + qw - 32), "看器：真实三维扫描，支持旋转观察与 AR 桌面展示", F_TITLE, 42, PAPER, anchor="lm", bold=1)
    th8 = int(qw * 0.52)
    ry = cy0 + qw + g
    cast = [("vr_model", "制模"), ("vr_outer", "翻范"), ("vr_carve", "刻铭"), ("vr_close", "合范"),
            ("vr_pour", "浇铸"), ("vr_open", "脱范"), ("vessel_xray", "入器"), ("vr_rise", "读铭")]
    for i, (f, lab) in enumerate(cast):
        x = cx0 + (i % 4) * (qw + g)
        yy = ry + (i // 4) * (th8 + 20)
        p.paste(PA / f"{f}.jpg", (x, yy, x + qw, yy + th8), mode="cover")
        p.dot(x + 40, yy + 40, 60, G_DARK, label=str(i + 1), label_size=34)
        p.rect((x, yy + th8 - 56, x + qw, yy + th8), fill=(30, 26, 20))
        p.text((x + qw / 2, yy + th8 - 28), lab, F_TITLE, 42, PAPER, anchor="mm", bold=1)
        if i % 4 < 3:
            p.tri(x + qw + g / 2, yy + th8 / 2, 18, "right")
    p.para(cx0, ry + 2 * th8 + 50,
           "借助 VR 眼镜进入铸铜作坊，依范铸法亲手完成一件青铜器：塑制器模，翻制外范，于内范反刻铭文，"
           "合范浇注铜液，冷却后脱范出器；随后进入器内，铭文环绕升起，注视单字即显示今译与上古音。",
           42, TEXT, cwid, path=F_SONG, lh=1.5)
    y += 2 * chh + gy + 70

    # ══ 实践成果：三栏，祥云小标题 + 壹贰叁 ══
    y = section(y, "实践成果", "SHIJIAN CHENGGUO")
    cg = 60
    colw = (CW - 2 * cg) // 3
    cols = [CX0 + i * (colw + cg) for i in range(3)]

    def col_head(x, t):
        mid = x + colw / 2
        tw_ = font(F_BRUSH, 96).getlength(t)
        p.text((mid, y + 50), t, F_BRUSH, 96, G_DARK, anchor="mm")
        cloud(d, mid - tw_ / 2 - 80, y + 40, 26, G_MID, flip=True)
        cloud(d, mid + tw_ / 2 + 80, y + 40, 26, G_MID)
        return y + 150

    def item(x, yy, n, head, body=None):
        d.ellipse((x, yy, x + 96, yy + 96), fill=G_DARK)
        d.ellipse((x + 8, yy + 8, x + 88, yy + 88), outline=G_LIGHT, width=3)
        p.text((x + 48, yy + 50), NUMS[n], F_BRUSH, 60, PAPER, anchor="mm")
        p.text((x + 125, yy + 4), head, F_TITLE, 54, INK, bold=1)
        ny = yy + 80
        if body:
            ny = p.para(x + 125, yy + 82, body, 40, TEXT, colw - 125, lh=1.4)
        return max(ny, yy + 100) + 20

    def fan(x, y0, w, h, keys):
        """几张论文首页扇形错落：两侧略旋转、压在中间一张下面。"""
        ph_ = int(h * 0.86)            # 页高约占区域的 86%，留出旋转后的余量
        pw_ = int(ph_ / 1.414)         # A4 比例
        cxm = x + w / 2
        spec = [(-1, 8), (1, -8), (0, 0)]   # (水平偏移方向, 旋转角)；最后画中间那张，压在上面
        order = [keys[0], keys[2], keys[1]]
        for (dx, ang), k in zip(spec, order):
            pg_ = Image.open(PA / f"{k}.jpg").convert("RGBA").resize((pw_, ph_), Image.LANCZOS)
            fr = Image.new("RGBA", (pw_ + 12, ph_ + 12), (205, 220, 200, 255))
            fr.alpha_composite(pg_, (6, 6))
            rot = fr.rotate(ang, expand=True, resample=Image.BICUBIC)
            cx_ = cxm + dx * w * 0.27
            cy_ = y0 + h / 2 + (30 if dx else 0)
            p.shadow_box((int(cx_ - pw_ / 2), int(cy_ - ph_ / 2), int(cx_ + pw_ / 2), int(cy_ + ph_ / 2)), blur=18, offset=10, alpha=55)
            p.im.alpha_composite(rot, (int(cx_ - rot.width / 2), int(cy_ - rot.height / 2)))

    def photo_or_slot(box, path, label):
        if path.exists():
            p.paste(path, box, mode="cover")
            d.rectangle(box, outline=G_LIGHT, width=3)
        else:   # 课堂照片还没拍：先留虚线框
            p.rect(box, fill=(234, 242, 230))
            x0, y0, x1, y1 = box
            for t in range(0, int(x1 - x0), 50):
                d.line((x0 + t, y0, min(x0 + t + 26, x1), y0), fill=G_MID, width=4)
                d.line((x0 + t, y1, min(x0 + t + 26, x1), y1), fill=G_MID, width=4)
            for t in range(0, int(y1 - y0), 50):
                d.line((x0, y0 + t, x0, min(y0 + t + 26, y1)), fill=G_MID, width=4)
                d.line((x1, y0 + t, x1, min(y0 + t + 26, y1)), fill=G_MID, width=4)
            p.text(((x0 + x1) / 2, (y0 + y1) / 2), label, F_BODY, 40, G_MID, anchor="mm")

    # 教学成果
    x = cols[0]
    yy = col_head(x, "互动教学")
    yy = item(x, yy, 0, "课堂教学", "辅助《古代汉语》《说文解字》等核心课程开展智慧化教学")
    photo_or_slot((x, yy, x + colw, yy + 660), PA / "class_1.jpg", "课堂照片待补")   # 一张课堂照片
    yy += 700
    yy = item(x, yy, 1, "海外中文教学", "参与巴黎西岱大学孔子学院 2025–2026 学年中文线上辅导")
    yy = item(x, yy, 2, "博物馆推广", "进入博物馆展厅推广，观众可在展柜前以手机识读铭文；正与多家博物馆洽谈合作")
    # 博物馆实拍：两位观众对着展柜举手机；取中间一条，留住手机和器物
    mp = Image.open(PA / "museum_promo.jpg")
    mb = p.paste(mp.crop((0, int(mp.height * 0.17), mp.width, int(mp.height * 0.83))), (x + 125, yy - 10, x + colw, yy + 560), mode="cover")
    d.rectangle(mb, outline=G_LIGHT, width=3)
    yy = mb[3] + 30
    yy = item(x, yy, 3, "展位体验", "输入姓氏，集字生成吉语祝福，获取 PDF 明信片")
    end_y = yy

    # 研发成果
    x = cols[1]
    yy = col_head(x, "研究进展")
    yy = item(x, yy, 0, "学术论文", "已发表 1 篇，在投 3 篇")
    fan_h = 720
    fan(x, yy, colw, fan_h, ["paper_p1_glyph", "paper_p1_published", "paper_p1_poetry"])
    yy += fan_h + 30
    papers = [("已发表", CINNABAR, "LT4HALA 2026 @ LREC 2026",
               "Multi-Task Learning Trade-offs in Vision–Language Models for Ancient Chinese OCR"),
              ("在投", G_MID, None, "Does Glyph Form Date Chinese Bronze Inscriptions? Controlling for Lexicon and Medium"),
              ("在投", G_MID, None, "When the Answer Key Is Online: Reference Retrievability and Metric Validity in Classical Chinese Poetry Evaluation"),
              ("在投", G_MID, None, "Learning to Read Bronze Inscriptions from Catalogue Transcriptions")]
    for status, col, venue, title in papers:
        stw = font(F_BOLD, 36).getlength(status) + 32
        p.rect((x, yy + 4, x + stw, yy + 58), fill=col)
        p.text((x + stw / 2, yy + 31), status, F_BOLD, 36, PAPER, anchor="mm")
        if venue:
            p.text((x + stw + 20, yy + 31), venue, F_NUM, 38, G_DARK, anchor="lm")
            yy = p.para(x, yy + 76, title, 38, TEXT, colw, path=F_EN, lh=1.3) + 22
        else:
            yy = p.para(x + stw + 20, yy + 6, title, 38, TEXT, colw - stw - 20, path=F_EN, lh=1.3) + 22
    yy += 10
    yy = item(x, yy, 1, "技术评测", "识读与古籍理解技术经多项国际公开评测验证")
    # 流程：拓片 → 检测 → 识别 → 释文
    fg_ = 44
    bw_ = (colw - 3 * fg_) / 4
    flow = [("拓片", "整篇输入", G_LIGHT, G_DARK), ("检测", "4 模型融合", G_MID, PAPER),
            ("识别", "7 模型集成", G_DARK, PAPER), ("释文", "专家审定", CINNABAR, PAPER)]
    for i, (t1, t2, bg_, fc_) in enumerate(flow):
        bx = x + i * (bw_ + fg_)
        p.rect((bx, yy, bx + bw_, yy + 170), fill=bg_, radius=20)
        p.text((bx + bw_ / 2, yy + 58), t1, F_TITLE, 52, fc_, anchor="mm", bold=1)
        p.text((bx + bw_ / 2, yy + 122), t2, F_BODY, 34, fc_, anchor="mm")
        if i < 3:
            p.tri(bx + bw_ + fg_ / 2, yy + 85, 22, "right")
    yy += 200
    # 大号 F1
    p.rect((x, yy, x + colw, yy + 250), fill=(255, 255, 255), outline=G_LIGHT, width=4, radius=20)
    p.text((x + 50, yy + 168), "F1", F_NUM, 70, G_MID, anchor="ls")
    p.text((x + 150, yy + 180), "0.803", F_NUM, 150, G_DARK, anchor="ls")
    tx_ = x + 150 + font(F_NUM, 150).getlength("0.803") + 40
    for j, l in enumerate(["真实拓片单字识别", "字框和释文同时正确才计分", "基于 DINOv3 视觉大模型"]):
        p.text((tx_, yy + 62 + j * 58), l, F_BODY if j else F_BOLD, 36, TEXT if j else G_DARK, anchor="lm")
    b = (x, yy, x + colw, yy + 250)
    end_y = max(end_y, b[3])

    # 宣传成果
    x = cols[2]
    yy = col_head(x, "推广成效")
    yy = item(x, yy, 0, "多平台推广", "在小红书等平台上线互动小工具，嵌入笔记即点即用；支持每日挑战与成绩卡分享，累计浏览量逾 1 万次")
    sw_ph = (colw - 2 * 24) // 3
    for i, f in enumerate(["xhs_name", "xhs_listen", "xhs_match"]):
        bx0 = x + i * (sw_ph + 24)
        b = p.paste(PA / f"{f}.png", (bx0, yy, bx0 + sw_ph, yy + int(sw_ph * 760 / 390)), mode="cover")
        d.rounded_rectangle((b[0] - 4, b[1] - 4, b[2] + 4, b[3] + 4), radius=18, outline=DARK, width=6)
    yy = b[3] + 50
    yy = item(x, yy, 1, "文创设计", "姓氏明信片、书签、帆布袋、印章贴纸、徽章")
    rh = 560
    row = [(A / "postcard_shadow_light.png", 0.25), (PA / "wc_bookmark1.png", 0.15), (PA / "wc_bookmark2.png", 0.15), (PA / "wc_tote.png", 0.45)]
    rx = x
    for f, frac in row:
        b = p.paste(f, (rx, yy, rx + colw * frac, yy + rh), align="top")
        rx += colw * frac
    yy += rh + 10
    b1 = p.paste(PA / "wc_stickers.png", (x, yy, x + colw * 0.55, yy + 380), align="top")
    b2 = p.paste(PA / "wc_badges.png", (x + colw * 0.55, yy, x + colw, yy + 380), align="top")
    end_y = max(end_y, b1[3], b2[3])

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
    ap.add_argument("--title", choices=["A", "B", "both"], default="B", help="A：“中国”二字…  B：以字为桥…")
    ap.add_argument("--template", default=str(TEMPLATE))
    ap.add_argument("--prep", action="store_true", help="先重新生成 build/poster/assets/")
    a = ap.parse_args()
    if a.prep:
        prep_assets()
    for k in (["A", "B"] if a.title == "both" else [a.title]):
        build(k, a.template)
