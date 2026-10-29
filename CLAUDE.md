# CLAUDE.md — pdf2epub

Local PDF → EPUB pipeline (Surya OCR + Calibre). macOS-only toolchain
(marker/Surya on Apple Silicon; see Pitfalls). Input: scanned/photographed
PDFs in `books/`, output: EPUBs in `out/`. Intermediates live in `work/`
(gitignored).

## Pipeline (end to end)

diagnostics (`scripts/diagnose.py`) → [photo book: `scripts/preprocess_pdf.py`]
→ chunked OCR (`scripts/run_chunks.zsh`) → merge (`scripts/merge_chunks.py`)
→ manual markdown polish (headings/cleanup, see `scripts/fix_toc.py` as an
example) → EPUB assembly (`scripts/assemble_epub.py`, calls `ebook-convert`).

**Sample before a full run (mandatory):** once the pipeline is tuned on
trial pages, build a SAMPLE-EPUB from the **first ~25 pages of the book in
sequence** (not scattered "representative" pages: the user reads the sample
linearly and checks it against the PDF page by page — they cannot jump
around the book as easily as the agent). Hand the file to the user for
review in a reader (ReadEra: night mode, highlighting, reflow). A full run
only after the user's explicit approval, never by default.

## Pitfalls (all verified the hard way, 2026-09-09)

- **marker 2.0 on Mac dies on long runs** — MPS bug
  (github.com/datalab-to/marker issue #960, still open): short runs fly, a full file hangs
  (CPU freezes, no errors in the log). Solution: chunks of ~24 pages only via
  `run_chunks.zsh` (it also does timeout-kill, zombie cleanup, chunk halving,
  resume via `.done` markers). Note: marker 2.1.0 (2026-10-29) swapped the
  Surya engine — retest the workaround once on a real book.
- **The auxiliary ocr_error model pulls its checkpoint from Amazon S3** — the
  connection can hang in CLOSE_WAIT for hours. Models are already cached →
  always run with `HF_HUB_OFFLINE=1`.
- **Zombie surya/llama-server servers survive pkill of marker** — after any
  kill, clean up: `pkill -9 -f "surya\."; pkill -9 -f llama-server`.
- **TCC:** the agent shell cannot read ~/Documents and ~/Desktop — ask the
  user to move files into `books/` in this repo (or grant Full Disk Access to
  the terminal).
- **marker 2.0 CLI takes a folder**, not a file: put a symlink to the PDF into
  `work/in_xxx/` and pass the folder. The 1.x CLI (`marker_single`) takes a file.
- Fallback: `.venv2` (python3.12 + marker 1.8.0) works without chunking and
  hangs, but the text is slightly dirtier ("by. constantly") — use only if
  chunked 2.0 completely fails.
- `pymupdf`: use `import pymupdf`, not `import fitz` (deprecated).

## EPUB assembly

`assemble_epub.py` strips empty `![]()` refs, rejoins hyphenated line breaks,
takes the cover from page 1 of `--src_pdf`, builds the TOC from headings
(`--level1-toc //h:h1|//h:h2`). Chapters must be `##` in markdown. Demote junk
H1s (poster fragments) to `**bold**` before assembly. For photo books, replace
the decorative title pages with full-page renders.

## Rules

- **Books whose content is mostly bright full-page images (atlases, photo
  books): stop BEFORE setting up the pipeline.** EPUB night mode recolors
  text only; maps/photos stay white over half the screen — a dark theme is
  fundamentally impossible, reflow does not help. Ask the user whether an
  EPUB is needed at all; alternatives: a PDF reader with full-page inversion
  (KOReader, Librera) or local PDF pre-inversion (render pages → invert
  brightness → reassemble the PDF). Case: History of the World Map by Map,
  2026-09-28 — dropped after the sample; user verdict: "converting such a
  book will turn out poorly".
- **File changes — Write/Edit tools only**, never `cat >`/python heredocs in
  Bash: diffs must be visible in the CLI and go through approval. Exception —
  programmatic transformation of large generated files: announce it explicitly
  and show a change summary. (2026-09-09)
- Commit messages: English, conventional prefix (`feat:`, `fix:`, `docs:` …),
  text only — no auto-added trailers (`Co-Authored-By: …`, "Generated with …").
- No clouds: local models and Calibre only.
- Never commit files from `books/` (gitignored, copyright).
- Before running a whole book — a 3–5 page trial (`--page_range`) and a
  text-quality check against the source; then a sample EPUB for the user's
  approval (see Pipeline) — full run only after an explicit "ок".
- Self-checks: contiguous chunk coverage, image refs set == files set, spot
  page checks via vision MCP (note: the content filter may block this book
  topic — then verify via captions in the text).
