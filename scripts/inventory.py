#!/usr/bin/env python3
"""Инвентаризация merged markdown: постранично какие картинки и какие текст-блоки между ними.
Выход: JSON {page: {"images": [...], "units": [{"after_img": idx, "text": ...}]}}
Юнит = текст между соседними ссылками на картинки (или заголовками).
"""
import json, re, sys

md_path, out_path = sys.argv[1], sys.argv[2]
md = open(md_path, encoding="utf-8").read()

ref_re = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
units = []  # (последняя картинка перед текстом или None, текст)
pos = 0
last_img = None
for m in ref_re.finditer(md):
    text = md[pos:m.start()].strip()
    if text:
        units.append({"after_img": last_img, "text": text})
    last_img = m.group(1)
    pos = m.end()
tail = md[pos:].strip()
if tail:
    units.append({"after_img": last_img, "text": tail})

# привязка картинок к страницам
pages = {}
for u in units:
    if u["after_img"]:
        pm = re.search(r"_page_(\d+)_", u["after_img"])
        u["page"] = int(pm.group(1)) if pm else None
    if u.get("page") is not None:
        pages.setdefault(u["page"], {"images": [], "captions": []})
    if u["after_img"] and u.get("page") is not None:
        pages[u["page"]]["images"].append(u["after_img"])
        pages[u["page"]]["captions"].append(u["text"][:400])

json.dump({"pages": {str(k): v for k, v in pages.items() if k is not None},
           "units": [{k: v for k, v in u.items() if k != "after_img"} for u in units if u.get("page") is not None]},
          open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n_img = sum(len(v["images"]) for v in pages.values() if v)
n_txt = sum(len(v["captions"]) for v in pages.values() if v)
print(f"страниц с контентом: {sum(1 for v in pages.values() if v)}, картинок: {n_img}, текст-блоков: {n_txt}")
