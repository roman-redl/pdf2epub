#!/usr/bin/env python3
"""Диагностика PDF: текстовый слой, страницы, картинки, DPI. Рендерит образцы."""
import sys, os
import fitz  # pymupdf

def probe(path, outdir):
    doc = fitz.open(path)
    n = len(doc)
    name = os.path.basename(path)[:40]
    print(f"\n=== {name} — {n} стр., {os.path.getsize(path)/1e6:.0f} МБ")
    idxs = sorted(set([0, n//8, n//4, n//2, 3*n//4, n-2, n-1]))
    total_chars, total_imgs, img_dpis = 0, 0, []
    for i in idxs:
        p = doc[i]
        txt = p.get_text().strip()
        chars = len(txt)
        words = len(txt.split())
        imgs = p.get_images(full=True)
        rect = p.rect
        for x in imgs:
            try:
                pix = fitz.Pixmap(doc, x[0])
                disp_w_in = rect.width / 72
                if disp_w_in > 0.5:  # только крупные изображения
                    img_dpis.append(int(pix.width / disp_w_in))
                pix = None
            except Exception:
                pass
        total_chars += chars; total_imgs += len(imgs)
        print(f"  стр.{i+1:>4}: текст {chars:>5} симв / {words:>4} слов | картинок {len(imgs)} | {rect.width:.0f}x{rect.height:.0f}pt")
        pm = p.get_pixmap(dpi=110)
        pm.save(os.path.join(outdir, f"p{i+1:04d}.png"))
    avg = total_chars // len(idxs)
    print(f"  >>> ср. {avg} симв/стр (по выборке) — {'ТЕКСТОВЫЙ СЛОЙ ЕСТЬ' if avg > 200 else 'СЛАБЫЙ/НЕТ — НУЖЕН OCR'}")
    if img_dpis:
        print(f"  >>> крупных картинок на стр.: {total_imgs//len(idxs)}, эффективный DPI: min {min(img_dpis)}, med {sorted(img_dpis)[len(img_dpis)//2]}")
    doc.close()

if __name__ == "__main__":
    outdir = sys.argv[-1]
    for p in sys.argv[1:-1]:
        probe(p, outdir)
