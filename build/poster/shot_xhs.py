"""小红书小工具截图（手机竖屏），给海报“落地应用”用。

先把 xhs-minitool 分支导出并打包网页版，再截图：
    git archive xhs-minitool | tar -x -C <临时目录>
    python -I <临时目录>/xhs/build.py
    python build/poster/shot_xhs.py <临时目录>/xhs/dist/web
输出 build/poster/assets/xhs_*.png
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

WEB = Path(sys.argv[1]).resolve()
OUT = Path(__file__).resolve().parent / "assets"


def main():
    url = WEB.joinpath("index.html").as_uri()
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge")
        pg = b.new_page(viewport={"width": 390, "height": 760}, device_scale_factor=3)
        pg.goto(url)
        pg.wait_for_timeout(800)
        # 姓氏墙：查“周”
        pg.click("button.game[data-go=name]")
        pg.fill("#nameInput", "周")
        pg.click("#nameForm button[type=submit]")
        pg.wait_for_timeout(800)
        pg.screenshot(path=OUT / "xhs_name.png")
        # 听音室：今日挑战，选一项看反馈
        pg.click("#v-name .back")
        pg.click("button.game[data-go=listen]")
        pg.wait_for_timeout(500)
        pg.click("#choices button >> nth=0")
        pg.wait_for_timeout(600)
        pg.screenshot(path=OUT / "xhs_listen.png")
        # 连连看
        pg.click("#v-listen .back")
        pg.click("button.game[data-go=match]")
        pg.wait_for_timeout(600)
        pg.screenshot(path=OUT / "xhs_match.png")
        b.close()
    print("ok", sorted(p.name for p in OUT.glob("xhs_*.png")))


if __name__ == "__main__":
    main()
