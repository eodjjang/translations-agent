"""
Typst 조판 검증기: .typ 파일 저장 시 마크업 품질을 자동 검증한다.

검증 항목:
1. 제목 중복 번호 — = / == 뒤에 수동 번호("= 4. 실험")가 있으면 경고
2. 캡션 중복 접두사 — caption 블록 내 "그림 N:" / "표 N:" 패턴 검출
3. 이미지 경로 존재 — image("...") 내 경로가 실제 파일로 존재하는지 확인
4. 수식 짝 검증 — 열린 $ 와 닫힌 $ 의 짝 확인
"""

from __future__ import annotations

import re
from pathlib import Path

HEADING_NUM_PATTERN = re.compile(r"^(=+)\s+\d+[\.\):]", re.MULTILINE)

CAPTION_DUP_PATTERN = re.compile(
    r"caption:\s*\[.*?(?:그림|표|Figure|Table)\s+\d+\s*:", re.IGNORECASE
)

IMAGE_PATH_PATTERN = re.compile(r'image\(\s*"([^"]+)"')


def _find_project_root(typ_path: Path) -> Path:
    p = typ_path.resolve()
    for parent in p.parents:
        if (parent / "input").is_dir() and (parent / "output").is_dir():
            return parent
    return p.parent.parent.parent.parent


def _check_heading_numbers(content: str) -> list[str]:
    matches = HEADING_NUM_PATTERN.findall(content)
    if matches:
        lines = []
        for i, line in enumerate(content.splitlines(), 1):
            if HEADING_NUM_PATTERN.match(line):
                lines.append(f"  L{i}: {line.strip()}")
        count = len(lines)
        sample = "\n".join(lines[:5])
        more = f"\n  ... 외 {count - 5}건" if count > 5 else ""
        return [
            f"제목 중복 번호 — 자동 절번호 사용 시 수동 번호 {count}건 발견. "
            f"중복 표기됩니다:\n{sample}{more}"
        ]
    return []


def _check_caption_duplicates(content: str) -> list[str]:
    matches = CAPTION_DUP_PATTERN.findall(content)
    if matches:
        return [
            f"캡션 중복 접두사 — caption 내부에 '그림/표 N:' 접두사 {len(matches)}건 발견. "
            f"Typst가 자동 부여하므로 중복됩니다."
        ]
    return []


def _check_image_paths(content: str, typ_path: Path) -> list[str]:
    root = _find_project_root(typ_path)
    typ_dir = typ_path.resolve().parent
    missing: list[str] = []

    for match in IMAGE_PATH_PATTERN.finditer(content):
        img_rel = match.group(1)
        candidates = [
            typ_dir / img_rel,
            root / img_rel,
        ]
        if not any(c.exists() for c in candidates):
            missing.append(img_rel)

    if missing:
        sample = missing[:5]
        more = f" 외 {len(missing) - 5}건" if len(missing) > 5 else ""
        return [
            f"이미지 경로 누락 — 파일이 존재하지 않는 경로 {len(missing)}건: "
            + ", ".join(f'"{p}"' for p in sample) + more
        ]
    return []


def _check_math_balance(content: str) -> list[str]:
    """인라인 수식 $...$ 의 열림/닫힘 짝을 검증한다. 블록 수식($$...$$)은 별도 처리."""
    # $$ 블록 수식을 먼저 제거
    stripped = re.sub(r"\$\$[\s\S]*?\$\$", "", content)

    # 코드 블록(```) 내부 제거
    stripped = re.sub(r"```[\s\S]*?```", "", stripped)

    # 남은 $ 개수가 홀수이면 짝이 안 맞음
    dollar_count = stripped.count("$")
    if dollar_count % 2 != 0:
        return [
            f"수식 짝 불일치 — $ 문자가 {dollar_count}개(홀수)입니다. "
            f"열린/닫힌 $가 짝이 맞는지 확인하세요."
        ]
    return []


def validate(file_path: str, hook_input: dict) -> list[str]:
    """
    Typst .typ 파일을 검증하고 오류 목록을 반환한다.
    오류가 없으면 빈 리스트를 반환한다.
    """
    typ_path = Path(file_path).resolve()
    if not typ_path.exists():
        return []

    content = typ_path.read_text(encoding="utf-8")
    if not content.strip():
        return ["Typst 검증 — 파일이 비어 있습니다."]

    errors: list[str] = []
    errors.extend(_check_heading_numbers(content))
    errors.extend(_check_caption_duplicates(content))
    errors.extend(_check_image_paths(content, typ_path))
    errors.extend(_check_math_balance(content))
    return errors
