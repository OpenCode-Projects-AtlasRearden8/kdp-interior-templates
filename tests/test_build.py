"""Tests for build.py: every trim build must emit a valid PDF at the
exact trim size, with front matter and page numbers in place."""

import importlib.util
import sys
from pathlib import Path

import pypdf
import pytest

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
build_mod = importlib.util.module_from_spec(spec)
sys.modules["build"] = build_mod
spec.loader.exec_module(build_mod)

# KDP trim sizes in PDF points (1 inch = 72 points)
TRIM_POINTS = {
    "5x8": (360, 576),
    "6x9": (432, 648),
    "8.5x11": (612, 792),
}

TEMPLATES = {"fiction", "nonfiction", "worksheet"}


def build(tmp_path, template, trim):
    return build_mod.build(
        template=ROOT / "templates" / f"{template}.html",
        trim=trim,
        outdir=tmp_path,
        overrides={},
    )


# Build fixtures once per session; each build is a real WeasyPrint render,
# so keep the count reasonable while still covering every template and trim.


@pytest.fixture(scope="session")
def build_fiction_5x8(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("fiction-5x8")
    return build(tmp, "fiction", "5x8"), tmp


@pytest.fixture(scope="session")
def build_nonfiction_6x9(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("nonfiction-6x9")
    return build(tmp, "nonfiction", "6x9"), tmp


@pytest.fixture(scope="session")
def build_worksheet_8x511(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("worksheet-8.5x11")
    return build(tmp, "worksheet", "8.5x11"), tmp


def test_every_trim_emits_valid_pdf(tmp_path):
    """Core guarantee: each trim build produces a valid PDF at that size."""
    for trim, (width_pt, height_pt) in TRIM_POINTS.items():
        stats = build(tmp_path, "fiction", trim)
        out = stats["output"]
        assert out.is_file() and out.stat().st_size > 0
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == stats["total_pages"] > 0
        box = reader.pages[0].mediabox
        assert (float(box.width), float(box.height)) == (
            float(width_pt), float(height_pt)), \
            f"trim {trim}: expected {width_pt}x{height_pt}pt, got {box}"
        for page in reader.pages[1:]:
            b = page.mediabox
            assert (float(b.width), float(b.height)) == (float(width_pt),
                                                         float(height_pt))


def test_each_template_builds_at_6x9(tmp_path):
    for template in sorted(TEMPLATES):
        stats = build(tmp_path, template, "6x9")
        reader = pypdf.PdfReader(str(stats["output"]))
        box = reader.pages[0].mediabox
        assert (float(box.width), float(box.height)) == (432.0, 648.0)


def test_template_names_match_files():
    assert {p.stem for p in (ROOT / "templates").glob("*.html")} == TEMPLATES


def test_front_matter_then_body_starts_at_recto(build_fiction_5x8):
    stats, _ = build_fiction_5x8
    assert stats["front_pages"] >= 2          # title page + copyright page
    # Even front-matter count means no blank page is needed; odd count
    # means exactly one blank verso was inserted.
    expected = stats["front_pages"] + stats["body_pages"]
    expected += stats["front_pages"] % 2
    assert stats["total_pages"] == expected


def test_page_numbers_present_in_body(build_fiction_5x8):
    stats, tmp = build_fiction_5x8
    reader = pypdf.PdfReader(str(stats["output"]))
    last = reader.pages[-1].extract_text() or ""
    assert str(stats["body_pages"]) in last.replace("\n", " ")


def test_title_page_is_unnumbered_and_copyright_shows_ii(build_fiction_5x8):
    stats, _ = build_fiction_5x8
    reader = pypdf.PdfReader(str(stats["output"]))
    title_text = (reader.pages[0].extract_text() or "").strip()
    assert "The Lighthouse Keeper" in title_text
    assert "ii" not in title_text.lower().replace("the lighthouse keeper", "")
    copyright_text = reader.pages[1].extract_text() or ""
    assert "ii" in copyright_text


def test_nonfiction_toc_gets_generated(build_nonfiction_6x9):
    stats, _ = build_nonfiction_6x9
    assert stats["toc_generated"] is True
    assert stats["chapters"] >= 3            # intro + three chapters
    reader = pypdf.PdfReader(str(stats["output"]))
    toc_text = reader.pages[2].extract_text() or ""
    assert "Introduction" in toc_text
    # TOC must reference body pages as arabic numbers starting at 1
    assert re_search(r"\n1\b", toc_text) or " 1" in toc_text


def re_search(pattern, text):
    import re
    return re.search(pattern, text)


def test_pdf_metadata_and_bookmarks(build_nonfiction_6x9):
    stats, _ = build_nonfiction_6x9
    reader = pypdf.PdfReader(str(stats["output"]))
    assert reader.metadata.title.startswith("The Massive AI Manual")
    assert reader.metadata.author == "Your Name Here"
    outlines = reader.outline
    assert outlines and not isinstance(outlines[0], list)
    assert "Introduction" in outlines[0].title


def test_marker_required(tmp_path):
    bad_dir = tmp_path / "templates"
    bad_dir.mkdir()
    bad = bad_dir / "nofiction.html"
    bad.write_text("<html><head><meta name=\"kdp:title\" content=\"x\">"
                   "</head><body><p>no marker</p></body></html>")
    with pytest.raises(ValueError):
        build_mod.build(bad, "6x9", bad_dir, {})


def test_missing_marker_message(tmp_path):
    bad_dir = tmp_path / "templates2"
    bad_dir.mkdir()
    bad = bad_dir / "bad.html"
    bad.write_text("<html><body><p>x</p></body></html>")
    with pytest.raises(ValueError, match="BOOK BODY STARTS HERE"):
        build_mod.build(bad, "6x9", bad_dir, {})


def test_gutter_tiers():
    assert build_mod.gutter_for_page_count(120) == 0.375 + 0.25
    assert build_mod.gutter_for_page_count(151) == 0.5 + 0.25
    assert build_mod.gutter_for_page_count(501) == 0.75 + 0.25
