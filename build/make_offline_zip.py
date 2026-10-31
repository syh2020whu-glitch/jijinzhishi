"""打决赛离线包：只收网站运行时真正要的文件，拷到任何一台装了 Python 的电脑上双击即可用。

用法（在 baijia-jinwen 目录下）：
    python build/make_offline_zip.py            # 输出 dist/吉金智识-离线包-YYYYMMDD.zip
    python build/make_offline_zip.py --list     # 只列清单和大小，不打包

包里没有识图模型，识图仍要连后端；后端不在时 Demo 显示 assets/cases/ 里的预存结果。
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 运行时引用的目录与文件（对照 demo.html / index.html / fonts.css 里的本地路径整理）
INCLUDE_DIRS = [
    "jinwen_svg",
    "data",
    "build/vendor",
    "js/vendor",
    "assets/atlas",
    "assets/audio",
    "assets/fonts",
    "assets/thumbs",
    "assets/cases",
]
INCLUDE_FILES = [
    "demo.html",
    "index.html",
    "serve.py",
    "ocr-endpoint.json",
    "启动服务器.bat",
]
# 器物图只要 webp，原始 png/jpg 每张 3–5MB，页面已不再引用
VESSEL_GLOB = "assets/vessels/*.webp"

LAUNCHER_NOTE = """吉金智识 · 离线包

1. 解压到任意文件夹（路径里有中文也可以）。
2. 双击「启动服务器.bat」，看到 http://localhost:8080/demo.html 后用 Chrome 或 Edge 打开。
   没有 bat 权限时，在本文件夹打开命令行运行：python serve.py
3. 关闭黑色窗口即停止服务。

不能直接双击 demo.html（file:// 下浏览器会拦截字表和音频加载）。
识图需要联网连后端；断网时识图页的 Demo 显示预存的真实识别结果。
"""


def collect() -> list[Path]:
    files: list[Path] = []
    for d in INCLUDE_DIRS:
        p = ROOT / d
        if not p.exists():
            print(f"  [跳过] 缺目录 {d}", file=sys.stderr)
            continue
        files += [f for f in p.rglob("*") if f.is_file() and f.name not in {"Thumbs.db", ".DS_Store"}]
    for f in INCLUDE_FILES:
        p = ROOT / f
        if p.exists():
            files.append(p)
        else:
            print(f"  [跳过] 缺文件 {f}", file=sys.stderr)
    files += sorted(ROOT.glob(VESSEL_GLOB))
    return sorted(set(files))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="只列清单和大小")
    ap.add_argument("--out", default=None, help="输出 zip 路径")
    args = ap.parse_args()

    files = collect()
    total = sum(f.stat().st_size for f in files)
    by_top: dict[str, int] = {}
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        parts = rel.split("/")
        key = "/".join(parts[:2]) if len(parts) > 2 else parts[0]
        by_top[key] = by_top.get(key, 0) + f.stat().st_size
    for k, v in sorted(by_top.items(), key=lambda kv: -kv[1]):
        print(f"  {v / 1e6:8.1f} MB  {k}")
    print(f"  共 {len(files)} 个文件，{total / 1e6:.1f} MB")
    if not (ROOT / "assets/cases/cases.json").exists():
        print("  [提醒] 还没有 assets/cases/cases.json，离线时识图 Demo 会提示缺预存案例", file=sys.stderr)
    if args.list:
        return 0

    out = Path(args.out) if args.out else ROOT / "dist" / f"吉金智识-离线包-{dt.date.today():%Y%m%d}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    top = "吉金智识"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in files:
            rel = f.relative_to(ROOT).as_posix()
            # 已压缩格式不再 deflate，省时间
            ctype = zipfile.ZIP_STORED if f.suffix.lower() in {".webp", ".png", ".jpg", ".mp3", ".woff2", ".zip"} else zipfile.ZIP_DEFLATED
            z.write(f, f"{top}/{rel}", compress_type=ctype)
        z.writestr(f"{top}/使用说明.txt", LAUNCHER_NOTE)
    print(f"  已写出 {out}（{out.stat().st_size / 1e6:.1f} MB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
