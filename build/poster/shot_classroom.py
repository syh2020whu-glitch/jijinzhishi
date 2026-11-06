"""古文字课堂（课后自练小程序）“闯关”页截图，给海报“课堂教学”用。

    python build/poster/shot_classroom.py <classroom 目录>
页面是 file:// 直接打开的离线 html，不用起服务。
输出 build/poster/assets/class_app.jpg：顶栏 + 闯关单元格，裁成约 2.2:1 的横幅。
"""
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

APP = Path(sys.argv[1]).resolve() / "古文字课堂.html"
OUT = Path(__file__).resolve().parent / "assets"


def main():
    tmp = OUT / "_class_units.png"
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge")
        pg = b.new_page(viewport={"width": 1280, "height": 860}, device_scale_factor=2)
        pg.goto(APP.as_uri())
        pg.wait_for_timeout(1200)
        pg.click("#tabs button[data-view=units]")
        pg.wait_for_timeout(900)
        pg.screenshot(path=tmp)
        b.close()
    im = Image.open(tmp).convert("RGB")
    im.crop((0, 0, im.width, int(im.width / 2.2))).save(OUT / "class_app.jpg", quality=90)
    tmp.unlink()
    print("ok", OUT / "class_app.jpg")


if __name__ == "__main__":
    main()
