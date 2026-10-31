"""
把 fonts.loli.net 的 Noto Sans/Serif TC + Source Sans/Serif 下载到 assets/fonts/web/，
生成离线可用的 assets/fonts/web/fonts.css（unicode-range 分片，按需加载）。

用法:  python build/vendor_fonts.py
"""
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "fonts" / "web"
CSS_URL = (
    "https://fonts.loli.net/css2?family=Noto+Sans+TC:wght@400;500"
    "&family=Noto+Serif+TC:wght@400;600;700&family=Source+Sans+3:wght@400;500"
    "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap"
)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def local_name(url: str) -> str:
    # .../s/notosanstc/v40/<hash>.12.woff2 -> notosanstc-v40-<hash>.12.woff2
    parts = url.split("/s/", 1)[1].split("/")
    return "-".join(parts)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    css = get(CSS_URL).decode("utf-8")
    urls = sorted(set(re.findall(r"url\((https://[^)]+\.woff2)\)", css)))
    print(f"{len(urls)} font files")

    def fetch(u):
        dst = OUT / local_name(u)
        if dst.exists() and dst.stat().st_size > 0:
            return 0
        for _ in range(3):
            try:
                dst.write_bytes(get(u))
                return 1
            except Exception as e:
                err = e
        print("FAIL", u, err, file=sys.stderr)
        return -1

    with ThreadPoolExecutor(16) as ex:
        res = list(ex.map(fetch, urls))
    if -1 in res:
        sys.exit(1)
    for u in urls:
        css = css.replace(u, local_name(u))
    (OUT / "fonts.css").write_text(css, encoding="utf-8")
    total = sum(p.stat().st_size for p in OUT.glob("*.woff2"))
    print(f"ok, {total / 1e6:.1f} MB -> {OUT}")


if __name__ == "__main__":
    main()
