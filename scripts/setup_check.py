"""
첫 실행 환경 점검: Python 패키지, typst CLI, 선택 폰트 디렉터리.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def check_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    root = project_root()
    issues: list[str] = []

    for mod, pip_name in [("fitz", "pymupdf"), ("PIL", "Pillow"), ("requests", "requests")]:
        if not check_module(mod):
            issues.append(f"Python 패키지 누락: {pip_name} (pip install -r scripts/requirements.txt)")

    if not shutil.which("typst"):
        issues.append("typst CLI 없음 (예: winget install typst)")

    fonts_dir = root / "fonts"
    has_font_files = bool(list(fonts_dir.glob("*.ttf")) + list(fonts_dir.glob("*.otf")))
    font_hint = None
    if not has_font_files:
        font_hint = (
            "fonts/ 에 .ttf/.otf가 없습니다. Pretendard 등을 넣거나 main.typ에서 폰트 목록을 조정하세요."
        )

    if issues:
        print("[setup_check] 다음 항목을 확인하세요:\n", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1

    print("[setup_check] Python 패키지 및 typst CLI 확인됨.")
    if font_hint:
        print(f"[setup_check] 참고: {font_hint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
