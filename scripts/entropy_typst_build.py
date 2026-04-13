"""
entropy.pdf(Shannon 통신이론) 추출 JSON → 페이지별 한국어 번역 텍스트 + Typst 골격 생성.

deep-translator(Google)로 페이지 단위 번역. 오프라인/실패 시 영문 원문만 저장.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def merge_pages(structure: dict) -> dict[int, str]:
    blocks = structure["text_blocks"]
    by: dict[int, list] = defaultdict(list)
    for b in blocks:
        by[b["page"]].append(b)
    out: dict[int, str] = {}
    for pg in sorted(by.keys()):
        bb = sorted(by[pg], key=lambda x: (x["bbox"][1], x["bbox"][0]))
        out[pg] = "\n\n".join(x["text"] for x in bb)
    return out


def translate_text(text: str, *, max_chunk: int = 4200) -> str:
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        return text

    tr = GoogleTranslator(source="en", target="ko")

    def one(s: str) -> str:
        for attempt in range(4):
            try:
                return tr.translate(s) or s
            except Exception:
                time.sleep(1.5 * (attempt + 1))
        return s

    if len(text) <= max_chunk:
        return one(text)
    parts: list[str] = []
    buf: list[str] = []
    n = 0
    for para in text.split("\n\n"):
        if n + len(para) + 2 > max_chunk and buf:
            parts.append(one("\n\n".join(buf)))
            buf = []
            n = 0
        buf.append(para)
        n += len(para) + 2
    if buf:
        parts.append(one("\n\n".join(buf)))
    return "\n\n".join(parts)


def write_utf8(path: Path, s: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8")


def escape_typst_text(s: str) -> str:
    """read()로 삽입될 때 마크업으로 해석되지 않게 이스케이프."""
    s = s.replace("\\", "\\\\")
    s = s.replace("#", "\\#")
    s = s.replace("[", "\\[")
    s = s.replace("]", "\\]")
    s = s.replace("*", "\\*")
    s = s.replace("_", "\\_")
    s = s.replace("`", "\\`")
    s = s.replace("$", "\\$")
    s = s.replace("@", "\\@")
    # 줄 시작 `:`는 용어 목록 등으로 파싱될 수 있음
    s = re.sub(r"(^|\n):", r"\1\\:", s)
    return s


def build_main_typ(
    pages_dir: Path,
    num_pages: int,
    out_main: Path,
    *,
    title_en: str,
    author_line: str,
) -> None:
    """페이지별 read만 사용(원문 1페이지 레이아웃·제목 유지)."""
    _ = pages_dir, author_line  # API 호환용
    chunks = [
        f'#read("pages/p{i:02d}.txt")' if i == 1 else f'#pagebreak()\n#read("pages/p{i:02d}.txt")'
        for i in range(1, num_pages + 1)
    ]
    body = "\n\n".join(chunks)
    src = f'''// 번역본: {title_en} — C. E. Shannon (1948). 자동 번역 초안; 수식·인용은 검토 권장.
#set page(paper: "a4", margin: (x: 2.0cm, y: 2.2cm))
#set text(
  lang: "ko",
  font: ("Malgun Gothic", "New Computer Modern"),
  size: 10pt,
  hyphenate: false,
  cjk-latin-spacing: auto,
)
#set par(
  justify: false,
  leading: 1.32em,
  spacing: 20pt,
  first-line-indent: 0pt,
  linebreaks: "optimized",
)

{body}
'''
    out_main.parent.mkdir(parents=True, exist_ok=True)
    out_main.write_text(src, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--structure",
        type=Path,
        default=None,
        help="extracted_structure.json",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="output/entropy/src",
    )
    ap.add_argument("--skip-translate", action="store_true", help="영문만 저장")
    args = ap.parse_args()
    root = project_root()
    struct_path = args.structure or (root / "output" / "entropy" / "extracted_structure.json")
    out_src = args.out_dir or (root / "output" / "entropy" / "src")
    pages_dir = out_src / "pages"

    if not struct_path.is_file():
        print(f"Not found: {struct_path}", file=sys.stderr)
        return 1

    structure = json.loads(struct_path.read_text(encoding="utf-8"))
    merged = merge_pages(structure)
    nmax = max(merged.keys())

    for pg in range(1, nmax + 1):
        en = merged.get(pg, "")
        if args.skip_translate:
            ko = en
        else:
            print(f"Translating page {pg}/{nmax} …", flush=True)
            ko = translate_text(en)
            time.sleep(0.4)
        write_utf8(pages_dir / f"p{pg:02d}.txt", escape_typst_text(ko))

    build_main_typ(
        pages_dir,
        nmax,
        out_src / "main.typ",
        title_en="A Mathematical Theory of Communication",
        author_line="C. E. Shannon",
    )

    glossary = {
        "entropy": {"ko": "엔트로피", "context": "정보 이론"},
        "channel capacity": {"ko": "채널 용량", "context": "통신"},
        "noise": {"ko": "잡음", "context": "채널"},
    }
    write_utf8(root / "output" / "entropy" / "glossary.json", json.dumps(glossary, ensure_ascii=False, indent=2))

    print(f"Wrote {nmax} page files → {pages_dir}")
    print(f"main.typ → {out_src / 'main.typ'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
