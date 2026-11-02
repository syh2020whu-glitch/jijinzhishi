"""决赛 PPT 用的网站截图。先起 serve.py（8080），再跑：python build/ppt/shots.py"""
import base64
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080/demo.html"
OUT = Path(__file__).parent / "assets" / "shots"
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name, wait=1500):
    page.wait_for_timeout(wait)
    page.screenshot(path=str(OUT / f"{name}.png"))
    print("saved", name)


def go(page, hash_, wait=2500):
    page.goto(BASE + hash_)
    page.wait_for_timeout(wait)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    ctx = browser.new_context(viewport={"width": 1600, "height": 900}, device_scale_factor=1.2)
    page = ctx.new_page()

    go(page, "#/", 9000)
    shot(page, "home", 500)

    go(page, "#/learn?tab=wall&q=周", 4000)
    shot(page, "wall_zhou")

    go(page, "#/learn?tab=listen", 3000)
    shot(page, "listen")

    go(page, "#/learn?tab=lookup&q=中", 3000)
    shot(page, "lookup_zhong")

    go(page, "#/play?tab=match", 3000)
    shot(page, "match")

    go(page, "#/play?tab=trace", 3000)
    shot(page, "trace")

    # 铸辞坊：选鼎 → 默认推荐字 → 铸辞 → 明信片
    go(page, "#/play?tab=ritual", 3000)
    shot(page, "ritual_step1")
    page.click("#ritualNext1")
    page.wait_for_timeout(1200)
    recs = page.locator("#blessFamilies button.rec")
    for i in range(min(2, recs.count())):
        recs.nth(i).click()
        page.wait_for_timeout(200)
    page.click("#blessBtn")
    page.wait_for_timeout(4000)
    shot(page, "ritual_card")
    data = page.evaluate("window._lastPostcard ? window._lastPostcard.toDataURL('image/png') : ''")
    if data:
        (OUT / "postcard.png").write_bytes(base64.b64decode(data.split(",", 1)[1]))
        print("saved postcard")

    # 识图：案例墙 → 第一张案例 → 选一个灰框看释读辅助
    go(page, "#/work?tab=rec", 4000)
    shot(page, "rec_wall")
    card = page.locator("[data-case]", has_text="㝅伯鼎")
    (card.first if card.count() else page.locator("[data-case]").first).click()
    page.wait_for_timeout(5000)
    shot(page, "rec_case")
    gray = page.locator(".ocr-box-item:has(.gray-dot) .gray-dot")
    if gray.count():
        gray.first.click()
        page.wait_for_timeout(2500)
        shot(page, "rec_assist")

    browser.close()
