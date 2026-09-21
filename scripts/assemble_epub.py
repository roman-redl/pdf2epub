#!/usr/bin/env python3
"""Сборка EPUB из вывода marker: чистка, переносы, метаданные, обложка, ebook-convert."""
import argparse, glob, os, re, shutil, subprocess, sys
import pymupdf

def clean_md(md):
    # пустые ссылки на картинки
    md = re.sub(r'!\[\]\(\)', '', md)
    # склейка переносов с конца строки: "judg-\nment" -> "judgment" (строчная после дефиса)
    md = re.sub(r'(\w+)-\n([a-z])', r'\1\2', md)
    # составные через перенос: "well-\nknown" -> "well-known"
    md = re.sub(r'(\w+)-\n([A-Z])', r'\1-\2', md)
    return md

def extract_cover(src_pdf, out_jpg):
    doc = pymupdf.open(src_pdf)
    p = doc[0]
    pix = p.get_pixmap(dpi=200)
    pix.save(out_jpg)
    doc.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker_out", required=True, help="папка вывода marker")
    ap.add_argument("--title", required=True)
    ap.add_argument("--authors", required=True)
    ap.add_argument("--src_pdf", required=True, help="для обложки")
    ap.add_argument("--out", required=True, help="итоговый .epub")
    ap.add_argument("--css", default=None, help="extra-css файл для ebook-convert")
    args = ap.parse_args()

    work = args.marker_out.rstrip("/") + "_epub"
    if os.path.exists(work):
        shutil.rmtree(work)
    shutil.copytree(args.marker_out, work)
    mds = sorted(glob.glob(work + "/**/*.md", recursive=True))
    md_path = next((m for m in mds if m.endswith("merged.md")), mds[0])

    md = open(md_path, encoding="utf-8").read()
    md = clean_md(md)
    open(md_path, "w", encoding="utf-8").write(md)

    cover = os.path.join(work, "cover.jpg")
    extract_cover(args.src_pdf, cover)

    tmp_epub = os.path.join(work, "book.epub")
    cmd = ["ebook-convert", md_path, tmp_epub,
           "--title", args.title, "--authors", args.authors,
           "--language", "en", "--cover", cover,
           "--preserve-cover-aspect-ratio",
           "--chapter", "//h:h2",
           "--level1-toc", "//h:h1|//h:h2",
           "--level2-toc", "//h:h3|//h:h4"]
    if args.css:
        cmd += ["--extra-css", open(args.css, encoding="utf-8").read()]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:]); print(r.stderr[-2000:]); sys.exit(1)
    shutil.move(tmp_epub, args.out)
    print("OK:", args.out, f"{os.path.getsize(args.out)/1e6:.1f} MB")

if __name__ == "__main__":
    main()
