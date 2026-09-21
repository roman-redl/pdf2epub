#!/usr/bin/env python3
"""Разбор merged markdown на элементы с оффсетами (универсально).
Элементы: img (файл, страница), heading (текст, уровень), text (абзац).
Выход work/ss_elements.json + сводка: какие страницы «однозначные» (после
каждого фото сразу его подпись-абзац), какие «сетки» (блок описывает N фото).
"""
import json, re, sys

md_path, out_path = sys.argv[1], sys.argv[2]
md = open(md_path, encoding="utf-8").read()

elements = []
img_re = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
pos = 0
last_img_end = None
for m in img_re.finditer(md):
    text = md[pos:m.start()]
    for chunk in re.split(r"\n\s*\n", text):
        c = chunk.strip()
        if not c:
            continue
        if c.startswith("#"):
            lvl = len(c) - len(c.lstrip("#"))
            elements.append({"type": "heading", "level": lvl, "text": c.lstrip("# ").strip(),
                             "start": md.find(c, pos), "end": md.find(c, pos) + len(c)})
        else:
            elements.append({"type": "text", "text": c,
                             "start": md.find(c, pos), "end": md.find(c, pos) + len(c)})
    fname = m.group(1)
    pm = re.search(r"_page_(\d+)_", fname)
    elements.append({"type": "img", "file": fname, "page": int(pm.group(1)) if pm else None,
                     "start": m.start(), "end": m.end()})
    pos = m.end()
for chunk in re.split(r"\n\s*\n", md[pos:]):
    c = chunk.strip()
    if c:
        elements.append({"type": "text" if not c.startswith("#") else "heading", "text": c.lstrip("# ").strip(),
                         "start": md.find(c, pos), "end": md.find(c, pos) + len(c)})

# позиционные слова в тексте
POSWORDS = re.compile(r"^\**\s*(OPPOSITE PAGE\s*,?\s*)?(ABOVE|BELOW|LEFT|RIGHT|TOP|BOTTOM|CENTRE|CENTER)"
                      r"([,\s]+(ABOVE|BELOW|LEFT|RIGHT|TOP|BOTTOM|CENTRE|CENTER))*\s*[:\.]?\s*\**", re.I)

# классификация страниц: считаем фото и подписи (текст-абзацы, начинающиеся
# с позиционного слова или короткие < 500 симв сразу после фото)
pages = {}
for i, e in enumerate(elements):
    if e["type"] != "img" or e["page"] is None:
        continue
    p = pages.setdefault(e["page"], {"imgs": [], "units": []})
    p["imgs"].append(i)
    # текст сразу после фото (до следующего img/heading)
    j = i + 1
    unit = []
    while j < len(elements) and elements[j]["type"] == "text":
        unit.append(j); j += 1
    if unit:
        p["units"].append(unit)

amb_pages = {}
for pg, p in pages.items():
    n_img, n_units = len(p["imgs"]), len(p["units"])
    # подпись = единица, где есть позиционные слова или она короткая
    n_caps = 0
    for u in p["units"]:
        t = " ".join(elements[k]["text"] for k in u)
        if POSWORDS.search(t) or len(t) < 500:
            n_caps += 1
    amb_pages[pg] = {"imgs": n_img, "units": n_units, "captions": n_caps,
                     "kind": "grid" if n_img > n_caps else "simple"}

json.dump({"elements": elements, "pages": {str(k): v for k, v in pages.items()}},
          open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

total_img = sum(len(v["imgs"]) for v in pages.values())
grids = {k: v for k, v in amb_pages.items() if v["kind"] == "grid"}
grid_imgs = sum(v["imgs"] for v in grids.values())
simple = len(amb_pages) - len(grids)
print(f"страниц: {len(pages)}, фото всего: {total_img}")
print(f"«простые» страницы (фото==подписи): {simple}, фото на них: {total_img - grid_imgs}")
print(f"«сетки» (фото > подписей): {len(grids)}, фото на них: {grid_imgs}")
