#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 20 张预存案例预先算好「考释助手」要用的数据 → assets/cases/kaoshi.json。

网页里不放整份《中华字库》目录释文，只放这 20 张用得到的结果：
- 每个字框的左右邻字（按网页同一套阅读顺序：按列从右到左、列内从上到下；灰框邻字记作 ?）
- 辞例检索（考释助手-功能设计.md 二·②2a）：先用左右各 2 字，少于 3 条依次退到左右各 1 字、单侧 2 字、单侧 1 字；
  读为层 / 隶定层 × 本卷 / 全部 四种都算好；排除本器（zhjwd 前 11 位）和它所在的近同铭文组；不跨句号、不跨缺字
- 近同铭文分组（2b）：同一器号、释文完全相同、或 ≥8 字且编辑距离 ≤10% 的并为一组，用来计"独立器数"
- 候选字的本地拓片缩略图（1a）：只用 assets/thumbs 已缓存的图，标来源、拓/未知、器名时代；SAIS 图记下原图器号，网页按器号排除本器
用法（在 baijia-jinwen 目录下）：python build/build_kaoshi_data.py
"""
from __future__ import annotations

import bisect
import collections
import csv
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

from rapidfuzz import process
from rapidfuzz.distance import Levenshtein

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_slots import is_written, transcript_slots  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SITE = Path(__file__).resolve().parent.parent
CATALOG = SITE / "data/zhjwd_catalog.csv"
CASES = SITE / "assets/cases/cases.json"
OUT = SITE / "assets/cases/kaoshi.json"
THUMBS = SITE / "assets/thumbs"
THUMBS_META = SITE / "_thumbs-meta.json"
LABELS = SITE / "mingjian-ocr-shitu/models/label_map.json"

# 候选字古音（4b）：古音小镜（kaom.net ny_word）各家拟音，取自 darkscope.cn/jinwen-data 整理好的逐字 JSON，缓存在 build/.cache
JWD = "https://darkscope.cn/jinwen-data/"
CACHE = SITE / "build/.cache/jinwen-data"
OC_ORDER = ["鄭張尚芳", "白一平-沙加爾", "白一平", "潘悟雲", "王力體系", "李方桂", "許思萊", "斯塔羅斯金③·詩經音", "高本漢", "董同龢", "周法高"]

LEVELS = [(2, 2), (1, 1), (2, 0), (0, 2), (1, 0), (0, 1)]   # 左右各几个字，依次退避
MIN_HITS = 3
TOP_GROUPS = 8
SOURCES_PER_GROUP = 3
NORM = str.maketrans({"匄": "匃"})                          # 同字异码归一，识别器只有「匃」
BOUNDARY = "|□\n"


def coined(ch: str) -> bool:
    cp = ord(ch)
    return 0xE000 <= cp <= 0xF8FF or 0xAC00 <= cp <= 0xD7AF or cp >= 0x40000


def layers(slots):
    """一条释文 → (隶定层, 读为层) 两个等长字符串；句子边界插 |，缺字为 □。"""
    li, rd = [], []
    for s in slots:
        if s.get("brk"):
            li.append("|"); rd.append("|")
        if s.get("gap"):
            li.append("□"); rd.append("□")
            continue
        o = s["orig"]
        lc = s["li"] if coined(o) and s.get("li") and len(s["li"]) == 1 and not coined(s["li"]) else o
        rc = s["read"] if len(s["read"]) == 1 else lc
        li.append(lc); rd.append(rc)
    return "".join(li).translate(NORM), "".join(rd).translate(NORM)


def reading_order(preds):
    """金文直行右起：按框中心 x 从右往左聚类分列，列内从上到下。结果写进 kaoshi.json，网页直接用这份顺序。
    不能用 round(中心x/列宽) 的固定网格：列稍斜或中心落在格线附近时，同一列会被劈成两列（盩厔鼎、伯克壺即如此）。
    并列条件：与列均值相距 < 0.45 列宽，且与列内每个框的纵向重叠不超过较小框高的一半（相邻字框本来就常有几像素重叠）。"""
    if not preds:
        return []
    ws = sorted(p["bbox"][2] for p in preds)
    col_w = max(8, ws[len(ws) // 2])
    cx = lambda i: preds[i]["bbox"][0] + preds[i]["bbox"][2] / 2
    cols = []
    for i in sorted(range(len(preds)), key=lambda i: -cx(i)):
        y, h = preds[i]["bbox"][1], preds[i]["bbox"][3]
        best = None
        for c in cols:
            d = abs(c["cx"] - cx(i))
            if d >= 0.45 * col_w:
                continue
            if any(min(y + h, preds[j]["bbox"][1] + preds[j]["bbox"][3]) - max(y, preds[j]["bbox"][1])
                   > 0.5 * min(h, preds[j]["bbox"][3]) for j in c["items"]):
                continue
            if best is None or d < abs(best["cx"] - cx(i)):
                best = c
        if best is None:
            cols.append({"cx": cx(i), "items": [i]})
        else:
            best["items"].append(i)
            best["cx"] = sum(cx(j) for j in best["items"]) / len(best["items"])
    cols.sort(key=lambda c: -c["cx"])
    return [i for c in cols for i in sorted(c["items"], key=lambda i: preds[i]["bbox"][1])]


def layer_equivalents(rows):
    """目录逐字对齐的隶定→读为对应。识别器输出多是隶定形（乍、白、隹、亯），读为层同一位置却已改成作、伯、唯、享；
    反过来模型也可能直接输出读为形。邻字检索时把这种对应并进来：在读为层查「乍」也认「作」，在隶定层查「作」也认「乍」。
    只收占该字出现次数 ≥20% 且 ≥5 次的对应。"""
    l2r, r2l = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    ltot, rtot = collections.Counter(), collections.Counter()
    for r in rows:
        for a, b in zip(r["L"], r["R"]):
            if a in BOUNDARY:
                continue
            ltot[a] += 1; rtot[b] += 1
            if a != b:
                l2r[a][b] += 1; r2l[b][a] += 1
    pick = lambda cnt, tot: {k: [x for x, n in v.most_common() if n >= 5 and n >= 0.2 * tot[k]] for k, v in cnt.items()}
    return {"R": pick(l2r, ltot), "L": pick(r2l, rtot)}


TITLE_TAIL = re.compile(r"[一二三四五六七八九十百甲乙丙丁戊己庚辛壬癸ABCDEFabcdef0-9ⅠⅡⅢⅣ\s]+$")


def title_stem(t: str) -> str:
    """器名去掉括注和末尾的件号（王孫誥鐘九→王孫誥鐘、曾侯乙鐘二十五→曾侯乙鐘），用来认同套编钟和同名器。"""
    return TITLE_TAIL.sub("", re.sub(r"（[^）]*）|\([^)]*\)", "", t or "")).strip()


class Union:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[max(a, b)] = min(a, b)


def near_duplicate_groups(rows):
    """同器号、释文完全相同、≥8 字且编辑距离 ≤10% 的条目并为一组。"""
    t0 = time.time()
    uf = Union(len(rows))
    by_z, by_text = collections.defaultdict(list), collections.defaultdict(list)
    plain = [re.sub(r"[|□]", "", r["R"]) for r in rows]
    for i, r in enumerate(rows):
        by_z[r["z11"]].append(i)
        if len(plain[i]) >= 8:
            by_text[plain[i]].append(i)
    for g in list(by_z.values()) + list(by_text.values()):
        for x in g[1:]:
            uf.join(g[0], x)
    uniq = sorted(by_text, key=len)
    lens = [len(s) for s in uniq]
    pairs = 0
    for a in range(0, len(uniq), 400):
        chunk = uniq[a:a + 400]
        lo = bisect.bisect_left(lens, int(len(chunk[0]) * 0.9))
        hi = bisect.bisect_right(lens, int(len(chunk[-1]) / 0.9) + 1)
        m = process.cdist(chunk, uniq[lo:hi], scorer=Levenshtein.normalized_distance,
                          score_cutoff=0.1, workers=-1)
        for x, y in zip(*((m <= 0.1).nonzero())):
            p, q = a + int(x), lo + int(y)
            if p < q:
                uf.join(by_text[uniq[p]][0], by_text[uniq[q]][0])
                pairs += 1
    gid = [uf.find(i) for i in range(len(rows))]
    sizes = collections.Counter(gid)
    multi = sum(1 for g, n in sizes.items() if n > 1)
    print(f"  近同铭文：{multi} 组含多条（含同器号），近似对 {pairs}，用时 {time.time() - t0:.0f}s")
    return gid


def fetch_json(rel: str):
    """取 jinwen-data 的一个 JSON，先看本地缓存；取不到返回 None。"""
    import urllib.parse
    import urllib.request
    path = CACHE / rel.split("?")[0]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        url = JWD + urllib.parse.quote(rel, safe="/?=&+")
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "jijin-kaoshi-build"}), timeout=30) as r:
            text = r.read().decode("utf-8")
    except Exception as e:
        print(f"  [取不到] {rel}：{e}", file=sys.stderr)
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return json.loads(text)


def distill_phono(d):
    """古音小镜逐字表 → 每位学者的上古拟音（每人只取第一读，注韵部、出处页，另记还有几读），
    以及郑张尚芳表同一读的中古地位、反切和声首（原表「曉陽開三上·許兩[亨]」，方括号是声首，不是小韵）。
    不再拼白一平–沙加尔的中古转写：它的第一条常常是另一个读音（如「享」取到「亨」的 xaeng），和郑张那一读对不上。"""
    data = (d or {}).get("数据") or {}
    oc = [x for x in (data.get("上古音") or {}).get("構擬", []) if x.get("拟音_整理")]
    oc.sort(key=lambda x: (OC_ORDER.index(x["学者"]) if x["学者"] in OC_ORDER else 99, int(x.get("序") or 0)))
    rows, by_scholar = [], collections.Counter()
    for x in oc:
        by_scholar[x["学者"]] += 1
    seen = set()
    for x in oc:
        if x["学者"] in seen:
            continue
        seen.add(x["学者"])
        rows.append([x["学者"], x["拟音_整理"], (x.get("韵部") or "").replace(" ?", "?").strip(),
                     x.get("出处") or "", by_scholar[x["学者"]] - 1])
    zz = next((x for x in oc if x["学者"] == "鄭張尚芳" and x.get("原表其他信息")), None)
    m = re.match(r"^(\S+?)·(\S+?)(?:\[(.+?)\])?(?:\s|$)", (zz or {}).get("原表其他信息", ""))
    mc = {"pos": m.group(1), "fq": m.group(2), "head": m.group(3) or ""} if m else None
    return {"oc": rows[:8], "mc": mc}


def collect_phono(chars):
    """按繁体字头查；jinwen-data 的古音多按简体字头存（宝、万、寿、无），繁体查不到时退到简体，并记下用了哪个简体字头。"""
    from concurrent.futures import ThreadPoolExecutor
    import zhconv
    index = (fetch_json("chars.json") or {}).get("chars", {})
    has = lambda ch: (index.get(ch) or {}).get("phono")
    plan = {}
    for ch in sorted(chars):
        if coined(ch):
            continue
        if has(ch):
            plan[ch] = ch
        else:
            s = zhconv.convert(ch, "zh-cn")
            if s != ch and has(s):
                plan[ch] = s
    with ThreadPoolExecutor(4) as pool:
        got = list(pool.map(lambda kv: (kv[0], kv[1], fetch_json(f"ny_word/{index[kv[1]]['cp']}.json")), plan.items()))
    out = {}
    for ch, via, d in got:
        v = distill_phono(d) if d else None
        if v and (v["oc"] or v["mc"]):
            if via != ch:
                v["via"] = via
            out[ch] = v
    print(f"  古音：候选字 {len(chars)} 个，有音韵数据 {len(plan)} 个（其中退到简体字头 {sum(1 for k, s in plan.items() if k != s)} 个），取到 {len(out)} 个")
    return out


def pattern_re(left, right):
    """left/right 是邻字的候选写法列表，如 [["乍","作"],["?"]]；? 匹配任一字（不跨句界、缺字）。"""
    one = "[^|□\n]"
    tok = lambda alts: one if alts == ["?"] else (re.escape(alts[0]) if len(alts) == 1
                                                 else "[" + "".join(re.escape(a) for a in alts) + "]")
    return re.compile("(?=" + "".join(map(tok, left)) + "(" + one + ")" + "".join(map(tok, right)) + ")")


def query_text(left, right):
    """检索式的显示写法：乍〔作〕□姜；? 显示为 ？。"""
    show = lambda alts: "？" if alts == ["?"] else alts[0] + ("〔" + "".join(alts[1:]) + "〕" if len(alts) > 1 else "")
    return "".join(map(show, left)) + "□" + "".join(map(show, right))


def main():
    rows = []
    with open(CATALOG, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            li, rd = layers(transcript_slots(r["transcript"], marks=True))
            if not rd.strip("|□"):
                continue
            rows.append({"zhjwd": r["zhjwd"], "z11": r["zhjwd"][:11], "vol": r["volume"], "title": r["title"],
                         "jicheng": r["jicheng"], "mingtu": r["mingtu"], "period": r["period"], "L": li, "R": rd})
    print(f"  目录 {len(rows)} 条有释文")
    gid = near_duplicate_groups(rows)

    # 每层拼成一个大字符串，正则一次扫完，再按偏移找回条目
    big, starts = {}, {}
    for lay in ("L", "R"):
        offs, parts, pos = [], [], 0
        for r in rows:
            offs.append(pos)
            parts.append(r[lay])
            pos += len(r[lay]) + 1
        big[lay], starts[lay] = "\n".join(parts), offs
    freq = {lay: collections.Counter(c for c in big[lay] if c not in BOUNDARY) for lay in ("L", "R")}
    classes = set(json.loads(LABELS.read_text(encoding="utf-8"))["char2id"]) if LABELS.exists() else set()

    eq = layer_equivalents(rows)
    stems = [title_stem(r["title"]) for r in rows]

    def alts(lay, ch):
        """邻字在某一层的候选写法：本字 + 目录对齐里常见的对应写法（读为层：乍→作；隶定层：作→乍）。"""
        return ["?"] if ch == "?" else [ch] + [x for x in eq[lay].get(ch, []) if x != ch]

    def search(lay, left, right):
        out = []
        for m in pattern_re(left, right).finditer(big[lay]):
            p = m.start(1)
            k = bisect.bisect_right(starts[lay], p) - 1
            out.append((k, p - starts[lay][k], m.group(1)))
        return out

    lib = json.loads(CASES.read_text(encoding="utf-8"))
    cache = {}
    result = {"built": dt.date.today().isoformat(),
              "note": "辞例为《中华字库》目录释读（含旧释），只作线索；已排除本器、近同铭文及同名同套器",
              "levels": LEVELS, "minHits": MIN_HITS, "norm": {"匄": "匃"}, "cases": {}}
    want_thumbs, want_phono = set(), set()
    t0 = time.time()
    for c in lib["cases"]:
        z11 = c["id"][:11]
        own_rows = [i for i, r in enumerate(rows) if r["z11"] == z11]
        own_g = {gid[i] for i in own_rows}
        # 同名同套器（王孫誥鐘二…十、曾侯乙鐘各件）分段刻同一篇或截断，整篇编辑距离并不进来，按器名词干一并排除
        own_stems = {stems[i] for i in own_rows if len(stems[i]) >= 3}
        excluded = lambda k: gid[k] in own_g or stems[k] in own_stems
        vol = (c.get("catalog") or {}).get("volume", "")
        preds = c["pred"]
        order = reading_order(preds)
        pos_of = {pi: k for k, pi in enumerate(order)}
        ents, ent_idx = [], {}
        boxes = []
        for pi, p in enumerate(preds):
            k = pos_of[pi]
            tx = lambda j: (preds[order[j]]["text"].translate(NORM) if preds[order[j]]["kept"] else "?") \
                if 0 <= j < len(order) else None
            nb = [tx(k - 2), tx(k - 1), tx(k + 1), tx(k + 2)]
            box = {"nb": nb, "v": {}}
            for lay in ("R", "L"):
                per_level = []
                for (l, r) in LEVELS:
                    left = nb[2 - l:2] if l else []
                    right = nb[2:2 + r] if r else []
                    if None in left or None in right or not (left + right) or all(x == "?" for x in left + right):
                        per_level.append(None)
                        continue
                    la, ra = [alts(lay, x) for x in left], [alts(lay, x) for x in right]
                    key = (lay, json.dumps(la), json.dumps(ra))
                    if key not in cache:
                        cache[key] = search(lay, la, ra)
                    hits = [h for h in cache[key] if not excluded(h[0])]
                    # 造字填入的命中不进分组和条数（设计 2a），另计一个数
                    per_level.append((l, r, query_text(la, ra), [h for h in hits if not coined(h[2])],
                                      [h for h in hits if coined(h[2])]))
                for scope in ("vol", "all"):
                    inscope = lambda hs: [h for h in hs if scope == "all" or rows[h[0]]["vol"] == vol]
                    rows_of = lambda hs: len({h[0] for h in hs})
                    summ, chosen = [], None
                    for i_lv, lv in enumerate(per_level):
                        if lv is None:
                            summ.append(None)
                            continue
                        l, r, q, hits, cz = lv
                        hs = inscope(hits)
                        summ.append([l, r, rows_of(hs), len({h[2] for h in hs})])   # 条数一律按不同条目计
                        if chosen is None and rows_of(hs) >= MIN_HITS:
                            chosen = (i_lv, hs, q, rows_of(inscope(cz)))
                    if chosen is None:
                        best = max(((i, s) for i, s in enumerate(summ) if s), key=lambda t: t[1][2], default=None)
                        if best and best[1][2] > 0:
                            l, r, q, hits, cz = per_level[best[0]]
                            chosen = (best[0], inscope(hits), q, rows_of(inscope(cz)))
                    groups = []
                    if chosen:
                        by_char = collections.defaultdict(list)
                        for h in chosen[1]:
                            by_char[h[2]].append(h)
                        ranked = sorted(by_char.items(), key=lambda kv: (-len({h[0] for h in kv[1]}), -len({gid[h[0]] for h in kv[1]})))
                        for ch, hs in ranked[:TOP_GROUPS]:
                            rws = sorted({h[0] for h in hs})
                            one_hit = {}
                            for h in hs:
                                one_hit.setdefault(h[0], h)
                            li_var = collections.Counter(rows[h[0]]["L"][h[1]] for h in one_hit.values()) if lay == "R" else collections.Counter()
                            # 出处：先每个近同铭文组各取一条，不够再补同组的
                            first, rest, seen_g, seen_r = [], [], set(), set()
                            for h in sorted(hs, key=lambda h: h[0]):
                                if h[0] in seen_r:
                                    continue
                                seen_r.add(h[0])
                                (rest if gid[h[0]] in seen_g else first).append(h)
                                seen_g.add(gid[h[0]])
                            srcs = []
                            for h in (first + rest)[:SOURCES_PER_GROUP]:
                                row = rows[h[0]]
                                s = row[lay]
                                if h[0] not in ent_idx:
                                    ent_idx[h[0]] = len(ents)
                                    ents.append([row["zhjwd"], row["title"], row["jicheng"], row["mingtu"], row["vol"], row["period"]])
                                a, b = max(0, h[1] - 5), min(len(s), h[1] + 6)
                                srcs.append([ent_idx[h[0]], s[a:h[1]].replace("|", "。"), s[h[1] + 1:b].replace("|", "。")])
                            li = [[x, n] for x, n in li_var.most_common(4) if x != ch] if lay == "R" else []
                            groups.append({"c": ch, "n": len(rws), "g": len({gid[r] for r in rws}),
                                           "li": li, "src": srcs, "few": freq[lay][ch] < 5, "cls": ch in classes})
                            want_phono.add(ch)
                            if len(groups) <= 3:
                                # 字形页按当前视图取前 3 组；读为层的组多半隶定作某字时显示隶定字，那个字也要备图
                                want_thumbs.add(ch)
                                if li and li[0][1] * 2 >= len(rws):
                                    want_thumbs.add(li[0][0])
                    box["v"][lay + "_" + scope] = {"lv": summ, "at": chosen[0] if chosen else None,
                                                   "q": chosen[2] if chosen else "", "cz": chosen[3] if chosen else 0,
                                                   "gr": groups}
            want_thumbs.update(t[0] for t in p.get("top5", []))
            boxes.append(box)
        result["cases"][c["stem"]] = {"z11": z11, "vol": vol, "order": order, "boxes": boxes, "ents": ents}
    print(f"  20 张案例检索完，用时 {time.time() - t0:.0f}s，不同检索式 {len(cache)} 个")

    # 本地已缓存的拓片缩略图：assets/thumbs/<来源>/<U+码>/<i>.webp 对应 _thumbs-meta.json 里同来源第 i 条
    manifest = json.loads((THUMBS / "manifest.json").read_text(encoding="utf-8"))["chars"]
    meta = json.loads(THUMBS_META.read_text(encoding="utf-8"))
    thumbs = {}
    for ch in sorted(want_thumbs):
        cp = "U+%04X" % ord(ch)
        have = manifest.get(cp) or {}
        items = []
        for src, kind in (("kaom", "拓"), ("qxk", "未知"), ("sais", "拓")):
            for i in range(have.get(src, 0)):
                m = ((meta.get(cp) or {}).get(src) or [])
                m = m[i] if i < len(m) else {}
                if src == "sais":
                    label = "SAIS " + ("訓練集" if m.get("split") == "train" else "驗證集" if m.get("split") else "")
                    items.append([src, i, kind, label.strip(), (m.get("orig") or "")[:11]])
                else:
                    items.append([src, i, kind, " · ".join(x for x in (m.get("src"), m.get("period")) if x), ""])
        if items:
            thumbs[ch] = items
    result["thumbs"] = thumbs
    result["thumbsNote"] = "kaom 为拓本；qxk 混有摹本和书影，标「未知」；SAIS 为比赛数据裁图，已按器号排除本器"
    result["phono"] = collect_phono(want_thumbs | want_phono)
    result["phonoNote"] = "古音小镜（kaom.net ny_word）各家构拟，经 darkscope.cn/jinwen-data 整理；仅供参考"
    result["eqNote"] = "读为层检索时邻字并入目录对齐中常见的读为写法（如乍→作），隶定层反之"
    OUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n_box = sum(len(v["boxes"]) for v in result["cases"].values())
    print(f"  字框 {n_box} 个；候选字 {len(want_thumbs)} 个，其中本地有拓片图 {len(thumbs)} 个")
    print(f"→ {OUT}（{OUT.stat().st_size / 1e6:.2f} MB）")


if __name__ == "__main__":
    main()
