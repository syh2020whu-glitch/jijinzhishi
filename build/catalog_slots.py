#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《中华字库》金文目录释文 → 逐字位。pick_cases_webp.py、export_cases_predictor.py、fix_case_slots.py 共用。

目录体例（按 25,733 条释文实测整理）：
  乍{作}          {} 读为（通读）
  𤔲（何）        （）隶定或释字；造字后面的（）就是它的隶定，如 񄱨（沬）{眉}
  雨〈霸〉        紧跟在字后的〈〉是正字（原字为误字）；不跟在字后的〈〉是补出的字
  子﹦［子子］    ﹦ 重文号，后面的［］给出展开写法；几个重文号共用一个展开：大﹦神﹦［大神。大神］= 大神大神
  卅［三十］      不跟重文号的［］是合文的展开，合文本身只占一个字位
  【內】 正面：   注记和位置标签，不是铭文
  □ … 标点        不占字位
半角 ( ) [ ] < > ｛ ｝ = 与全角同义。造字在 Unicode 第 4–16 平面、私用区，另有一批被抽成了韩文音节码位，都算一个字。

每个字位：{"orig": 原字, "read": 最终读法}，按需附带
  li 隶定 / zheng 正字 / he 合文展开 / sup 补出的字（拓片上可能没有）。
read 的取法：{} 读为 > 〈〉正字 > （）隶定 > 原字。
"""
import re

OPEN = {"（": "）", "［": "］", "〈": "〉", "{": "}"}
ASCII = str.maketrans({"(": "（", ")": "）", "[": "［", "]": "］", "<": "〈", ">": "〉",
                       "｛": "{", "｝": "}", "=": "﹦", "＝": "﹦"})
REPEAT = "﹦"
GAPS = set("□☐…⋯")
SENTENCE_END = set("。；;！!？?")


def is_written(ch: str) -> bool:
    """是否算一个铭文字（含造字）。"""
    cp = ord(ch)
    return (0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF or cp == 0x3007
            or 0xE000 <= cp <= 0xF8FF        # 私用区造字
            or 0xAC00 <= cp <= 0xD7AF        # 被抽成韩文音节码位的造字
            or cp >= 0x20000)                # 扩展 B 以后、第 4–16 平面造字


def _han(s: str) -> str:
    return "".join(c for c in s if is_written(c))


def _strip_labels(t: str) -> str:
    t = re.sub(r"【[^】]*】", "", t)
    # 「正面：」「劍首：」之类的位置标签去掉；「某曰：」是铭文，只去冒号
    def label(m):
        word = m.group(2)
        return m.group(1) + (word if word.endswith("曰") else "")
    t = re.sub(r"(^|[。、，,；;\s])([^。、，,；;\s：:{}（）［］〈〉]{1,8})[：:]", label, t)
    return t.replace("：", "").replace(":", "")


def transcript_slots(t: str, marks: bool = False) -> list:
    """marks=True 时另外输出缺字（□、… 记作 {"orig": "□", "gap": True}）和句子边界（句末后第一个字位带 brk），
    供辞例检索用：检索式不跨句号，也不跨缺字。案例对照用默认的 marks=False。"""
    t = _strip_labels((t or "").translate(ASCII))
    brk_at = set()
    slots = []
    group = []        # 最近一个字（或一组展开字）的字位下标，后面的括注挂在它们身上
    run = []          # 带重文号、还没展开的字位下标
    last = ""         # 上一个记号的类型：char / repeat / bracket / sep

    def flush_run():
        # 没有［］展开的重文：每个字后面补一个同字（字的多少不变，顺序按 子子孫孫 处理）
        for k in sorted(run, reverse=True):
            slots.insert(k + 1, {"orig": slots[k]["orig"]})
        run.clear()

    def attach(key, content):
        han = _han(content)
        if not han or not group:
            return
        if len(han) == len(group):
            for k, c in zip(group, han):
                slots[k][key] = c
        elif len(group) == 1:
            slots[group[0]][key] = han            # 合文等一个字位对多字
        else:
            slots[group[-1]][key] = han

    i, n = 0, len(t)
    while i < n:
        ch = t[i]
        if ch in OPEN:
            j = t.find(OPEN[ch], i + 1)
            content = t[i + 1:j] if j > 0 else t[i + 1:]
            i = j + 1 if j > 0 else n
            if ch == "［":
                han = _han(content)
                if run and last == "repeat":
                    # 重文展开：用展开写法替换带重文号的那几个字
                    start = run[0]
                    del slots[start:]
                    slots.extend({"orig": c} for c in han)
                    group = list(range(start, len(slots)))
                    run.clear()
                elif group and han:
                    slots[group[-1]]["he"] = han      # 合文展开
                last = "bracket"
            elif ch == "〈":
                if group and last in ("char", "bracket") and slots[group[-1]].get("sup") is None:
                    attach("zheng", content)
                else:
                    flush_run()
                    han = _han(content)
                    start = len(slots)
                    slots.extend({"orig": c, "sup": True} for c in han)
                    group = list(range(start, len(slots)))
                last = "bracket"
            else:
                attach("li" if ch == "（" else "read", content)
                last = "bracket"
            continue
        if ch == REPEAT:
            if slots and last in ("char", "bracket") and group:
                for k in group:
                    if k not in run:
                        run.append(k)
            last = "repeat"
        elif is_written(ch):
            if run and last != "repeat":
                flush_run()
            slots.append({"orig": ch})
            group = [len(slots) - 1]
            last = "char"
        elif not ch.isspace():
            # 标点、□、… 都是断开：把没展开的重文补齐，括注不再往前挂
            flush_run()
            group = []
            last = "sep"
            if marks and ch in GAPS:
                slots.append({"orig": "□", "gap": True})
            elif marks and ch in SENTENCE_END:
                brk_at.add(len(slots))
        i += 1
    flush_run()

    for k, s in enumerate(slots):
        s["read"] = s.get("read") or s.get("zheng") or s.get("li") or s["orig"]
        if s.get("sup") is None:
            s.pop("sup", None)
    if marks:
        # 句末标点之后的第一个字位记 brk；重文展开、补字会挪动下标，这里按标点出现时的字位数近似
        for k in brk_at:
            if 0 < k < len(slots):
                slots[k]["brk"] = True
    return slots


def slot_chars(s: dict) -> set:
    """一个字位能和识别结果对上的写法：原字、隶定、正字、读为。"""
    return {v for v in (s.get("orig"), s.get("li"), s.get("zheng"), s.get("read")) if v}


def match_transcript(slots, preds):
    """没有逐字框标注时，用目录释文当答案：kept 框按把握从高到低，各占一个还没被占的字位
    （原字、隶定、正字、读为任一相同都算），占上记 cat_hit。另算每个框 top5 是否含释文里的字（top5_hit），
    以及释文字位里有多少个在任一框的 top5 中出现过（top5_cover）。
    这是集合比对，不是逐字位对齐，比逐框 F1 宽松。"""
    if not slots:
        return None
    used = [False] * len(slots)
    chars = set().union(*(slot_chars(s) for s in slots))
    hit = 0
    for p in preds:
        p["cat_hit"] = False
    for p in sorted((p for p in preds if p["kept"]), key=lambda p: -p["rec_conf"]):
        for k, s in enumerate(slots):
            if not used[k] and p["text"] in slot_chars(s):
                used[k] = p["cat_hit"] = True
                hit += 1
                break
    cand = set()
    for p in preds:
        top = {t[0] for t in p["top5"]}
        p["top5_hit"] = bool(top & chars)
        cand |= top
    cover = sum(1 for s in slots if slot_chars(s) & cand)
    kept = sum(1 for p in preds if p["kept"])
    return {"slots": len(slots), "kept": kept, "hit": hit, "top5_cover": cover,
            "hit_rate": round(hit / len(slots), 4), "cover_rate": round(cover / len(slots), 4)}
