"""
把 darkscope 金文字庫的真拓片缩略图预拉到本地，供断网时「變體檢索」使用。

字集 = demo.html 里的百家姓、简繁对照、姓氏故事/连连看/祝福/字典标签/描红等字 + 上古音种子字。
每个来源最多存 CAP 张，输出:
  assets/thumbs/<src>/<U+XXXX>/<i>.webp
  assets/thumbs/manifest.json   {"U+738B": {"kaom": 8, "sais": 8, "qxk": 8}, ...}

用法:  python build/cache_thumbs.py [--cap 8]
"""
import argparse
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "thumbs"
BASE = "https://darkscope.cn/jinwen-data/thumbs/"
SOURCES = ["kaom", "sais", "qxk"]
CJK = r"[㐀-鿿\U00020000-\U0003134f]"


def collect_chars() -> list[str]:
    html = (ROOT / "demo.html").read_text(encoding="utf-8")
    chars = set()
    m = re.search(r"const BAIJIA = '([^']+)'", html)
    chars.update(m.group(1))
    s2t = re.search(r"const S2T = \{(.*?)\};", html, re.S).group(1)
    chars.update(re.findall(rf"'({CJK})'", s2t))
    for name in ("SURNAME_STORIES", "MATCH_CHARS", "BLESS_FAMILIES", "DICT_TAGS", "WALL_SEED"):
        m = re.search(rf"const {name} = (.*?);\n", html, re.S)
        if m:
            chars.update(re.findall(rf"'({CJK})'", m.group(1)))
    chars.update(re.findall(rf"char: '({CJK})'", html))
    seed = json.loads((ROOT / "data" / "laoyin_seed.json").read_text(encoding="utf-8"))
    chars.update(e["char"] for e in seed["entries"] if re.fullmatch(CJK, e.get("char", "")))
    return sorted(chars)


def cp_token(ch: str) -> str:
    return "U+%04X" % ord(ch)


def fetch(url: str):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return r.read()
        except urllib.error.HTTPError:
            return None
        except (urllib.error.URLError, OSError):
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"network failed: {url}")


def cache_char(ch: str, cap: int) -> tuple[str, dict]:
    cp = cp_token(ch)
    got = {}
    for src in SOURCES:
        n = 0
        for i in range(cap):
            dst = OUT / src / cp / f"{i}.webp"
            if not (dst.exists() and dst.stat().st_size > 0):
                data = fetch(f"{BASE}{src}/{cp}/{i}.webp")
                if not data:
                    break
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(data)
            n += 1
        if n:
            got[src] = n
    return cp, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=8)
    args = ap.parse_args()
    chars = collect_chars()
    print(f"{len(chars)} chars, cap {args.cap}/source")
    manifest = {}
    with ThreadPoolExecutor(6) as ex:
        for k, (cp, got) in enumerate(ex.map(lambda c: cache_char(c, args.cap), chars), 1):
            if got:
                manifest[cp] = got
            if k % 50 == 0:
                print(f"  {k}/{len(chars)}", flush=True)
    (OUT / "manifest.json").write_text(
        json.dumps({"cap": args.cap, "chars": manifest}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    total = sum(p.stat().st_size for p in OUT.rglob("*.webp"))
    print(f"ok: {len(manifest)} chars with thumbs, {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
