#!/usr/bin/env python3
"""Build KDP-ready interior PDFs from HTML manuscript templates.

Usage:
    python3 build.py --template fiction --trim 6x9
    python3 build.py --template nonfiction --trim 8.5x11
    python3 build.py --all

Front matter (everything before the BOOK BODY STARTS HERE marker in the
template) is typeset in lowercase roman numerals; the body restarts at
page 1 on a right-hand page, the way a printed book opens. Mirrored
margins follow the KDP no-bleed guidelines for the chosen trim size,
widening automatically if the page count crosses a KDP tier. For
nonfiction, the table of contents page (a div with id="toc-placeholder")
is filled in automatically from the rendered chapter headings.
"""

import argparse
import html as html_mod
import io
import re
import sys
from pathlib import Path

try:
    from weasyprint import HTML, CSS
    import pypdf
except ImportError as exc:
    sys.exit(f"Missing dependency: {exc}\n"
             "Install with:  pip install weasyprint pypdf")

ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"
BASE_CSS = ROOT / "assets" / "base.css"
MARKER = re.compile(r"\s*<!--\s*BOOK BODY STARTS HERE\s*-->\s*")
TOC_PLACEHOLDER = re.compile(r'\s*<div id="toc-placeholder"></div>\s*')
META_KEYS = ("title", "subtitle", "author", "publisher", "year", "isbn")
TOC_PLACEHOLDER_DEFAULT = (
    '<div class="toc-heading">Contents</div>\n'
    "<table class=\"toc\">\n"
    "<tr><td class=\"toc-title\">Your chapters will appear here</td>"
    "<td class=\"toc-page\">-</td></tr>\n</table>\n"
)

TRIMS = {
    "5x8": (5.0, 8.0),
    "6x9": (6.0, 9.0),
    "8.5x11": (8.5, 11.0),
}

TOP_MARGIN = 0.75
BOTTOM_MARGIN = 0.75
OUTSIDE_MARGIN = 0.5
GUTTER_HEADROOM = 0.25

# KDP "no bleed" minimum gutters by page count (self-published trim sizes
# 5x8, 6x9, 8.5x11): https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6
KDP_GUTTER_TIERS = (
    (150, 0.375),
    (300, 0.5),
    (500, 0.625),
    (700, 0.75),
    (828, 0.875),
)


def gutter_for_page_count(page_count: int) -> float:
    """KDP-recommended minimum gutter plus a headroom allowance."""
    for max_pages, minimum in KDP_GUTTER_TIERS:
        if page_count <= max_pages:
            return minimum + GUTTER_HEADROOM
    return KDP_GUTTER_TIERS[-1][1] + GUTTER_HEADROOM


def page_css(trim: str, gutter: float, mode: str) -> CSS:
    """Trim/margin CSS. mode is 'front' (roman numerals) or 'body' (arabic)."""
    width, height = TRIMS[trim]
    footer = ("counter(page, lower-roman)" if mode == "front"
              else "counter(page)")
    suppress_on_first = ("" if mode == "body" else
                         "\n@page :first { @bottom-center { content: none; } }")
    return CSS(string=f"""
        @page {{
            size: {width}in {height}in;
            margin-top: {TOP_MARGIN}in;
            margin-bottom: {BOTTOM_MARGIN}in;
            @bottom-center {{ content: {footer}; }}
        }}
        @page :left {{ margin-right: {gutter}in; margin-left: {OUTSIDE_MARGIN}in; }}
        @page :right {{ margin-left: {gutter}in; margin-right: {OUTSIDE_MARGIN}in; }}
        {suppress_on_first}
    """)


def read_meta(source: str) -> dict:
    meta = {}
    for key in META_KEYS:
        match = re.search(
            rf'<meta\s+name="kdp:{key}"\s+content="(.*?)"\s*/?>', source)
        if match:
            meta[key] = html_mod.unescape(match.group(1))
    meta.setdefault("title", "Untitled Book")
    meta.setdefault("subtitle", "")
    meta.setdefault("author", "Author Name")
    meta.setdefault("year", "2026")
    return meta


def split_template(source: str, meta: dict):
    """Split template at the BOOK BODY STARTS HERE marker."""
    match = MARKER.search(source)
    if not match:
        raise ValueError(
            'Template is missing the marker "<!-- BOOK BODY STARTS HERE -->". '
            "Everything before the marker is typeset as front matter, "
            "everything after it as the body.")
    front_src = source[:match.start()] + "\n</body>\n</html>\n"
    body_title = html_mod.escape(meta["title"])
    body_author = html_mod.escape(meta.get("author", ""))
    body_src = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        f"<title>{body_title}</title>\n"
        f"<meta name=\"author\" content=\"{body_author}\">\n"
        "</head>\n<body>\n"
        + source[match.end():]
    )
    return front_src, body_src


def inject_toc(front_html: str, outline):
    rows = []
    for entry in outline:
        page_number = html_mod.escape(str(entry["page"]))
        title = html_mod.escape(entry["title"])
        rows.append(
            f'<tr><td class="toc-title">{title}</td>'
            f'<td class="toc-page">{page_number}</td></tr>')
    toc_html = "<table class=\"toc\">\n" + "\n".join(rows) + "\n</table>"
    if not TOC_PLACEHOLDER.search(front_html):
        return front_html, False
    return TOC_PLACEHOLDER.sub(toc_html, front_html, count=1), True


def render(html_source: str, trim: str, gutter: float, mode: str):
    document = HTML(string=html_source, base_url=str(ROOT))
    return document.write_pdf(
        target=None,
        stylesheets=[CSS(filename=str(BASE_CSS)),
                     page_css(trim, gutter, mode)])


def render_body(body_html: str, trim: str, gutter: float):
    pdf_bytes = render(body_html, trim, gutter, "body")
    reader = pypdf.PdfReader(io_stream(pdf_bytes))
    outline = []
    for item in reader.outline:
        if isinstance(item, list):
            continue
        page_index = reader.get_destination_page_number(item)
        outline.append({"title": item.title.strip(), "page": page_index + 1})
    return pdf_bytes, len(reader.pages), outline


def io_stream(data: bytes) -> io.BytesIO:
    return io.BytesIO(data)


def build(template: Path, trim: str, outdir: Path, overrides: dict) -> dict:
    source = template.read_text(encoding="utf-8")
    meta = read_meta(source)
    meta.update({k: v for k, v in overrides.items() if v})
    front_src, body_src = split_template(source, meta)

    gutter = gutter_for_page_count(0)
    for _ in range(6):
        body_pdf, body_pages, outline = render_body(body_src, trim, gutter)
        front_final, toc_generated = inject_toc(front_src, outline)
        front_pdf = render(front_final, trim, gutter, "front")
        front_reader = pypdf.PdfReader(io_stream(front_pdf))
        front_pages = len(front_reader.pages)
        new_gutter = gutter_for_page_count(front_pages + body_pages)
        if new_gutter == gutter:
            break
        gutter = new_gutter
    else:
        sys.exit("Could not stop growing the gutter; the template is "
                 "unusually long. Please report this as a bug.")

    page_w, page_h = TRIMS[trim]
    writer = pypdf.PdfWriter()
    writer.append(front_reader)
    if front_pages % 2 == 1:
        writer.add_blank_page(width=int(page_w * 72), height=int(page_h * 72))
        blank_inserted = True
    else:
        blank_inserted = False
    writer.append(pypdf.PdfReader(io_stream(body_pdf)))
    writer.add_metadata({
        "/Title": f"{meta['title']} — {meta['subtitle']}".strip(" —"),
        "/Author": meta["author"],
        "/Producer": "KDP Interior Templates (WeasyPrint)",
    })

    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"{template.stem}-{trim}.pdf"
    with open(out_path, "wb") as handle:
        writer.write(handle)

    total = front_pages + body_pages + (1 if blank_inserted else 0)
    return {
        "template": template.stem,
        "trim": trim,
        "output": out_path,
        "front_pages": front_pages,
        "body_pages": body_pages,
        "total_pages": total,
        "gutter": gutter,
        "blank_inserted": blank_inserted,
        "toc_generated": toc_generated,
        "chapters": len(outline),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--template", help="template name (fiction, nonfiction, "
                        "worksheet) or a path to your own HTML file")
    parser.add_argument("--trim", choices=sorted(TRIMS),
                        help="finished book size before binding")
    parser.add_argument("--all", action="store_true",
                        help="build every template in every trim")
    parser.add_argument("--outdir", default=str(ROOT / "build"))
    parser.add_argument("--title"); parser.add_argument("--subtitle")
    parser.add_argument("--author"); parser.add_argument("--publisher")
    parser.add_argument("--year"); parser.add_argument("--isbn")
    return parser.parse_args(argv)


def resolve_template(name: str) -> Path:
    candidate = Path(name)
    if candidate.suffix or any(sep in name for sep in ("/", "\\")):
        if not candidate.is_file():
            sys.exit(f"Template file not found: {name}")
        return candidate
    built_in = TEMPLATE_DIR / f"{name}.html"
    if not built_in.is_file():
        sys.exit(f"Unknown template '{name}'. Built-in templates: "
                 + ", ".join(sorted(p.stem for p in TEMPLATE_DIR.glob("*.html"))))
    return built_in


def main(argv=None) -> int:
    args = parse_args(argv)
    overrides = {key: getattr(args, key) for key in META_KEYS}
    outdir = Path(args.outdir)

    jobs = []
    if args.all:
        for template in sorted(TEMPLATE_DIR.glob("*.html")):
            jobs.extend((template, trim) for trim in sorted(TRIMS))
    else:
        if not args.template or not args.trim:
            sys.exit("Specify --template and --trim (or use --all). "
                     "Example: python3 build.py --template fiction --trim 6x9")
        jobs.append((resolve_template(args.template), args.trim))

    for template, trim in jobs:
        stats = build(template, trim, outdir, overrides)
        print(f"[{stats['template']} / {stats['trim']}] "
              f"{stats['total_pages']} pages "
              f"(front matter {stats['front_pages']}, body {stats['body_pages']}, "
              f"gutter {stats['gutter']:.3f}\") "
              f"-> {stats['output'].relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
