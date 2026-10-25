# KDP Interior Templates

Print-ready book interiors for Amazon KDP, without buying design software.

Paste your manuscript into an HTML file, run one build script, and get a
PDF with the right trim size, mirrored margins, front matter, and page
numbers — ready to upload to Kindle Direct Publishing.

Three templates are included:

| Template | For | Trim sizes |
|---|---|---|
| `fiction` | novels, memoirs, short stories | 5x8, 6x9, 8.5x11 |
| `nonfiction` | guides and manuals (auto page-numbered TOC) | 5x8, 6x9, 8.5x11 |
| `worksheet` | workbooks, planners, fill-in exercises | 5x8, 6x9, 8.5x11 |

Made with warm, plain English by **Asdale Dynamics, LLC** — the same
beginner-first spirit as *The Massive AI Manual* and
[dylanasdale.github.io](https://dylanasdale.github.io). Licensed MIT (see
`LICENSE`).

---

## Quick start

You need Python 3.11+ and two pip packages:

```bash
pip install weasyprint pypdf pytest
```

Build a book:

```bash
python3 build.py --template fiction --trim 6x9
```

The PDF appears in `build/fiction-6x9.pdf`. That's it — that file uploads
to KDP as-is.

Check every template in every trim:

```bash
python3 build.py --all
```

Run the test suite (each test performs a real build and verifies the PDF):

```bash
python3 -m pytest tests/ -v
```

Optional overrides, in case you'd rather not edit the template's meta tags:

```bash
python3 build.py --template nonfiction --trim 6x9 \
    --title "My Book" --author "Me" --year 2026 --isbn "1234-5678"
```

You can also build a book from your own HTML file — copy a template, edit
it, and pass a path instead of a name:

```bash
python3 build.py --template my-book/my-manuscript.html --trim 5x8
```

## How a template works

Open any file in `templates/` and you'll see three zones, clearly marked:

1. **Meta tags at the top.** Fill in your title, subtitle, author, publisher,
   year, and ISBN. The build reads these for the title page and the PDF's
   embedded metadata.
2. **Front matter.** Title page, copyright page, dedication — everything
   your reader sees before the book starts. The build typesets all of this
   with lowercase roman numerals (i, ii, iii), and leaves your title page
   unnumbered, the way printed books do.
3. **The body, after the `<!-- BOOK BODY STARTS HERE -->` marker.** Paste
   your manuscript here. Everything after the marker starts numbering at
   page 1, on a right-hand (recto) page, with a blank verso inserted
   automatically if needed.

For nonfiction, a page with `<div id="toc-placeholder"></div>` is auto-filled:
the build reads your chapter headings and writes the **real page numbers**
into the table of contents for you. Never update a TOC by hand again.

Chapter headings use:

```html
<h1 class="chapter"><span class="ch-number">Chapter One</span>The Visitor</h1>
```

Every template header comment lists the helper classes you can use — scene
breaks, drop caps, boxed tips, tables, checkboxes, ruled answer lines, and
more.

## Trim sizes and margins (the sensible defaults)

The build handles margins for you using KDP's no-bleed guidelines. Pages
get mirrored margins (wider on the binding side), and the gutter widens
automatically once the page count crosses a KDP tier:

| Pages | KDP minimum gutter | This build uses (adds breathing room) |
|---|---|---|
| 24 – 150 | 0.375in | 0.625in |
| 151 – 300 | 0.5in | 0.75in |
| 301 – 500 | 0.625in | 0.875in |
| 501 – 700 | 0.75in | 1.0in |
| 701 – 828 | 0.875in | 1.125in |

Outside margins are 0.5in; top and bottom are 0.75in — all comfortably above
KDP's 0.25in minimums.

Which trim should you pick? 6x9 is the friendly default: big enough to read
comfortably, small enough to feel like a "real" book, and it's the most
common indie paperback size. 5x8 suits fiction and slim guides; 8.5x11 is
the workbook size, best for the `worksheet` template where people write in
the book.

## Uploading to KDP, step by step

This walkthrough covers the **interior file** you build here, plus the
screens you'll meet when publishing a paperback on
[kdp.amazon.com](https://kdp.amazon.com). Budget an unhurried hour the
first time; every step after that takes minutes.

**Before you start:** your final PDF from `python3 build.py --template ...
--trim ...`. Decide your trim size now, because the whole book is typeset
for it. Also have your description, author name, and a cover ready
(KDP sells you a free cover *creator* later — don't let the cover stall
step one).

**1. Make one account and start a paperback.** Sign in at kdp.amazon.com,
click **Create**, and choose **Paperback**. (Kindle eBooks don't take PDF
interiors — that's a different pipeline.)

**2. Fill in the title fields.** Language, Book Title, and Author exactly as
they should appear on the cover. Use the same author name you burn into the
template's meta tags — KDP reviewers compare them.

**3. Say no to the free ISBN, or yes if you've decided you don't care.**
KDP offers a free KDP-printed ISBN. If you have no ISBN plans of your own,
take it and put nothing in the template's ISBN slot — or leave the template
line `[ISBN will appear here]` and change it later. (KDP requires the
interior ISBN, when present, to match the one they assign or you supply.)

**4. Choose your trim size — the same one you built with.** In the
"Print options" section, pick the trim (6x9, 5x8, or 8.5x11) that you built
the PDF for. Mixing trims is the #1 source of upload rejections.

**5. Choose "No bleed."** Everything this repo produces is a no-bleed
interior (all content sits inside the margins, no edge-to-edge art).

**6. Choose "Print reprographic quality" vs. standard.** For text-only
books, standard is fine. If you use the `worksheet` template with shaded
boxes and expect precise grays, premium color costs more per copy — see
KDP's printing cost calculator before deciding.

**7. Upload the interior PDF.** Click **Upload manuscript**, choose the
file from your `build/` folder, wait for the preview. KDP's previewer will
ask you to confirm that no headers/footers sit inside the danger margins —
ours don't; that's what the mirrored gutters are for. KDP computes the
page count and printing cost from the file itself.

**8. Upload or create a cover.** If you clicked "Launch Cover Creator",
KDP will offer your chosen trim and a spine width computed from your page
count. If you designed your own, upload it.

**9. Preview both files** and click **Publish** once the previewer shows
green checks. KDP reviews the interior manually — usually within 72 hours.
If they ask for changes, rebuild here with slightly larger margins, and
re-upload; the page-number scheme stays consistent.

**Important:** Amazon reviews each book before it goes on sale, and their
policy prohibits misleading content — publish your own original writing.

## Customizing typography

`assets/base.css` holds every font, size, and style decision as plain CSS —
set the serif body font, heading font, text alignment, line height, and
colors in one place and all three templates follow. A safe, boring change
with visible impact: body text size (`html { font-size: 11pt }`) and line
height. Keep any change you make above KDP's minimum margins, rebuild, and
preview.

Fonts are embedded into the PDF automatically (subsetted), so no font
installation is needed on Amazon's end.

## Troubleshooting

- **`Missing dependency: ...`** — run `pip install weasyprint pypdf`.
- **WeasyPrint says Pango is missing** — some Linux systems need the
  system libraries first, e.g. `sudo apt install libpango-1.0-0
  libpangocairo-1.0-0 libgdk-pixbuf-2.0-0` (this is a one-time setup).
- **Template is missing the marker** — every template needs
  `<!-- BOOK BODY STARTS HERE -->` exactly once.
- **Odd page count after publish** — that's KDP adding a blank last page
  for binding; the interior PDF we produce is already well-formed, and KDP
  knows what to do.

## Project layout

```
build.py               one build script (front matter + auto TOC + merging)
assets/base.css        all typography and style decisions
templates/fiction.html          sample fiction manuscript — replace the text
templates/nonfiction.html       sample guide — replace the text
templates/worksheet.html        sample workbook — replace the pages
tests/test_build.py    builds every trim and verifies the PDFs
build/                 your generated PDFs (not committed)
```

## Credits and license

Built and maintained by **Asdale Dynamics, LLC** as part of a set of
beginner-friendly AI, publishing, and life-admin tools. Released under the
MIT License — see [`LICENSE`](LICENSE). Copyright (c) 2026 Asdale
Dynamics, LLC.
