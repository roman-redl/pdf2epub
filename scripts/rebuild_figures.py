#!/usr/bin/env python3
"""Пересборка merged.md: пары «фото+подпись» в <figure>-блоки (универсально).
сегменты-подписи удаляются из текстового потока (без дублей).
Использование: rebuild_ss.py <merged.md> <ss_elements.json> <pairs_dir> <out.md>"""
import glob, html, json, re, sys
from difflib import SequenceMatcher

md_path, el_path, pairs_dir, out_path = sys.argv[1:5]
md = open(md_path, encoding="utf-8").read()
elements = json.load(open(el_path))["elements"]

pairs = []
for f in sorted(glob.glob(f"{pairs_dir}/pairs_*.json")):
    pairs += json.load(open(f))
applied = {p["img"]: p for p in pairs if p.get("conf", "high") in ("high", "medium")}
print(f"пар к применению: {len(applied)} (high+medium), отброшено low: "
      f"{sum(1 for p in pairs if p.get('conf') not in ('high','medium'))}")

def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

consumed = [norm(p["caption"]) for p in applied.values()]

POSMARK = re.compile(r"(?:(?:OPPOSITE PAGE|PREVIOUS PAGES)[,\s]+)?(?:ABOVE|BELOW|LEFT|RIGHT|TOP|BOTTOM|MIDDLE|CENTRE|CENTER|FAR LEFT|FAR RIGHT|BELOW LEFT|BELOW RIGHT|ABOVE LEFT|ABOVE RIGHT)"
                     r"(?:[,\s]+(?:ABOVE|BELOW|LEFT|RIGHT|TOP|BOTTOM|FAR))*\s*:?", re.I)

def split_segments(text):
    """Текст-юнит -> [(start_offset_in_text, seg_text)]"""
    out, pos = [], 0
    marks = list(POSMARK.finditer(text))
    if not marks:
        return [(0, text)]
    if marks[0].start() > 0:
        out.append((0, text[:marks[0].start()]))
    for k, m in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(text)
        out.append((m.start(), text[m.start():end]))
    return out

def seg_consumed(seg):
    ns = norm(POSMARK.sub("", seg))
    if len(ns) < 15:
        return False
    for c in consumed:
        if len(c) >= 15:
            head = c[:100]
            if head and (head[:60] in ns or ns[:60] in c
                         or SequenceMatcher(None, ns[:100], head).ratio() > 0.85):
                return True
    return False

# обрабатываем снизу вверх, чтобы оффсеты не ехали
ops = []
for e in reversed(elements):
    if e["type"] == "img" and e["file"] in applied:
        cap = html.escape(applied[e["file"]]["caption"])
        fig = f'<figure>\n<img src="{e["file"]}"/>\n<figcaption>{cap}</figcaption>\n</figure>'
        ops.append((e["start"], e["end"], fig))
    elif e["type"] == "text":
        segs = split_segments(e["text"])
        keep, dropped = [], 0
        for off, seg in segs:
            if seg_consumed(seg):
                dropped += 1
            else:
                keep.append(seg)
        if dropped:
            new_text = "\n\n".join(k.strip() for k in keep if k.strip())
            ops.append((e["start"], e["end"], new_text))

for start, end, repl in ops:
    md = md[:start] + repl + md[end:]

# срезаем позиционные маркеры с оставшихся (непривязанных) сегментов-подписей
md = re.sub(r"(?:\*\*)?\s*(?:(?:OPPOSITE PAGE|PREVIOUS PAGES)[,\s]+)?(?:ABOVE|BELOW|LEFT|RIGHT|TOP|BOTTOM|MIDDLE|CENTRE|CENTER|FAR LEFT|FAR RIGHT|BELOW LEFT|BELOW RIGHT|ABOVE LEFT|ABOVE RIGHT)(?:[,\s]+(?:ABOVE|BELOW|LEFT|RIGHT|TOP|BOTTOM|FAR))*\s*:\s*(?:\*\*)?\s*", " ", md)
md = re.sub(r"\n{3,}", "\n\n", md)

open(out_path, "w", encoding="utf-8").write(md)
n_fig = md.count("<figure>")
print(f"figure-блоков: {n_fig}, замен текстовых юнитов: {sum(1 for s,e,r in ops if not r.startswith('<figure'))}")
print(f"старых markdown-ссылок ![] осталось: {len(re.findall(r'!\[', md))}")
print(f"позиционных маркеров с двоеточиями осталось: {len(re.findall(r'[A-Z][A-Z ,]+:', md))}")
