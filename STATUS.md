# STATUS

**Project:** KDP Interior Templates — print-on-demand book interior builder
**Owner:** Asdale Dynamics, LLC
**Date:** October 25, 2026

## What was built

A template repo that turns HTML manuscripts into KDP-ready paperback
interior PDFs. Paste your manuscript into one of three HTML templates,
run one build script, and receive a trim-size-correct, print-ready PDF.

Components:

- `build.py` — single build script. Splits each template at the
  `<!-- BOOK BODY STARTS HERE -->` marker into front matter and body,
  then:
  - typesets front matter with lowercase roman folios (title page
    unnumbered, copyright ii, ...),
  - typesets the body restarting at page 1 on a right-hand page,
    implementing true recto/verso mirrored margins,
  - inserts a blank verso automatically when front matter ends on a recto
    so body page 1 opens on the correct side,
  - auto-generates the nonfiction table of contents with real page
    numbers, parsed from the rendered PDF's bookmark outline (two-pass
    build; converges when gutter tiers change pagination),
  - widens gutters automatically per KDP no-bleed tiers (0.625" starting,
    up to 1.125" for 700+ pages) and re-renders until stable,
  - merges front matter + body into one PDF with pypdf and embeds
    title/author metadata.
- `assets/base.css` — all typography: Alegreya body, Albert Sans headings,
  drop caps, scene breaks, boxed tips, tables, checkboxes, ruled answer
  lines, TOC styling.
- `templates/fiction.html` — sample novel (4 chapters, sample prose).
- `templates/nonfiction.html` — sample beginner guide with auto-TOC,
  tips, tables, preformatted blocks, checklists.
- `templates/worksheet.html` — sample low-energy workbook: exercises,
  labeled write-in fields, ruled answer lines, checkboxes, page-break-per-
  worksheet.
- `tests/test_build.py` — 11 tests; each performs real WeasyPrint builds
  and verifies the resulting PDFs with pypdf.
- `README.md` — quick start, template reference, trim/margin tables, and a
  step-by-step KDP upload walkthrough.

## How to run it

```bash
pip install weasyprint pypdf pytest      # one-time setup
python3 build.py --template fiction --trim 6x9      # one book
python3 build.py --all                              # all 9 combinations
python3 -m pytest tests/ -v                         # test suite
```

PDFs are written to `build/<template>-<trim>.pdf`.

## Verification results

- `python3 build.py --all` — all 9 template/trim combinations build
  successfully (verified October 25, 2026).
- `python3 -m pytest tests/` — 11/11 passed.
- Page sizes verified via pypdf MediaBox across all pages:
  - 5x8 -> 360 x 576 pt
  - 6x9 -> 432 x 648 pt
  - 8.5x11 -> 612 x 792 pt
- Folio scheme verified by text extraction: title page unnumbered,
  copyright page shows "ii", dedication "iii", body pages numbered
  "1, 2, 3, ..." starting on a recto.
- Nonfiction TOC verified: chapter titles and correct arabic body page
  numbers generated automatically; PDF bookmarks present; PDF metadata
  (Title/Author) embedded.
- Visual spot-checks via pdftoppm: chapter opener with drop cap, worksheet
  pages, front matter all render correctly.

## Known gaps (intentional v1 scope)

- **No bleed support.** Builds target KDP "no bleed" interiors only;
  edge-to-edge art is out of scope until requested.
- **TOC is one level deep** (top-level bookmarks, i.e. `h1.chapter`
  headings; subsections are not listed).
- **TOC entries are text, not clickable links** — the merge across the
  front-matter/body renders drops internal hyperlinks; page numbers are
  accurate but not tappable in PDF readers.
- **Fonts depend on the build machine's installed system fonts** (falls
  back through Alegreya -> Georgia -> DejaVu Serif). WeasyPrint embeds
  whatever it uses, so output is portable, but exact fonts may vary on
  systems without these families.
- **Running heads** (chapter-name headers at the top of body pages) are
  not implemented; page numbers are bottom-center only.
- **KDP review is external:** the walkthrough assumes the current KDP
  paperback screens; wording may drift over time.
- Sample content in the templates is original placeholder prose meant to
  be replaced; it is not proofread literature.

## License

MIT — Copyright (c) 2026 Asdale Dynamics, LLC. See `LICENSE`.
