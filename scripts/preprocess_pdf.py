#!/usr/bin/env python3
"""Предобработка фото-книги (снимки страниц): развороты -> страницы, денойз,
апскейл x4, шарп, пересборка в портретный PDF для OCR.
Использование: preprocess_pdf.py <in.pdf> <out.pdf> [страницы_титула_целиком]
Исходники-страницы пишутся в <out>.pages/, JPEG-версия PDF -- в <out>."""
import sys, os
import numpy as np
import pymupdf
import cv2

src, out_pdf = sys.argv[1], sys.argv[2]
SCALE = 4
out_imgs = out_pdf + ".pages"
os.makedirs(out_imgs, exist_ok=True)
doc = pymupdf.open(src)

def enhance(bgr):
    img = cv2.fastNlMeansDenoisingColored(bgr, None, 5, 5, 7, 21)
    img = cv2.resize(img, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(img, (0, 0), 3)
    return cv2.addWeighted(img, 1.6, blur, -0.6, 0)

pages, n = [], 0
for i in range(len(doc)):
    p = doc[i]
    imgs = p.get_images(full=True)
    rects = [p.get_image_rects(x[0])[0] for x in imgs] if imgs else []
    for k in sorted(range(len(imgs)), key=lambda k: rects[k].x0):
        pix = pymupdf.Pixmap(doc, imgs[k][0])
        if pix.n - pix.alpha > 3:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        e = enhance(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
        f = f"{out_imgs}/p{n:03d}.png"
        cv2.imwrite(f, e)
        pages.append((f, e.shape[1], e.shape[0])); n += 1
        if i % 20 == 0:
            print(f"лист {i+1}/{len(doc)}, стр. {n}", flush=True)

res = pymupdf.open()
for f, w, h in pages:
    img = cv2.imread(f)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    page = res.new_page(width=w / SCALE, height=h / SCALE)
    page.insert_image(page.rect, stream=buf.tobytes())
res.save(out_pdf, deflate=True, garbage=3)
print(f"готово: {n} стр. -> {out_pdf}")
