"""
원본 PDF에서 표 영역을 이미지로 크롭하여 output/assets/에 저장.
extracted_structure.json의 bbox 좌표를 기반으로 영역을 결정한다.
"""
from __future__ import annotations
import sys
from pathlib import Path

try:
    import fitz
except ImportError:
    print("Install: pip install pymupdf", file=sys.stderr)
    raise


def crop_region(doc: fitz.Document, page_num: int, rect: fitz.Rect, out_path: Path, dpi: int = 300) -> None:
    page = doc[page_num - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, clip=rect)
    pix.save(str(out_path))
    print(f"  Saved: {out_path} ({pix.width}x{pix.height})")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Crop table regions from PDF as images.")
    parser.add_argument("pdf", type=Path, nargs="?", default=None, help="Input PDF path")
    parser.add_argument("--slug", default=None, help="Paper slug for output subfolder")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    pdf_path = args.pdf or root / "input" / "1706.03762v7.pdf"
    slug = args.slug or "attention-is-all-you-need"
    assets_dir = root / "output" / slug / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    doc = fitz.open(pdf_path)

    tables = [
        {
            "name": "table1",
            "page": 6,
            "rect": fitz.Rect(107, 68, 505, 185),
        },
        {
            "name": "table2",
            "page": 8,
            "rect": fitz.Rect(107, 68, 505, 245),
        },
        {
            "name": "table3",
            "page": 9,
            "rect": fitz.Rect(107, 68, 505, 390),
        },
        {
            "name": "table4",
            "page": 10,
            "rect": fitz.Rect(107, 68, 505, 240),
        },
    ]

    for t in tables:
        out_path = assets_dir / f"{t['name']}.png"
        print(f"Cropping {t['name']} from page {t['page']}...")
        crop_region(doc, t["page"], t["rect"], out_path)

    doc.close()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
