"""
번역 검증기: .typ 파일 저장 시 번역 품질을 자동 검증한다.

검증 항목:
1. 수식 훼손 — 원문 vs 번역문의 $...$ 패턴 개수 비교
2. 길이 비율 — 원문 대비 0.7~1.2배 범위
3. 용어 일관성 — glossary.json 대비 번역문 내 한국어 용어 출현
4. 구조 대응 — 원문과 번역문의 문단 수 비교
"""

from __future__ import annotations

import json
import re
from pathlib import Path

MATH_PATTERN = re.compile(r"\$[^$]+\$")
LENGTH_RATIO_MIN = 0.7
LENGTH_RATIO_MAX = 1.2


def _find_project_root(typ_path: Path) -> Path:
    """output/{slug}/src/*.typ 에서 프로젝트 루트를 역추적한다."""
    # typ_path = .../output/{slug}/src/something.typ
    # 루트 = typ_path의 output 상위
    p = typ_path.resolve()
    for parent in p.parents:
        if (parent / "input").is_dir() and (parent / "output").is_dir():
            return parent
    return p.parent.parent.parent.parent


def _find_slug(typ_path: Path) -> str | None:
    """output/{slug}/src/*.typ 경로에서 slug를 추출한다."""
    parts = typ_path.resolve().parts
    for i, part in enumerate(parts):
        if part == "output" and i + 2 < len(parts) and parts[i + 2] == "src":
            return parts[i + 1]
    return None


def _load_glossary(root: Path, slug: str) -> dict | None:
    gpath = root / "output" / slug / "glossary.json"
    if gpath.exists():
        try:
            return json.loads(gpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _load_extracted_text(root: Path, slug: str) -> str | None:
    """추출된 원문 텍스트를 찾아 반환한다. assets_manifest 또는 progress에서 원문 참조."""
    manifest = root / "output" / slug / "assets_manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if "extracted_text" in data:
                return data["extracted_text"]
        except (json.JSONDecodeError, OSError):
            pass

    # progress.json에서 원본 파일 경로를 찾아 원문 길이 추정 용도
    progress = root / "output" / slug / "progress.json"
    if progress.exists():
        try:
            pdata = json.loads(progress.read_text(encoding="utf-8"))
            paper = pdata.get("paper", "")
            source = root / "input" / paper
            if source.exists() and source.suffix == ".txt":
                return source.read_text(encoding="utf-8")
        except (json.JSONDecodeError, OSError):
            pass

    return None


def _count_paragraphs(text: str) -> int:
    """비어 있지 않은 문단(빈 줄로 구분) 수를 센다."""
    return len([p for p in text.split("\n\n") if p.strip()])


def validate(file_path: str, hook_input: dict) -> list[str]:
    """
    번역된 .typ 파일을 검증하고 오류 목록을 반환한다.
    오류가 없으면 빈 리스트를 반환한다.
    """
    errors: list[str] = []
    typ_path = Path(file_path).resolve()

    if not typ_path.exists():
        return errors

    translated = typ_path.read_text(encoding="utf-8")
    if not translated.strip():
        errors.append("번역 검증 — 파일이 비어 있습니다.")
        return errors

    root = _find_project_root(typ_path)
    slug = _find_slug(typ_path)
    if not slug:
        return errors

    original = _load_extracted_text(root, slug)

    # --- 1. 수식 훼손 검증 ---
    translated_math = MATH_PATTERN.findall(translated)
    if original:
        original_math = MATH_PATTERN.findall(original)
        if len(original_math) > 0:
            diff = len(original_math) - len(translated_math)
            if diff > 0:
                errors.append(
                    f"수식 훼손 감지 — 원문 $...$ 패턴: {len(original_math)}개, "
                    f"번역문: {len(translated_math)}개 ({diff}개 누락)"
                )
            elif diff < 0:
                errors.append(
                    f"수식 패턴 불일치 — 원문: {len(original_math)}개, "
                    f"번역문: {len(translated_math)}개 ({-diff}개 추가됨, 오탈자 의심)"
                )

    # --- 2. 길이 비율 검증 ---
    if original:
        orig_len = len(original.strip())
        trans_len = len(translated.strip())
        if orig_len > 0:
            ratio = trans_len / orig_len
            if ratio < LENGTH_RATIO_MIN:
                errors.append(
                    f"길이 비율 이상 — 원문 대비 {ratio:.2f}배 (최소 {LENGTH_RATIO_MIN}). "
                    f"번역 누락 의심"
                )
            elif ratio > LENGTH_RATIO_MAX:
                errors.append(
                    f"길이 비율 이상 — 원문 대비 {ratio:.2f}배 (최대 {LENGTH_RATIO_MAX}). "
                    f"번역 중복 의심"
                )

    # --- 3. 용어 일관성 검증 ---
    if slug:
        glossary = _load_glossary(root, slug)
        if glossary:
            missing_terms: list[str] = []
            for eng_term, info in glossary.items():
                ko_term = info.get("ko", "")
                if ko_term and ko_term not in translated and eng_term not in translated:
                    missing_terms.append(f"'{eng_term}' → '{ko_term}'")
            if missing_terms:
                sample = missing_terms[:5]
                more = f" 외 {len(missing_terms) - 5}건" if len(missing_terms) > 5 else ""
                errors.append(
                    f"용어 일관성 — glossary 용어 {len(missing_terms)}개 미사용: "
                    + ", ".join(sample) + more
                )

    # --- 4. 구조 대응 검증 ---
    if original:
        orig_para = _count_paragraphs(original)
        trans_para = _count_paragraphs(translated)
        if orig_para > 0:
            para_ratio = trans_para / orig_para
            if para_ratio < 0.5:
                errors.append(
                    f"구조 대응 — 원문 문단 {orig_para}개 vs 번역문 {trans_para}개. "
                    f"문단 누락 의심"
                )
            elif para_ratio > 2.0:
                errors.append(
                    f"구조 대응 — 원문 문단 {orig_para}개 vs 번역문 {trans_para}개. "
                    f"과도한 문단 분리 의심"
                )

    return errors
