#!/usr/bin/env python3
"""Пробник для ReadEra: неделимые блоки <figure>фото+figcaption</figure> на выбранных страницах.
Использование: probe_figures.py <merged.md> <pagedir> <out.epub> <p1,p2-p3,...>"""
import re, sys, subprocess, os, shutil

md_path, img_dir, out_epub, pages_arg = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
want = set()
for part in pages_arg.split(","):
    a, _, b = part.partition("-")
    want.update(range(int(a), int(b or a) + 1))

md = open(md_path, encoding="utf-8").read()
# режем поток на элементы: заголовки, картинки, абзацы
elems = []
for chunk in re.split(r"\n\n+", md):
    c = chunk.strip()
    if not c:
        continue
    elems.append(c)

out, cur_page = [], None
for i, c in enumerate(elems):
    m = re.match(r"!\[[^\]]*\]\((_page_\d+_[^)]+)\)", c)
    if m:
        pm = re.search(r"_page_(\d+)_", m.group(1))
        cur_page = int(pm.group(1)) if pm else cur_page
        if cur_page in want:
            # ищем следующий текст-элемент, не картинку и не заголовок
            j = i + 1
            while j < len(elems) and re.match(r"!\[", elems[j]):
                j += 1
            cap = ""
            if j < len(elems) and not elems[j].startswith("#"):
                cap = elems[j]
                cap = re.sub(r"^(\*\*)?(LEFT|RIGHT|TOP|BOTTOM|ABOVE|BELOW|CENTRE|CENTER|OPPOSITE PAGE)[,:\s]*(ABOVE|BELOW|LEFT|RIGHT|TOP|BOTTOM)?[,:]*\s*(\*\*)?", "", cap, flags=re.I)
                cap = cap.strip()
            out.append(f'<figure>\n<img src="{m.group(1)}"/>\n<figcaption>{cap}</figcaption>\n</figure>')
    elif cur_page in want and not c.startswith("![]") and not re.match(r"!\[", c):
        # текст, уже съедённый как подпись, не дублируем — грубая проверка ниже по сборке
        pass

probe_md = img_dir + "/probe.md"
open(probe_md, "w", encoding="utf-8").write("\n\n".join(out))
css = "figure{break-inside:avoid;page-break-inside:avoid;margin:0.5em 0} figcaption{font-size:0.85em;font-style:italic;line-height:1.3;margin-top:0.3em}"
r = subprocess.run(["ebook-convert", probe_md, out_epub, "--title", "Figure probe", "--extra-css", css,
                    "--language", "en"], capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-1500:]); sys.exit(1)
print("OK:", out_epub, f"{os.path.getsize(out_epub)/1e6:.1f} MB, figure-блоков: {len(out)}")
