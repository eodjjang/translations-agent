"""
arXiv 1506.02640 (YOLO v1) PDF에서 그림·식(3) 영역만 크롭해 assets/에 저장.
주변 본문·헤더·영문 캡션은 clip 직사각형에서 제외한다.

- 그림 2: 오른쪽 열만(좌측 본문 제외), 임베디드 패널 상단이 잘리지 않도록 y0를 충분히 올린다.
- 그림 4: 파이 차트 상단 라벨이 잘리지 않도록 y0를 충분히 올린다.
- 그림 5+6: 같은 페이지에서 세로로 이어지도록 두 구간을 크롭한 뒤 하나의 PNG로 병합한다.
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

import fitz

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore


def merge_vertical_png(
    top_bytes: bytes,
    bottom_bytes: bytes,
    *,
    gap_px: int = 8,
    bg: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """두 PNG 바이트를 같은 너비로 맞춘 뒤 세로로 이어 붙인다."""
    if Image is None:
        raise RuntimeError("Pillow is required: pip install Pillow")
    img5 = Image.open(io.BytesIO(top_bytes)).convert("RGB")
    img6 = Image.open(io.BytesIO(bottom_bytes)).convert("RGB")
    w = max(img5.width, img6.width)
    if img5.width != w:
        img5 = img5.resize((w, int(img5.height * w / img5.width)), Image.Resampling.LANCZOS)
    if img6.width != w:
        img6 = img6.resize((w, int(img6.height * w / img6.width)), Image.Resampling.LANCZOS)
    h = img5.height + gap_px + img6.height
    out = Image.new("RGB", (w, h), bg)
    out.paste(img5, (0, 0))
    out.paste(img6, (0, img5.height + gap_px))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Crop YOLO paper figures from PDF.")
    p.add_argument(
        "pdf",
        type=Path,
        nargs="?",
        default=None,
        help="Input PDF (default: input/1506.02640v5.pdf)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output assets dir (default: output/yolo-unified-real-time-object-detection/assets)",
    )
    p.add_argument("--dpi-scale", type=float, default=2.5, help="Matrix scale vs 72 dpi")
    args = p.parse_args()

    root = Path(__file__).resolve().parent.parent
    pdf_path = args.pdf or root / "input" / "1506.02640v5.pdf"
    out_dir = args.out or root / "output" / "yolo-unified-real-time-object-detection" / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", flush=True)
        return 1

    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(args.dpi_scale, args.dpi_scale)

    # (page_index_0based, filename, clip Rect in PDF points)
    specs: list[tuple[int, str, fitz.Rect]] = [
        (0, "figure1.png", fitz.Rect(306, 168, 546, 261)),
        # 우측 열만; 임베디드 이미지 상단(~203pt) 위로 여유
        (1, "figure2.png", fitz.Rect(305, 196, 548, 370)),
        (2, "figure3.png", fitz.Rect(46, 68, 566, 240)),
        (5, "figure4.png", fitz.Rect(300, 66, 552, 208)),
        (3, "eq3.png", fitz.Rect(48, 72, 292, 238)),
    ]

    for pidx, name, rect in specs:
        pix = doc[pidx].get_pixmap(matrix=mat, clip=rect)
        out_path = out_dir / name
        pix.save(str(out_path))
        print(f"{name} {pix.width}x{pix.height}", flush=True)

    # Figure 5 + 6 병합 (원문 'Figure 5:' 캡션 줄은 제외하고 시각 영역만)
    page8 = doc[7]
    r5 = fitz.Rect(44, 66, 558, 270)
    r6 = fitz.Rect(48, 293, 556, 502)
    pix5 = page8.get_pixmap(matrix=mat, clip=r5)
    pix6 = page8.get_pixmap(matrix=mat, clip=r6)
    merged = merge_vertical_png(pix5.tobytes("png"), pix6.tobytes("png"))
    merged_path = out_dir / "figure5_6.png"
    merged.save(str(merged_path), optimize=True)
    print(f"figure5_6.png {merged.width}x{merged.height}", flush=True)

    doc.close()
    print("Done.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
