#!/usr/bin/env python3
"""Слияние чанков run_chunks.zsh в одну папку: merged.md + все картинки.
Использование: merge_chunks.py <seg_root> <имя_книги_в_чанках> <dst>"""
import sys, glob, os, shutil
seg_root, name, dst = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(dst, exist_ok=True)
mds = []
for d in sorted(glob.glob(f"{seg_root}/seg_*/")):
    md = glob.glob(f"{d}{name}/*.md")
    if md:
        mds.append(open(md[0], encoding="utf-8").read())
        for img in glob.glob(f"{d}{name}/*.jpeg") + glob.glob(f"{d}{name}/*.jpg") + glob.glob(f"{d}{name}/*.png"):
            shutil.copy(img, dst)
    elif not os.path.exists(d + ".done"):
        print("ВНИМАНИЕ: чанк без результата:", d, file=sys.stderr)
open(f"{dst}/merged.md", "w", encoding="utf-8").write("\n".join(mds))
print(f"{len(mds)} чанков -> {dst}/merged.md, {len(os.listdir(dst))-1} картинок")
