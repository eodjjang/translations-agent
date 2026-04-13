"""
PDF 분석·비텍스트 크롭·메타데이터 기록 (PyMuPDF 중심, GROBID 선택).

설계서: 표/그림/블록 수식/알고리즘은 텍스트 추출 없이 이미지 크롭 + 캡션은 메타데이터.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Install dependencies: pip install -r scripts/requirements.txt", file=sys.stderr)
    raise

try:
    import requests
except ImportError:
    requests = None  # type: ignore


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def paper_slug(stem: str) -> str:
    """논문 파일명에서 slug 생성 (예: '1706.03762v7' -> 'attention-is-all-you-need' 등).
    간단히 stem 그대로 사용; 에이전트가 후처리로 rename 가능."""
    return stem


def ensure_dirs(root: Path, slug: str) -> None:
    (root / "output" / slug / "assets").mkdir(parents=True, exist_ok=True)
    (root / "output" / slug / "src").mkdir(parents=True, exist_ok=True)


def fetch_grobid_tei(pdf_path: Path, grobid_base: str, timeout: float = 300.0) -> str | None:
    """GROBID /api/processFulltextDocument → TEI XML 문자열. 실패 시 None."""
    if requests is None:
        return None
    url = grobid_base.rstrip("/") + "/api/processFulltextDocument"
    try:
        with pdf_path.open("rb") as f:
            r = requests.post(
                url,
                files={"input": (pdf_path.name, f, "application/pdf")},
                timeout=timeout,
            )
        if r.status_code == 200:
            return r.text
    except OSError:
        return None
    return None


def extract_page_text_blocks(doc: fitz.Document) -> list[dict]:
    """페이지별 텍스트 블록 (좌표 포함) — 구조 추출 MVP."""
    blocks_out: list[dict] = []
    for page_index in range(len(doc)):
        page = doc[page_index]
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for b in blocks:
            if b.get("type") != 0:
                continue
            bbox = b.get("bbox")
            lines_text: list[str] = []
            for line in b.get("lines", []):
                spans = line.get("spans", [])
                lines_text.append("".join(s.get("text", "") for s in spans))
            text = "\n".join(lines_text).strip()
            if not text:
                continue
            blocks_out.append(
                {
                    "page": page_index + 1,
                    "bbox": list(bbox) if bbox else None,
                    "text": text,
                }
            )
    return blocks_out


def extract_images_as_assets(
    doc: fitz.Document,
    assets_dir: Path,
    paper_stem: str,
) -> list[dict]:
    """
    페이지 내 임베디드 이미지를 파일로 저장하고 매니페스트 항목 생성.
    고급 Figure/Table 분리는 GROBID+좌표 또는 후속 단계에서 보강.
    """
    manifest: list[dict] = []
    img_counter = 0
    for page_index in range(len(doc)):
        page = doc[page_index]
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
            except Exception:
                continue
            img_counter += 1
            ext = base.get("ext", "png")
            name = f"{paper_stem}_p{page_index + 1}_img{img_counter}.{ext}"
            out_path = assets_dir / name
            out_path.write_bytes(base["image"])
            manifest.append(
                {
                    "file": name,
                    "type": "figure",  # MVP: 세분류는 에이전트/후처리
                    "page": page_index + 1,
                    "caption": None,
                }
            )
    return manifest


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_extraction(
    pdf_path: Path,
    root: Path,
    grobid_url: str | None,
    slug_override: str | None = None,
) -> dict:
    paper_stem = pdf_path.stem
    slug = slug_override or paper_slug(paper_stem)
    ensure_dirs(root, slug)
    paper_dir = root / "output" / slug
    assets_dir = paper_dir / "assets"
    out_manifest = paper_dir / "assets_manifest.json"
    out_structure = paper_dir / "extracted_structure.json"
    out_progress = paper_dir / "progress.json"

    doc = fitz.open(pdf_path)
    try:
        text_blocks = extract_page_text_blocks(doc)
        manifest = extract_images_as_assets(doc, assets_dir, paper_stem)
    finally:
        doc.close()

    grobid_tei_path = None
    if grobid_url:
        tei = fetch_grobid_tei(pdf_path, grobid_url)
        if tei:
            grobid_tei_path = paper_dir / "grobid_fulltext.tei.xml"
            grobid_tei_path.write_text(tei, encoding="utf-8")

    structure = {
        "paper": pdf_path.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "text_blocks": text_blocks,
        "grobid_tei_file": str(grobid_tei_path).replace("\\", "/") if grobid_tei_path else None,
    }
    write_json(out_structure, structure)
    write_json(out_manifest, {"assets": manifest})

    progress = {
        "paper": pdf_path.name,
        "current_step": 2,
        "completed_sections": [],
        "pending_sections": [],
        "assets_extracted": True,
        "glossary_generated": False,
        "typst_compiled": False,
        "grobid_available": grobid_tei_path is not None,
    }
    write_json(out_progress, progress)

    return {
        "structure_path": out_structure,
        "manifest_path": out_manifest,
        "progress_path": out_progress,
        "asset_count": len(manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract PDF structure and crop embedded images.")
    parser.add_argument("pdf", type=Path, help="Input PDF under input/ or absolute path")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--grobid-url",
        default=None,
        help="e.g. http://127.0.0.1:8070 if GROBID Docker is running",
    )
    parser.add_argument(
        "--slug",
        default=None,
        help="Output folder name under output/ (default: PDF filename stem)",
    )
    args = parser.parse_args()
    root = args.root or project_root()
    pdf_path = args.pdf
    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    result = run_extraction(pdf_path.resolve(), root.resolve(), args.grobid_url, slug_override=args.slug)
    print(f"Structure: {result['structure_path']}")
    print(f"Manifest: {result['manifest_path']}")
    print(f"Progress: {result['progress_path']}")
    print(f"Embedded images saved: {result['asset_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
