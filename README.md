# pdf2epub — PDF → EPUB, local and free

Converts scanned/photographed books to EPUB with OCR (Surya), extracted color
illustrations, a cover, and a table of contents. The goal: night reading in
ReadEra — text recolors, images stay in full color. Fully local, no clouds.

## How to use

**The easy path — hand it to an agent (Claude Code):** drop the PDF into
`books/` and say "convert this book to EPUB". The agent runs the pipeline and
handles the pitfalls documented in CLAUDE.md.

**By hand** (without an agent):

1. Diagnostics: text layer? DPI? scan or photo?
   `.venv/bin/python scripts/diagnose.py books/X.pdf work/samples`
2. Chunked OCR (marker 2.0, short runs — works around the MPS bug, see CLAUDE.md):
   `scripts/run_chunks.zsh work/in_folder work/out_root DPI TOTAL_PAGES [CHUNK]`
   (marker 2.0 takes a folder — put a symlink to the PDF inside)
3. Merge: `.venv/bin/python scripts/merge_chunks.py work/out_root name work/merged`
4. (photo book with photographed pages) — before step 2:
   `.venv/bin/python scripts/preprocess_pdf.py input.pdf work/enhanced.pdf`
   then OCR the enhanced.pdf
5. Manual markdown polish (chapter headings, cleanup) — done by the agent per
   book, one-off (past examples live outside git, in `work/one_offs/`).
6. EPUB assembly (Calibre `ebook-convert` must be in PATH):
   `.venv/bin/python scripts/assemble_epub.py --marker_out work/merged \
     --title "..." --authors "..." --src_pdf source.pdf --out out/X.epub`

## Semantic caption binding (photo reference books)

Photo reference books often use positional captions ("LEFT:", "OPPOSITE
PAGE:") that break apart in reflow. Workflow:

1. `scripts/extract_elements.py` → page-by-page inventory: photos + text units
   with byte offsets.
2. Vision pass over every photo (`mcp__zai-mcp-server__analyze_image`): a
   one-sentence description of what is depicted. ~2K tokens/image; the content
   filter rejects ~1% of photos on this topic — those fall back to geometry.
3. Manual semantic matching, **verified-only policy**: rebind a caption to a
   photo only when the vision description and the caption text clearly agree.
   Ambiguous → leave the old order. A wrong binding is worse than a distant one.
4. Lessons: position markers (LEFT/RIGHT) refer to the printed spread, not the
   reader screen — treat them as hints, never as rules; markers in caption text
   of one caption covering several photos of a plate → attach to the first
   photo, leave the rest bare; captions can describe photos on previous or
   opposite pages (check neighbors when a marker mismatches).
5. `scripts/rebuild_figures.py`: applies pairs to the markdown
   (`<figure><img/><figcaption>`), removes consumed caption segments from the
   text flow (no duplicates), strips leftover position markers.
6. Test the CSS probe first (`scripts/probe_figures.py` + `figure.css` with
   `break-inside: avoid`) in the target reader before running the whole pass.

Cost estimate: ~1 photo ≈ 2K vision tokens + a few seconds, so budget
accordingly for the book size (e.g. ~350 photos ≈ 0.7–1M tokens + 1–1.5 h).
Book-specific artifacts (descriptions, pairs) stay in `work/` — not committed.

## Known limitations

- **Reflow is mandatory** (decision, 2026-09-09): selectable text is needed
  for translation and vocabulary building, and per-page zoom is unacceptable.
  Therefore any CBZ/fixed-layout/full-page-image approach is off the table,
  even though EPUB images are not inverted in night mode.
- Photo reference books with positional captions ("this item on the left,
  that one on the right") lose the strict caption↔photo binding in reflow:
  the order is preserved, but on a phone screen the pair can drift apart.
  The semantic binding section above is the mitigation; plates with one
  caption for many small photos can only get the caption attached to the
  first photo.
- marker shreds decorative title spreads into fragments: fix by replacing
  them with full-page renders of those pages.
- Paragraph spacing in ReadEra is adjustable in the reader itself.

## Environment

- `.venv` — Python 3.14, marker-pdf 2.0 (chunked! see CLAUDE.md), surya-ocr
- `.venv2` — Python 3.12, marker-pdf 1.8.0 (fast MPS variant, but slightly
  dirtier text: detached periods)
- brew: llama.cpp (needed by surya 0.22), calibre (ebook-convert)
- Models: `~/.cache/huggingface` (surya-ocr-2-gguf, surya_layout2)
